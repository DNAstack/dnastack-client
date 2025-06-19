"""Simple coverage tests for Explorer modules"""
import unittest
import tempfile
import os
import json


class TestExplorerSimpleCoverage(unittest.TestCase):
    """Simple tests to improve Explorer coverage above 80%"""

    def test_commands_write_file_function(self):
        """Test _write_results_to_file function directly"""
        from dnastack.cli.commands.explorer.questions.commands import _write_results_to_file
        
        # Test JSON output
        test_data = [{"key": "value", "number": 42}]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_name = tmp.name
        
        try:
            _write_results_to_file(test_data, tmp_name, 'json')
            with open(tmp_name, 'r') as f:
                loaded = json.load(f)
                self.assertEqual(loaded, test_data)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        # Test CSV output
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_name = tmp.name
        
        try:
            _write_results_to_file(test_data, tmp_name, 'csv')
            self.assertTrue(os.path.exists(tmp_name))
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        # Test YAML output
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp:
            tmp_name = tmp.name
        
        try:
            _write_results_to_file(test_data, tmp_name, 'yaml')
            self.assertTrue(os.path.exists(tmp_name))
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        # Test empty CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_name = tmp.name
        
        try:
            _write_results_to_file([], tmp_name, 'csv')
            self.assertTrue(os.path.exists(tmp_name))
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

        # Test directory creation
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "file.json")
            _write_results_to_file(test_data, nested_path, 'json')
            self.assertTrue(os.path.exists(nested_path))

    def test_client_static_methods_comprehensive(self):
        """Test ExplorerClient static methods thoroughly"""
        from dnastack.client.explorer.client import ExplorerClient, EXPLORER_SERVICE_TYPE_V1_0
        
        # Test get_supported_service_types
        types = ExplorerClient.get_supported_service_types()
        self.assertIsInstance(types, list)
        self.assertEqual(len(types), 1)
        self.assertEqual(types[0], EXPLORER_SERVICE_TYPE_V1_0)
        
        # Test service type properties
        service_type = EXPLORER_SERVICE_TYPE_V1_0
        self.assertEqual(service_type.group, 'com.dnastack.explorer')
        self.assertEqual(service_type.artifact, 'collection-service')
        self.assertEqual(service_type.version, '1.0.0')
        
        # Test get_adapter_type
        adapter = ExplorerClient.get_adapter_type()
        self.assertEqual(adapter, "com.dnastack.explorer:questions:1.0.0")

    def test_tables_flatten_dict_comprehensive(self):
        """Test _flatten_dict function thoroughly"""
        from dnastack.cli.commands.explorer.questions.tables import _flatten_dict
        
        # Test empty dict
        self.assertEqual(_flatten_dict({}), {})
        
        # Test simple values
        simple = {"str": "text", "num": 42, "bool": True, "none": None}
        result = _flatten_dict(simple)
        self.assertEqual(result["str"], "text")
        self.assertEqual(result["num"], 42)
        self.assertEqual(result["bool"], True)
        self.assertEqual(result["none"], None)
        
        # Test nested dict
        nested = {"level1": {"level2": {"value": "deep"}}}
        result = _flatten_dict(nested)
        self.assertEqual(result["level1.level2.value"], "deep")
        
        # Test simple list
        simple_list = {"numbers": [1, 2, 3]}
        result = _flatten_dict(simple_list)
        self.assertEqual(result["numbers"], "1, 2, 3")
        
        # Test empty list
        empty_list = {"empty": []}
        result = _flatten_dict(empty_list)
        self.assertEqual(result["empty"], "")
        
        # Test list of dicts
        dict_list = {"items": [{"name": "a"}, {"name": "b"}]}
        result = _flatten_dict(dict_list)
        self.assertEqual(result["items[0].name"], "a")
        self.assertEqual(result["items[1].name"], "b")

    def test_tables_functions_comprehensive(self):
        """Test table formatting functions comprehensively"""
        from dnastack.cli.commands.explorer.questions.tables import (
            format_question_list_table,
            format_question_results_table,
            format_question_detail_table
        )
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
        
        # Test empty inputs
        self.assertEqual(format_question_list_table([]), [])
        self.assertEqual(format_question_results_table([]), [])
        
        # Test with real question data
        param = QuestionParam(
            id="1",
            name="test_param",
            label="Test Parameter",
            inputType="string",
            required=True
        )
        
        collection = QuestionCollection(
            id="c1",
            name="Test Collection",
            slug="test-collection",
            questionId="q1"
        )
        
        question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[param],
            collections=[collection]
        )
        
        # Test question list table
        list_result = format_question_list_table([question])
        self.assertEqual(len(list_result), 1)
        row = list_result[0]
        self.assertEqual(row['ID'], 'q1')
        self.assertEqual(row['Name'], 'Test Question')
        
        # Test question detail table
        detail_result = format_question_detail_table(question)
        self.assertIn('question', detail_result)
        self.assertIn('parameters', detail_result)
        self.assertIn('collections', detail_result)
        
        # Test with results data
        results_data = [{"key": "value", "nested": {"data": "test"}}]
        results_table = format_question_results_table(results_data)
        self.assertEqual(len(results_table), 1)
        
    def test_utils_functions_comprehensive(self):
        """Test utils functions comprehensively"""
        from dnastack.cli.commands.explorer.questions.utils import (
            parse_collections_argument,
            flatten_result_for_export,
            format_question_parameters,
            format_question_collections
        )
        from dnastack.client.explorer.models import QuestionParam, QuestionCollection
        
        # Test parse_collections_argument
        self.assertIsNone(parse_collections_argument(None))
        self.assertIsNone(parse_collections_argument(""))
        self.assertEqual(parse_collections_argument("   "), [])
        self.assertEqual(parse_collections_argument("a"), ["a"])
        self.assertEqual(parse_collections_argument("a,b,c"), ["a", "b", "c"])
        self.assertEqual(parse_collections_argument(" a , b , c "), ["a", "b", "c"])
        
        # Test with empty elements
        result = parse_collections_argument("a,,b")
        self.assertEqual(result, ["a", "b"])
        
        # Test flatten_result_for_export
        simple_result = {"key": "value"}
        self.assertEqual(flatten_result_for_export(simple_result), simple_result)
        
        nested_result = {"level1": {"level2": "value"}}
        flattened = flatten_result_for_export(nested_result)
        self.assertEqual(flattened["level1.level2"], "value")
        
        # Test format functions with None/empty
        self.assertEqual(format_question_parameters(None), "No parameters")
        self.assertEqual(format_question_parameters([]), "No parameters")
        self.assertEqual(format_question_collections(None), "No collections")
        self.assertEqual(format_question_collections([]), "No collections")
        
        # Test with actual data
        param = QuestionParam(
            id="1",
            name="test_param",
            label="Test Parameter",
            inputType="string",
            description="A test parameter"
        )
        
        param_text = format_question_parameters([param])
        self.assertIn("test_param", param_text)
        self.assertIn("A test parameter", param_text)
        
        collection = QuestionCollection(
            id="c1",
            name="Test Collection",
            slug="test-collection",
            questionId="q1"
        )
        
        collection_text = format_question_collections([collection])
        self.assertIn("Test Collection", collection_text)
        self.assertIn("test-collection", collection_text)

    def test_validation_function(self):
        """Test parameter validation function"""
        from dnastack.cli.commands.explorer.questions.utils import validate_question_parameters
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam
        
        # Test with no parameters
        question_no_params = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[],
            collections=[]
        )
        
        result = validate_question_parameters({}, question_no_params)
        self.assertEqual(result, {})
        
        result = validate_question_parameters({"extra": "value"}, question_no_params)
        self.assertEqual(result, {"extra": "value"})
        
        # Test with required parameter missing
        required_param = QuestionParam(
            id="1",
            name="required_param",
            label="Required",
            inputType="string",
            required=True
        )
        
        question_with_required = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[required_param],
            collections=[]
        )
        
        # Should raise ValueError for missing required param
        with self.assertRaises(ValueError) as context:
            validate_question_parameters({}, question_with_required)
        
        error_msg = str(context.exception)
        self.assertIn("Missing required parameters", error_msg)
        self.assertIn("required_param", error_msg)
        
        # Should pass with required param provided
        result = validate_question_parameters({"required_param": "value"}, question_with_required)
        self.assertEqual(result, {"required_param": "value"})

    def test_models_comprehensive(self):
        """Test model creation and properties"""
        from dnastack.client.explorer.models import QuestionParam, QuestionCollection, FederatedQuestion
        
        # Test QuestionParam with all fields
        param = QuestionParam(
            id="1",
            name="test_param",
            label="Test Parameter",
            inputType="string",
            description="A test parameter",
            required=True,
            defaultValue="default",
            testValue="test",
            inputSubtype="TEXT",
            allowedValues="a,b,c",
            values="x\ny\nz"
        )
        
        # Test aliases work
        self.assertEqual(param.input_type, "string")
        self.assertEqual(param.default_value, "default")
        self.assertEqual(param.test_value, "test")
        self.assertEqual(param.input_subtype, "TEXT")
        self.assertEqual(param.allowed_values, "a,b,c")
        
        # Test dict conversion
        param_dict = param.dict()
        self.assertEqual(param_dict['input_type'], "string")
        self.assertEqual(param_dict['required'], True)
        
        # Test QuestionCollection
        collection = QuestionCollection(
            id="c1",
            name="Test Collection",
            slug="test-collection",
            questionId="q1"
        )
        
        self.assertEqual(collection.question_id, "q1")
        
        # Test FederatedQuestion
        question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="A test question",
            params=[param],
            collections=[collection]
        )
        
        self.assertEqual(question.id, "q1")
        self.assertEqual(len(question.params), 1)
        self.assertEqual(len(question.collections), 1)
        
        # Test question dict conversion
        question_dict = question.dict()
        self.assertEqual(question_dict['id'], 'q1')
        self.assertEqual(len(question_dict['params']), 1)
        self.assertEqual(len(question_dict['collections']), 1)


if __name__ == '__main__':
    unittest.main()