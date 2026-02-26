from typing import Optional

import click
from click import Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.models import BaseListOptions
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient


NAMESPACE_ARG = ArgumentSpec(
    name='namespace',
    arg_names=['--namespace', '-n'],
    help='The namespace ID. Defaults to the active namespace.',
    required=False,
)

EMAIL_ARG = ArgumentSpec(
    name='email',
    arg_names=['--email'],
    help='The email address of the user.',
    required=False,
)

USER_ID_ARG = ArgumentSpec(
    name='user_id',
    arg_names=['--id'],
    help='The user ID (UUID).',
    required=False,
)

ROLE_ARG = ArgumentSpec(
    name='role',
    arg_names=['--role'],
    help='The role to assign to the member (e.g. ADMIN).',
    required=True,
)


def resolve_namespace(client: WorkbenchUserClient, namespace: Optional[str]) -> str:
    """Resolve namespace ID, falling back to the user's active namespace."""
    if namespace:
        return namespace
    return client.get_user_config().default_namespace


def _validate_email_or_id(email: Optional[str], user_id: Optional[str]):
    """Validate that exactly one of email or user_id is provided."""
    if email and user_id:
        raise click.UsageError("Specify either --email or --id, not both.")
    if not email and not user_id:
        raise click.UsageError("Specify either --email or --id.")


def init_members_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            NAMESPACE_ARG,
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_members(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     max_results: Optional[int],
                     page: Optional[int],
                     page_size: Optional[int]):
        """
        List members and their roles in a namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-members-list
        """
        client = get_user_client(context, endpoint_id)
        namespace = resolve_namespace(client, namespace)
        list_options = BaseListOptions(page=page, page_size=page_size)
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=client.list_namespace_members(namespace, list_options, max_results))

    @formatted_command(
        group=group,
        name='add',
        specs=[
            NAMESPACE_ARG,
            EMAIL_ARG,
            USER_ID_ARG,
            ROLE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def add_member(context: Optional[str],
                   endpoint_id: Optional[str],
                   namespace: Optional[str],
                   email: Optional[str],
                   user_id: Optional[str],
                   role: str):
        """
        Add a member to a namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-members-add
        """
        _validate_email_or_id(email, user_id)
        client = get_user_client(context, endpoint_id)
        namespace = resolve_namespace(client, namespace)
        member = client.add_namespace_member(namespace, email=email, user_id=user_id, role=role)
        click.echo(to_json(normalize(member)))

    @formatted_command(
        group=group,
        name='remove',
        specs=[
            NAMESPACE_ARG,
            EMAIL_ARG,
            USER_ID_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def remove_member(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      email: Optional[str],
                      user_id: Optional[str]):
        """
        Remove a member from a namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-members-remove
        """
        _validate_email_or_id(email, user_id)
        client = get_user_client(context, endpoint_id)
        namespace = resolve_namespace(client, namespace)
        client.remove_namespace_member(namespace, email=email, user_id=user_id)
