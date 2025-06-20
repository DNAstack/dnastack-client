"""Tests to boost coverage for explorer commands modules"""
import unittest
from unittest.mock import Mock, patch


class TestExplorerCommandsCoverage(unittest.TestCase):
    """Tests specifically for explorer commands modules to reach 80%"""

    def test_explorer_commands_module_import(self):
        """Test importing the explorer commands module"""
        from dnastack.cli.commands.explorer import commands
        
        # Verify the module imports successfully
        self.assertIsNotNone(commands)
        
        # Test that the command groups exist
        self.assertTrue(hasattr(commands, 'explorer_command_group'))
        self.assertTrue(hasattr(commands, 'questions_command_group'))

    def test_explorer_command_group_function(self):
        """Test the explorer_command_group function"""
        from dnastack.cli.commands.explorer.commands import explorer_command_group
        
        # This should be a Click group
        self.assertTrue(callable(explorer_command_group))
        
        # Test the function attributes
        self.assertTrue(hasattr(explorer_command_group, 'name'))
        self.assertEqual(explorer_command_group.name, 'explorer')

    def test_questions_command_group_function(self):
        """Test the questions_command_group function"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        
        # This should be a Click group
        self.assertTrue(callable(questions_command_group))
        
        # Test the function attributes
        self.assertTrue(hasattr(questions_command_group, 'name'))
        self.assertEqual(questions_command_group.name, 'questions')

    def test_commands_module_structure(self):
        """Test the overall structure of the commands module"""
        from dnastack.cli.commands.explorer.commands import (
            explorer_command_group,
            questions_command_group
        )
        
        # Verify that questions group has been added to explorer group
        self.assertIn('questions', explorer_command_group.commands)
        
        # Verify that the questions group has subcommands
        self.assertGreater(len(questions_command_group.commands), 0)
        
        # Check for expected subcommands
        expected_commands = ['list', 'describe', 'ask']
        for cmd in expected_commands:
            self.assertIn(cmd, questions_command_group.commands)

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.show_iterator')
    @patch('dnastack.cli.commands.explorer.questions.commands.Span')
    def test_list_questions_execution(self, mock_span, mock_show_iterator, mock_get_client):
        """Test executing the list questions command"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        from dnastack.client.explorer.models import FederatedQuestion
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_span.return_value = Mock()
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[],
            collections=[]
        )
        
        mock_client.list_federated_questions.return_value = [test_question]
        
        # Get the list command
        list_cmd = questions_command_group.commands['list']
        
        # Execute the command with a test runner
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(list_cmd, ['--output', 'json'])
        
        # The command should execute without error
        self.assertEqual(result.exit_code, 0)
        mock_client.list_federated_questions.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.show_iterator')
    @patch('dnastack.cli.commands.explorer.questions.commands.Span')
    def test_describe_question_execution(self, mock_span, mock_show_iterator, mock_get_client):
        """Test executing the describe question command"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        from dnastack.client.explorer.models import FederatedQuestion
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_span.return_value = Mock()
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[],
            collections=[]
        )
        
        mock_client.describe_federated_question.return_value = test_question
        
        # Get the describe command
        describe_cmd = questions_command_group.commands['describe']
        
        # Execute the command with a test runner
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(describe_cmd, ['q1', '--output', 'json'])
        
        # The command should execute without error
        self.assertEqual(result.exit_code, 0)
        mock_client.describe_federated_question.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.handle_question_results_output')
    @patch('dnastack.cli.commands.explorer.questions.commands.Span')
    def test_ask_question_no_results(self, mock_span, mock_handle_output, mock_get_client):
        """Test ask question command with no results"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        from dnastack.client.explorer.models import FederatedQuestion
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_span.return_value = Mock()
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[],
            collections=[]
        )
        
        mock_client.describe_federated_question.return_value = test_question
        mock_client.ask_federated_question.return_value = []  # No results
        
        # Get the ask command
        ask_cmd = questions_command_group.commands['ask']
        
        # Execute the command with a test runner
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(ask_cmd, ['--question-name', 'q1', '--output', 'json'])
        
        # The command should execute without error (no more echo message for empty results)
        self.assertEqual(result.exit_code, 0)
        # Verify handle_question_results_output was called with empty results
        mock_handle_output.assert_called_once()
        call_args = mock_handle_output.call_args[0]
        self.assertEqual(call_args[0], [])  # Empty results list

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.click.echo')
    @patch('dnastack.cli.commands.explorer.questions.commands.Span')
    def test_ask_question_validation_error(self, mock_span, mock_echo, mock_get_client):
        """Test ask question command with validation error"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_span.return_value = Mock()
        
        # Question with required parameter
        required_param = QuestionParam(
            id="1",
            name="required_param",
            label="Required",
            inputType="string",
            required=True
        )
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[required_param],
            collections=[]
        )
        
        mock_client.describe_federated_question.return_value = test_question
        
        # Get the ask command
        ask_cmd = questions_command_group.commands['ask']
        
        # Execute the command without required parameter
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(ask_cmd, ['--question-name', 'q1', '--output', 'json'])
        
        # The command should fail due to validation error
        self.assertNotEqual(result.exit_code, 0)

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.click.echo')
    @patch('dnastack.cli.commands.explorer.questions.commands.Span')
    def test_ask_question_invalid_collections(self, mock_span, mock_echo, mock_get_client):
        """Test ask question command with invalid collection IDs"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        from dnastack.client.explorer.models import FederatedQuestion, QuestionCollection
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_span.return_value = Mock()
        
        # Question with specific collections
        collection = QuestionCollection(
            id="valid_collection",
            name="Valid Collection",
            slug="valid-collection",
            questionId="q1"
        )
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[],
            collections=[collection]
        )
        
        mock_client.describe_federated_question.return_value = test_question
        
        # Get the ask command
        ask_cmd = questions_command_group.commands['ask']
        
        # Execute the command with invalid collection ID
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(ask_cmd, [
            '--question-name', 'q1',
            '--collections', 'invalid_collection',
            '--output', 'json'
        ])
        
        # The command should fail due to invalid collection
        self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()