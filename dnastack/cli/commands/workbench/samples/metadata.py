from pathlib import Path
from typing import List, Optional

import click

from dnastack.cli.commands.workbench.utils import get_samples_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.client.workbench.samples.models import MetadataProcessingResponse, ProcessingOutcome

ACCEPTED_SUFFIXES = ('.ped', '.json', '.jsonl', '.zip')

EXIT_NOTHING_APPLIED = 1
EXIT_PARTIALLY_APPLIED = 2


@formatted_group("metadata")
def metadata_command_group():
    """ Upload sample metadata """


def _unreadable_name_error(files: List[Path]) -> Optional[str]:
    for file in files:
        if not file.name.lower().endswith(ACCEPTED_SUFFIXES):
            return (
                f'{file.name} is not a metadata file.\n'
                f'Expected one of: *.ped (pedigree), *.attributes.json (custom attributes), '
                f'*.json or *.jsonl (phenopacket), or a *.zip containing any of them.'
            )
    return None


def _exit_code(response: MetadataProcessingResponse) -> int:
    applied = any(result.sample_ids for result in response.results)
    if not applied:
        return EXIT_NOTHING_APPLIED
    unclean = any(result.errors or result.outcome == ProcessingOutcome.failed for result in response.results)
    return EXIT_PARTIALLY_APPLIED if unclean else 0


@formatted_command(
    group=metadata_command_group,
    name='upload',
    specs=[
        ArgumentSpec(
            name='files',
            arg_type=ArgumentType.POSITIONAL,
            help='The metadata files to upload.',
            required=True,
            nargs=-1,
        ),
        ArgumentSpec(
            name='preserve_existing',
            arg_names=['--preserve-existing'],
            help="Keep existing sex, affected status, family and parentage wherever they are already "
                 "set, and add phenotypes to the sample's existing ones instead of replacing them. "
                 "No effect on attributes, which always replace.",
            type=bool,
            default=False,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def upload_metadata(context: Optional[str],
                    endpoint_id: Optional[str],
                    namespace: Optional[str],
                    files: List[str],
                    preserve_existing: bool = False):
    """
    Upload pedigree, phenopacket or attributes files.

    The file name decides how each file is read. There is no content detection:

      *.ped                pedigree
      *.attributes.json    custom attributes, keyed by sample ID
      *.json  *.jsonl      phenopacket
      *.zip                an archive of any of the above

    So cohort.json is read as a phenopacket and fails as one, even when it holds attributes.
    Rename it cohort.attributes.json.

    An attributes document is keyed by sample ID, and replaces each named sample's attributes
    outright. Anything it omits is deleted:

      {"HG002": {"kit_lot": "A7-2291"}}

    Upload {} for a sample to clear its attributes.

    By default the file's values also replace existing sex, affected status, family and parentage,
    and replace phenotypes rather than adding to them. This is not reversible.

    Every file is reported on its own, and sampleIds lists what was written. A file can write some
    samples and fail others, and files that already succeeded stay written when a later one fails.

    Exit code: 0 every file applied cleanly, 1 nothing was written, 2 partial.

    docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/samples-metadata-upload
    """
    paths = [Path(file) for file in files]
    name_error = _unreadable_name_error(paths)
    if name_error:
        click.secho(name_error, fg='red', err=True)
        raise SystemExit(EXIT_NOTHING_APPLIED)

    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    response = client.upload_metadata(files=paths, preserve_existing=preserve_existing)
    click.echo(to_json(normalize(response)))

    exit_code = _exit_code(response)
    if exit_code == EXIT_NOTHING_APPLIED:
        click.secho('No samples were written.', fg='red', err=True)
    elif exit_code == EXIT_PARTIALLY_APPLIED:
        click.secho('Some files wrote only part of their samples. See errors in the results above.',
                    fg='yellow', err=True)
    if exit_code:
        raise SystemExit(exit_code)
