from typing import Optional

from dnastack.cli.commands.dataconnect.utils import DECIMAL_POINT_OUTPUT_ARG, _get
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import DATA_OUTPUT_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import show_iterator


@formatted_group("data-connect", aliases=["dc"])
def alpha_data_connect_command_group():
    """Interact with Data Connect Service (testing)"""


@formatted_command(
    group=alpha_data_connect_command_group,
    name="table-data",
    specs=[
        DATA_OUTPUT_ARG,
        DECIMAL_POINT_OUTPUT_ARG,
    ],
)
def get_table_data(
    context: Optional[str],
    endpoint_id: Optional[str],
    table_name: str,
    decimal_as: str = "string",
    no_auth: bool = False,
    output: Optional[str] = None,
):
    """Get data from the given table"""
    table = _get(context=context, id=endpoint_id).table(table_name, no_auth=no_auth)
    show_iterator(output, table.data, decimal_as=decimal_as, sort_keys=False)
