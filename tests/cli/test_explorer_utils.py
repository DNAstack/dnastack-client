import unittest
import tempfile
import os
import json
import csv
from unittest.mock import Mock, patch

from dnastack.cli.commands.explorer.questions.utils import (
    get_explorer_client,
    parse_collections_argument,
    format_question_parameters,
    format_question_collections,
    validate_question_parameters,
    flatten_result_for_export,
    handle_question_results_output,
    write_results_to_file,
    _write_json_results,
    _write_csv_results,
    _write_yaml_results
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


class TestExplorerOutputUtils(unittest.TestCase):
    """Test cases for the new output utility functions added during PR review resolution."""

    def setUp(self):
        """Set up test data."""
        self.sample_results = [
            {"id": 1, "name": "test1", "value": "data1"},
            {"id": 2, "name": "test2", "value": "data2"}
        ]
        
        self.nested_results = [
            {
                "id": 1,
                "metadata": {"count": 5, "tags": ["a", "b"]},
                "nested": {"deep": {"value": "test"}}
            }
        ]

    @patch('dnastack.cli.commands.explorer.questions.utils.show_iterator')
    def test_handle_question_results_output_to_stdout_json(self, mock_show_iterator):
        """Test output to stdout in JSON format."""
        results = self.sample_results
        
        handle_question_results_output(results, None, 'json')
        
        mock_show_iterator.assert_called_once_with(
            output_format='json',
            iterator=results
        )

    @patch('dnastack.cli.commands.explorer.questions.utils.show_iterator')
    def test_handle_question_results_output_to_stdout_yaml(self, mock_show_iterator):
        """Test output to stdout in YAML format."""
        results = self.sample_results
        
        handle_question_results_output(results, None, 'yaml')
        
        mock_show_iterator.assert_called_once_with(
            output_format='yaml',
            iterator=results
        )

    @patch('dnastack.cli.commands.explorer.questions.utils.write_results_to_file')
    @patch('dnastack.cli.commands.explorer.questions.utils.click.echo')
    def test_handle_question_results_output_to_file_calls_writer(self, mock_echo, mock_write_file):
        """Test that file output calls write_results_to_file."""
        results = self.sample_results
        output_file = "/tmp/test.json"
        
        handle_question_results_output(results, output_file, 'json')
        
        mock_write_file.assert_called_once_with(results, output_file, 'json')
        mock_echo.assert_called_once_with("Results written to /tmp/test.json")

    @patch('dnastack.cli.commands.explorer.questions.utils.show_iterator')
    def test_handle_question_results_output_empty_results(self, mock_show_iterator):
        """Test handling of empty results list."""
        empty_results = []
        
        handle_question_results_output(empty_results, None, 'json')
        
        mock_show_iterator.assert_called_once_with(
            output_format='json',
            iterator=empty_results
        )

    def test_write_results_to_file_creates_directory(self):
        """Test directory creation for nested output paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir", "test.json")
            results = self.sample_results
            
            write_results_to_file(results, nested_path, 'json')
            
            # Verify directory was created
            self.assertTrue(os.path.exists(os.path.dirname(nested_path)))
            # Verify file was created
            self.assertTrue(os.path.exists(nested_path))

    def test_write_results_to_file_json_format(self):
        """Test JSON file writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.json")
            results = self.sample_results
            
            write_results_to_file(results, output_file, 'json')
            
            # Verify file content
            with open(output_file, 'r') as f:
                content = json.load(f)
            
            self.assertEqual(content, results)

    def test_write_results_to_file_csv_format(self):
        """Test CSV file writing with flattened data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.csv")
            results = self.sample_results
            
            write_results_to_file(results, output_file, 'csv')
            
            # Verify file content
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['id'], '1')
            self.assertEqual(rows[0]['name'], 'test1')

    @patch('yaml.dump')
    def test_write_results_to_file_yaml_format(self, mock_yaml_dump):
        """Test YAML file writing."""
        mock_yaml_dump.return_value = "yaml_content"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.yaml")
            results = self.sample_results
            
            write_results_to_file(results, output_file, 'yaml')
            
            # Verify YAML dump was called
            mock_yaml_dump.assert_called_once()
            
            # Verify file content
            with open(output_file, 'r') as f:
                content = f.read()
            
            self.assertEqual(content, "yaml_content")

    def test_write_json_results_simple_data(self):
        """Test JSON writing with simple data structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "simple.json")
            results = self.sample_results
            
            _write_json_results(results, output_file)
            
            with open(output_file, 'r') as f:
                content = json.load(f)
            
            self.assertEqual(content, results)

    def test_write_json_results_complex_nested_data(self):
        """Test JSON writing with complex nested data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "nested.json")
            results = self.nested_results
            
            _write_json_results(results, output_file)
            
            with open(output_file, 'r') as f:
                content = json.load(f)
            
            self.assertEqual(content, results)

    def test_write_csv_results_empty_data(self):
        """Test CSV writing with empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "empty.csv")
            empty_results = []
            
            _write_csv_results(empty_results, output_file)
            
            # Verify empty file was created
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, "")

    @patch('dnastack.cli.commands.explorer.questions.utils.flatten_result_for_export')
    def test_write_csv_results_with_nested_flattening(self, mock_flatten):
        """Test CSV writing flattens nested structures properly."""
        mock_flatten.side_effect = [
            {"id": "1", "metadata.count": "5"},
            {"id": "2", "metadata.count": "10"}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "flattened.csv")
            results = self.nested_results + [{"id": 2, "metadata": {"count": 10}}]
            
            _write_csv_results(results, output_file)
            
            # Verify flatten was called for each result
            self.assertEqual(mock_flatten.call_count, 2)
            
            # Verify CSV structure
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertIn('id', rows[0])
            self.assertIn('metadata.count', rows[0])

    @patch('dnastack.cli.commands.explorer.questions.utils.normalize')
    @patch('yaml.dump')
    def test_write_yaml_results_normalization(self, mock_yaml_dump, mock_normalize):
        """Test YAML writing uses normalize() function."""
        mock_normalize.side_effect = lambda x: x  # Identity function
        mock_yaml_dump.return_value = "normalized_yaml"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "normalized.yaml")
            results = self.sample_results
            
            _write_yaml_results(results, output_file)
            
            # Verify normalize was called for each result
            self.assertEqual(mock_normalize.call_count, len(results))
            mock_yaml_dump.assert_called_once()


if __name__ == '__main__':
    unittest.main()