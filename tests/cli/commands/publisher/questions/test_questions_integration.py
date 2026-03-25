from click.testing import CliRunner
from dnastack.cli.commands.publisher import publisher_command_group


def test_questions_group_registered():
    """Test questions command group is registered under publisher"""
    runner = CliRunner()

    result = runner.invoke(publisher_command_group, ['questions', '--help'])

    assert result.exit_code == 0
    assert "questions" in result.output.lower()
    assert "list" in result.output
    assert "describe" in result.output
    assert "ask" in result.output


def test_questions_list_available():
    """Test list command is available"""
    runner = CliRunner()

    result = runner.invoke(publisher_command_group, ['questions', 'list', '--help'])

    assert result.exit_code == 0
    assert "collection" in result.output.lower()
