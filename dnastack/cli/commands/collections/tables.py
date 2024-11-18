from typing import Optional

import click

from dnastack.cli.commands.collections.utils import COLLECTION_ID_CLI_ARG, _switch_to_data_connect, _get_context, _get
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import RESOURCE_OUTPUT_ARG, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json, to_yaml
from dnastack.cli.helpers.iterator_printer import show_iterator


@formatted_group("tables")
def tables_command_group():
    """ Data Client API for Collections """


@formatted_command(
    group=tables_command_group,
    name='list',
    specs=[
        COLLECTION_ID_CLI_ARG,
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def list_tables(context: Optional[str],
                endpoint_id: Optional[str],
                collection: Optional[str],
                no_auth: bool = False,
                output: Optional[str] = None):
    """ List all accessible tables """
    client = _switch_to_data_connect(_get_context(context), _get(context, endpoint_id), collection, no_auth=no_auth)
    show_iterator(output, client.iterate_tables(no_auth=no_auth))


@formatted_command(
    group=tables_command_group,
    name='get',
    specs=[
        COLLECTION_ID_CLI_ARG,
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def get_table_info(context: Optional[str],
                   endpoint_id: Optional[str],
                   collection: Optional[str],
                   table_name: str,
                   no_auth: bool = False,
                   output: Optional[str] = None):
    """ List all accessible tables """
    client = _switch_to_data_connect(_get_context(context), _get(context, endpoint_id), collection, no_auth=no_auth)
    obj = client.table(table_name, no_auth=no_auth).info
    click.echo((to_json if output == 'json' else to_yaml)(obj.dict()))