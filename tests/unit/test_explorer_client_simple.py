"""Simple tests for explorer client module to boost coverage"""
import unittest
from unittest.mock import Mock, patch


class TestExplorerClientSimple(unittest.TestCase):
    """Simple tests for explorer client module"""

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_client_initialization(self, mock_create_session):
        """Test ExplorerClient initialization"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        # Mock session
        mock_session = Mock()
        mock_create_session.return_value = mock_session
        
        # Create mock endpoint
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        # Initialize client
        client = ExplorerClient(mock_endpoint)
        
        # Verify initialization
        self.assertEqual(client._endpoint, mock_endpoint)
        self.assertEqual(client._session, mock_session)
        mock_create_session.assert_called_once()

    def test_client_static_methods(self):
        """Test ExplorerClient static methods"""
        from dnastack.client.explorer.client import ExplorerClient, EXPLORER_SERVICE_TYPE_V1_0
        
        # Test get_supported_service_types
        service_types = ExplorerClient.get_supported_service_types()
        self.assertEqual(len(service_types), 1)
        self.assertEqual(service_types[0], EXPLORER_SERVICE_TYPE_V1_0)
        
        # Test get_adapter_type
        adapter_type = ExplorerClient.get_adapter_type()
        self.assertEqual(adapter_type, "com.dnastack.explorer:questions:1.0.0")

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_list_federated_questions_method(self, mock_create_session):
        """Test list_federated_questions method"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        # Mock session
        mock_session = Mock()
        mock_create_session.return_value = mock_session
        
        # Create client
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        client = ExplorerClient(mock_endpoint)
        
        # Call the method
        result_iter = client.list_federated_questions()
        
        # Verify we get a ResultIterator
        from dnastack.client.result_iterator import ResultIterator
        self.assertIsInstance(result_iter, ResultIterator)

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    @patch('dnastack.client.explorer.client.ExplorerClient.describe_federated_question')
    def test_ask_federated_question_method(self, mock_describe, mock_create_session):
        """Test ask_federated_question method"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        from dnastack.client.explorer.models import FederatedQuestion, QuestionCollection
        
        # Mock session
        mock_session = Mock()
        mock_create_session.return_value = mock_session
        
        # Create client
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        client = ExplorerClient(mock_endpoint)
        
        # Test with collections=None (should get collections from question)
        collection = QuestionCollection(
            id="c1",
            name="Collection 1",
            slug="collection-1",
            questionId="q1"
        )
        
        test_question = FederatedQuestion(
            id="q1",
            name="Test Question",
            description="Test",
            params=[],
            collections=[collection]
        )
        
        mock_describe.return_value = test_question
        
        result_iter = client.ask_federated_question(
            question_id="q1",
            inputs={"param1": "value1"}
        )
        
        # Verify we get a ResultIterator
        from dnastack.client.result_iterator import ResultIterator
        self.assertIsInstance(result_iter, ResultIterator)
        
        # Verify describe was called to get collections
        mock_describe.assert_called_once()
        
        # Test with explicit collections
        result_iter2 = client.ask_federated_question(
            question_id="q1",
            inputs={"param1": "value1"},
            collections=["c1", "c2"]
        )
        
        self.assertIsInstance(result_iter2, ResultIterator)

    def test_federated_question_list_result_loader_basic(self):
        """Test FederatedQuestionListResultLoader basic functionality"""
        from dnastack.client.explorer.client import FederatedQuestionListResultLoader
        from dnastack.http.session import HttpSession
        
        # Mock session
        mock_session = Mock(spec=HttpSession)
        
        # Create loader
        loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session
        )
        
        # Test has_more
        self.assertTrue(loader.has_more())
        
        # Test that loader has expected attributes
        self.assertTrue(hasattr(loader, 'load'))
        self.assertTrue(hasattr(loader, 'has_more'))

    def test_federated_question_query_result_loader_basic(self):
        """Test FederatedQuestionQueryResultLoader basic functionality"""
        from dnastack.client.explorer.client import FederatedQuestionQueryResultLoader
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        from dnastack.http.session import HttpSession
        
        # Mock session
        mock_session = Mock(spec=HttpSession)
        
        # Create request payload
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        # Create loader
        loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        
        # Test has_more
        self.assertTrue(loader.has_more())
        
        # Test that loader has expected attributes
        self.assertTrue(hasattr(loader, 'load'))
        self.assertTrue(hasattr(loader, 'has_more'))

    def test_service_type_constant(self):
        """Test the EXPLORER_SERVICE_TYPE_V1_0 constant"""
        from dnastack.client.explorer.client import EXPLORER_SERVICE_TYPE_V1_0
        
        # Test service type properties
        self.assertEqual(EXPLORER_SERVICE_TYPE_V1_0.group, 'com.dnastack.explorer')
        self.assertEqual(EXPLORER_SERVICE_TYPE_V1_0.artifact, 'collection-service')
        self.assertEqual(EXPLORER_SERVICE_TYPE_V1_0.version, '1.0.0')

    def test_client_url_property(self):
        """Test client URL property access"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        # Create mock endpoint
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/api"
        
        with patch.object(ExplorerClient, 'create_http_session') as mock_create_session:
            mock_session = Mock()
            mock_create_session.return_value = mock_session
            
            client = ExplorerClient(mock_endpoint)
            
            # Test that url property is accessible
            self.assertEqual(client.url, "https://example.com/api/")

    def test_client_methods_exist(self):
        """Test that client methods exist and are callable"""
        from dnastack.client.explorer.client import ExplorerClient
        
        # Test that expected methods exist
        self.assertTrue(hasattr(ExplorerClient, 'list_federated_questions'))
        self.assertTrue(hasattr(ExplorerClient, 'describe_federated_question'))
        self.assertTrue(hasattr(ExplorerClient, 'ask_federated_question'))
        
        # Test that methods are callable
        self.assertTrue(callable(ExplorerClient.list_federated_questions))
        self.assertTrue(callable(ExplorerClient.describe_federated_question))
        self.assertTrue(callable(ExplorerClient.ask_federated_question))


if __name__ == '__main__':
    unittest.main()