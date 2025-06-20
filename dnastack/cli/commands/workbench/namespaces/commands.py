from typing import Optional

import click
from click import Group

from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG


def init_namespace_commands(group: Group):
    @formatted_command(
        group=group,
        name="get-default",
        specs=[
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def get_default_namespace(context: Optional[str], endpoint_id: Optional[str]):
        """
        Get the default namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-get-default
        """

        namespace = get_user_client(context, endpoint_id).get_user_config().default_namespace
        click.echo(namespace)
