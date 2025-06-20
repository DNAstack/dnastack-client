import unittest
from unittest.mock import Mock, patch, MagicMock
import json

from dnastack.client.explorer.client import ExplorerClient
from dnastack.client.explorer.models import FederatedQuestion, QuestionParam, QuestionCollection
from dnastack.client.models import ServiceType
from dnastack.client.result_iterator import ResultLoader


class TestExplorerClient(unittest.TestCase):

    def setUp(self):
        """Set up test client and mock data"""
        # Mock session and endpoint
        self.mock_session = Mock()
        self.mock_endpoint = Mock()
        self.mock_endpoint.adapter_type = "com.dnastack.explorer:questions:1.0.0"
        
        # Create client
        self.client = ExplorerClient(
            session=self.mock_session,
            endpoint=self.mock_endpoint
        )
        
        # Sample test data
        self.sample_question_data = {
            "id": "q1",
            "name": "Test Question",
            "description": "A test question",
            "params": [
                {
                    "name": "param1",
                    "description": "Test parameter",
                    "input_type": "string",
                    "required": True
                }
            ],
            "collections": [
                {
                    "slug": "collection1"
                }
            ]
        }

    def test_service_type(self):
        """Test service type definition"""
        expected_service_type = ServiceType(
            group='com.dnastack.explorer',
            artifact='collection-service',
            version='1.0.0'
        )
        self.assertEqual(self.client.service_type, expected_service_type)

    def test_adapter_type(self):
        """Test adapter type"""
        self.assertEqual(self.client.adapter_type, "com.dnastack.explorer:questions:1.0.0")

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_list_federated_questions(self, mock_result_loader):
        """Test listing federated questions"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {
            "questions": [self.sample_question_data]
        }
        self.mock_session.get.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader_instance = Mock()
        mock_result_loader.return_value = mock_loader_instance
        
        # Call the method
        result = self.client.list_federated_questions()
        
        # Verify the session was called correctly
        self.mock_session.get.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions"
        )
        
        # Verify ResultLoader was created
        mock_result_loader.assert_called_once()
        self.assertEqual(result, mock_loader_instance)

    def test_describe_federated_question(self):
        """Test describing a federated question"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = self.sample_question_data
        self.mock_session.get.return_value = mock_response
        
        # Call the method
        result = self.client.describe_federated_question("q1")
        
        # Verify the session was called correctly
        self.mock_session.get.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions/q1"
        )
        
        # Verify the result is a FederatedQuestion
        self.assertIsInstance(result, FederatedQuestion)
        self.assertEqual(result.id, "q1")
        self.assertEqual(result.name, "Test Question")

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_basic(self, mock_result_loader):
        """Test asking a federated question with basic parameters"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"col1": "value1"}]}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader_instance = Mock()
        mock_result_loader.return_value = mock_loader_instance
        
        # Call the method
        result = self.client.ask_federated_question("q1")
        
        # Verify the session was called correctly
        self.mock_session.post.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions/q1/ask",
            json={}
        )
        
        # Verify ResultLoader was created
        mock_result_loader.assert_called_once()
        self.assertEqual(result, mock_loader_instance)

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_with_args(self, mock_result_loader):
        """Test asking a federated question with arguments"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"col1": "value1"}]}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader_instance = Mock()
        mock_result_loader.return_value = mock_loader_instance
        
        # Test arguments
        args = {"param1": "value1", "param2": "value2"}
        
        # Call the method
        result = self.client.ask_federated_question("q1", args=args)
        
        # Verify the session was called correctly
        expected_payload = {"args": args}
        self.mock_session.post.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions/q1/ask",
            json=expected_payload
        )
        
        # Verify ResultLoader was created
        mock_result_loader.assert_called_once()
        self.assertEqual(result, mock_loader_instance)

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_with_collections(self, mock_result_loader):
        """Test asking a federated question with collections filter"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"col1": "value1"}]}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader_instance = Mock()
        mock_result_loader.return_value = mock_loader_instance
        
        # Test collections
        collections = ["collection1", "collection2"]
        
        # Call the method
        result = self.client.ask_federated_question("q1", collections=collections)
        
        # Verify the session was called correctly
        expected_payload = {"collections": collections}
        self.mock_session.post.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions/q1/ask",
            json=expected_payload
        )
        
        # Verify ResultLoader was created
        mock_result_loader.assert_called_once()
        self.assertEqual(result, mock_loader_instance)

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_with_all_params(self, mock_result_loader):
        """Test asking a federated question with all parameters"""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"col1": "value1"}]}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader_instance = Mock()
        mock_result_loader.return_value = mock_loader_instance
        
        # Test parameters
        args = {"param1": "value1"}
        collections = ["collection1"]
        
        # Call the method
        result = self.client.ask_federated_question("q1", args=args, collections=collections)
        
        # Verify the session was called correctly
        expected_payload = {
            "args": args,
            "collections": collections
        }
        self.mock_session.post.assert_called_once_with(
            f"{self.mock_endpoint.url}/questions/q1/ask",
            json=expected_payload
        )
        
        # Verify ResultLoader was created
        mock_result_loader.assert_called_once()
        self.assertEqual(result, mock_loader_instance)

    def test_describe_federated_question_with_complex_data(self):
        """Test describing a question with complex parameter data"""
        complex_question_data = {
            "id": "complex_q",
            "name": "Complex Question",
            "description": "A complex question with multiple parameters",
            "params": [
                {
                    "name": "required_param",
                    "description": "Required parameter",
                    "input_type": "string",
                    "required": True
                },
                {
                    "name": "optional_param",
                    "description": "Optional parameter",
                    "input_type": "integer",
                    "required": False
                }
            ],
            "collections": [
                {"slug": "collection1"},
                {"slug": "collection2"},
                {"slug": "collection3"}
            ]
        }
        
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = complex_question_data
        self.mock_session.get.return_value = mock_response
        
        # Call the method
        result = self.client.describe_federated_question("complex_q")
        
        # Verify the result
        self.assertIsInstance(result, FederatedQuestion)
        self.assertEqual(result.id, "complex_q")
        self.assertEqual(len(result.params), 2)
        self.assertEqual(len(result.collections), 3)
        
        # Verify parameter details
        required_param = next(p for p in result.params if p.name == "required_param")
        self.assertTrue(required_param.required)
        self.assertEqual(required_param.input_type, "string")
        
        optional_param = next(p for p in result.params if p.name == "optional_param")
        self.assertFalse(optional_param.required)
        self.assertEqual(optional_param.input_type, "integer")

    def test_client_initialization(self):
        """Test client initialization"""
        self.assertIsNotNone(self.client.session)
        self.assertIsNotNone(self.client.endpoint)
        self.assertEqual(self.client.session, self.mock_session)
        self.assertEqual(self.client.endpoint, self.mock_endpoint)

    def test_endpoint_url_construction(self):
        """Test that endpoint URL is properly used"""
        # Set a specific URL
        self.mock_endpoint.url = "https://example.com/api"
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = self.sample_question_data
        self.mock_session.get.return_value = mock_response
        
        # Call method
        self.client.describe_federated_question("test_id")
        
        # Verify URL construction
        self.mock_session.get.assert_called_once_with(
            "https://example.com/api/questions/test_id"
        )


if __name__ == '__main__':
    unittest.main()