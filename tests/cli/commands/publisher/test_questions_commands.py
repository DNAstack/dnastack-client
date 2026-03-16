from unittest.mock import Mock, patch
from click.testing import CliRunner
from dnastack.cli.commands.publisher.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group
from dnastack.client.collections.model import Question


@formatted_group("test_questions")
def test_questions_group():
    """Test questions command group"""
    pass


def test_list_questions_command():
    """Test list questions command"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    mock_question = Question(
        id="q1",
        name="Test Question",
        collection_id="coll1",
        parameters=[]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.list_questions.return_value = [mock_question]
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, ['list', '--collection', 'test-coll'])

    assert result.exit_code == 0
    assert "q1" in result.output
    assert "Test Question" in result.output


def test_list_questions_missing_collection():
    """Test list questions command without collection flag"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    result = runner.invoke(test_questions_group, ['list'])

    assert result.exit_code != 0
    assert "collection" in result.output.lower() or "required" in result.output.lower()
