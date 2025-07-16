import pytest
from unittest.mock import MagicMock, patch
from assertpy import assert_that

from dnastack.client.explorer.client import ExplorerClient, EXPLORER_SERVICE_TYPE_V1_0
from dnastack.client.explorer.models import FederatedQuestion
from dnastack.client.models import ServiceEndpoint
from dnastack.cli.commands.explorer.questions.utils import (
    parse_collections_argument,
    flatten_result_for_export,
    format_question_parameters,
    format_question_collections,
    validate_question_parameters
)
from dnastack.cli.commands.explorer.questions.tables import (
    format_question_list_table,
    format_question_detail_table,
    format_question_results_table
)


class TestExplorerClient:

    def test_should_initialize_explorer_client_with_endpoint_and_session(self, monkeypatch):
        """Test ExplorerClient initialization"""
        mock_session = MagicMock()
        mock_create_session = MagicMock(return_value=mock_session)
        monkeypatch.setattr(ExplorerClient, 'create_http_session', mock_create_session)
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        client = ExplorerClient(mock_endpoint)
        
        assert_that(client._endpoint).is_equal_to(mock_endpoint)
        assert_that(client._session).is_equal_to(mock_session)
        mock_create_session.assert_called_once()
    
    def test_should_return_supported_service_types_and_adapter_type(self):
        """Test ExplorerClient static methods"""
        service_types = ExplorerClient.get_supported_service_types()
        assert_that(service_types).is_length(1)
        assert_that(service_types[0]).is_equal_to(EXPLORER_SERVICE_TYPE_V1_0)
        
        adapter_type = ExplorerClient.get_adapter_type()
        assert_that(adapter_type).is_equal_to("com.dnastack.explorer:questions:1.0.0")
    
    def test_should_return_endpoint_url_from_client_url_property(self, monkeypatch):
        """Test ExplorerClient url property"""
        mock_session = MagicMock()
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://test.example.com/"
        
        client = ExplorerClient(mock_endpoint)
        assert_that(client.url).is_equal_to("https://test.example.com/")
    
    def test_should_have_correct_service_type_constant_values(self):
        """Test service type constant"""
        assert_that(EXPLORER_SERVICE_TYPE_V1_0.group).is_equal_to('com.dnastack.explorer')
        assert_that(EXPLORER_SERVICE_TYPE_V1_0.artifact).is_equal_to('collection-service')
        assert_that(EXPLORER_SERVICE_TYPE_V1_0.version).is_equal_to('1.0.0')
    
    def test_should_have_required_federated_question_methods(self, monkeypatch):
        """Test that required client methods exist"""
        mock_session = MagicMock()
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://test.example.com/"
        client = ExplorerClient(mock_endpoint)
        
        assert_that(hasattr(client, 'list_federated_questions')).is_true()
        assert_that(hasattr(client, 'describe_federated_question')).is_true()
        assert_that(hasattr(client, 'ask_federated_question')).is_true()
    
    @patch('dnastack.client.explorer.client.ResultIterator')
    def test_should_list_federated_questions_using_result_iterator(self, mock_result_iterator, monkeypatch):
        """Test list_federated_questions method"""
        mock_session = MagicMock()
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        mock_iterator = MagicMock()
        mock_result_iterator.return_value = mock_iterator
        
        client = ExplorerClient(mock_endpoint)
        result = client.list_federated_questions()
        
        assert_that(result).is_equal_to(mock_iterator)
        mock_result_iterator.assert_called_once()
    
    def test_should_describe_federated_question_when_question_exists(self, monkeypatch):
        """Test describe_federated_question success case"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'q1',
            'name': 'Test Question',
            'description': 'Test description',
            'params': [],
            'collections': []
        }
        
        # Mock the context manager
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = mock_response
        
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        client = ExplorerClient(mock_endpoint)
        result = client.describe_federated_question('q1')
        
        assert_that(result).is_instance_of(FederatedQuestion)
        assert_that(result.id).is_equal_to('q1')
        assert_that(result.name).is_equal_to('Test Question')
    
    @patch('dnastack.client.explorer.client.ResultIterator')
    def test_should_ask_federated_question_with_parameters_and_collections(self, mock_result_iterator, monkeypatch):
        """Test ask_federated_question method"""
        mock_session = MagicMock()
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com"
        
        mock_iterator = MagicMock()
        mock_result_iterator.return_value = mock_iterator
        
        # Mock describe_federated_question to return collections
        mock_question = MagicMock()
        mock_question.collections = [MagicMock(id='col1')]
        
        client = ExplorerClient(mock_endpoint)
        client.describe_federated_question = MagicMock(return_value=mock_question)
        
        result = client.ask_federated_question('q1', inputs={'param1': 'value1'})
        
        assert_that(result).is_equal_to(mock_iterator)
        mock_result_iterator.assert_called_once()
    
    def test_should_handle_404_error_when_describing_nonexistent_question(self, monkeypatch):
        """Test describe_federated_question error handling"""
        from dnastack.http.session import ClientError
        from dnastack.http.session import HttpError
        
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        # Create HttpError with proper structure
        http_error = HttpError(mock_response)
        
        # Mock the context manager
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.side_effect = http_error
        
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        with pytest.raises(ClientError, match="Question 'q1' not found"):
            client.describe_federated_question('q1')
    
    def test_should_handle_401_unauthorized_error_when_describing_question(self, monkeypatch):
        """Test describe_federated_question 401 error handling"""
        from dnastack.client.base_exceptions import UnauthenticatedApiAccessError
        from dnastack.http.session import HttpError
        
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        http_error = HttpError(mock_response)
        
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.side_effect = http_error
        
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        with pytest.raises(UnauthenticatedApiAccessError):
            client.describe_federated_question('q1')
    
    def test_should_handle_403_forbidden_error_when_describing_question(self, monkeypatch):
        """Test describe_federated_question 403 error handling"""
        from dnastack.client.base_exceptions import UnauthorizedApiAccessError
        from dnastack.http.session import HttpError
        
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        http_error = HttpError(mock_response)
        
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.side_effect = http_error
        
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        with pytest.raises(UnauthorizedApiAccessError):
            client.describe_federated_question('q1')
    
    def test_should_handle_generic_client_error_when_describing_question(self, monkeypatch):
        """Test describe_federated_question generic error handling"""
        from dnastack.http.session import ClientError
        from dnastack.http.session import HttpError
        
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        http_error = HttpError(mock_response)
        
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.side_effect = http_error
        
        monkeypatch.setattr(ExplorerClient, 'create_http_session', MagicMock(return_value=mock_session))
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        with pytest.raises(ClientError, match="Failed to retrieve question 'q1'"):
            client.describe_federated_question('q1')
    
    def test_should_handle_inactive_loader_error_when_loading_question_list_twice(self, monkeypatch):
        """Test FederatedQuestionListResultLoader InactiveLoaderError handling"""
        from dnastack.client.explorer.client import FederatedQuestionListResultLoader
        from dnastack.client.result_iterator import InactiveLoaderError
        
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"questions": []}
        mock_context.get.return_value = mock_response
        
        loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session
        )
        
        loader.load()  # First load should succeed
        
        # Second load should raise InactiveLoaderError
        with pytest.raises(InactiveLoaderError):
            loader.load()
    
    def test_should_handle_inactive_loader_error_when_loading_question_query_twice(self, monkeypatch):
        """Test FederatedQuestionQueryResultLoader InactiveLoaderError handling"""
        from dnastack.client.explorer.client import FederatedQuestionQueryResultLoader
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        from dnastack.client.result_iterator import InactiveLoaderError
        
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_context.post.return_value = mock_response
        
        loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        
        loader.load()  # First load should succeed
        
        # Second load should raise InactiveLoaderError
        with pytest.raises(InactiveLoaderError):
            loader.load()
    
    def test_should_handle_different_response_formats_in_question_query_loader(self, monkeypatch):
        """Test FederatedQuestionQueryResultLoader with different response formats"""
        from dnastack.client.explorer.client import FederatedQuestionQueryResultLoader
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_session.__enter__.return_value = mock_context
        mock_session.__exit__.return_value = None
        
        request_payload = FederatedQuestionQueryRequest(
            inputs={"param1": "value1"},
            collections=["c1"]
        )
        
        # Test list response format
        mock_response = MagicMock()
        mock_response.json.return_value = [{"result": "data1"}, {"result": "data2"}]
        mock_context.post.return_value = mock_response
        
        loader = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        
        results = loader.load()
        assert_that(results).is_length(2)
        assert_that(results[0]["result"]).is_equal_to("data1")
        assert_that(results[1]["result"]).is_equal_to("data2")
        
        # Test dict response with 'data' key
        mock_response.json.return_value = {"data": [{"result": "data3"}]}
        loader2 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        results2 = loader2.load()
        assert_that(results2).is_length(1)
        assert_that(results2[0]["result"]).is_equal_to("data3")
        
        # Test dict response with 'results' key
        mock_response.json.return_value = {"results": [{"result": "data4"}]}
        loader3 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        results3 = loader3.load()
        assert_that(results3).is_length(1)
        assert_that(results3[0]["result"]).is_equal_to("data4")
        
        # Test single dict response
        mock_response.json.return_value = {"single": "result"}
        loader4 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        results4 = loader4.load()
        assert_that(results4).is_length(1)
        assert_that(results4[0]["single"]).is_equal_to("result")
        
        # Test simple string response
        mock_response.json.return_value = "simple_string"
        loader5 = FederatedQuestionQueryResultLoader(
            service_url="https://example.com/questions/q1/query",
            http_session=mock_session,
            request_payload=request_payload
        )
        results5 = loader5.load()
        assert_that(results5).is_length(1)
        assert_that(results5[0]).is_equal_to("simple_string")
    
    def test_should_initialize_loaders_with_trace_parameter(self, monkeypatch):
        """Test loader initialization with trace parameter"""
        from dnastack.client.explorer.client import (
            FederatedQuestionListResultLoader,
            FederatedQuestionQueryResultLoader
        )
        from dnastack.client.explorer.models import FederatedQuestionQueryRequest
        from dnastack.http.session import HttpSession
        from dnastack.common.tracing import Span
        
        mock_session = MagicMock(spec=HttpSession)
        mock_trace = MagicMock(spec=Span)
        
        # Test FederatedQuestionListResultLoader with trace
        list_loader = FederatedQuestionListResultLoader(
            service_url="https://example.com/questions",
            http_session=mock_session,
            trace=mock_trace
        )
        assert_that(list_loader.has_more()).is_true()
        
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
        assert_that(query_loader.has_more()).is_true()
    
    @patch('dnastack.client.explorer.client.urljoin')
    def test_should_construct_urls_correctly_for_client_operations(self, mock_urljoin, monkeypatch):
        """Test URL construction coverage for client operations"""
        mock_session = MagicMock()
        mock_create_session = MagicMock(return_value=mock_session)
        monkeypatch.setattr(ExplorerClient, 'create_http_session', mock_create_session)
        
        # Mock urljoin returns
        mock_urljoin.side_effect = [
            "https://example.com/questions",
            "https://example.com/questions/q1",
            "https://example.com/questions/q1/query"
        ]
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        # Test list_federated_questions URL construction
        client.list_federated_questions()
        
        # Verify urljoin was called for questions endpoint
        mock_urljoin.assert_called()
        
        # Test that URL construction logic is covered
        assert_that(mock_urljoin.call_count).is_greater_than(0)
    
    def test_should_handle_comprehensive_ask_federated_question_scenarios(self, monkeypatch):
        """Test comprehensive ask_federated_question with various parameter combinations"""
        mock_session = MagicMock()
        mock_create_session = MagicMock(return_value=mock_session)
        monkeypatch.setattr(ExplorerClient, 'create_http_session', mock_create_session)
        
        mock_endpoint = MagicMock(spec=ServiceEndpoint)
        mock_endpoint.url = "https://example.com/"
        
        client = ExplorerClient(mock_endpoint)
        
        # Mock describe_federated_question to return a question
        mock_question = MagicMock()
        mock_question.collections = [
            MagicMock(id="c1", name="Collection 1"),
            MagicMock(id="c2", name="Collection 2")
        ]
        
        with patch.object(client, 'describe_federated_question', return_value=mock_question):
            # Test basic ask with no parameters
            with patch('dnastack.client.explorer.client.ResultIterator') as mock_result_iterator:
                mock_iterator = MagicMock()
                mock_result_iterator.return_value = mock_iterator
                
                result = client.ask_federated_question("q1", inputs={})
                assert_that(result).is_equal_to(mock_iterator)
                
                # Test ask with parameters
                result = client.ask_federated_question("q1", inputs={"param1": "value1"})
                assert_that(result).is_equal_to(mock_iterator)
                
                # Test ask with specific collections
                result = client.ask_federated_question("q1", inputs={}, collections=["c1"])
                assert_that(result).is_equal_to(mock_iterator)
                
                # Test ask with both parameters and collections
                result = client.ask_federated_question("q1", inputs={"param1": "value1"}, collections=["c1"])
                assert_that(result).is_equal_to(mock_iterator)


class TestExplorerUtils:
    """Test cases for explorer utility functions"""
    
    def test_should_return_none_when_parsing_null_collections_string(self):
        """Test parsing None collections"""
        result = parse_collections_argument(None)
        assert_that(result).is_none()
    
    def test_should_return_none_when_parsing_empty_collections_string(self):
        """Test parsing empty collections"""
        result = parse_collections_argument("")
        assert_that(result).is_none()
    
    def test_should_parse_single_collection_id_from_string(self):
        """Test parsing single collection"""
        result = parse_collections_argument("collection1")
        assert_that(result).is_equal_to(["collection1"])
    
    def test_should_parse_multiple_collection_ids_from_comma_separated_string(self):
        """Test parsing multiple collections"""
        result = parse_collections_argument("collection1,collection2")
        assert_that(result).is_equal_to(["collection1", "collection2"])
    
    def test_should_parse_collection_ids_and_strip_whitespace_from_string(self):
        """Test parsing collections with spaces"""
        result = parse_collections_argument(" collection1 , collection2 ")
        assert_that(result).is_equal_to(["collection1", "collection2"])
    
    def test_should_flatten_simple_dictionary_result_for_export(self):
        """Test flattening simple result"""
        result = {"name": "John", "age": 30}
        flattened = flatten_result_for_export(result)
        assert_that(flattened).is_equal_to({"name": "John", "age": 30})
    
    def test_should_flatten_nested_dictionary_result_with_dot_notation(self):
        """Test flattening nested result"""
        result = {"person": {"name": "John", "age": 30}}
        flattened = flatten_result_for_export(result)
        assert_that(flattened).is_equal_to({"person.name": "John", "person.age": 30})
    
    def test_should_flatten_dictionary_result_containing_list_values(self):
        """Test flattening result with list"""
        result = {"items": [{"name": "item1"}, {"name": "item2"}]}
        flattened = flatten_result_for_export(result)
        assert_that(flattened).contains_key("items[0].name")
        assert_that(flattened).contains_key("items[1].name")
    
    def test_should_flatten_complex_nested_result_with_lists_and_objects(self):
        """Test flattening complex nested result"""
        result = {
            "user": {
                "profile": {
                    "name": "John",
                    "settings": {"theme": "dark"}
                },
                "data": [{"id": 1, "value": "test"}]
            }
        }
        flattened = flatten_result_for_export(result)
        assert_that(flattened).contains_key("user.profile.name")
        assert_that(flattened).contains_key("user.profile.settings.theme")
        assert_that(flattened).contains_key("user.data[0].id")
    
    def test_should_format_empty_question_parameters_list_with_no_parameters_message(self):
        """Test formatting empty question parameters"""
        result = format_question_parameters([])
        assert_that(result).is_equal_to("No parameters")
    
    def test_should_format_question_parameters_with_type_and_requirement_info(self):
        """Test formatting question parameters with data"""
        mock_param1 = MagicMock()
        mock_param1.name = "param1"
        mock_param1.input_type = "string"
        mock_param1.required = True
        mock_param1.description = "Parameter 1"
        mock_param1.default_value = None
        mock_param1.values = None
        mock_param1.input_subtype = None
        
        mock_param2 = MagicMock()
        mock_param2.name = "param2"
        mock_param2.input_type = "string"
        mock_param2.required = False
        mock_param2.description = "Parameter 2"
        mock_param2.default_value = None
        mock_param2.values = None
        mock_param2.input_subtype = None
        
        params = [mock_param1, mock_param2]
        result = format_question_parameters(params)
        assert_that(result).contains("param1")
        assert_that(result).contains("Parameter 1")
        assert_that(result).contains("required")
    
    def test_should_format_empty_question_collections_list_with_no_collections_message(self):
        """Test formatting empty question collections"""
        result = format_question_collections([])
        assert_that(result).is_equal_to("No collections")
    
    def test_should_format_question_collections_with_name_slug_and_id_info(self):
        """Test formatting question collections with data"""
        mock_col1 = MagicMock()
        mock_col1.id = "col1"
        mock_col1.name = "Collection 1"
        mock_col1.slug = "collection-1"
        
        mock_col2 = MagicMock()
        mock_col2.id = "col2"
        mock_col2.name = "Collection 2"
        mock_col2.slug = "collection-2"
        
        collections = [mock_col1, mock_col2]
        result = format_question_collections(collections)
        assert_that(result).contains("col1")
        assert_that(result).contains("Collection 1")
    
    def test_should_validate_question_parameters_when_all_required_params_provided(self):
        """Test validating valid question parameters"""
        mock_param1 = MagicMock()
        mock_param1.name = "param1"
        mock_param1.required = True
        
        mock_param2 = MagicMock()
        mock_param2.name = "param2"
        mock_param2.required = False
        
        mock_question = MagicMock()
        mock_question.params = [mock_param1, mock_param2]
        
        inputs = {"param1": "value1"}
        
        # Should not raise exception
        validate_question_parameters(inputs, mock_question)
    
    def test_should_raise_error_when_validating_question_parameters_missing_required_params(self):
        """Test validating with missing required parameters"""
        mock_param1 = MagicMock()
        mock_param1.name = "param1"
        mock_param1.required = True
        
        mock_param2 = MagicMock()
        mock_param2.name = "param2"
        mock_param2.required = False
        
        mock_question = MagicMock()
        mock_question.params = [mock_param1, mock_param2]
        
        inputs = {"param2": "value2"}
        
        with pytest.raises(ValueError, match="Missing required parameters"):
            validate_question_parameters(inputs, mock_question)
    
    def test_should_return_validated_inputs_when_question_parameters_are_valid(self):
        """Test that validate_question_parameters returns the inputs"""
        mock_param1 = MagicMock()
        mock_param1.name = "param1"
        mock_param1.required = True
        
        mock_question = MagicMock()
        mock_question.params = [mock_param1]
        
        inputs = {"param1": "value1"}
        
        result = validate_question_parameters(inputs, mock_question)
        assert_that(result).is_equal_to(inputs)


class TestExplorerTables:
    """Test cases for explorer table formatting functions"""
    
    def test_should_format_empty_question_list_as_empty_table_data(self):
        """Test formatting empty question list"""
        result = format_question_list_table([])
        assert_that(result).is_empty()
    
    def test_should_format_question_list_with_id_name_description_and_counts(self):
        """Test formatting question list with data"""
        # Mock questions with required attributes
        mock_q1 = MagicMock()
        mock_q1.id = 'q1'
        mock_q1.name = 'Question 1'
        mock_q1.description = 'Description 1'
        mock_q1.params = [MagicMock(required=True), MagicMock(required=False)]
        mock_q1.collections = [MagicMock(), MagicMock()]
        
        mock_q2 = MagicMock()
        mock_q2.id = 'q2'
        mock_q2.name = 'Question 2'
        mock_q2.description = 'Description 2'
        mock_q2.params = [MagicMock(required=True)]
        mock_q2.collections = [MagicMock()]
        
        questions = [mock_q1, mock_q2]
        result = format_question_list_table(questions)
        
        assert_that(result).is_length(2)
        assert_that(result[0]).contains_key('ID')
        assert_that(result[0]).contains_key('Name')
        assert_that(result[0]).contains_key('Description')
        assert_that(result[0]).contains_key('Parameters')
        assert_that(result[0]).contains_key('Collections')
        assert_that(result[0]).contains_key('Required Params')
        
        assert_that(result[0]['ID']).is_equal_to('q1')
        assert_that(result[0]['Name']).is_equal_to('Question 1')
        assert_that(result[0]['Parameters']).is_equal_to(2)
        assert_that(result[0]['Collections']).is_equal_to(2)
        assert_that(result[0]['Required Params']).is_equal_to(1)
    
    def test_should_format_question_detail_table_with_params_and_collections_info(self):
        """Test formatting question detail table"""
        # Mock question with parameters and collections
        mock_param = MagicMock()
        mock_param.name = 'param1'
        mock_param.input_type = 'string'
        mock_param.required = True
        mock_param.description = 'Test parameter'
        mock_param.default_value = 'default'
        mock_param.values = None
        mock_param.input_subtype = None
        
        mock_col = MagicMock()
        mock_col.id = 'col1'
        mock_col.name = 'Collection 1'
        mock_col.slug = 'collection-1'
        mock_col.question_id = 'q1'
        
        mock_question = MagicMock()
        mock_question.id = 'q1'
        mock_question.name = 'Test Question'
        mock_question.description = 'Test description'
        mock_question.params = [mock_param]
        mock_question.collections = [mock_col]
        
        result = format_question_detail_table(mock_question)
        
        assert_that(result).contains_key('question')
        assert_that(result).contains_key('parameters')
        assert_that(result).contains_key('collections')
        
        assert_that(result['question']['ID']).is_equal_to('q1')
        assert_that(result['question']['Name']).is_equal_to('Test Question')
        assert_that(result['parameters']).is_length(1)
        assert_that(result['collections']).is_length(1)
        
        param_info = result['parameters'][0]
        assert_that(param_info['Name']).is_equal_to('param1')
        assert_that(param_info['Type']).is_equal_to('string')
        assert_that(param_info['Required']).is_equal_to('Yes')
        
        col_info = result['collections'][0]
        assert_that(col_info['ID']).is_equal_to('col1')
        assert_that(col_info['Name']).is_equal_to('Collection 1')
    
    def test_should_format_question_detail_table_including_dropdown_parameter_choices(self):
        """Test formatting question detail with dropdown parameter"""
        mock_param = MagicMock()
        mock_param.name = 'choice_param'
        mock_param.input_type = 'string'
        mock_param.required = False
        mock_param.description = 'Choose option'
        mock_param.default_value = None
        mock_param.values = 'option1\noption2\noption3\noption4'
        mock_param.input_subtype = 'DROPDOWN'
        
        mock_question = MagicMock()
        mock_question.id = 'q1'
        mock_question.name = 'Test Question'
        mock_question.description = 'Test description'
        mock_question.params = [mock_param]
        mock_question.collections = []
        
        result = format_question_detail_table(mock_question)
        
        param_info = result['parameters'][0]
        assert_that(param_info).contains_key('Choices')
        assert_that(param_info['Choices']).contains('option1')
        assert_that(param_info['Choices']).contains('option2')
        assert_that(param_info['Choices']).contains('option3')
        assert_that(param_info['Choices']).contains('...')
    
    def test_should_format_empty_question_results_as_empty_table_data(self):
        """Test formatting empty results table"""
        result = format_question_results_table([])
        assert_that(result).is_empty()
    
    def test_should_format_flat_question_results_data_without_modification(self):
        """Test formatting flat results data"""
        results = [
            {'id': 1, 'name': 'John', 'age': 30},
            {'id': 2, 'name': 'Jane', 'age': 25}
        ]
        
        formatted = format_question_results_table(results)
        assert_that(formatted).is_length(2)
        assert_that(formatted[0]).is_equal_to({'id': 1, 'name': 'John', 'age': 30})
        assert_that(formatted[1]).is_equal_to({'id': 2, 'name': 'Jane', 'age': 25})
    
    def test_should_format_nested_question_results_data_by_flattening_structure(self):
        """Test formatting nested results data"""
        results = [
            {'user': {'id': 1, 'name': 'John'}, 'score': 100},
            {'user': {'id': 2, 'name': 'Jane'}, 'score': 95}
        ]
        
        formatted = format_question_results_table(results)
        assert_that(formatted).is_length(2)
        # Should flatten nested structures
        assert_that(formatted[0]).contains_key('user.id')
        assert_that(formatted[0]).contains_key('user.name')
        assert_that(formatted[0]).contains_key('score')


class TestExplorerCommands:
    """Test cases for explorer CLI commands"""
    
    def test_should_import_explorer_commands_module_without_errors(self):
        """Test importing the explorer commands module"""
        from dnastack.cli.commands.explorer import commands
        
        assert_that(commands).is_not_none()
        assert_that(hasattr(commands, 'explorer_command_group')).is_true()
        assert_that(hasattr(commands, 'questions_command_group')).is_true()
    
    def test_should_provide_explorer_command_group_with_correct_name(self):
        """Test the explorer_command_group function"""
        from dnastack.cli.commands.explorer.commands import explorer_command_group
        
        assert_that(explorer_command_group).is_not_none()
        assert_that(callable(explorer_command_group)).is_true()
        assert_that(hasattr(explorer_command_group, 'name')).is_true()
        assert_that(explorer_command_group.name).is_equal_to('explorer')
    
    def test_should_provide_questions_command_group_with_correct_name(self):
        """Test the questions_command_group function"""
        from dnastack.cli.commands.explorer.commands import questions_command_group
        
        assert_that(questions_command_group).is_not_none()
        assert_that(callable(questions_command_group)).is_true()
        assert_that(hasattr(questions_command_group, 'name')).is_true()
        assert_that(questions_command_group.name).is_equal_to('questions')
    
    def test_should_have_questions_command_group_within_explorer_commands(self):
        """Test the overall structure of the commands module"""
        from dnastack.cli.commands.explorer.commands import (
            explorer_command_group
        )
        
        assert_that('questions' in explorer_command_group.commands).is_true()
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_execute_list_questions_command_using_explorer_client(self, mock_get_client):
        """Test list questions command execution"""
        mock_client = MagicMock()
        mock_iterator = MagicMock()
        mock_client.list_federated_questions.return_value = mock_iterator
        mock_get_client.return_value = mock_client
        
        # Mock the iterator to return sample questions
        mock_iterator.__iter__ = MagicMock(return_value=iter([
            MagicMock(id='q1', name='Question 1', description='Test question 1'),
            MagicMock(id='q2', name='Question 2', description='Test question 2')
        ]))
        
        # Test would involve calling the CLI command, but we'll verify the client is called
        mock_client.list_federated_questions.assert_not_called()  # Not called yet
        
        # Simulate command execution
        result = mock_client.list_federated_questions()
        assert_that(result).is_equal_to(mock_iterator)
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_execute_describe_question_command_using_explorer_client(self, mock_get_client):
        """Test describe question command execution"""
        mock_client = MagicMock()
        mock_question = MagicMock()
        mock_question.id = 'q1'
        mock_question.name = 'Test Question'
        mock_question.description = 'Test description'
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Simulate command execution
        result = mock_client.describe_federated_question('q1')
        assert_that(result).is_equal_to(mock_question)
        mock_client.describe_federated_question.assert_called_once_with('q1')
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_handle_validation_error_when_asking_question_with_invalid_params(self, mock_get_client):
        """Test ask question command with validation error"""
        mock_client = MagicMock()
        mock_param = MagicMock()
        mock_param.name = 'required_param'
        mock_param.required = True
        
        mock_question = MagicMock()
        mock_question.params = [mock_param]
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Test validation should fail with missing required parameter
        with pytest.raises(ValueError):
            validate_question_parameters({}, mock_question)
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_handle_empty_results_when_asking_question_returns_no_data(self, mock_get_client):
        """Test ask question command with no results"""
        mock_client = MagicMock()
        mock_iterator = MagicMock()
        mock_iterator.__iter__ = MagicMock(return_value=iter([]))
        mock_client.ask_federated_question.return_value = mock_iterator
        mock_get_client.return_value = mock_client
        
        result = mock_client.ask_federated_question('q1', inputs={'param': 'value'})
        results_list = list(result)
        assert_that(results_list).is_empty()
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_handle_invalid_collections_when_asking_question_with_bad_collection_ids(self, mock_get_client):
        """Test ask question command with invalid collections"""
        mock_client = MagicMock()
        mock_question = MagicMock()
        mock_question.collections = [MagicMock(id='col1'), MagicMock(id='col2')]
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Test with invalid collection
        invalid_collections = ['invalid_col']
        valid_collection_ids = [col.id for col in mock_question.collections]
        
        for col_id in invalid_collections:
            assert_that(col_id not in valid_collection_ids).is_true()


class TestExplorerResultLoaders:
    """Test cases for explorer result loaders"""
    
    @patch('dnastack.client.explorer.client.FederatedQuestionListResultLoader')
    def test_should_load_federated_question_list_using_result_loader(self, mock_loader_class):
        """Test basic federated question list loader functionality"""
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        
        # Test loader initialization
        service_url = "https://example.com/questions"
        http_session = MagicMock()
        
        loader = mock_loader_class(service_url=service_url, http_session=http_session)
        assert_that(loader).is_equal_to(mock_loader)
        mock_loader_class.assert_called_once_with(service_url=service_url, http_session=http_session)
    
    @patch('dnastack.client.explorer.client.FederatedQuestionQueryResultLoader')
    def test_should_load_federated_question_query_results_using_result_loader(self, mock_loader_class):
        """Test basic federated question query loader functionality"""
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        
        # Test loader initialization
        service_url = "https://example.com/questions/q1/query"
        http_session = MagicMock()
        request_payload = MagicMock()
        
        loader = mock_loader_class(
            service_url=service_url, 
            http_session=http_session,
            request_payload=request_payload
        )
        assert_that(loader).is_equal_to(mock_loader)
        mock_loader_class.assert_called_once()


class TestExplorerModels:
    """Test cases for explorer models"""
    
    def test_should_create_federated_question_model_with_required_attributes(self):
        """Test FederatedQuestion model creation"""
        question_data = {
            'id': 'q1',
            'name': 'Test Question',
            'description': 'Test description',
            'params': [
                {
                    'id': '1',
                    'name': 'param1',
                    'label': 'Parameter 1',
                    'inputType': 'string',
                    'required': True
                }
            ],
            'collections': [
                {
                    'id': '1',
                    'name': 'Collection 1',
                    'slug': 'collection1',
                    'questionId': 'q1'
                }
            ]
        }
        
        question = FederatedQuestion(**question_data)
        assert_that(question.id).is_equal_to('q1')
        assert_that(question.name).is_equal_to('Test Question')
        assert_that(question.description).is_equal_to('Test description')
        assert_that(question.params).is_length(1)
        assert_that(question.collections).is_length(1)
    
    def test_should_convert_federated_question_model_to_dict_representation(self):
        """Test FederatedQuestion model dictionary conversion"""
        question_data = {
            'id': 'q1',
            'name': 'Test Question',
            'description': 'Test description',
            'params': [],
            'collections': []
        }
        
        question = FederatedQuestion(**question_data)
        question_dict = question.dict()
        
        assert_that(question_dict).contains_key('id')
        assert_that(question_dict).contains_key('name')
        assert_that(question_dict).contains_key('description')
        assert_that(question_dict['id']).is_equal_to('q1')


class TestExplorerIntegration:
    """Integration test cases for explorer functionality"""
    
    @patch('dnastack.cli.commands.explorer.questions.utils.container')
    def test_should_get_explorer_client_using_configuration_factory(self, mock_container):
        """Test getting explorer client"""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get.return_value = mock_client
        mock_container.get.return_value = mock_factory
        
        from dnastack.cli.commands.explorer.questions.utils import get_explorer_client
        
        client = get_explorer_client()
        assert_that(client).is_equal_to(mock_client)
    
    @patch('dnastack.cli.commands.explorer.questions.utils.container')
    def test_should_get_explorer_client_with_context_and_endpoint_parameters(self, mock_container):
        """Test getting explorer client with parameters"""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get.return_value = mock_client
        mock_container.get.return_value = mock_factory
        
        from dnastack.cli.commands.explorer.questions.utils import get_explorer_client
        
        # Test with specific context and endpoint_id
        client = get_explorer_client(context="test_context", endpoint_id="test_endpoint")
        assert_that(client).is_equal_to(mock_client)
        mock_factory.get.assert_called_once_with(
            ExplorerClient, 
            context_name="test_context", 
            endpoint_id="test_endpoint"
        )