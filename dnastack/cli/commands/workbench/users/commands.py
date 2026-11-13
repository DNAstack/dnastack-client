from typing import List, Optional

import click
from click import Group

from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize


def _require_email_address(email: str):
    """Reject a value with no text on both sides of an '@' before it reaches the server."""
    local_part, at, domain = email.rpartition('@')
    if not (at and local_part.strip() and domain.strip()):
        raise click.BadParameter(f"'{email}' is not an email address.", param_hint="'--email'")


def init_users_commands(group: Group):
    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='email_or_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The email address or user ID (UUID) of the user.',
                required=True,
                multiple=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_users(context: Optional[str],
                       endpoint_id: Optional[str],
                       email_or_id: List[str]):
        """
        Get details for one or more users

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/users-describe
        """
        client = get_user_client(context, endpoint_id)
        users = [client.get_user(user) for user in email_or_id]
        click.echo(to_json(normalize(users)))

    @formatted_command(
        group=group,
        name='register',
        specs=[
            ArgumentSpec(
                name='email',
                arg_names=['--email'],
                help='The email address of the user to register. Takes one email; if --email is repeated, '
                     'only the last one is registered.',
                required=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def register_user(context: Optional[str],
                      endpoint_id: Optional[str],
                      email: str):
        """
        Register a user by email

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/users-register
        """
        _require_email_address(email)
        client = get_user_client(context, endpoint_id)
        user = client.register_user(email)
        click.echo(to_json(normalize(user)))
