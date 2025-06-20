import unittest
from unittest.mock import Mock, patch

from dnastack.cli.commands.explorer.questions.commands import (
    list_federated_questions,
    describe_federated_question,
    ask_federated_question
)


class TestExplorerCommandsSimple(unittest.TestCase):
    """Simple tests for Explorer CLI commands to improve coverage"""

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.print_formatted_result')
    def test_list_federated_questions_function(self, mock_print, mock_get_client):
        """Test the list_federated_questions function directly"""
        # Mock client
        mock_client = Mock()
        mock_client.list_federated_questions.return_value = []
        mock_get_client.return_value = mock_client
        
        # Call function
        list_federated_questions(
            context=None,
            endpoint_id=None,
            output_format='json',
            trace=None
        )
        
        # Verify calls
        mock_get_client.assert_called_once()
        mock_client.list_federated_questions.assert_called_once()
        mock_print.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.print_formatted_result')
    def test_describe_federated_question_function(self, mock_print, mock_get_client):
        """Test the describe_federated_question function directly"""
        # Mock client
        mock_client = Mock()
        mock_question = Mock()
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Call function
        describe_federated_question(
            question_id='test_id',
            context=None,
            endpoint_id=None,
            output_format='json',
            trace=None
        )
        
        # Verify calls
        mock_get_client.assert_called_once()
        mock_client.describe_federated_question.assert_called_once_with('test_id')
        mock_print.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.export_to_file')
    @patch('dnastack.cli.commands.explorer.questions.commands.print_formatted_result')
    def test_ask_federated_question_function(self, mock_print, mock_export, mock_get_client):
        """Test the ask_federated_question function directly"""
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([{'col1': 'value1'}]))
        mock_client.ask_federated_question.return_value = mock_result
        mock_get_client.return_value = mock_client
        
        # Call function
        ask_federated_question(
            question_name='test_question',
            args=None,
            collections=None,
            output_file=None,
            output_format='json',
            context=None,
            endpoint_id=None,
            trace=None
        )
        
        # Verify calls
        mock_get_client.assert_called_once()
        mock_client.ask_federated_question.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.export_to_file')
    @patch('dnastack.cli.commands.explorer.questions.commands.print_formatted_result')
    def test_ask_federated_question_with_args(self, mock_print, mock_export, mock_get_client):
        """Test ask_federated_question with arguments"""
        # Mock client
        mock_client = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([{'col1': 'value1'}]))
        mock_client.ask_federated_question.return_value = mock_result
        mock_get_client.return_value = mock_client
        
        # Call function with arguments
        ask_federated_question(
            question_name='test_question',
            args=[{'key': 'param1', 'value': 'test_value'}],
            collections='collection1,collection2',
            output_file='/tmp/test.csv',
            output_format='csv',
            context='test_context',
            endpoint_id='test_endpoint',
            trace=None
        )
        
        # Verify calls
        mock_get_client.assert_called_once()
        mock_client.ask_federated_question.assert_called_once()


if __name__ == '__main__':
    unittest.main()