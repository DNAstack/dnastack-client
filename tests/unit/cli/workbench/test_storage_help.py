"""Unit tests for the storage add and update help texts."""
import click
import pytest

from dnastack.cli.commands.workbench.storage import storage_command_group


@pytest.mark.parametrize('verb', ['add', 'update'])
@pytest.mark.parametrize('storage_type', ['aws', 'gcp', 'azure'])
def test_every_storage_option_help_ends_with_a_period(verb, storage_type):
    command = storage_command_group.commands[verb].commands[storage_type]
    for param in command.params:
        if isinstance(param, click.Option) and param.help:
            assert param.help.endswith('.'), f'{verb} {storage_type} {param.opts}: {param.help!r}'
