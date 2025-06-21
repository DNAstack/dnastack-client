import unittest
from dnastack.cli.commands.explorer.questions.tables import (
    format_question_list_table,
    format_question_detail_table,
    format_question_results_table,
    _flatten_dict
)
from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection


class TestExplorerTables(unittest.TestCase):

    def setUp(self):
        """Set up test data"""
        self.sample_questions = [
            FederatedQuestion(
                id="q1",
                name="Test Question 1",
                description="First test question",
                params=[
                    QuestionParam(
                        name="param1",
                        description="Required parameter",
                        input_type="string",
                        required=True
                    ),
                    QuestionParam(
                        name="param2",
                        description="Optional parameter",
                        input_type="integer",
                        required=False
                    )
                ],
                collections=[
                    QuestionCollection(slug="collection1"),
                    QuestionCollection(slug="collection2")
                ]
            ),
            FederatedQuestion(
                id="q2",
                name="Test Question 2",
                description="Second test question",
                params=[
                    QuestionParam(
                        name="param3",
                        description="Another parameter",
                        input_type="boolean",
                        required=True
                    )
                ],
                collections=[
                    QuestionCollection(slug="collection3")
                ]
            )
        ]

    def test_format_question_list_table_empty(self):
        """Test formatting empty question list"""
        result = format_question_list_table([])
        self.assertEqual(result, [])

    def test_format_question_list_table_single(self):
        """Test formatting single question"""
        result = format_question_list_table([self.sample_questions[0]])
        
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row['ID'], 'q1')
        self.assertEqual(row['Name'], 'Test Question 1')
        self.assertEqual(row['Description'], 'First test question')
        self.assertEqual(row['Parameters'], 2)
        self.assertEqual(row['Collections'], 2)
        self.assertEqual(row['Required Params'], 1)

    def test_format_question_list_table_multiple(self):
        """Test formatting multiple questions"""
        result = format_question_list_table(self.sample_questions)
        
        self.assertEqual(len(result), 2)
        
        # Check first question
        row1 = result[0]
        self.assertEqual(row1['ID'], 'q1')
        self.assertEqual(row1['Name'], 'Test Question 1')
        self.assertEqual(row1['Parameters'], 2)
        self.assertEqual(row1['Required Params'], 1)
        
        # Check second question
        row2 = result[1]
        self.assertEqual(row2['ID'], 'q2')
        self.assertEqual(row2['Name'], 'Test Question 2')
        self.assertEqual(row2['Parameters'], 1)
        self.assertEqual(row2['Required Params'], 1)

    def test_format_question_detail_table(self):
        """Test formatting question detail table"""
        question = self.sample_questions[0]
        result = format_question_detail_table(question)
        
        self.assertIsInstance(result, dict)
        self.assertIn('question', result)
        self.assertIn('parameters', result)
        self.assertIn('collections', result)
        
        self.assertEqual(result['question']['ID'], 'q1')
        self.assertEqual(result['question']['Name'], 'Test Question 1')
        self.assertEqual(len(result['parameters']), 2)
        self.assertEqual(len(result['collections']), 2)

    def test_format_question_results_table_empty(self):
        """Test formatting empty results table"""
        result = format_question_results_table([])
        self.assertEqual(result, [])

    def test_format_question_results_table_simple(self):
        """Test formatting simple results"""
        results = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        formatted = format_question_results_table(results)
        
        self.assertEqual(len(formatted), 2)
        self.assertEqual(formatted[0]["name"], "John")
        self.assertEqual(formatted[1]["name"], "Jane")

    def test_format_question_results_table_nested(self):
        """Test formatting nested results"""
        results = [{"person": {"name": "John", "details": {"age": 30}}}]
        formatted = format_question_results_table(results)
        
        self.assertEqual(len(formatted), 1)
        self.assertIn("person.name", formatted[0])
        self.assertIn("person.details.age", formatted[0])

    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary"""
        d = {"name": "John", "age": 30}
        result = _flatten_dict(d)
        self.assertEqual(result, {"name": "John", "age": 30})

    def test_flatten_dict_nested(self):
        """Test flattening nested dictionary"""
        d = {"person": {"name": "John", "age": 30}}
        result = _flatten_dict(d)
        self.assertEqual(result, {"person.name": "John", "person.age": 30})

    def test_flatten_dict_with_list(self):
        """Test flattening dictionary with list"""
        d = {"names": ["John", "Jane"]}
        result = _flatten_dict(d)
        self.assertEqual(result, {"names": "John, Jane"})

    def test_format_question_list_table_no_params(self):
        """Test formatting question with no parameters"""
        question = FederatedQuestion(
            id="q3",
            name="No Params Question",
            description="Question without parameters",
            params=[],
            collections=[]
        )
        
        result = format_question_list_table([question])
        
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row['Parameters'], 0)
        self.assertEqual(row['Collections'], 0)
        self.assertEqual(row['Required Params'], 0)

    def test_format_question_list_table_no_collections(self):
        """Test formatting question with no collections"""
        question = FederatedQuestion(
            id="q4",
            name="No Collections Question",
            description="Question without collections",
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
        
        result = format_question_list_table([question])
        
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row['Parameters'], 1)
        self.assertEqual(row['Collections'], 0)
        self.assertEqual(row['Required Params'], 1)


if __name__ == '__main__':
    unittest.main()