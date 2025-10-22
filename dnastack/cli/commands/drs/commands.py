import os
from threading import Lock
from typing import List, Dict, Optional

import click
from click import Group

from dnastack.cli.commands.drs.utils import _get
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.printer import echo_result
from dnastack.client.drs import DownloadOkEvent, DownloadFailureEvent, DownloadProgressEvent
from dnastack.feature_flags import in_interactive_shell


def init_drs_commands(group: Group):
    @formatted_command(
        group=group,
        name='download',
        specs=[
            ArgumentSpec(
                name='id_or_urls',
                arg_type=ArgumentType.POSITIONAL,
                help='DRS IDs or URLs (drs://<host>/<id>)',
                required=False,
                multiple=True,
            ),
            ArgumentSpec(
                name='quiet',
                arg_names=['-q', '--quiet'],
                help='Download files quietly',
                type=bool,
                required=False,
            ),
            ArgumentSpec(
                name='input_file',
                arg_names=['-i', '--input-file'],
                help='Input file',
                required=False,
            ),
            ArgumentSpec(
                name='output_dir',
                arg_names=['-o', '--output-dir'],
                help='Output directory',
                required=False,
            ),
            ArgumentSpec(
                name='no_auth',
                arg_names=['--no-auth'],
                help='Skip automatic authentication if set',
                type=bool,
                required=False,
                hidden=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def download(context: Optional[str],
                 endpoint_id: str,
                 id_or_urls: List[str],
                 output_dir: str = os.getcwd(),
                 input_file: str = None,
                 quiet: bool = False,
                 no_auth: bool = False):
        """
        Download files with either DRS IDs or URLs, e.g., drs://<hostname>/<drs_id>.

        You can find out more about DRS URLs from the Data Repository Service Specification 1.1.0 at
        https://ga4gh.github.io/data-repository-service-schemas/preview/release/drs-1.1.0/docs/#_drs_uris.
        """
        output_lock = Lock()
        download_urls = []
        full_output = not quiet and in_interactive_shell

        if not output_dir:
            output_dir = os.getcwd()

        if len(id_or_urls) > 0:
            download_urls = list(id_or_urls)
        elif input_file:
            with open(input_file, "r") as infile:
                download_urls = filter(None, infile.read().split("\n"))  # need to filter out invalid values
        else:
            if in_interactive_shell:
                click.echo("Enter one or more URLs. Press q to quit")

            while True:
                try:
                    url = click.prompt("", prompt_suffix="", type=str)
                    url = url.strip()
                    if url[0] == "q" or len(url) == 0:
                        break
                except click.Abort:
                    break

                download_urls.append(url)

        drs = _get(context, endpoint_id)

        def display_ok(event: DownloadOkEvent):
            with output_lock:
                if full_output:
                    print()
                echo_result(None, 'green', 'complete', event.drs_url)
                if event.output_file_path:
                    click.secho(f' → Saved as {event.output_file_path}', dim=True)

        def display_failure(event: DownloadFailureEvent):
            with output_lock:
                if not quiet:
                    print()
                echo_result(None, 'red', 'failed', event.drs_url)
                if event.reason:
                    click.secho(f' ● Reason: {event.reason}', dim=True)
                if event.error:
                    click.secho(f' ● Error: {type(event.error).__name__}: {event.error}', dim=True)

        drs.events.on('download-ok', display_ok)
        drs.events.on('download-failure', display_failure)

        stats: Dict[str, DownloadProgressEvent] = {}

        if not full_output:
            drs._download_files(id_or_urls=download_urls,
                                output_dir=output_dir,
                                no_auth=no_auth)
        else:
            with click.progressbar(label='Downloading...', color=True, length=1) as progress:
                def update_progress(event: DownloadProgressEvent):
                    stats[event.drs_url] = event

                    # Update the progress bar.
                    position = 0
                    total = 0

                    for e in stats.values():
                        position += e.read_byte_count
                        total += e.total_byte_count

                    progress.pos = position
                    progress.length = total if total > 0 else 1

                    progress.render_progress()

                drs.events.on('download-progress', update_progress)
                drs._download_files(id_or_urls=download_urls,
                                    output_dir=output_dir,
                                    no_auth=no_auth)
            print('DONE')
