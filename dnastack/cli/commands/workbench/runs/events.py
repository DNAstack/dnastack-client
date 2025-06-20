from typing import Optional

from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_ewes_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator


@formatted_group("events")
def events_command_group():
    """Interact with a run's events"""


@formatted_command(
    group=events_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="run_id",
            arg_names=["--run-id"],
            help="Specify the run whose events should be listed.",
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_run_events(context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str], run_id: str):
    """
    Lists run events
    """

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    show_iterator(output_format=OutputFormat.JSON, iterator=client.list_events(run_id).events)
