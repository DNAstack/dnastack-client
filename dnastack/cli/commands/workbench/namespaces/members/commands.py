from typing import Optional

from click import Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.models import BaseListOptions


def init_members_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            ArgumentSpec(
                name='namespace',
                arg_names=['--namespace', '-n'],
                help='The namespace ID to list members for.',
                required=True,
            ),
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_members(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: str,
                     max_results: Optional[int],
                     page: Optional[int],
                     page_size: Optional[int]):
        """
        List members and their roles in a namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-members-list
        """
        client = get_user_client(context, endpoint_id)
        list_options = BaseListOptions(page=page, page_size=page_size)
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=client.list_namespace_members(namespace, list_options, max_results))
