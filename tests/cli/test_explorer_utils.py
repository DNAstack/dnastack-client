import unittest
from unittest.mock import Mock, patch, MagicMock

from dnastack.cli.commands.explorer.questions.utils import (
    get_explorer_client,
    parse_collections_argument,
    format_question_parameters,
    format_question_collections,
    validate_question_parameters,
    flatten_result_for_export
)
from dnastack.client.explorer.client import ExplorerClient
from dnastack.client.explorer.models import QuestionParam


class TestExplorerUtils(unittest.TestCase):

    @patch('dnastack.cli.commands.explorer.questions.utils.container.get')
    def test_get_explorer_client(self, mock_container_get):
        """Test getting an explorer client"""
        mock_factory = Mock()
        mock_client = Mock(spec=ExplorerClient)
        mock_factory.get.return_value = mock_client
        mock_container_get.return_value = mock_factory

        result = get_explorer_client()

        self.assertEqual(result, mock_client)
        mock_factory.get.assert_called_once_with(
            ExplorerClient, 
            context_name=None, 
            endpoint_id=None
        )

    @patch('dnastack.cli.commands.explorer.questions.utils.container.get')
    def test_get_explorer_client_with_context(self, mock_container_get):
        """Test getting an explorer client with context"""
        mock_factory = Mock()
        mock_client = Mock(spec=ExplorerClient)
        mock_factory.get.return_value = mock_client
        mock_container_get.return_value = mock_factory

        result = get_explorer_client(context="test_context", endpoint_id="test_endpoint")

        self.assertEqual(result, mock_client)
        mock_factory.get.assert_called_once_with(
            ExplorerClient, 
            context_name="test_context", 
            endpoint_id="test_endpoint"
        )

    def test_parse_collections_argument_none(self):
        """Test parsing None collections argument"""
        result = parse_collections_argument(None)
        self.assertIsNone(result)

    def test_parse_collections_argument_empty(self):
        """Test parsing empty collections argument"""
        result = parse_collections_argument("")
        self.assertIsNone(result)

    def test_parse_collections_argument_single(self):
        """Test parsing single collection"""
        result = parse_collections_argument("collection1")
        self.assertEqual(result, ["collection1"])

    def test_parse_collections_argument_multiple(self):
        """Test parsing multiple collections"""
        result = parse_collections_argument("collection1,collection2,collection3")
        self.assertEqual(result, ["collection1", "collection2", "collection3"])

    def test_parse_collections_argument_with_spaces(self):
        """Test parsing collections with spaces"""
        result = parse_collections_argument("collection1, collection2 , collection3")
        self.assertEqual(result, ["collection1", "collection2", "collection3"])

    def test_flatten_result_for_export_simple(self):
        """Test flattening simple result"""
        result = {"name": "John", "age": 30}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"name": "John", "age": 30})

    def test_flatten_result_for_export_nested(self):
        """Test flattening nested result"""
        result = {"person": {"name": "John", "age": 30}}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"person.name": "John", "person.age": 30})

    def test_flatten_result_for_export_with_list(self):
        """Test flattening result with list"""
        result = {"names": ["John", "Jane"]}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"names[0]": "John", "names[1]": "Jane"})

    def test_format_question_parameters_empty(self):
        """Test formatting empty question parameters"""
        result = format_question_parameters([])
        self.assertEqual(result, "")

    def test_format_question_parameters_single(self):
        """Test formatting single question parameter"""
        params = [
            QuestionParam(
                name="param1",
                description="Test parameter",
                input_type="string",
                required=True
            )
        ]
        result = format_question_parameters(params)
        self.assertIn("param1", result)
        self.assertIn("Test parameter", result)
        self.assertIn("string", result)
        self.assertIn("required", result)

    def test_format_question_parameters_multiple(self):
        """Test formatting multiple question parameters"""
        params = [
            QuestionParam(
                name="param1",
                description="Test parameter 1",
                input_type="string",
                required=True
            ),
            QuestionParam(
                name="param2",
                description="Test parameter 2",
                input_type="integer",
                required=False
            )
        ]
        result = format_question_parameters(params)
        self.assertIn("param1", result)
        self.assertIn("param2", result)
        self.assertIn("Test parameter 1", result)
        self.assertIn("Test parameter 2", result)

    def test_format_question_collections_empty(self):
        """Test formatting empty collections"""
        result = format_question_collections([])
        self.assertEqual(result, "No collections")

    def test_format_question_collections_single(self):
        """Test formatting single collection"""
        from dnastack.client.explorer.models import QuestionCollection
        collections = [QuestionCollection(id="1", name="Collection 1", slug="collection1")]
        result = format_question_collections(collections)
        self.assertIn("Collection 1", result)
        self.assertIn("collection1", result)

    def test_validate_question_parameters_valid(self):
        """Test validating valid question parameters"""
        from dnastack.client.explorer.models import FederatedQuestion
        question = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[
                QuestionParam(
                    name="param1",
                    description="Test parameter",
                    input_type="string",
                    required=True
                )
            ],
            collections=[]
        )
        args = {"param1": "value1"}
        
        # Should not raise an exception
        validate_question_parameters(args, question)

    def test_validate_question_parameters_missing_required(self):
        """Test validating question parameters with missing required parameter"""
        from dnastack.client.explorer.models import FederatedQuestion
        question = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[
                QuestionParam(
                    name="param1",
                    description="Test parameter",
                    input_type="string",
                    required=True
                )
            ],
            collections=[]
        )
        args = {}
        
        with self.assertRaises(ValueError) as context:
            validate_question_parameters(args, question)
        
        self.assertIn("param1", str(context.exception))
        self.assertIn("required", str(context.exception))


if __name__ == '__main__':
    unittest.main()