from typing import List, Optional

import click
from click import Group, style

from dnastack.cli.commands.utils import MAX_RESULTS_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_ewes_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.ewes.models import ExecutionEngineListOptions


def init_engines_commands(group: Group):
    """Initialize engine commands"""

    @formatted_command(
        group=group,
        name="list",
        specs=[
            MAX_RESULTS_ARG,
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def list_engines(
        context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str], max_results: Optional[int]
    ):
        """List engines"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        list_options: ExecutionEngineListOptions = ExecutionEngineListOptions()
        show_iterator(output_format=OutputFormat.JSON, iterator=client.list_engines(list_options, max_results))

    @formatted_command(
        group=group,
        name="describe",
        specs=[
            ArgumentSpec(
                name="engine_id", arg_type=ArgumentType.POSITIONAL, help="The engine id.", required=True, multiple=True
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def describe_engines(
        context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str], engine_id: List[str]
    ):
        """Describe one or more engines"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

        if not engine_id:
            click.echo(style("You must specify at least one engine ID", fg="red"), err=True, color=True)
            exit(1)

        described_engines = [client.get_engine(engine_id=engine) for engine in engine_id]
        click.echo(to_json(normalize(described_engines)))
