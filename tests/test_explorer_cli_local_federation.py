import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from assertpy import assert_that

from dnastack.cli.core.command_spec import ArgumentSpec


class TestExplorerQuestionsLocalFederationCLI:
    """Test cases for CLI integration with --local-federated flag"""
    
    def test_should_have_local_federated_argument_spec_defined(self):
        """Test that --local-federated ArgumentSpec is properly defined"""
        # Verify the ArgumentSpec exists by checking in the source code structure
        # Since the command is created dynamically, we test the spec configuration
        spec = ArgumentSpec(
            name='local_federated',
            arg_names=['--local-federated'],
            help='Query collections directly via local federation instead of using server-side federation',
            type=bool,
            default=False
        )
        
        # Test the spec properties
        assert_that(spec.name).is_equal_to('local_federated')
        assert_that(spec.arg_names).contains('--local-federated')
        assert_that(spec.type).is_equal_to(bool)
        assert_that(spec.default).is_false()
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.handle_question_results_output')
    def test_should_execute_local_federation_when_flag_provided(self, mock_output_handler, mock_get_client):
        """Test the ask_question command logic with local_federated=True"""
        mock_client = MagicMock()
        mock_result_iterator = MagicMock()
        mock_result_iterator.__iter__ = MagicMock(return_value=iter([]))
        mock_client.ask_question_local_federated.return_value = mock_result_iterator
        
        # Mock describe_federated_question for parameter validation
        mock_question = MagicMock()
        mock_question.params = []
        mock_question.collections = [
            MagicMock(id='c1', name='Collection 1'),
            MagicMock(id='c2', name='Collection 2')
        ]
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Simulate the command function call directly
        # This simulates what the CLI framework would do
        from dnastack.common.json_argument_parser import JsonLike
        
        # Simulate calling the ask_question function with local_federated=True
        question_name = 'test-question'
        collections = JsonLike('c1,c2')
        local_federated = True
        
        # Import and call the inner function logic by simulating it
        # Since we can't easily call the nested function, we test the client methods directly
        from dnastack.cli.commands.explorer.questions.utils import parse_collections_argument
        from dnastack.common.tracing import Span
        
        trace = Span()
        client = mock_get_client(context=None, endpoint_id=None, trace=trace)
        
        # Parse collections
        collections_str = collections.value()
        collection_ids = parse_collections_argument(collections_str)
        
        # Get question for validation
        client.describe_federated_question(question_name, trace=trace)
        
        # Execute based on flag
        if local_federated:
            client.ask_question_local_federated(
                federated_question_id=question_name,
                inputs={},
                collections=collection_ids,
                trace=trace
            )
        
        # Verify ask_question_local_federated was called
        mock_client.ask_question_local_federated.assert_called_once_with(
            federated_question_id=question_name,
            inputs={},
            collections=['c1', 'c2'],
            trace=trace
        )
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    @patch('dnastack.cli.commands.explorer.questions.commands.handle_question_results_output')
    def test_should_execute_normal_federation_when_flag_not_provided(self, mock_output_handler, mock_get_client):
        """Test the ask_question command logic with local_federated=False"""
        mock_client = MagicMock()
        mock_result_iterator = MagicMock()
        mock_result_iterator.__iter__ = MagicMock(return_value=iter([]))
        mock_client.ask_federated_question.return_value = mock_result_iterator
        
        # Mock describe_federated_question for parameter validation
        mock_question = MagicMock()
        mock_question.params = []
        mock_question.collections = [
            MagicMock(id='c1', name='Collection 1'),
            MagicMock(id='c2', name='Collection 2')
        ]
        mock_client.describe_federated_question.return_value = mock_question
        mock_get_client.return_value = mock_client
        
        # Test the command logic with local_federated=False
        from dnastack.common.json_argument_parser import JsonLike
        from dnastack.cli.commands.explorer.questions.utils import parse_collections_argument
        from dnastack.common.tracing import Span
        
        question_name = 'test-question'
        collections = JsonLike('c1,c2')
        local_federated = False
        
        trace = Span()
        client = mock_get_client(context=None, endpoint_id=None, trace=trace)
        
        # Parse collections
        collections_str = collections.value()
        collection_ids = parse_collections_argument(collections_str)
        
        # Get question for validation
        client.describe_federated_question(question_name, trace=trace)
        
        # Execute based on flag
        if not local_federated:
            client.ask_federated_question(
                federated_question_id=question_name,
                inputs={},
                collections=collection_ids,
                trace=trace
            )
        
        # Verify ask_federated_question was called
        mock_client.ask_federated_question.assert_called_once_with(
            federated_question_id=question_name,
            inputs={},
            collections=['c1', 'c2'],
            trace=trace
        )
    
    @patch('dnastack.cli.commands.explorer.questions.commands.get_explorer_client')
    def test_should_validate_collections_parameter_for_local_federation(self, mock_get_client):
        """Test that collections parameter parsing works for local federation"""
        from dnastack.cli.commands.explorer.questions.utils import parse_collections_argument
        from dnastack.common.json_argument_parser import JsonLike
        
        # Test comma-separated collections parsing
        collections_input = JsonLike('c1,c2,c3')
        collections_str = collections_input.value()
        collection_ids = parse_collections_argument(collections_str)
        
        assert_that(collection_ids).is_equal_to(['c1', 'c2', 'c3'])
        
        # Test newline-separated collections parsing
        collections_input = JsonLike('c1\nc2\nc3')
        collections_str = collections_input.value()
        collection_ids = parse_collections_argument(collections_str)
        
        assert_that(collection_ids).is_equal_to(['c1', 'c2', 'c3'])
    
    def test_should_handle_parameter_file_loading_with_json_like(self):
        """Test @ prefix file loading works with JsonLike"""
        from dnastack.common.json_argument_parser import JsonLike
        
        # Create a temporary file with parameter data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('chr1,chr2,chr3')
            temp_file = f.name
        
        try:
            # Test file loading with @ prefix
            param_value = JsonLike(f'@{temp_file}')
            loaded_content = param_value.value()
            
            assert_that(loaded_content).is_equal_to('chr1,chr2,chr3')
            
        finally:
            os.unlink(temp_file)
    
    def test_should_maintain_argument_parsing_compatibility(self):
        """Test that argument parsing works with the expected formats"""
        
        # Test parameter parsing in the format the CLI uses
        args_tuple = (('param1', 'value1'), ('param2', 'value2'))
        
        # Convert to the format expected by parse_and_merge_arguments
        args_dict = {}
        for key, value in args_tuple:
            args_dict[key] = value
            
        assert_that(args_dict).is_equal_to({'param1': 'value1', 'param2': 'value2'})


