from click.testing import CliRunner
import click

from dnastack.cli.core.command_spec import ArgumentSpec
from dnastack.cli.core.command import formatted_command


def test_argument_spec_hidden_field_defaults_to_false():
    """ArgumentSpec.hidden should default to False."""
    spec = ArgumentSpec(name='test_arg', arg_names=['--test'])
    assert spec.hidden is False


def test_argument_spec_hidden_field_can_be_set_true():
    """ArgumentSpec.hidden can be set to True."""
    spec = ArgumentSpec(name='test_arg', arg_names=['--test'], hidden=True)
    assert spec.hidden is True


def test_hidden_option_not_in_help_output():
    """A hidden option should not appear in --help output."""
    group = click.Group(name='test')

    @formatted_command(
        group=group,
        name='cmd',
        specs=[
            ArgumentSpec(
                name='visible_flag',
                arg_names=['--visible'],
                help='This should be visible',
                type=bool,
            ),
            ArgumentSpec(
                name='hidden_flag',
                arg_names=['--hidden'],
                help='This should NOT be visible',
                type=bool,
                hidden=True,
            ),
        ]
    )
    def cmd(visible_flag: bool = False, hidden_flag: bool = False):
        """A test command."""
        click.echo(f"visible={visible_flag} hidden={hidden_flag}")

    runner = CliRunner()
    result = runner.invoke(group, ['cmd', '--help'])
    assert '--visible' in result.output
    assert '--hidden' not in result.output


def test_hidden_option_still_works():
    """A hidden option should still be usable even though it's not in --help."""
    group = click.Group(name='test')

    @formatted_command(
        group=group,
        name='cmd',
        specs=[
            ArgumentSpec(
                name='hidden_flag',
                arg_names=['--hidden'],
                help='This should NOT be visible',
                type=bool,
                hidden=True,
            ),
        ]
    )
    def cmd(hidden_flag: bool = False):
        """A test command."""
        click.echo(f"hidden={hidden_flag}")

    runner = CliRunner()
    result = runner.invoke(group, ['cmd', '--hidden'])
    assert result.exit_code == 0
    assert 'hidden=True' in result.output
