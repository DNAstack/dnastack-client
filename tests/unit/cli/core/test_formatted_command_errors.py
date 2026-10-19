"""How formatted_command reports errors raised by a command."""
import click
from click.testing import CliRunner

from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.group import formatted_group


def _group_raising(error: Exception):
    @formatted_group('test')
    def group():
        """A test group"""

    @formatted_command(group=group, name='cmd', specs=[])
    def cmd():
        """A test command."""
        raise error

    return group


def _invoke(error: Exception):
    return CliRunner(mix_stderr=False).invoke(_group_raising(error), ['cmd'])


def test_usage_error_is_printed_by_click():
    result = _invoke(click.UsageError('Specify x.'))
    assert result.exit_code == 2
    assert 'Usage:' in result.stderr
    assert 'Error: Specify x.' in result.stderr
    assert 'UsageError:' not in result.stderr


def test_bad_parameter_is_printed_by_click():
    result = _invoke(click.BadParameter('bad', param_hint="'--x'"))
    assert result.exit_code == 2
    assert "Error: Invalid value for '--x': bad" in result.stderr
    assert 'BadParameter:' not in result.stderr


def test_other_errors_keep_their_type_prefix():
    result = _invoke(ValueError('boom'))
    assert result.exit_code == 1
    assert 'ValueError: boom' in result.stderr
