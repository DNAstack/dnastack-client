from unittest.mock import Mock, patch
import pytest
from dnastack.cli.commands.publisher.questions.utils import (
    get_collection_service_client,
    validate_question_parameters,
    handle_question_results_output
)
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.collections.model import Question, QuestionParameter


class TestGetCollectionServiceClient:
    """Tests for get_collection_service_client utility"""

    def test_get_collection_service_client_no_args(self):
        """Test get_collection_service_client with no arguments"""
        with patch('dnastack.cli.commands.publisher.questions.utils.container') as mock_container:
            mock_factory = Mock()
            mock_client = Mock(spec=CollectionServiceClient)
            mock_factory.get.return_value = mock_client
            mock_container.get.return_value = mock_factory

            client = get_collection_service_client()

            assert client == mock_client
            mock_factory.get.assert_called_once_with(
                CollectionServiceClient,
                context_name=None,
                endpoint_id=None
            )

    def test_get_collection_service_client_with_context(self):
        """Test get_collection_service_client with context"""
        with patch('dnastack.cli.commands.publisher.questions.utils.container') as mock_container:
            mock_factory = Mock()
            mock_client = Mock(spec=CollectionServiceClient)
            mock_factory.get.return_value = mock_client
            mock_container.get.return_value = mock_factory

            client = get_collection_service_client(context="test-ctx", endpoint_id="ep1")

            assert client == mock_client
            mock_factory.get.assert_called_once_with(
                CollectionServiceClient,
                context_name="test-ctx",
                endpoint_id="ep1"
            )


class TestValidateQuestionParameters:
    """Tests for validate_question_parameters utility"""

    def test_validate_question_parameters_all_present(self):
        """Test validation passes when all required params present"""
        question = Question(
            id="q1",
            name="Test",
            collection_id="c1",
            parameters=[
                QuestionParameter(name="x", input_type="STRING", required=True),
                QuestionParameter(name="y", input_type="STRING", required=False)
            ]
        )

        inputs = {"x": "value1", "y": "value2"}

        result = validate_question_parameters(inputs, question)

        assert result == inputs

    def test_validate_question_parameters_missing_required(self):
        """Test validation fails when required param missing"""
        question = Question(
            id="q1",
            name="Test",
            collection_id="c1",
            parameters=[
                QuestionParameter(name="req1", input_type="STRING", required=True),
                QuestionParameter(name="req2", input_type="STRING", required=True),
                QuestionParameter(name="opt", input_type="STRING", required=False)
            ]
        )

        inputs = {"req1": "value1"}  # Missing req2

        with pytest.raises(ValueError) as exc_info:
            validate_question_parameters(inputs, question)

        assert "Missing required parameters: req2" in str(exc_info.value)

    def test_validate_question_parameters_only_required(self):
        """Test validation passes with only required params"""
        question = Question(
            id="q1",
            name="Test",
            collection_id="c1",
            parameters=[
                QuestionParameter(name="req", input_type="STRING", required=True),
                QuestionParameter(name="opt", input_type="STRING", required=False)
            ]
        )

        inputs = {"req": "value1"}

        result = validate_question_parameters(inputs, question)

        assert result == inputs

    def test_validate_question_parameters_multiple_missing(self):
        """Test validation with multiple missing required parameters"""
        question = Question(
            id="q1",
            name="Test",
            collection_id="c1",
            parameters=[
                QuestionParameter(name="req1", input_type="STRING", required=True),
                QuestionParameter(name="req2", input_type="STRING", required=True),
                QuestionParameter(name="req3", input_type="STRING", required=True)
            ]
        )

        inputs = {}

        with pytest.raises(ValueError) as exc_info:
            validate_question_parameters(inputs, question)

        error_msg = str(exc_info.value)
        assert "Missing required parameters:" in error_msg
        assert "req1" in error_msg or "req2" in error_msg or "req3" in error_msg


class TestHandleQuestionResultsOutput:
    """Tests for handle_question_results_output utility"""

    def test_handle_question_results_output_delegates_to_explorer(self):
        """Test handle_question_results_output delegates to explorer util"""
        results = [{"id": "1"}, {"id": "2"}]

        with patch('dnastack.cli.commands.explorer.questions.utils.handle_question_results_output') as mock_handler:
            handle_question_results_output(results, None, "json")

            mock_handler.assert_called_once_with(results, None, "json")

    def test_handle_question_results_output_with_file(self):
        """Test handle_question_results_output with output file"""
        results = [{"id": "1"}]

        with patch('dnastack.cli.commands.explorer.questions.utils.handle_question_results_output') as mock_handler:
            handle_question_results_output(results, "output.json", "json")

            mock_handler.assert_called_once_with(results, "output.json", "json")

    def test_handle_question_results_output_different_formats(self):
        """Test handle_question_results_output with different output formats"""
        results = [{"id": "1"}]

        with patch('dnastack.cli.commands.explorer.questions.utils.handle_question_results_output') as mock_handler:
            for fmt in ["json", "csv", "yaml", "table"]:
                handle_question_results_output(results, None, fmt)
                mock_handler.assert_called_with(results, None, fmt)
