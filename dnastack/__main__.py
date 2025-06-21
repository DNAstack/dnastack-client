import sys
from typing import Optional

import click

from dnastack.alpha.cli.commands import alpha_command_group
from dnastack.cli.commands.auth import auth_command_group
from dnastack.cli.commands.collections import collections_command_group
from dnastack.cli.commands.config import config_command_group
from dnastack.cli.commands.config.contexts import contexts_command_group, ContextCommandHandler
from dnastack.cli.commands.dataconnect import data_connect_command_group
from dnastack.cli.commands.drs import drs_command_group
from dnastack.cli.commands.explorer.commands import explorer_command_group
from dnastack.cli.commands.publisher import publisher_command_group
from dnastack.cli.commands.workbench import workbench_command_group
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType
from dnastack.cli.core.group import formatted_group
from dnastack.common.logger import get_logger
from dnastack.constants import __version__

APP_NAME = sys.argv[0]

__library_version = __version__
__python_version = str(sys.version).replace("\n", " ")
__app_signature = f'{APP_NAME} {__library_version} with Python {__python_version}'

_context_command_handler = ContextCommandHandler()


@formatted_group(APP_NAME)
@click.version_option(__version__, message="%(version)s")
def dnastack():
    """
    DNAstack Client CLI

    https://dnastack.com
    """
    get_logger(APP_NAME).debug(__app_signature)


@formatted_command(
    group=dnastack,
    name='version',
    specs=[]
)
def version():
    """ Show the version of CLI/library """
    click.echo(__app_signature)


@formatted_command(
    group=dnastack,
    name='use',
    specs=[
        ArgumentSpec(
            name='registry_hostname_or_url',
            arg_type=ArgumentType.POSITIONAL,
            help='The hostname or URL.',
            required=True,
        ),
        ArgumentSpec(
            name='context_name',
            arg_names=['--name'],
            help='Context name -- default to hostname'
        ),
        ArgumentSpec(
            name='no_auth',
            arg_names=['--no-auth'],
            help='Skip automatic authentication if set',
            type=bool,
            required=False,
            hidden=True,
        )
    ]
)
def use(registry_hostname_or_url: str,
        context_name: Optional[str] = None,
        no_auth: bool = False):
    """
    Import a configuration from host's service registry (if available) or the corresponding public configuration from
    cloud storage. If "--no-auth" is not defined, it will automatically initiate all authentication.

    This will also switch the default context to the given hostname.

    This is a shortcut to dnastack config contexts use".
    """
    _context_command_handler.use(registry_hostname_or_url, context_name=context_name, no_auth=no_auth)


# noinspection PyTypeChecker
dnastack.add_command(data_connect_command_group)
# noinspection PyTypeChecker
dnastack.add_command(config_command_group)
# noinspection PyTypeChecker
dnastack.add_command(drs_command_group)
# noinspection PyTypeChecker
dnastack.add_command(auth_command_group)
# noinspection PyTypeChecker
dnastack.add_command(collections_command_group)
# noinspection PyTypeChecker
dnastack.add_command(contexts_command_group)
# noinspection PyTypeChecker
dnastack.add_command(alpha_command_group)
# noinspection PyTypeChecker
dnastack.add_command(publisher_command_group)
# noinspection PyTypeChecker
dnastack.add_command(workbench_command_group)

# noinspection PyTypeChecker
dnastack.add_command(explorer_command_group)


if __name__ == "__main__":
    dnastack.main(prog_name=APP_NAME)
