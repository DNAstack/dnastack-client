"""Working tests for explorer client to boost coverage"""
import unittest
from unittest.mock import Mock, patch, MagicMock


class TestExplorerClientWorking(unittest.TestCase):
    """Working tests for explorer client module"""

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_describe_federated_question_success(self, mock_create_session):
        """Test describe_federated_question successful response"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        # Create mock session with context manager support
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session
        
        # Mock the context manager behavior
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "q1",
            "name": "Test Question",
            "description": "Test",
            "params": [],
            "collections": []
        }
        mock_context.get.return_value = mock_response
        
        # Create client
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        # Call method
        question = client.describe_federated_question("q1")
        
        # Verify result
        self.assertEqual(question.id, "q1")
        self.assertEqual(question.name, "Test Question")
        
        # Verify session was used correctly
        mock_session.__enter__.assert_called_once()
        mock_context.get.assert_called_once()

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_federated_question_list_loader_success(self, mock_create_session):
        """Test FederatedQuestionListResultLoader successful loading"""
        from dnastack.client.explorer.client import FederatedQuestionListResultLoader
        
        # Create mock session with context manager
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "questions": [
                {
                    "id": "q1",
                    "name": "Test Question",
                    "description": "Test",
                    "params": [],
                    "collections": []
                }
            ]
        }
        mock_context.get.return_value = mock_response
        
        # Create loader
        loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session
        )
        
        # Test initial state
        self.assertTrue(loader.has_more())
        
        # Test loading
        questions = loader.load()
        
        # Verify results
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].id, "q1")
        
        # After loading, should not have more
        self.assertFalse(loader.has_more())
        
        # Verify session was used
        mock_session.__enter__.assert_called_once()
        mock_context.get.assert_called_once()

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_federated_question_list_loader_inactive_error(self, mock_create_session):
        """Test FederatedQuestionListResultLoader InactiveLoaderError"""
        from dnastack.client.explorer.client import FederatedQuestionListResultLoader
        from dnastack.client.result_iterator import InactiveLoaderError
        
        # Create mock session
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        mock_response = Mock()
        mock_response.json.return_value = {"questions": []}
        mock_context.get.return_value = mock_response
        
        loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session
        )
        
        loader.load()  # First load
        with self.assertRaises(InactiveLoaderError):
            loader.load()  # Second load should fail

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_federated_question_query_loader_response_formats(self, mock_create_session):
        """Test FederatedQuestionQueryResultLoader with different response formats"""
        from dnastack.client.explorer.client import FederatedQuestionQueryResultLoader
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        
        # Create mock session
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        # Test list response
        mock_response = Mock()
        mock_response.json.return_value = [{"result": "data1"}, {"result": "data2"}]
        mock_context.post.return_value = mock_response
        
        loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        
        results = loader.load()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["result"], "data1")
        
        # Test dict response with 'data' key
        loader2 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        mock_response.json.return_value = {"data": [{"result": "data3"}]}
        results2 = loader2.load()
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["result"], "data3")
        
        # Test dict response with 'results' key
        loader3 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        mock_response.json.return_value = {"results": [{"result": "data4"}]}
        results3 = loader3.load()
        self.assertEqual(len(results3), 1)
        self.assertEqual(results3[0]["result"], "data4")
        
        # Test single dict response
        loader4 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        mock_response.json.return_value = {"single": "result"}
        results4 = loader4.load()
        self.assertEqual(len(results4), 1)
        self.assertEqual(results4[0]["single"], "result")
        
        # Test non-dict, non-list response
        loader5 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        mock_response.json.return_value = "simple_string"
        results5 = loader5.load()
        self.assertEqual(len(results5), 1)
        self.assertEqual(results5[0], "simple_string")

    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_federated_question_query_loader_inactive_error(self, mock_create_session):
        """Test FederatedQuestionQueryResultLoader InactiveLoaderError"""
        from dnastack.client.explorer.client import FederatedQuestionQueryResultLoader
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        from dnastack.client.result_iterator import InactiveLoaderError
        
        # Create mock session
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_context.post.return_value = mock_response
        
        loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        
        loader.load()  # First load
        with self.assertRaises(InactiveLoaderError):
            loader.load()  # Second load should fail

    def test_loader_initialization_with_trace(self):
        """Test loader initialization with trace parameter"""
        from dnastack.client.explorer.client import (
            FederatedQuestionListResultLoader,
            FederatedQuestionQueryResultLoader
        )
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        from dnastack.http.session import HttpSession
        from dnastack.common.tracing import Span
        
        # Mock session and trace
        mock_session = Mock(spec=HttpSession)
        mock_trace = Mock(spec=Span)
        
        # Test FederatedQuestionListResultLoader with trace
        list_loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session,
            trace=mock_trace
        )
        self.assertTrue(list_loader.has_more())
        
        # Test FederatedQuestionQueryResultLoader with trace
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        query_loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload,
            trace=mock_trace
        )
        self.assertTrue(query_loader.has_more())

    @patch('dnastack.client.explorer.client.urljoin')
    @patch('dnastack.client.explorer.client.ExplorerClient.create_http_session')
    def test_url_construction_coverage(self, mock_create_session, mock_urljoin):
        """Test URL construction coverage"""
        from dnastack.client.explorer.client import ExplorerClient
        from dnastack.client.models import ServiceEndpoint
        
        # Mock urljoin returns
        mock_urljoin.side_effect = [
            "https://example.com/questions",
            "https://example.com/questions/q1",
            "https://example.com/questions/q1/query"
        ]
        
        # Mock session
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session
        
        # Create client
        mock_endpoint = Mock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        # Test list_federated_questions URL construction
        client.list_federated_questions()
        
        # Test ask_federated_question URL construction (without describe call)
        with patch.object(client, 'describe_federated_question') as mock_describe:
            from dnastack.client.explorer.models import FederatedQuestion, QuestionCollection
            
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
            
            client.ask_federated_question(
                question_id="q1",
                inputs={"param1": "value1"}
            )
        
        # Verify urljoin was called for URL construction
        self.assertGreater(mock_urljoin.call_count, 0)

    def test_service_constant_coverage(self):
        """Test service constant to ensure it's covered"""
        from dnastack.client.explorer.client import EXPLORER_SERVICE_TYPE_V1_0
        
        # Access all attributes to ensure coverage
        group = EXPLORER_SERVICE_TYPE_V1_0.group
        artifact = EXPLORER_SERVICE_TYPE_V1_0.artifact
        version = EXPLORER_SERVICE_TYPE_V1_0.version
        
        self.assertEqual(group, 'com.dnastack.explorer')
        self.assertEqual(artifact, 'collection-service')
        self.assertEqual(version, '1.0.0')


if __name__ == '__main__':
    unittest.main()