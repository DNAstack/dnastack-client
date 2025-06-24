from unittest.mock import Mock, patch

from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
from tests.cli.base import CliTestCase


class ExplorerCliTestCase(CliTestCase):
    def setUp(self):
        super().setUp()
        # Sample test data
        self.sample_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[
                QuestionParam(
                    name="param1",
                    description="Test parameter",
                    type="string",
                    required=True
                )
            ],
            collections=[
                QuestionCollection(
                    slug="collection1"
                )
            ]
        )

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_list(self, mock_factory):
        """Test explorer questions list command"""
        # Mock the client
        mock_client = Mock()
        mock_client.list_federated_questions.return_value = [self.sample_question]
        mock_factory.return_value = mock_client

        # Run the command
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'list']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.list_federated_questions.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_describe(self, mock_factory):
        """Test explorer questions describe command"""
        # Mock the client
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_factory.return_value = mock_client

        # Run the command
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'describe', 'q1']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.describe_federated_question.assert_called_once_with('q1')

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_ask(self, mock_factory):
        """Test explorer questions ask command"""
        # Mock the client
        mock_client = Mock()
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'col1': 'value1'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_ask_with_args(self, mock_factory):
        """Test explorer questions ask command with arguments"""
        # Mock the client
        mock_client = Mock()
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'col1': 'value1'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with arguments
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--param', 'param1=test_value']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_ask_with_collections(self, mock_factory):
        """Test explorer questions ask command with collections filter"""
        # Mock the client
        mock_client = Mock()
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'col1': 'value1'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with collections
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--collections', 'collection1,collection2']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_explorer_questions_list_json_output(self, mock_factory):
        """Test explorer questions list with JSON output format"""
        # Mock the client
        mock_client = Mock()
        mock_client.list_federated_questions.return_value = [self.sample_question]
        mock_factory.return_value = mock_client

        # Run the command with JSON output
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'list', '--output-format', 'json']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.list_federated_questions.assert_called_once()


class TestExplorerCliFlags(CliTestCase):
    """Test cases for CLI flag changes made during PR review resolution."""

    def setUp(self):
        super().setUp()
        # Sample test data
        self.sample_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[
                QuestionParam(
                    name="param1",
                    description="Test parameter",
                    input_type="string",
                    required=True
                )
            ],
            collections=[
                QuestionCollection(
                    id="collection1",
                    name="Collection 1",
                    slug="collection-1",
                    question_id="q1"
                )
            ]
        )

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_with_param_flag(self, mock_factory):
        """Test that --param flag works for question parameters."""
        # Mock the client
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'result': 'data'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with --param flag
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--param', 'param1=test_value']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_multiple_param_flags(self, mock_factory):
        """Test multiple --param flags are handled correctly."""
        # Add another parameter to the question
        question_with_multiple_params = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[
                QuestionParam(
                    name="param1",
                    description="Test parameter 1",
                    input_type="string",
                    required=True
                ),
                QuestionParam(
                    name="param2",
                    description="Test parameter 2",
                    input_type="string",
                    required=False
                )
            ],
            collections=[
                QuestionCollection(
                    id="collection1",
                    name="Collection 1",
                    slug="collection-1",
                    question_id="q1"
                )
            ]
        )

        # Mock the client
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = question_with_multiple_params
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'result': 'data'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with multiple --param flags
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', 
             '--param', 'param1=value1', '--param', 'param2=value2']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_param_flag_parsing(self, mock_factory):
        """Test parameter parsing with new --param flag."""
        # Mock the client
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([{'result': 'data'}]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with complex parameter value
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', 
             '--param', 'param1=complex_value_with_spaces']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        
        # Verify the client was called with correct parameters
        call_args = mock_client.ask_federated_question.call_args
        inputs = call_args[1]['inputs']
        self.assertEqual(inputs['param1'], 'complex_value_with_spaces')

    def test_ask_question_param_help_text(self):
        """Test that help text shows --param not --arg."""
        # Run help command for ask
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--help']
        )

        # Verify help text contains --param
        self.assertIn('--param', result.output)
        # Verify help text doesn't contain --arg (old flag)
        self.assertNotIn('--arg', result.output)

    @property
    def cli_app(self):
        from dnastack.__main__ import dnastack
        return dnastack


class TestExplorerOutputBehavior(CliTestCase):
    """Test cases for output behavior changes made during PR review resolution."""

    def setUp(self):
        super().setUp()
        # Sample test data
        self.sample_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[],
            collections=[
                QuestionCollection(
                    id="collection1",
                    name="Collection 1",
                    slug="collection-1",
                    question_id="q1"
                )
            ]
        )

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_empty_results_no_echo(self, mock_factory):
        """Test that empty results don't print 'No results returned'."""
        # Mock the client to return empty results
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([]))  # Empty results
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        # Verify the old "No results returned" message is NOT in output
        self.assertNotIn("No results returned from query", result.output)

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_empty_results_json_output(self, mock_factory):
        """Test empty results output as empty JSON array."""
        # Mock the client to return empty results
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([]))  # Empty results
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with JSON output
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--output-format', 'json']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        # Verify output contains empty JSON array
        self.assertIn('[]', result.output)

    @patch('dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory.make')
    def test_ask_question_empty_results_yaml_output(self, mock_factory):
        """Test empty results output as empty YAML list."""
        # Mock the client to return empty results
        mock_client = Mock()
        mock_client.describe_federated_question.return_value = self.sample_question
        mock_result_iterator = Mock()
        mock_result_iterator.__iter__ = Mock(return_value=iter([]))  # Empty results
        mock_client.ask_federated_question.return_value = mock_result_iterator
        mock_factory.return_value = mock_client

        # Run the command with YAML output
        result = self._runner.invoke(
            self.cli_app,
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--output-format', 'yaml']
        )

        # Verify the command executed successfully
        self.assertEqual(result.exit_code, 0)
        # Empty YAML list should be represented as empty or []
        self.assertTrue('[]' in result.output or result.output.strip() == '')

    @property
    def cli_app(self):
        from dnastack.__main__ import dnastack
        return dnastack