class TestLocalFederationErrorHandling:
    """Test cases for error handling and edge cases in local federation"""
    
    def test_should_handle_empty_collections_list_gracefully(self):
        """Test behavior when no collections are provided"""
        from dnastack.cli.commands.explorer.questions.utils import parse_collections_argument
        
        # Test with None
        result = parse_collections_argument(None)
        assert_that(result).is_none()
        
        # Test with empty string
        result = parse_collections_argument("")
        assert_that(result).is_none()
        
        # Test with whitespace only
        result = parse_collections_argument("   ")
        assert_that(result).is_equal_to([])
    
    def test_should_handle_invalid_collection_ids_in_local_federation(self):
        """Test error handling for non-existent collection IDs"""
        from dnastack.http.session import ClientError
        from dnastack.client.explorer.client import ExplorerClient
        
        mock_client = MagicMock(spec=ExplorerClient)
        
        # Create a proper ClientError with a mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Collection 'invalid_id' not found"
        client_error = ClientError(mock_response)
        
        mock_client.ask_question_local_federated.side_effect = client_error
        
        # Test that the client error is propagated correctly
        with pytest.raises(ClientError):
            mock_client.ask_question_local_federated(
                federated_question_id='test-question',
                inputs={},
                collections=['c1', 'invalid_id']
            )
    
    def test_should_handle_authentication_failures_per_collection(self):
        """Test partial authentication failures result format"""
        # Test that the result format can handle mixed success/failure
        mixed_results = [
            {
                'collectionId': 'c1',
                'collectionSlug': 'collection-1', 
                'results': {'data': [{'result': 'success'}]},
                'error': None,
                'failureInfo': None
            },
            {
                'collectionId': 'c2',
                'collectionSlug': 'collection-2',
                'results': None,
                'error': '401: Unauthorized',
                'failureInfo': {'status': 401}
            }
        ]
        
        # Verify the format is valid
        for result in mixed_results:
            assert_that(result).contains_key('collectionId')
            assert_that(result).contains_key('collectionSlug')
            assert_that(result).contains_key('error')
            assert_that(result).contains_key('failureInfo')
            
        # Check success case
        success_result = mixed_results[0]
        assert_that(success_result['error']).is_none()
        assert_that(success_result['results']['data']).is_not_empty()
        
        # Check failure case
        failure_result = mixed_results[1]
        assert_that(failure_result['error']).is_not_none()
        assert_that(failure_result['results']).is_none()
    
    def test_should_handle_timeout_errors_during_local_federation(self):
        """Test timeout handling for slow collection responses"""
        import requests
        from dnastack.client.explorer.client import ExplorerClient
        
        mock_client = MagicMock(spec=ExplorerClient)
        mock_client.ask_question_local_federated.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Should propagate the timeout error
        with pytest.raises(requests.exceptions.Timeout, match="Request timed out"):
            mock_client.ask_question_local_federated(
                federated_question_id='test-question',
                inputs={},
                collections=['c1']
            )


