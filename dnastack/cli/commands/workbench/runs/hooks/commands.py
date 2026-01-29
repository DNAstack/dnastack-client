from typing import Optional

import click

from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat


def init_hooks_commands(group):

    @formatted_command(
        group=group,
        name='list',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_names=['--run-id'],
                help='Specify the run whose hooks should be listed.',
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_hooks(context: Optional[str],
                   endpoint_id: Optional[str],
                   namespace: Optional[str],
                   run_id: str):
        """
        List hooks for a run
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        response = client.list_hooks(run_id)
        show_iterator(output_format=OutputFormat.JSON, iterator=response.hooks or [])

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='hook_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The hook ID to describe.',
                required=True,
            ),
            ArgumentSpec(
                name='run_id',
                arg_names=['--run-id'],
                help='Specify the run the hook belongs to.',
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_hook(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      run_id: str,
                      hook_id: str):
        """
        Describe a specific hook for a run
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        hook = client.get_hook(run_id, hook_id)
        click.echo(to_json(normalize(hook)))