from typing import Optional, List

import click
from click import style, Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.models import BaseListOptions


def init_namespace_commands(group: Group):
    @formatted_command(
        group=group,
        name='get-default',
        specs=[
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def get_default_namespace(context: Optional[str],
                              endpoint_id: Optional[str]):
        """
        Get the default namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-get-default
        """

        namespace = get_user_client(context, endpoint_id).get_user_config().default_namespace
        click.echo(namespace)

    @formatted_command(
        group=group,
        name='list',
        specs=[
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_namespaces(context: Optional[str],
                        endpoint_id: Optional[str],
                        max_results: Optional[int],
                        page: Optional[int],
                        page_size: Optional[int]):
        """
        List namespaces the authenticated user belongs to

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-list
        """
        client = get_user_client(context, endpoint_id)
        list_options = BaseListOptions(page=page, page_size=page_size)
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=client.list_namespaces(list_options, max_results))

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='namespace_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The namespace id',
                required=True,
                multiple=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_namespace(context: Optional[str],
                           endpoint_id: Optional[str],
                           namespace_id: List[str]):
        """
        Get details for one or more namespaces

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-describe
        """

        if not namespace_id:
            click.echo(style("You must specify at least one namespace ID", fg='red'), err=True, color=True)
            exit(1)

        client = get_user_client(context, endpoint_id)
        namespaces = [client.get_namespace(ns_id) for ns_id in namespace_id]
        click.echo(to_json(normalize(namespaces)))

    @formatted_command(
        group=group,
        name='get-active',
        specs=[
            ArgumentSpec(
                name='id_only',
                arg_names=['--id'],
                help='Only output the namespace ID',
                type=bool,
                required=False,
                default=False,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def get_active_namespace(context: Optional[str],
                             endpoint_id: Optional[str],
                             id_only: bool):
        """
        Get the active namespace
        """

        client = get_user_client(context, endpoint_id)
        namespace = client.get_active_namespace()
        if id_only:
            click.echo(namespace.id)
        else:
            click.echo(to_json(normalize(namespace)))

    @formatted_command(
        group=group,
        name='set-active',
        specs=[
            ArgumentSpec(
                name='namespace_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The namespace id to set as active',
                required=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def set_active_namespace(context: Optional[str],
                             endpoint_id: Optional[str],
                             namespace_id: str):
        """
        Set the active namespace
        """

        client = get_user_client(context, endpoint_id)
        namespace = client.set_active_namespace(namespace_id)
        click.echo(to_json(normalize(namespace)))