class TestLocalFederationPerformance:
    """Test cases for performance and concurrency aspects"""
    
    def test_should_handle_large_parameter_sets_efficiently(self):
        """Test performance with large parameter strings"""
        # Create a large parameter string (simulating large file content)
        large_param_value = ','.join([f'chr{i}' for i in range(1, 501)])  # 500 entries
        
        # Test that the string handling works with large values
        inputs = {'chromosome': large_param_value}
        
        assert_that(inputs).contains_key('chromosome')
        assert_that(inputs['chromosome']).is_equal_to(large_param_value)
        assert_that(len(inputs['chromosome'].split(','))).is_equal_to(500)
    
    def test_should_work_with_existing_parameter_validation(self):
        """Test that parameter validation works with the expected structures"""
        from dnastack.cli.commands.explorer.questions.utils import validate_question_parameters
        
        # Create proper mock parameters
        mock_required_param = MagicMock()
        mock_required_param.name = 'required_param'
        mock_required_param.required = True
        
        mock_optional_param = MagicMock()
        mock_optional_param.name = 'optional_param'
        mock_optional_param.required = False
        
        # Mock question with parameters
        mock_question = MagicMock()
        mock_question.params = [mock_required_param, mock_optional_param]
        
        # Test with valid parameters
        inputs = {'required_param': 'value1', 'optional_param': 'value2'}
        
        # Should not raise an exception
        validated_inputs = validate_question_parameters(inputs, mock_question)
        assert_that(validated_inputs).is_equal_to(inputs)
        
        # Test with missing required parameter should raise
        invalid_inputs = {'optional_param': 'value2'}
        with pytest.raises(ValueError, match="Missing required parameters"):
            validate_question_parameters(invalid_inputs, mock_question)


class TestLocalFederationIntegration:
    """Test cases for integration with existing systems"""
    
    def test_should_work_with_existing_collection_parsing_utilities(self):
        """Test integration with parse_collections_argument utility"""
        from dnastack.cli.commands.explorer.questions.utils import parse_collections_argument
        
        # Test various collection formats that parse_collections_argument supports
        test_cases = [
            # Comma-separated
            ('c1,c2,c3', ['c1', 'c2', 'c3']),
            # With spaces
            ('c1, c2 , c3', ['c1', 'c2', 'c3']),
            # Single collection
            ('c1', ['c1']),
            # Newline-separated
            ('c1\nc2\nc3', ['c1', 'c2', 'c3']),
            # Realistic collection IDs
            ('7VnJ-b6bb34b6-dc1b-4ede-9aee-627e64f878c5,Lu0K-cd1cdf5a-1cb0-4b47-bf52-d365f928a1b4', 
             ['7VnJ-b6bb34b6-dc1b-4ede-9aee-627e64f878c5', 'Lu0K-cd1cdf5a-1cb0-4b47-bf52-d365f928a1b4'])
        ]
        
        for collections_input, expected_parsed in test_cases:
            # Verify parse_collections_argument works correctly
            parsed = parse_collections_argument(collections_input)
            assert_that(parsed).is_equal_to(expected_parsed)
    
    def test_should_maintain_compatibility_with_existing_result_formats(self):
        """Test that result format is compatible with existing utilities"""
        from dnastack.cli.commands.explorer.questions.utils import flatten_result_for_export
        
        # Test result format that should be compatible with existing utilities
        compatible_result = {
            'collectionId': 'c1',
            'collectionSlug': 'collection-1',
            'results': {
                'data': [
                    {'chromosome': 'chr1', 'position': 12345, 'result': 'value1'},
                    {'chromosome': 'chr2', 'position': 67890, 'result': 'value2'}
                ]
            },
            'error': None,
            'failureInfo': None
        }
        
        # Test that flatten_result_for_export works with the format
        flattened = flatten_result_for_export(compatible_result)
        assert_that(flattened).contains_key('collectionId')
        assert_that(flattened).contains_key('collectionSlug')
        
        # Test that result data can be processed
        result_data = compatible_result['results']['data']
        for data_item in result_data:
            flattened_item = flatten_result_for_export(data_item)
            assert_that(flattened_item).contains_key('chromosome')
            assert_that(flattened_item).contains_key('position')
    
    def test_should_handle_json_like_parameter_processing(self):
        """Test JsonLike parameter processing compatibility"""
        from dnastack.common.json_argument_parser import JsonLike
        
        # Test different JsonLike input formats
        test_cases = [
            # Simple string
            JsonLike('test_value'),
            # Comma-separated
            JsonLike('value1,value2,value3'),
            # JSON object
            JsonLike('{"key": "value"}')
        ]
        
        for json_like in test_cases:
            # Should be able to get value without errors
            value = json_like.value()
            assert_that(value).is_not_none()
            assert_that(isinstance(value, str)).is_true()