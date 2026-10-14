import click
from click.testing import CliRunner

from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec

TITLE = 'Required Options (unless given in --config):'


def _group(specs, **kwargs):
    group = click.Group(name='test')

    @formatted_command(group=group, name='cmd', specs=specs, **kwargs)
    def cmd(**values):
        """A test command."""
        click.echo(f'ran with {values}')

    return group


def _help(specs, **kwargs):
    result = CliRunner().invoke(_group(specs, **kwargs), ['cmd', '--help'])
    assert result.exit_code == 0, result.output
    return result.output


def test_display_required_option_listed_under_the_custom_heading():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one', display_required=True),
                    ArgumentSpec(name='size', arg_names=['--size'], help='Pick a size')],
                   required_section_title=TITLE)
    required_at = output.index(TITLE)
    options_at = output.index('\nOptions:\n')
    examples_at = output.index('Examples:')
    assert required_at < options_at < examples_at
    assert '--color' in output[required_at:options_at]
    assert '--color' not in output[options_at:examples_at]
    assert '--size' in output[options_at:examples_at]
    assert '(Required)' not in output
    assert 'Required Options:' not in output
    assert 'REQUIRED_OPTIONS' in output.splitlines()[0]


def test_display_required_option_uses_the_default_heading_without_a_title():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one', display_required=True)])
    assert 'Required Options:' in output
    assert '(Required)' not in output


def test_click_required_option_keeps_its_required_suffix():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one', required=True)],
                   required_section_title=TITLE)
    assert TITLE in output
    assert '(Required)' in output


def test_display_required_option_is_not_enforced_by_click():
    specs = [ArgumentSpec(name='color', arg_names=['--color'], help='Pick one', display_required=True)]
    result = CliRunner().invoke(_group(specs, required_section_title=TITLE), ['cmd'])
    assert result.exit_code == 0, result.output
    assert "ran with {'color': None}" in result.output


def test_no_required_section_without_required_options():
    output = _help([ArgumentSpec(name='color', arg_names=['--color'], help='Pick one')],
                   required_section_title=TITLE)
    assert TITLE not in output
    assert 'Required Options' not in output
    assert 'REQUIRED_OPTIONS' not in output
    assert 'Options:' in output


def test_example_value_replaces_value_in_the_examples_line():
    output = _help([ArgumentSpec(name='x', arg_names=['--x'], help='A path', required=True, example_value='@PATH'),
                    ArgumentSpec(name='y', arg_names=['--y'], help='A thing', required=True)])
    examples = output.split('Examples:')[1]
    assert '--x @PATH' in examples
    assert '--x VALUE' not in examples
    assert '--y VALUE' in examples
