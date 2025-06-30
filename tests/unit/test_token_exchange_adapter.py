import json
import base64
import secrets
import string
from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
from time import time

from dnastack.http.authenticators.oauth2_adapter.token_exchange import TokenExchangeAdapter
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication, GRANT_TYPE_TOKEN_EXCHANGE
from dnastack.http.authenticators.oauth2_adapter.abstract import AuthException
from dnastack.http.authenticators.oauth2_adapter.cloud_providers import (
    GCPMetadataProvider, CloudProviderFactory
)
from dnastack.common.tracing import Span



def generate_dummy_secret():
    """Generate a dummy secret that won't be flagged as a real secret."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(24))


class TestTokenExchangeAdapter(TestCase):

    def setUp(self):
        self.sample_gcp_token_payload = {
            "aud": "http://localhost:8081",
            "azp": "100483287612623142116",
            "email": "217706947495-compute@developer.gserviceaccount.com",
            "email_verified": True,
            "exp": int(time()) + 3600,  # Valid for 1 hour
            "google": {
                "compute_engine": {
                    "instance_creation_timestamp": 1731425864,
                    "instance_id": "3047934050210597033",
                    "instance_name": "fedml-server",
                    "project_id": "striking-effort-817",
                    "project_number": 217706947495,
                    "zone": "us-central1-c"
                }
            },
            "iat": int(time()),
            "iss": "https://accounts.google.com",
            "sub": "100483287612623142116"
        }
        
        # Create a fake JWT token (header.payload.signature)
        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps(self.sample_gcp_token_payload).encode()).decode().rstrip("=")
        self.sample_gcp_id_token = f"{header}.{payload}.fake_signature"
        
        # Minimal required auth info for token exchange
        self.base_auth_info = {
            'grant_type': GRANT_TYPE_TOKEN_EXCHANGE,
            'token_endpoint': 'http://localhost:8081/oauth/token',
            'resource_url': 'http://localhost:8185',
            'type': 'oauth2'
        }

    def _create_mock_responses(self,access_token:str='gcp_derived_access_token' , expires_in:int=7200) -> Tuple [Mock, Mock]:
        """Create standard mock GCP metadata and token exchange responses."""
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = self.sample_gcp_id_token

        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in
        }
        
        return mock_metadata_response, mock_token_response

    def _setup_mock_http_session(self, mock_factory:Mock, mock_metadata_response:Mock, mock_token_response:Mock) -> Mock:
        """Set up mock HTTP session with standard responses."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.get.return_value = mock_metadata_response
        mock_session.post.return_value = mock_token_response
        mock_factory.return_value = mock_session
        return mock_session

    def _verify_gcp_metadata_call(self, mock_session:Mock, expected_audience:str):
        """Verify that GCP metadata was called with the expected audience."""
        identity_calls = [call for call in mock_session.get.call_args_list 
                        if 'identity' in call[0][0] and 'audience=' in call[0][0]]
        self.assertEqual(len(identity_calls), 1)
        self.assertIn(f'audience={expected_audience}', identity_calls[0][0][0])

    def test_is_compatible_with_correct_grant_type(self):
        """Test that adapter correctly identifies compatible auth configurations"""
        auth_info = OAuth2Authentication(**self.base_auth_info)
        self.assertTrue(TokenExchangeAdapter.is_compatible_with(auth_info))
    
    def test_is_compatible_with_wrong_grant_type(self):
        """Test that adapter rejects incompatible grant types"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['grant_type'] = 'client_credentials'
        auth_info = OAuth2Authentication(**auth_info_dict)
        self.assertFalse(TokenExchangeAdapter.is_compatible_with(auth_info))
    
    def test_is_compatible_with_missing_required_fields(self):
        """Test that adapter rejects configs missing required fields"""
        # Test with None token_endpoint (which is Optional in the model)
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['token_endpoint'] = None
        auth_info = OAuth2Authentication(**auth_info_dict)
        self.assertFalse(TokenExchangeAdapter.is_compatible_with(auth_info))
        
        # Test with empty string token_endpoint
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['token_endpoint'] = ''
        auth_info = OAuth2Authentication(**auth_info_dict)
        self.assertFalse(TokenExchangeAdapter.is_compatible_with(auth_info))
        
        # Test with empty string resource_url (which is required but can be empty string)
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['resource_url'] = ''
        auth_info = OAuth2Authentication(**auth_info_dict)
        self.assertFalse(TokenExchangeAdapter.is_compatible_with(auth_info))
    
    def test_exchange_tokens_with_provided_subject_token(self):
        """Test token exchange when subject token is provided"""
        dummy_secret = generate_dummy_secret()
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        # Explicitly set client credentials (as would be done by CLI)
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = dummy_secret
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        _, mock_response =  self._create_mock_responses(access_token='exchanged_access_token', expires_in=3600)
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=_, mock_token_response=mock_response)

            result = adapter.exchange_tokens(trace_context)
            
            # Verify the result
            self.assertEqual(result['access_token'], 'exchanged_access_token')
            self.assertEqual(result['token_type'], 'Bearer')
            self.assertEqual(result['expires_in'], 3600)
            
            # Verify the HTTP call
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            
            # Check URL
            self.assertEqual(call_args[0][0], 'http://localhost:8081/oauth/token')
            
            # Check data payload
            data = call_args[1]['data']
            self.assertEqual(data['grant_type'], GRANT_TYPE_TOKEN_EXCHANGE)
            self.assertEqual(data['subject_token_type'], 'urn:ietf:params:oauth:token-type:jwt')
            self.assertEqual(data['subject_token'], self.sample_gcp_id_token)
            self.assertEqual(data['resource'], 'http://localhost:8185')
            
            # Check auth (explorer credentials)
            self.assertEqual(call_args[1]['auth'], ('dnastack-client', dummy_secret))
    
    def test_exchange_tokens_with_gcp_metadata_fetch(self):
        """Test token exchange when fetching ID token from GCP metadata"""
        # No subject_token provided - should fetch from GCP
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_metadata_response, mock_token_response = self._create_mock_responses()
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=mock_token_response)

            result = adapter.exchange_tokens(trace_context)
            
            # Verify the result
            self.assertEqual(result['access_token'], 'gcp_derived_access_token')
            self.assertEqual(result['expires_in'], 7200)
            
            # Verify GCP metadata was called with client_id as audience (since no explicit audience set)
            get_call = mock_session.get.call_args
            assert mock_session.get.call_count >= 1
            self.assertIn('metadata.google.internal', get_call[0][0])
            self.assertIn('audience=dnastack-client', get_call[0][0])
            self.assertEqual(get_call[1]['headers']['Metadata-Flavor'], 'Google')
            self.assertEqual(get_call[1]['timeout'], 10)
            # Verify token exchange was called with fetched token
            post_call = mock_session.post.call_args
            self.assertEqual(post_call[1]['data']['subject_token'], self.sample_gcp_id_token)
    
    def test_exchange_tokens_with_custom_audience(self):
        """Test that custom audience is used for GCP metadata fetch"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['audience'] = 'https://custom-audience.example.com'
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_metadata_response, mock_token_response = self._create_mock_responses(access_token='token', expires_in=3600)
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=mock_token_response)

            adapter.exchange_tokens(trace_context)
            
            # Verify custom audience was used
            get_call = mock_session.get.call_args
            self.assertIn('audience=https://custom-audience.example.com', get_call[0][0])
    
    def test_exchange_tokens_with_configured_cloud_provider(self):
        """Test token exchange with explicitly configured cloud provider."""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['cloud_provider'] = 'gcp'
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_metadata_response, mock_token_response = self._create_mock_responses(access_token='gcp_configured_access_token',expires_in=3600)
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=mock_token_response)
            
            result = adapter.exchange_tokens(trace_context)
            
            self.assertEqual(result['access_token'], 'gcp_configured_access_token')
            assert mock_session.get.call_count >= 1
            get_call = mock_session.get.call_args
            self.assertIn('metadata.google.internal', get_call[0][0])
            self.assertEqual(get_call[1]['headers']['Metadata-Flavor'], 'Google')
    
    def test_exchange_tokens_metadata_fetch_failure(self):
        """Test handling when cloud metadata service fails"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock all cloud providers as unavailable
        with patch.object(CloudProviderFactory, 'detect_provider', return_value=None):
            with self.assertRaises(AuthException) as context:
                adapter.exchange_tokens(trace_context)
            
            self.assertIn('No subject token provided', str(context.exception))
            self.assertIn('unable to fetch from cloud', str(context.exception))
    
    def test_exchange_tokens_with_auto_detected_provider(self):
        """Test token exchange with auto-detected cloud provider."""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock auto-detection to return GCP
        mock_gcp_provider = Mock(spec=GCPMetadataProvider)
        mock_gcp_provider.name = 'gcp'
        mock_gcp_provider.get_identity_token.return_value = self.sample_gcp_id_token
        
        # Mock token exchange response
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': 'auto_detected_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch.object(CloudProviderFactory, 'detect_provider', return_value=mock_gcp_provider), \
             patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_token_response
            mock_factory.return_value = mock_session
            
            result = adapter.exchange_tokens(trace_context)
            
            # Verify the result
            self.assertEqual(result['access_token'], 'auto_detected_access_token')
            
            # Verify cloud provider was used with client_id as audience
            mock_gcp_provider.get_identity_token.assert_called_once_with(
                'dnastack-client', 
                trace_context
            )
    
    def test_exchange_tokens_with_optional_parameters(self):
        """Test token exchange with scope and requested_token_type"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        auth_info_dict['scope'] = 'read write admin'
        auth_info_dict['requested_token_type'] = 'urn:ietf:params:oauth:token-type:access_token'
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        _, mock_token_response = self._create_mock_responses(access_token='scoped_token', expires_in=3600)
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=_, mock_token_response=mock_token_response)

            adapter.exchange_tokens(trace_context)
            
            # Verify optional parameters were included
            post_call = mock_session.post.call_args
            data = post_call[1]['data']
            self.assertEqual(data['scope'], 'read write admin')
            self.assertEqual(data['requested_token_type'], 'urn:ietf:params:oauth:token-type:access_token')
    
    def test_exchange_tokens_server_error(self):
        """Test handling of server errors during token exchange"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = 'Invalid subject token or client credentials'
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            with self.assertRaises(AuthException) as context:
                adapter.exchange_tokens(trace_context)
            
            self.assertIn('Failed to perform token exchange', str(context.exception))
            self.assertIn('401', str(context.exception))
            self.assertIn('Invalid subject token', str(context.exception))
    
    def test_multiple_resource_urls(self):
        """Test that multiple resource URLs are properly formatted"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        auth_info_dict['resource_url'] = 'http://resource1.com http://resource2.com,http://resource3.com'
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'access_token': 'token', 'token_type': 'Bearer', 'expires_in': 3600}
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            adapter.exchange_tokens(trace_context)
            
            # Verify resource URLs were properly formatted
            post_call = mock_session.post.call_args
            data = post_call[1]['data']
            self.assertEqual(data['resource'], 'http://resource1.com,http://resource2.com,http://resource3.com')
    
    def test_exchange_tokens_without_client_credentials(self):
        """Test that exchange fails when client credentials are not provided"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        # No client_id/client_secret provided
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'access_token': 'token', 'token_type': 'Bearer', 'expires_in': 3600}
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            adapter.exchange_tokens(trace_context)
            
            # Verify that None credentials are passed (would fail in real scenario)
            post_call = mock_session.post.call_args
            self.assertEqual(post_call[1]['auth'], (None, None))

    def test_get_and_clear_context_subject_token(self):
        """Test context subject token retrieval and clearing"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info = OAuth2Authentication(**auth_info_dict)
        adapter = TokenExchangeAdapter(auth_info)
        
        # Mock context manager with a platform subject token
        mock_context = Mock()
        mock_context.platform_subject_token = 'context_token_123'
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = mock_context
        mock_context_manager.contexts.current_context_name = 'test_context'
        
        with patch('imagination.container.get', return_value=mock_context_manager):
            token = adapter._get_and_clear_context_subject_token()
            
            # Should return the token
            self.assertEqual(token, 'context_token_123')
            
            # Should have cleared the token
            self.assertIsNone(mock_context.platform_subject_token)
            
            # Should have saved the context
            mock_context_manager.contexts.set.assert_called_once_with('test_context', mock_context)

    def test_get_and_clear_context_subject_token_no_context(self):
        """Test context subject token when no context is available"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info = OAuth2Authentication(**auth_info_dict)
        adapter = TokenExchangeAdapter(auth_info)
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = None
        
        with patch('imagination.container.get', return_value=mock_context_manager):
            token = adapter._get_and_clear_context_subject_token()
            self.assertIsNone(token)

    def test_fetch_cloud_identity_token_with_configured_provider_success(self):
        """Test cloud provider success when already configured"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Set up a configured provider that will succeed
        mock_cloud_provider = Mock()
        mock_cloud_provider.name = 'gcp'
        mock_cloud_provider.get_identity_token.return_value = self.sample_gcp_id_token
        adapter._cloud_provider = mock_cloud_provider
        
        token = adapter._fetch_cloud_identity_token('test_audience', trace_context)
        
        self.assertEqual(token, self.sample_gcp_id_token)
        # Ensure configured provider was called
        mock_cloud_provider.get_identity_token.assert_called_once_with('test_audience', trace_context)

    def test_fetch_cloud_identity_token_with_configured_provider_failure(self):
        """Test cloud provider failure when already configured"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Set up a configured provider that will fail
        mock_cloud_provider = Mock()
        mock_cloud_provider.name = 'gcp'
        mock_cloud_provider.get_identity_token.return_value = None  # Simulates failure
        adapter._cloud_provider = mock_cloud_provider
        
        # Mock auto-detection to also fail
        with patch.object(CloudProviderFactory, 'detect_provider', return_value=None):
            token = adapter._fetch_cloud_identity_token('test_audience', trace_context)
            
            self.assertIsNone(token)
            # Ensure configured provider was called first
            mock_cloud_provider.get_identity_token.assert_called_once_with('test_audience', trace_context)

    def test_fetch_cloud_identity_token_auto_detect_failure(self):
        """Test auto-detected provider failure"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client' 
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock auto-detection to return a provider that fails to get token
        mock_provider = Mock()
        mock_provider.name = 'gcp'
        mock_provider.get_identity_token.return_value = None
        
        with patch.object(CloudProviderFactory, 'detect_provider', return_value=mock_provider):
            token = adapter._fetch_cloud_identity_token('test_audience', trace_context)
            
            self.assertIsNone(token)
            self.assertEqual(adapter._cloud_provider, mock_provider)
            mock_provider.get_identity_token.assert_called_once_with('test_audience', trace_context)

    def test_exchange_tokens_with_context_subject_token(self):
        """Test token exchange using context subject token"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock context with subject token
        mock_context = Mock()
        mock_context.platform_subject_token = self.sample_gcp_id_token
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = mock_context
        mock_context_manager.contexts.current_context_name = 'test_context'
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'context_token_access',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock_metadata_response,_ = self._create_mock_responses(access_token='context_token_access', expires_in=3600)
        
        with patch('imagination.container.get', return_value=mock_context_manager), \
             patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=_)

            result = adapter.exchange_tokens(trace_context)
            
            self.assertEqual(result['access_token'], 'context_token_access')
            
            self.assertIsNone(mock_context.platform_subject_token)
            
            # Verify the exchange request used the context token
            post_call = mock_session.post.call_args
            self.assertEqual(post_call[1]['data']['subject_token'], self.sample_gcp_id_token)

    def test_audience_priority_order(self):
        """Regression test: Ensure audience priority order is: audience > client_id > resource_url"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['audience'] = 'https://passport.alpha.rc.dnastack.com'
        auth_info_dict['client_id'] = 'explorer.alpha.rc.dnastack.com-public-client'
        auth_info_dict['resource_url'] = 'https://explorer.alpha.rc.dnastack.com/'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        mock_metadata_response, mock_token_response = self._create_mock_responses()
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=mock_token_response)
            result = adapter.exchange_tokens(trace_context)
            
            self.assertEqual(result['access_token'], 'gcp_derived_access_token')
            self._verify_gcp_metadata_call(mock_session, 'https://passport.alpha.rc.dnastack.com')
            
    def test_audience_fallback_to_client_id(self):
        """Test that client_id is used when audience is not set"""
        auth_info_dict = self.base_auth_info.copy()
        # No explicit audience set
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['resource_url'] = 'https://explorer.alpha.rc.dnastack.com/'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        mock_metadata_response, mock_token_response = self._create_mock_responses()
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = self._setup_mock_http_session(mock_factory=mock_factory, mock_metadata_response=mock_metadata_response, mock_token_response=mock_token_response)
            
            result = adapter.exchange_tokens(trace_context)
            
            self.assertEqual(result['access_token'], 'gcp_derived_access_token')
            self._verify_gcp_metadata_call(mock_session, 'dnastack-client')
    
