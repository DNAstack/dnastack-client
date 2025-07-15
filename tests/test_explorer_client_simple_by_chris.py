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
            source={"source_id": "test_source", "external_id": "test_external"}
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

    @patch('dnastack.client.explorer.client.ResultIterator')
    def test_list_federated_questions(self, mock_result_iterator):
        """Test listing federated questions"""
        # Mock ResultIterator
        mock_iterator = Mock()
        mock_result_iterator.return_value = mock_iterator
        
        # Call method
        result = self.client.list_federated_questions()
        
        # Verify ResultIterator was created
        self.assertEqual(result, mock_iterator)
        # Verify ResultIterator was called with a loader
        mock_result_iterator.assert_called_once()

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
        
        # Mock session context manager
        self.mock_session.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.__exit__ = Mock(return_value=False)
        self.mock_session.get.return_value = mock_response
        
        # Call method
        result = self.client.describe_federated_question("q1")
        
        # Verify
        self.mock_session.get.assert_called_once_with(
            "https://test.example.com/api/questions/q1",
            trace_context=None
        )
        self.assertIsInstance(result, FederatedQuestion)
        self.assertEqual(result.id, "q1")
        self.assertEqual(result.name, "Test Question")

    @patch('dnastack.client.explorer.client.ResultIterator')
    def test_ask_federated_question_basic(self, mock_result_iterator):
        """Test asking a federated question"""
        # Mock the describe_federated_question method to return mock collections
        mock_question = Mock()
        mock_question.collections = [Mock(id="col1"), Mock(id="col2")]
        self.client.describe_federated_question = Mock(return_value=mock_question)
        
        # Mock ResultIterator
        mock_iterator = Mock()
        mock_result_iterator.return_value = mock_iterator
        
        # Call method with required inputs parameter
        inputs = {"param1": "value1"}
        result = self.client.ask_federated_question("q1", inputs=inputs)
        
        # Verify ResultIterator was created
        self.assertEqual(result, mock_iterator)
        mock_result_iterator.assert_called_once()

    @patch('dnastack.client.explorer.client.ResultIterator')
    def test_ask_federated_question_with_params(self, mock_result_iterator):
        """Test asking a federated question with parameters"""
        # Mock ResultIterator
        mock_iterator = Mock()
        mock_result_iterator.return_value = mock_iterator
        
        # Call method with parameters
        inputs = {"param1": "value1"}
        collections = ["collection1", "collection2"]
        
        result = self.client.ask_federated_question("q1", inputs=inputs, collections=collections)
        
        # Verify ResultIterator was created
        self.assertEqual(result, mock_iterator)
        mock_result_iterator.assert_called_once()

    def test_client_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client._session, self.mock_session)
        self.assertEqual(self.client.endpoint, self.mock_endpoint)


if __name__ == '__main__':
    unittest.main()