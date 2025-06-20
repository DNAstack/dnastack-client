from typing import Optional

from click import Group

from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import (
    CONTEXT_ARG,
    DATA_OUTPUT_ARG,
    SINGLE_ENDPOINT_ID_ARG,
    ArgumentSpec,
    ArgumentType,
)
from dnastack.common.tracing import Span

from .utils import DECIMAL_POINT_OUTPUT_ARG, _get, handle_query


def init_data_connect_commands(group: Group):
    @formatted_command(
        group=group,
        name="query",
        specs=[
            ArgumentSpec(
                name="query",
                arg_type=ArgumentType.POSITIONAL,
                help="The query.",
                required=True,
            ),
            ArgumentSpec(
                name="no_auth",
                arg_names=["--no-auth"],
                help="Skip automatic authentication if set",
                type=bool,
                required=False,
                hidden=True,
            ),
            DATA_OUTPUT_ARG,
            DECIMAL_POINT_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def data_connect_query(
        context: Optional[str],
        endpoint_id: Optional[str],
        query: str,
        output: Optional[str] = None,
        decimal_as: str = "string",
        no_auth: bool = False,
    ):
        """Perform a search query"""
        trace = Span(origin="cli.data_connect.query")
        return handle_query(
            _get(context=context, id=endpoint_id),
            query,
            decimal_as=decimal_as,
            no_auth=no_auth,
            output_format=output,
            trace=trace,
        )
