import json
from unittest.mock import Mock, patch, MagicMock

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
            ['explorer', 'questions', 'ask', '--question-name', 'q1', '--arg', 'param1=test_value']
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

    @property
    def cli_app(self):
        from dnastack.__main__ import dnastack
        return dnastack