import click
from click.testing import CliRunner

from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, CONTEXT_ARG, MULTIPLE_ENDPOINT_ID_ARG, SINGLE_ENDPOINT_ID_ARG


def _help(specs):
    group = click.Group(name='test')

    @formatted_command(group=group, name='cmd', specs=specs)
    def cmd(**kwargs):
        """A test command."""

    result = CliRunner().invoke(group, ['cmd', '--help'])
    assert result.exit_code == 0, result.output
    return result.output


def test_common_option_listed_after_options_section():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one'), CONTEXT_ARG])
    options_at = output.index('Options:\n')
    common_at = output.index('Common Options:')
    examples_at = output.index('Examples:')
    assert options_at < common_at < examples_at
    options_section = output[options_at:common_at]
    assert '--color' in options_section
    assert '--context' not in options_section
    assert '--context' in output[common_at:examples_at]


def test_no_common_section_without_common_options():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one')])
    assert 'Common Options:' not in output


def test_multiple_endpoint_id_option_listed_as_common_option():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one'), MULTIPLE_ENDPOINT_ID_ARG])
    options_at = output.index('Options:\n')
    common_at = output.index('Common Options:')
    examples_at = output.index('Examples:')
    assert options_at < common_at < examples_at
    assert '--endpoint-id' not in output[options_at:common_at]
    assert '--endpoint-id' in output[common_at:examples_at]


def test_multi_line_docstring_prints_flush():
    group = click.Group(name='test')

    @formatted_command(group=group, name='cmd', specs=[])
    def cmd(**kwargs):
        """
        First line of a long description
        that goes on.
        """

    output = CliRunner().invoke(group, ['cmd', '--help']).output
    assert '\n\nFirst line of a long description\nthat goes on.\n' in output


def test_shared_option_help():
    output = ' '.join(_help([CONTEXT_ARG, MULTIPLE_ENDPOINT_ID_ARG]).split())
    assert 'Defaults to the default context.' in output
    assert 'separated by commas.' in output
    single = ' '.join(_help([SINGLE_ENDPOINT_ID_ARG]).split())
    assert 'The id of the service endpoint to use.' in single
    assert 'If not provided' not in output + single


def test_a_long_option_name_does_not_run_into_its_description():
    long_name = '--' + 'a-very-long-option-name' * 2
    lines = _help([ArgumentSpec(name='long', arg_names=[long_name], help='The description of the long option.')])
    lines = lines.splitlines()
    index = next(i for i, line in enumerate(lines) if line.strip() == long_name)
    assert lines[index + 1].strip() == 'The description of the long option.'


def test_a_short_option_name_shares_a_line_with_its_description():
    lines = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one')]).splitlines()
    assert any(line.split() == ['--color', 'Pick', 'one'] for line in lines)
