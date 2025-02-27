from typing import Optional

from click import Group

from dnastack.cli.commands.publisher.datasources.utils import _get_datasource_client, _filter_datasource_fields
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import RESOURCE_OUTPUT_ARG, ArgumentSpec
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.tracing import Span

TYPE_ARG = ArgumentSpec(
    name='type',
    arg_names=['--type'],
    help='Filter datasources by type (e.g., "AWS")',
    required=False
)

def init_datasources_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            RESOURCE_OUTPUT_ARG,
            TYPE_ARG,
        ]
    )
    def list_datasources(output: Optional[str] = None, type: Optional[str] = None):
        """ List all data sources """
        with Span("list_datasources") as span:
            client = _get_datasource_client()
            response = client.list_datasources(trace=span, type=type)

            show_iterator(output,
                        [
                            _filter_datasource_fields(datasource.dict())
                            for datasource in response.connections
                        ])
