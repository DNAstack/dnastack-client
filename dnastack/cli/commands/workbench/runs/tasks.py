from typing import Optional

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_ewes_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.ewes.models import TaskListOptions


@formatted_group("tasks")
def tasks_command_group():
    """Interact with a run's tasks"""


@formatted_command(
    group=tasks_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="run",
            arg_names=["--run"],
            help="Specify the run ID to list tasks for.",
            required=True,
        ),
        NAMESPACE_ARG,
        MAX_RESULTS_ARG,
        PAGINATION_PAGE_ARG,
        PAGINATION_PAGE_SIZE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_tasks(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    max_results: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    run: str,
):
    """
    List tasks for a run

    docs: https://docs.omics.ai/docs/runs-tasks-list
    """
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options = TaskListOptions(page=page, page_size=page_size)
    show_iterator(output_format=OutputFormat.JSON, iterator=client.list_tasks(run, list_options, max_results))
