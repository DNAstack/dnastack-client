from typing import Optional

from click import Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, create_sort_arg, get_samples_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.samples.models import InstrumentListOptions
from dnastack.client.workbench.storage.models import PlatformType


def init_instruments_commands(group: Group):
    """Initialize instrument commands"""

    @formatted_command(
        group=group,
        name="list",
        specs=[
            ArgumentSpec(
                name="platform_type",
                arg_names=["--platform-type"],
                help="Filter the files by the platform type.",
                type=PlatformType,
                choices=[e.value for e in PlatformType],
            ),
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            create_sort_arg('--sort "id:ASC"'),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def list_instruments(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        max_results: Optional[int],
        page: Optional[int],
        page_size: Optional[int],
        sort: Optional[str],
        platform_type: Optional[PlatformType],
    ):
        """
        List instruments.
        """

        client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        options = InstrumentListOptions(page=page, page_size=page_size, sort=sort, platform_type=platform_type)

        instruments_list = client.list_instruments(list_options=options, max_results=max_results)
        show_iterator(output_format=OutputFormat.JSON, iterator=instruments_list)
