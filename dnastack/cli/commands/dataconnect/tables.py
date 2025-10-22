from typing import Optional

import click

from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import RESOURCE_OUTPUT_ARG, ArgumentSpec, ArgumentType, CONTEXT_ARG, \
    SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from .utils import _get
from ...helpers.exporter import to_json, to_yaml
from ...helpers.iterator_printer import show_iterator


@formatted_group("tables")
def tables_command_group():
    """ Table API commands """


@formatted_command(
    group=tables_command_group,
    name='list',
    specs=[
        ArgumentSpec(
            name='no_auth',
            arg_names=['--no-auth'],
            help='Skip automatic authentication if set',
            type=bool,
            required=False,
            hidden=True,
        ),
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def list_tables(context: Optional[str],
                endpoint_id: Optional[str],
                no_auth: bool = False,
                output: Optional[str] = None):
    """ List all accessible tables """
    show_iterator(output, _get(context=context, id=endpoint_id).iterate_tables(no_auth=no_auth))


@formatted_command(
    group=tables_command_group,
    name='get',
    specs=[
        ArgumentSpec(
            name='table_name',
            arg_type=ArgumentType.POSITIONAL,
            help='The table name.',
            required=True,
        ),
        ArgumentSpec(
            name='no_auth',
            arg_names=['--no-auth'],
            help='Skip automatic authentication if set',
            type=bool,
            required=False,
            hidden=True,
        ),
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def get_table_info(context: Optional[str],
                   endpoint_id: Optional[str],
                   table_name: str,
                   no_auth: bool = False,
                   output: Optional[str] = None):
    """ Get info from the given table """
    obj = _get(context=context, id=endpoint_id).table(table_name, no_auth=no_auth).info.model_dump()
    click.echo((to_json if output == 'json' else to_yaml)(obj))
