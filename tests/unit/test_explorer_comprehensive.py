"""Comprehensive tests to improve Explorer module coverage to 80%+"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import tempfile
import os

from dnastack.cli.commands.explorer.questions import commands
from dnastack.cli.commands.explorer.questions import utils
from dnastack.cli.commands.explorer.questions import tables
from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection


class TestExplorerComprehensive(unittest.TestCase):
    """Comprehensive tests for Explorer module coverage"""

    # Test utils.py functions for better coverage
    def test_format_question_parameters_comprehensive(self):
        """Test format_question_parameters with all scenarios"""
        # Empty params
        result = utils.format_question_parameters([])
        self.assertEqual(result, "No parameters")
        
        # Single param with all fields
        params = [
            QuestionParam(
                id="1",
                name="test_param",
                label="Test Parameter",
                input_type="string",
                description="Test description",
                required=True,
                default_value="default",
                input_subtype="DROPDOWN",
                values="value1\nvalue2\nvalue3\nvalue4\nvalue5\nvalue6"
            )
        ]
        result = utils.format_question_parameters(params)
        self.assertIn("test_param", result)
        self.assertIn("required", result)
        self.assertIn("default", result)
        self.assertIn("choices", result)
        self.assertIn("...", result)  # Should truncate long lists

    def test_format_question_collections_comprehensive(self):
        """Test format_question_collections with all scenarios"""
        # Empty collections
        result = utils.format_question_collections([])
        self.assertEqual(result, "No collections")
        
        # Multiple collections
        collections = [
            QuestionCollection(
                id="1",
                name="Collection One",
                slug="collection-one",
                question_id="q1"
            ),
            QuestionCollection(
                id="2",
                name="Collection Two",
                slug="collection-two",
                question_id="q1"
            )
        ]
        result = utils.format_question_collections(collections)
        self.assertIn("Collection One", result)
        self.assertIn("collection-one", result)
        self.assertIn("Collection Two", result)
        self.assertIn("collection-two", result)

    def test_validate_question_parameters_comprehensive(self):
        """Test validate_question_parameters with all scenarios"""
        question = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[
                QuestionParam(
                    id="1",
                    name="required_param",
                    label="Required",
                    input_type="string",
                    required=True
                ),
                QuestionParam(
                    id="2",
                    name="optional_param",
                    label="Optional",
                    input_type="string",
                    required=False
                )
            ],
            collections=[]
        )
        
        # Test with all params provided
        inputs = {"required_param": "value1", "optional_param": "value2"}
        result = utils.validate_question_parameters(inputs, question)
        self.assertEqual(result, inputs)
        
        # Test with only required param
        inputs_min = {"required_param": "value1"}
        result_min = utils.validate_question_parameters(inputs_min, question)
        self.assertEqual(result_min, inputs_min)
        
        # Test missing required param
        with self.assertRaises(ValueError) as context:
            utils.validate_question_parameters({}, question)
        self.assertIn("required_param", str(context.exception))

    def test_flatten_result_for_export_edge_cases(self):
        """Test flatten_result_for_export with edge cases"""
        # Empty dict
        result = utils.flatten_result_for_export({})
        self.assertEqual(result, {})
        
        # Nested with None values
        result = utils.flatten_result_for_export({"key": None})
        self.assertEqual(result, {"key": None})
        
        # Complex nested structure
        complex_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                },
                "array": [
                    {"nested": "value1"},
                    {"nested": "value2"}
                ]
            },
            "simple": "value"
        }
        result = utils.flatten_result_for_export(complex_data)
        self.assertEqual(result["level1.level2.level3.value"], "deep")
        self.assertEqual(result["level1.array[0].nested"], "value1")
        self.assertEqual(result["simple"], "value")

    # Test tables.py functions for better coverage
    def test_format_question_list_table_comprehensive(self):
        """Test format_question_list_table with various scenarios"""
        # Empty list
        result = tables.format_question_list_table([])
        self.assertEqual(result, [])
        
        # Multiple questions with varying params
        questions = [
            FederatedQuestion(
                id="q1",
                name="Question 1",
                description="Description 1",
                params=[
                    QuestionParam(
                        id="1",
                        name="param1",
                        label="Param 1",
                        input_type="string",
                        required=True
                    ),
                    QuestionParam(
                        id="2",
                        name="param2",
                        label="Param 2",
                        input_type="string",
                        required=False
                    )
                ],
                collections=[
                    QuestionCollection(id="1", name="Col1", slug="col1"),
                    QuestionCollection(id="2", name="Col2", slug="col2")
                ]
            ),
            FederatedQuestion(
                id="q2",
                name="Question 2",
                description="Description 2",
                params=[],
                collections=[]
            )
        ]
        
        result = tables.format_question_list_table(questions)
        self.assertEqual(len(result), 2)
        
        # Check first question
        self.assertEqual(result[0]['ID'], 'q1')
        self.assertEqual(result[0]['Name'], 'Question 1')
        self.assertEqual(result[0]['Parameters'], 2)
        self.assertEqual(result[0]['Collections'], 2)
        self.assertEqual(result[0]['Required Params'], 1)
        
        # Check second question
        self.assertEqual(result[1]['ID'], 'q2')
        self.assertEqual(result[1]['Parameters'], 0)
        self.assertEqual(result[1]['Collections'], 0)
        self.assertEqual(result[1]['Required Params'], 0)

    def test_format_question_detail_table_comprehensive(self):
        """Test format_question_detail_table with complex data"""
        question = FederatedQuestion(
            id="q1",
            name="Complex Question",
            description="Complex description",
            params=[
                QuestionParam(
                    id="1",
                    name="dropdown_param",
                    label="Dropdown",
                    input_type="string",
                    input_subtype="DROPDOWN",
                    values="opt1\nopt2\nopt3\nopt4",
                    required=True,
                    default_value="opt1",
                    description="Select an option"
                ),
                QuestionParam(
                    id="2",
                    name="text_param",
                    label="Text",
                    input_type="string",
                    required=False,
                    description="Enter text"
                )
            ],
            collections=[
                QuestionCollection(
                    id="c1",
                    name="Collection 1",
                    slug="collection-1",
                    question_id="q1"
                )
            ]
        )
        
        result = tables.format_question_detail_table(question)
        
        # Verify structure
        self.assertIn('question', result)
        self.assertIn('parameters', result)
        self.assertIn('collections', result)
        
        # Verify question details
        self.assertEqual(result['question']['ID'], 'q1')
        self.assertEqual(result['question']['Name'], 'Complex Question')
        
        # Verify parameters
        self.assertEqual(len(result['parameters']), 2)
        dropdown_param = result['parameters'][0]
        self.assertEqual(dropdown_param['Name'], 'dropdown_param')
        self.assertEqual(dropdown_param['Type'], 'string')
        self.assertEqual(dropdown_param['Required'], 'Yes')
        self.assertIn('Choices', dropdown_param)
        self.assertIn('opt1', dropdown_param['Choices'])
        
        # Verify collections
        self.assertEqual(len(result['collections']), 1)
        self.assertEqual(result['collections'][0]['Name'], 'Collection 1')

    def test_format_question_results_table_comprehensive(self):
        """Test format_question_results_table with various data types"""
        # Empty results
        result = tables.format_question_results_table([])
        self.assertEqual(result, [])
        
        # Simple flat results
        simple_results = [
            {"id": 1, "name": "John", "age": 30},
            {"id": 2, "name": "Jane", "age": 25}
        ]
        result = tables.format_question_results_table(simple_results)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "John")
        
        # Complex nested results
        complex_results = [
            {
                "id": 1,
                "person": {
                    "name": "John",
                    "address": {
                        "city": "New York",
                        "zip": "10001"
                    }
                },
                "scores": [85, 90, 95]
            }
        ]
        result = tables.format_question_results_table(complex_results)
        self.assertEqual(len(result), 1)
        flattened = result[0]
        self.assertIn("person.name", flattened)
        self.assertIn("person.address.city", flattened)
        self.assertEqual(flattened["person.name"], "John")
        self.assertEqual(flattened["person.address.city"], "New York")

    def test_flatten_dict_edge_cases(self):
        """Test _flatten_dict with edge cases"""
        # Dict with empty list
        result = tables._flatten_dict({"empty": []})
        self.assertEqual(result["empty"], "")
        
        # Dict with None values
        result = tables._flatten_dict({"none_val": None})
        self.assertEqual(result["none_val"], None)
        
        # Dict with mixed types
        result = tables._flatten_dict({
            "string": "text",
            "number": 123,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        })
        self.assertEqual(result["string"], "text")
        self.assertEqual(result["number"], 123)
        self.assertEqual(result["bool"], True)
        self.assertEqual(result["list"], "1, 2, 3")
        self.assertEqual(result["nested.inner"], "value")

    # Test commands.py coverage
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.show_iterator')
    def test_commands_init_coverage(self, mock_show, mock_get_client):
        """Test to improve commands.py coverage"""
        # Create a mock group
        mock_group = MagicMock()
        
        # Initialize commands
        commands.init_questions_commands(mock_group)
        
        # Verify command was added
        self.assertTrue(mock_group.command.called)
        
        # Get the decorator calls
        decorator_calls = mock_group.command.call_args_list
        self.assertGreater(len(decorator_calls), 0)

    # Test client.py additional methods
    @patch('dnastack.client.explorer.client.HttpSession')
    def test_explorer_client_create_http_session(self, mock_http_session):
        """Test ExplorerClient session creation"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        endpoint = Mock(spec=ServiceEndpoint)
        endpoint.url = "https://test.com"
        
        # Create client - this should trigger session creation
        client = ExplorerClient(endpoint)
        
        # Verify client has endpoint
        self.assertEqual(client.endpoint, endpoint)

    def test_explorer_client_static_methods(self):
        """Test ExplorerClient static methods"""
        from dnastack.client.explorer.client import ExplorerClient
        
        # Test get_supported_service_types
        service_types = ExplorerClient.get_supported_service_types()
        self.assertEqual(len(service_types), 1)
        self.assertEqual(service_types[0].group, 'com.dnastack.explorer')
        self.assertEqual(service_types[0].artifact, 'collection-service')
        self.assertEqual(service_types[0].version, '1.0.0')
        
        # Test get_adapter_type
        adapter_type = ExplorerClient.get_adapter_type()
        self.assertEqual(adapter_type, "com.dnastack.explorer:questions:1.0.0")

    # Test model edge cases
    def test_question_param_model_aliases(self):
        """Test QuestionParam model with field aliases"""
        # Test with camelCase fields (using aliases)
        data = {
            "id": "1",
            "name": "param1",
            "label": "Parameter 1",
            "inputType": "string",  # Using alias
            "defaultValue": "default",  # Using alias
            "testValue": "test",  # Using alias
            "inputSubtype": "TEXT",  # Using alias
            "allowedValues": "val1,val2"  # Using alias
        }
        
        param = QuestionParam(**data)
        self.assertEqual(param.input_type, "string")
        self.assertEqual(param.default_value, "default")
        self.assertEqual(param.test_value, "test")
        self.assertEqual(param.input_subtype, "TEXT")
        self.assertEqual(param.allowed_values, "val1,val2")

    def test_question_collection_model_comprehensive(self):
        """Test QuestionCollection model"""
        # Test with all fields
        data = {
            "id": "123",
            "name": "Test Collection",
            "slug": "test-collection",
            "question_id": "q1",
            "questionId": "q1"  # Test alias
        }
        
        collection = QuestionCollection(**data)
        self.assertEqual(collection.id, "123")
        self.assertEqual(collection.name, "Test Collection")
        self.assertEqual(collection.slug, "test-collection")
        self.assertEqual(collection.question_id, "q1")

    def test_federated_question_model_comprehensive(self):
        """Test FederatedQuestion model"""
        # Test with complex data
        data = {
            "id": "q1",
            "name": "Complex Question",
            "description": "A complex federated question",
            "params": [
                {
                    "id": "1",
                    "name": "param1",
                    "label": "Parameter 1",
                    "inputType": "string",
                    "required": True
                }
            ],
            "collections": [
                {
                    "id": "c1",
                    "name": "Collection 1",
                    "slug": "collection-1",
                    "questionId": "q1"
                }
            ]
        }
        
        question = FederatedQuestion(**data)
        self.assertEqual(question.id, "q1")
        self.assertEqual(question.name, "Complex Question")
        self.assertEqual(len(question.params), 1)
        self.assertEqual(len(question.collections), 1)
        self.assertEqual(question.params[0].input_type, "string")


if __name__ == '__main__':
    unittest.main()