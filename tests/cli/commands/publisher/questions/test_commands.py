from unittest.mock import Mock, patch
from click.testing import CliRunner
from dnastack.cli.commands.publisher.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group
from dnastack.client.collections.model import Question, QuestionParameter


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


def test_describe_question_command():
    """Test describe question command"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    mock_question = Question(
        id="variant_lookup",
        name="Variant Lookup",
        description="Look up variants by position",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="chromosome", input_type="STRING", required=True),
            QuestionParameter(name="position", input_type="INTEGER", required=True)
        ]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, [
            'describe',
            'variant_lookup',
            '--collection', 'test-coll'
        ])

    assert result.exit_code == 0
    assert "variant_lookup" in result.output
    assert "Variant Lookup" in result.output
    assert "chromosome" in result.output


def test_describe_question_missing_args():
    """Test describe command without required args"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    result = runner.invoke(test_questions_group, ['describe'])

    assert result.exit_code != 0


def test_ask_question_command():
    """Test ask question command"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    mock_question = Question(
        id="test_q",
        name="Test Q",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="x", input_type="STRING", required=True)
        ]
    )

    mock_results = [
        {"id": "1", "value": "result1"},
        {"id": "2", "value": "result2"}
    ]

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_client.ask_question.return_value = iter(mock_results)
        mock_get_client.return_value = mock_client

        with patch('dnastack.cli.commands.publisher.questions.commands.handle_question_results_output') as mock_output:
            result = runner.invoke(test_questions_group, [
                'ask',
                '--question-name', 'test_q',
                '--collection', 'test-coll',
                '--param', 'x=value1'
            ])

    assert result.exit_code == 0
    mock_output.assert_called_once()


def test_ask_question_missing_required_param():
    """Test ask command fails when required param missing"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    mock_question = Question(
        id="test_q",
        name="Test Q",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="required_param", input_type="STRING", required=True)
        ]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, [
            'ask',
            '--question-name', 'test_q',
            '--collection', 'test-coll'
        ])

    assert result.exit_code != 0
    assert "Missing required parameters" in result.output
