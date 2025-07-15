"""Focused tests to push coverage above 80%"""
import unittest


class TestExplorerFocused(unittest.TestCase):
    """Focused tests for specific coverage gaps"""

    def test_utils_format_question_parameters_detailed(self):
        """Test format_question_parameters with different scenarios"""
        from dnastack.cli.commands.explorer.questions.utils import format_question_parameters
        from dnastack.client.explorer.models import QuestionParam
        
        # Test with parameter having values but no DROPDOWN subtype
        param1 = QuestionParam(
            id="1", 
            name="param1", 
            label="Param 1",
            inputType="string",
            values="val1\nval2"
        )
        result = format_question_parameters([param1])
        self.assertIn("param1", result)
        
        # Test with parameter having default value  
        param2 = QuestionParam(
            id="2",
            name="param2",
            label="Param 2", 
            inputType="string",
            defaultValue="default_val"
        )
        result = format_question_parameters([param2])
        self.assertIn("default_val", result)
        
        # Test with parameter having no description
        param3 = QuestionParam(
            id="3",
            name="param3",
            label="Param 3",
            inputType="string"
        )
        result = format_question_parameters([param3])
        self.assertIn("param3", result)

    def test_utils_format_question_collections_detailed(self):
        """Test format_question_collections with various inputs"""
        from dnastack.cli.commands.explorer.questions.utils import format_question_collections
        from dnastack.client.explorer.models import QuestionCollection
        
        # Test with collection having all fields
        collection = QuestionCollection(
            id="c1",
            name="Collection One",
            slug="collection-one", 
            questionId="q1"
        )
        result = format_question_collections([collection])
        self.assertIn("Collection One", result)
        self.assertIn("collection-one", result)
        self.assertIn("c1", result)

    def test_utils_validate_question_parameters_errors(self):
        """Test validate_question_parameters error conditions"""
        from dnastack.cli.commands.explorer.questions.utils import validate_question_parameters
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam
        
        # Create question with required parameter
        question = FederatedQuestion(
            id="q1",
            name="Test",
            description="Test",
            params=[
                QuestionParam(
                    id="1",
                    name="required_param",
                    label="Required",
                    inputType="string",
                    required=True
                )
            ],
            collections=[]
        )
        
        # Test missing required parameter raises ValueError
        with self.assertRaises(ValueError) as context:
            validate_question_parameters({}, question)
        
        error_msg = str(context.exception)
        self.assertIn("Missing required parameters", error_msg)
        self.assertIn("required_param", error_msg)

    def test_tables_format_question_list_with_real_data(self):
        """Test format_question_list_table with realistic data"""
        from dnastack.cli.commands.explorer.questions.tables import format_question_list_table
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
        
        # Create question with mixed required/optional params
        question = FederatedQuestion(
            id="q1",
            name="Sample Question",
            description="A sample question for testing",
            params=[
                QuestionParam(
                    id="1",
                    name="required_param",
                    label="Required Parameter",
                    inputType="string",
                    required=True
                ),
                QuestionParam(
                    id="2", 
                    name="optional_param",
                    label="Optional Parameter",
                    inputType="integer",
                    required=False
                )
            ],
            collections=[
                QuestionCollection(
                    id="c1",
                    name="Collection 1",
                    slug="collection-1",
                    questionId="q1"
                )
            ]
        )
        
        result = format_question_list_table([question])
        self.assertEqual(len(result), 1)
        
        row = result[0]
        self.assertEqual(row['ID'], 'q1')
        self.assertEqual(row['Name'], 'Sample Question')
        self.assertEqual(row['Description'], 'A sample question for testing')
        self.assertEqual(row['Parameters'], 2)
        self.assertEqual(row['Collections'], 1)
        self.assertEqual(row['Required Params'], 1)

    def test_tables_format_question_detail_with_realistic_data(self):
        """Test format_question_detail_table with realistic data"""
        from dnastack.cli.commands.explorer.questions.tables import format_question_detail_table
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
        
        # Create complex question
        question = FederatedQuestion(
            id="complex_q",
            name="Complex Question",
            description="A complex question with multiple parameters",
            params=[
                QuestionParam(
                    id="1",
                    name="text_param",
                    label="Text Parameter",
                    inputType="string",
                    description="Enter some text",
                    required=True,
                    defaultValue="default text"
                )
            ],
            collections=[
                QuestionCollection(
                    id="c1",
                    name="Test Collection",
                    slug="test-collection",
                    questionId="complex_q"
                )
            ]
        )
        
        result = format_question_detail_table(question)
        
        # Verify main structure
        self.assertIn('question', result)
        self.assertIn('parameters', result)
        self.assertIn('collections', result)
        
        # Verify question details
        question_details = result['question']
        self.assertEqual(question_details['ID'], 'complex_q')
        self.assertEqual(question_details['Name'], 'Complex Question')
        
        # Verify parameter details
        params = result['parameters']
        self.assertEqual(len(params), 1)
        param = params[0]
        self.assertEqual(param['Name'], 'text_param')
        self.assertEqual(param['Type'], 'string')
        self.assertEqual(param['Required'], 'Yes')
        self.assertEqual(param['Default'], 'default text')
        
        # Verify collection details
        collections = result['collections']
        self.assertEqual(len(collections), 1)
        collection = collections[0]
        self.assertEqual(collection['ID'], 'c1')
        self.assertEqual(collection['Name'], 'Test Collection')

    def test_flatten_dict_comprehensive(self):
        """Test _flatten_dict with comprehensive scenarios"""
        from dnastack.cli.commands.explorer.questions.tables import _flatten_dict
        
        # Test with simple values
        result = _flatten_dict({"str": "text", "num": 42, "bool": True})
        self.assertEqual(result["str"], "text")
        self.assertEqual(result["num"], 42)
        self.assertEqual(result["bool"], True)
        
        # Test with nested structure
        nested = {
            "level1": {
                "level2": {
                    "value": "deep"
                }
            }
        }
        result = _flatten_dict(nested)
        self.assertEqual(result["level1.level2.value"], "deep")
        
        # Test with list of simple values
        simple_list = {"numbers": [1, 2, 3]}
        result = _flatten_dict(simple_list)
        self.assertEqual(result["numbers"], "1, 2, 3")
        
        # Test with list of dicts
        dict_list = {"items": [{"name": "item1"}, {"name": "item2"}]}
        result = _flatten_dict(dict_list)
        self.assertEqual(result["items[0].name"], "item1")
        self.assertEqual(result["items[1].name"], "item2")
        
        # Test with empty list
        empty_list = {"empty": []}
        result = _flatten_dict(empty_list)
        self.assertEqual(result["empty"], "")

    def test_commands_init_realistic(self):
        """Test commands initialization more realistically"""
        from dnastack.cli.commands.explorer.questions.commands import init_questions_commands
        from click import Group
        
        # Create actual Click group
        group = Group()
        
        # This should add commands to the group
        init_questions_commands(group)
        
        # The group should now have commands
        self.assertGreater(len(group.commands), 0)

    def test_client_service_types_comprehensive(self):
        """Test client service types and constants"""
        from dnastack.client.explorer.client import (
            ExplorerClient,
            EXPLORER_SERVICE_TYPE_V1_0
        )
        
        # Test service type details
        service_type = EXPLORER_SERVICE_TYPE_V1_0
        self.assertEqual(service_type.group, 'com.dnastack.explorer')
        self.assertEqual(service_type.artifact, 'collection-service')
        self.assertEqual(service_type.version, '1.0.0')
        
        # Test that get_supported_service_types returns this type
        supported = ExplorerClient.get_supported_service_types()
        self.assertIn(service_type, supported)
        
        # Test adapter type
        adapter = ExplorerClient.get_adapter_type()
        self.assertTrue(adapter.startswith('com.dnastack.explorer'))
        self.assertIn('questions', adapter)

    def test_model_dict_conversion(self):
        """Test model dict conversion and serialization"""
        from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
        
        # Create models and test dict conversion
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
            description="Test description",
            params=[param],
            collections=[collection]
        )
        
        # Test that models can be converted to dict
        question_dict = question.dict()
        self.assertEqual(question_dict['id'], 'q1')
        self.assertEqual(question_dict['name'], 'Test Question')
        self.assertEqual(len(question_dict['params']), 1)
        self.assertEqual(len(question_dict['collections']), 1)


if __name__ == '__main__':
    unittest.main()