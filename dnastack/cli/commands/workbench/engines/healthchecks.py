from typing import Optional

from dnastack.cli.commands.utils import MAX_RESULTS_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_ewes_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.ewes.models import CheckType, EngineHealthCheckListOptions, Outcome


@formatted_group("health-checks")
def engine_healthchecks_command_group():
    """List engine health-checks"""


@formatted_command(
    group=engine_healthchecks_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="engine_id",
            arg_names=["--engine"],
            help="Specify the engine whose health checks should be listed.",
            required=True,
        ),
        ArgumentSpec(
            name="outcome",
            arg_names=["--outcome"],
            help="Specify the expected health outcome of the check.",
            type=Outcome,
            choices=[e.value for e in Outcome],
        ),
        ArgumentSpec(
            name="check_type",
            arg_names=["--check-type"],
            help="Specify the kind of check.",
            type=CheckType,
            choices=[e.value for e in CheckType],
        ),
        NAMESPACE_ARG,
        MAX_RESULTS_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_engine_health_checks(
    context: Optional[str],
    endpoint_id: Optional[str],
    outcome: Optional[Outcome],
    check_type: Optional[CheckType],
    namespace: Optional[str],
    max_results: Optional[int],
    engine_id: str,
):
    """
    Lists engine health checks
    """

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options: EngineHealthCheckListOptions = EngineHealthCheckListOptions(
        outcome=outcome,
        check_type=check_type,
    )
    show_iterator(
        output_format=OutputFormat.JSON, iterator=client.list_engine_health_checks(engine_id, list_options, max_results)
    )
