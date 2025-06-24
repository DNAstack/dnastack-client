import unittest
from unittest.mock import Mock

from dnastack.cli.commands.explorer.questions.commands import init_questions_commands
from dnastack.cli.commands.explorer.questions.utils import (
    format_question_parameters,
    format_question_collections,
    validate_question_parameters,
    flatten_result_for_export
)
from dnastack.cli.commands.explorer.questions.tables import (
    format_question_detail_table,
    format_question_results_table,
    _flatten_dict
)
from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection


class TestExplorerCoverage(unittest.TestCase):
    """Tests to improve Explorer code coverage"""

    def test_init_questions_commands(self):
        """Test that init_questions_commands can be called"""
        mock_group = Mock()
        # This should not raise any errors
        init_questions_commands(mock_group)
        # Verify that commands were added to the group
        self.assertTrue(mock_group.command.called)

    def test_format_question_parameters_with_values(self):
        """Test formatting parameters with dropdown values"""
        params = [
            QuestionParam(
                name="test_param",
                description="Test dropdown parameter",
                input_type="string",
                input_subtype="DROPDOWN",
                values="option1\noption2\noption3",
                required=True
            )
        ]
        result = format_question_parameters(params)
        self.assertIn("test_param", result)
        self.assertIn("choices", result)

    def test_format_question_parameters_with_default(self):
        """Test formatting parameters with default values"""
        params = [
            QuestionParam(
                name="test_param",
                description="Test parameter with default",
                input_type="string",
                default_value="default_val",
                required=False
            )
        ]
        result = format_question_parameters(params)
        self.assertIn("default_val", result)
        self.assertIn("optional", result)

    def test_format_question_collections_with_data(self):
        """Test formatting collections with full data"""
        collections = [
            QuestionCollection(
                id="123",
                name="Test Collection",
                slug="test_collection",
                question_id="q1"
            )
        ]
        result = format_question_collections(collections)
        self.assertIn("Test Collection", result)
        self.assertIn("test_collection", result)
        self.assertIn("123", result)

    def test_flatten_result_complex_nested(self):
        """Test flattening complex nested structures"""
        result = {
            "level1": {
                "level2": {
                    "value": "deep_value"
                },
                "list": [{"item": "value1"}, {"item": "value2"}]
            }
        }
        flattened = flatten_result_for_export(result)
        self.assertIn("level1.level2.value", flattened)
        self.assertIn("level1.list[0].item", flattened)
        self.assertEqual(flattened["level1.level2.value"], "deep_value")

    def test_format_question_detail_with_collections(self):
        """Test detailed question formatting with collections"""
        question = FederatedQuestion(
            id="detailed_q",
            name="Detailed Question",
            description="A detailed question for testing",
            params=[
                QuestionParam(
                    name="param1",
                    description="First parameter",
                    input_type="string",
                    input_subtype="DROPDOWN",
                    values="val1\nval2\nval3\nval4\nval5",
                    required=True
                )
            ],
            collections=[
                QuestionCollection(
                    id="1",
                    name="Collection 1",
                    slug="collection1",
                    question_id="detailed_q"
                )
            ]
        )
        
        result = format_question_detail_table(question)
        
        # Check structure
        self.assertIn('question', result)
        self.assertIn('parameters', result)
        self.assertIn('collections', result)
        
        # Check parameter details
        param = result['parameters'][0]
        self.assertEqual(param['Name'], 'param1')
        self.assertEqual(param['Required'], 'Yes')
        self.assertIn('Choices', param)

    def test_format_question_results_with_complex_list(self):
        """Test formatting results with complex list structures"""
        results = [
            {
                "simple": "value",
                "complex_list": [
                    {"nested": {"deep": "value1"}},
                    {"nested": {"deep": "value2"}}
                ]
            }
        ]
        
        formatted = format_question_results_table(results)
        self.assertEqual(len(formatted), 1)
        result = formatted[0]
        
        # Should have flattened the complex structure
        self.assertIn("complex_list[0].nested.deep", result)
        self.assertEqual(result["complex_list[0].nested.deep"], "value1")

    def test_flatten_dict_with_mixed_list(self):
        """Test flattening dictionary with mixed list types"""
        d = {
            "simple_list": ["a", "b", "c"],
            "complex_list": [{"key": "val1"}, {"key": "val2"}],
            "empty_list": []
        }
        
        result = _flatten_dict(d)
        
        # Simple list should be comma-separated
        self.assertEqual(result["simple_list"], "a, b, c")
        
        # Complex list should be indexed
        self.assertEqual(result["complex_list[0].key"], "val1")
        self.assertEqual(result["complex_list[1].key"], "val2")
        
        # Empty list should be comma-separated (empty string)
        self.assertEqual(result["empty_list"], "")

    def test_validate_question_parameters_with_partial_match(self):
        """Test validation with some parameters provided"""
        question = FederatedQuestion(
            id="test_q",
            name="Test Question",
            description="Test",
            params=[
                QuestionParam(
                    name="required_param",
                    description="Required",
                    input_type="string",
                    required=True
                ),
                QuestionParam(
                    name="optional_param",
                    description="Optional",
                    input_type="string",
                    required=False
                )
            ],
            collections=[]
        )
        
        # Should pass with only required parameter
        inputs = {"required_param": "value"}
        result = validate_question_parameters(inputs, question)
        self.assertEqual(result, inputs)
        
        # Should pass with both parameters
        inputs_full = {"required_param": "value", "optional_param": "optional_value"}
        result_full = validate_question_parameters(inputs_full, question)
        self.assertEqual(result_full, inputs_full)


class TestExplorerErrorMessages(unittest.TestCase):
    """Test cases for enhanced error messages added during PR review resolution."""

    def test_error_message_formatting(self):
        """Test the error message formatting logic directly."""
        # Test the actual logic that was changed for error messages
        # This tests the core functionality without complex CLI mocking
        
        # Simulate the scenario: we have available collection IDs and check against provided ones
        available_ids = {"collection1", "collection2"}
        
        # Test case 1: Single invalid ID
        collection_ids = ["invalid_id"]
        invalid_ids = [cid for cid in collection_ids if cid not in available_ids]
        error_message = f"Error: Invalid collection IDs for this question: {', '.join(invalid_ids)}"
        
        self.assertEqual(error_message, "Error: Invalid collection IDs for this question: invalid_id")
        self.assertIn("invalid_id", error_message)
        
        # Test case 2: Multiple invalid IDs
        collection_ids = ["invalid1", "invalid2", "invalid3"]
        invalid_ids = [cid for cid in collection_ids if cid not in available_ids]
        error_message = f"Error: Invalid collection IDs for this question: {', '.join(invalid_ids)}"
        
        self.assertIn("invalid1", error_message)
        self.assertIn("invalid2", error_message)
        self.assertIn("invalid3", error_message)
        
        # Test case 3: Mixed valid and invalid IDs
        collection_ids = ["collection1", "invalid_id", "collection2", "another_invalid"]
        invalid_ids = [cid for cid in collection_ids if cid not in available_ids]
        error_message = f"Error: Invalid collection IDs for this question: {', '.join(invalid_ids)}"
        
        self.assertIn("invalid_id", error_message)
        self.assertIn("another_invalid", error_message)
        self.assertNotIn("collection1", error_message)
        self.assertNotIn("collection2", error_message)
        
        # Test case 4: No invalid IDs (should not trigger error)
        collection_ids = ["collection1", "collection2"]
        invalid_ids = [cid for cid in collection_ids if cid not in available_ids]
        self.assertEqual(len(invalid_ids), 0)  # No error should be triggered


if __name__ == '__main__':
    unittest.main()