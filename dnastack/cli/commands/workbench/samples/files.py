from typing import Optional

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, create_sort_arg, get_samples_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.samples.models import SampleFilesListOptions
from dnastack.client.workbench.storage.models import PlatformType


@formatted_group("files")
def files_command_group():
    """Interact with files"""


@formatted_command(
    group=files_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="sample_id",
            arg_names=["--sample"],
            help="The ID of the sample for which the files will be listed.",
            required=True,
        ),
        ArgumentSpec(
            name="storage",
            arg_names=["--storage"],
            help="Filter the files by their storage account.",
        ),
        ArgumentSpec(
            name="instrument_id",
            arg_names=["--instrument"],
            help="Filter the files by the instrument ID that generated them.",
        ),
        ArgumentSpec(
            name="platform_type",
            arg_names=["--platform-type"],
            help="Filter the files by the platform type.",
            type=PlatformType,
            choices=[e.value for e in PlatformType],
        ),
        ArgumentSpec(
            name="search",
            arg_names=["--search"],
            help="Filter the files by a search term.",
        ),
        NAMESPACE_ARG,
        MAX_RESULTS_ARG,
        PAGINATION_PAGE_ARG,
        PAGINATION_PAGE_SIZE_ARG,
        create_sort_arg('--sort "path:ASC"'),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_sample_files(
    context: Optional[str],
    endpoint_id: Optional[str],
    sample_id: str,
    namespace: Optional[str],
    max_results: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    sort: Optional[str],
    storage: Optional[str],
    instrument_id: Optional[str],
    platform_type: Optional[PlatformType],
    search: Optional[str],
):
    """
    List files for a given sample.
    """

    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    options = SampleFilesListOptions(
        page=page,
        page_size=page_size,
        sort=sort,
        storage_id=storage,
        platform_type=platform_type,
        instrument_id=instrument_id,
        search=search,
    )

    files_list = client.list_sample_files(sample_id=sample_id, list_options=options, max_results=max_results)
    show_iterator(output_format=OutputFormat.JSON, iterator=files_list)
