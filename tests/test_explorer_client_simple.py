import unittest
from unittest.mock import Mock, patch

from dnastack.client.explorer.client import ExplorerClient
from dnastack.client.explorer.models import FederatedQuestion


class TestExplorerClientSimple(unittest.TestCase):
    """Simple ExplorerClient tests for coverage"""

    def setUp(self):
        """Set up test client"""
        from dnastack.client.models import ServiceEndpoint
        
        # Create a proper ServiceEndpoint mock
        self.mock_endpoint = ServiceEndpoint(
            id="test_endpoint",
            url="https://test.example.com/api",
            type={"group": "com.dnastack.explorer", "artifact": "collection-service", "version": "1.0.0"},
            mode="test",
            source="test"
        )
        
        self.client = ExplorerClient(endpoint=self.mock_endpoint)
        
        # Mock the session after client creation
        self.mock_session = Mock()
        self.client._session = self.mock_session

    def test_service_type(self):
        """Test service type property"""
        supported_types = ExplorerClient.get_supported_service_types()
        self.assertEqual(len(supported_types), 1)
        service_type = supported_types[0]
        self.assertEqual(service_type.group, 'com.dnastack.explorer')
        self.assertEqual(service_type.artifact, 'collection-service')
        self.assertEqual(service_type.version, '1.0.0')

    def test_adapter_type(self):
        """Test adapter type property"""
        adapter_type = ExplorerClient.get_adapter_type()
        self.assertEqual(adapter_type, "com.dnastack.explorer:questions:1.0.0")

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_list_federated_questions(self, mock_result_loader):
        """Test listing federated questions"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"questions": []}
        self.mock_session.get.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader = Mock()
        mock_result_loader.return_value = mock_loader
        
        # Call method
        result = self.client.list_federated_questions()
        
        # Verify - use the actual endpoint URL
        expected_url = self.mock_endpoint.url + "/questions"
        self.mock_session.get.assert_called_once_with(expected_url)
        self.assertEqual(result, mock_loader)

    def test_describe_federated_question(self):
        """Test describing a federated question"""
        # Sample question data with proper field names
        question_data = {
            "id": "q1",
            "name": "Test Question",
            "description": "A test question",
            "params": [
                {
                    "id": "1",
                    "name": "param1",
                    "label": "Parameter 1",
                    "inputType": "string",
                    "description": "Test parameter",
                    "required": True
                }
            ],
            "collections": [
                {
                    "id": "1",
                    "name": "Collection 1",
                    "slug": "collection1",
                    "questionId": "q1"
                }
            ]
        }
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = question_data
        self.mock_session.get.return_value = mock_response
        
        # Call method
        result = self.client.describe_federated_question("q1")
        
        # Verify
        expected_url = self.mock_endpoint.url + "/questions/q1"
        self.mock_session.get.assert_called_once_with(expected_url)
        self.assertIsInstance(result, FederatedQuestion)
        self.assertEqual(result.id, "q1")
        self.assertEqual(result.name, "Test Question")

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_basic(self, mock_result_loader):
        """Test asking a federated question"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader = Mock()
        mock_result_loader.return_value = mock_loader
        
        # Call method
        result = self.client.ask_federated_question("q1")
        
        # Verify
        expected_url = self.mock_endpoint.url + "/questions/q1/ask"
        self.mock_session.post.assert_called_once_with(expected_url, json={})
        self.assertEqual(result, mock_loader)

    @patch('dnastack.client.explorer.client.ResultLoader')
    def test_ask_federated_question_with_params(self, mock_result_loader):
        """Test asking a federated question with parameters"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        self.mock_session.post.return_value = mock_response
        
        # Mock ResultLoader
        mock_loader = Mock()
        mock_result_loader.return_value = mock_loader
        
        # Call method with parameters
        args = {"param1": "value1"}
        collections = ["collection1", "collection2"]
        
        result = self.client.ask_federated_question("q1", args=args, collections=collections)
        
        # Verify
        expected_payload = {
            "args": args,
            "collections": collections
        }
        expected_url = self.mock_endpoint.url + "/questions/q1/ask"
        self.mock_session.post.assert_called_once_with(expected_url, json=expected_payload)
        self.assertEqual(result, mock_loader)

    def test_client_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client._session, self.mock_session)
        self.assertEqual(self.client.endpoint, self.mock_endpoint)


if __name__ == '__main__':
    unittest.main()