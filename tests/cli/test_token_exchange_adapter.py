import json
import base64
import secrets
import string
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
from time import time
from requests.exceptions import Timeout

from dnastack.http.authenticators.oauth2_adapter.token_exchange import TokenExchangeAdapter
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication
from dnastack.http.authenticators.oauth2_adapter.abstract import AuthException
from dnastack.common.tracing import Span


def mock_exchange_tokens(trace_context):
    return {
        'access_token': 'cloud_refreshed_token',
        'token_type': 'Bearer',
        'expires_in': 3600
    }

def generate_dummy_secret(length=32):
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
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'token_endpoint': 'http://localhost:8081/oauth/token',
            'resource_url': 'http://localhost:8185',
            'type': 'oauth2'
        }

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
        
        # Mock successful token exchange response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'exchanged_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read write'
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
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
            self.assertEqual(data['grant_type'], 'urn:ietf:params:oauth:grant-type:token-exchange')
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
        
        # Mock GCP metadata response
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = self.sample_gcp_id_token
        
        # Mock token exchange response
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': 'gcp_derived_access_token',
            'token_type': 'Bearer',
            'expires_in': 7200
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_metadata_response
            mock_session.post.return_value = mock_token_response
            mock_factory.return_value = mock_session
            
            result = adapter.exchange_tokens(trace_context)
            
            # Verify the result
            self.assertEqual(result['access_token'], 'gcp_derived_access_token')
            self.assertEqual(result['expires_in'], 7200)
            
            # Verify GCP metadata was called
            mock_session.get.assert_called_once()
            get_call = mock_session.get.call_args
            self.assertIn('metadata.google.internal', get_call[0][0])
            self.assertIn(f'audience={self.base_auth_info["resource_url"]}', get_call[0][0])
            self.assertEqual(get_call[1]['headers']['Metadata-Flavor'], 'Google')
            self.assertEqual(get_call[1]['timeout'], 5)
            
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
        
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = self.sample_gcp_id_token
        
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {'access_token': 'token', 'token_type': 'Bearer', 'expires_in': 3600}
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_metadata_response
            mock_session.post.return_value = mock_token_response
            mock_factory.return_value = mock_session
            
            adapter.exchange_tokens(trace_context)
            
            # Verify custom audience was used
            get_call = mock_session.get.call_args
            self.assertIn('audience=https://custom-audience.example.com', get_call[0][0])
    
    def test_exchange_tokens_metadata_fetch_failure(self):
        """Test handling when GCP metadata service fails"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock failed metadata response
        mock_metadata_response = Mock()
        mock_metadata_response.ok = False
        mock_metadata_response.status_code = 404
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_metadata_response
            mock_factory.return_value = mock_session
            
            with self.assertRaises(AuthException) as context:
                adapter.exchange_tokens(trace_context)
            
            self.assertIn('No subject token provided', str(context.exception))
            self.assertIn('unable to fetch from cloud', str(context.exception))
    
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
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'access_token': 'scoped_token', 'token_type': 'Bearer', 'expires_in': 3600}
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
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
    
    def test_reauthenticate_token_exchange_flow(self):
        """Test that expired token exchange sessions trigger reauthentication flow"""
        from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
        from dnastack.http.authenticators.abstract import RefreshRequired, ReauthenticationRequired
        from dnastack.http.session_info import SessionInfo, SessionInfoHandler
        from dnastack.client.models import ServiceEndpoint
        from dnastack.common.tracing import Span
        
        # Setup auth info for token exchange
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = self.sample_gcp_id_token
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        endpoint = ServiceEndpoint(id='test-endpoint', url='http://localhost:8081')
        authenticator = OAuth2Authenticator(endpoint, auth_info_dict)
        
        # Create an expired session that was created via token exchange (valid but needing refresh)
        expired_session = SessionInfo(
            model_version=4,
            config_hash=authenticator.session_id,
            access_token='expired_token',
            refresh_token=None,  # Token exchange doesn't provide refresh tokens
            scope='read write',
            token_type='Bearer',
            issued_at=int(time() - 7200),  # Issued 2 hours ago
            valid_until=int(time() - 3600),  # Expired 1 hour ago
            handler=SessionInfoHandler(auth_info=auth_info_dict)
        )
        
        # Mock successful token exchange response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read write'
        }
        
        # Mock the adapter factory and adapter
        mock_adapter = Mock()
        mock_adapter.exchange_tokens.return_value = mock_response.json.return_value
        mock_adapter.events = Mock()
        trace_context = Span(origin='test')
        
        with patch.object(authenticator._adapter_factory, 'get_from', return_value=mock_adapter), \
             patch.object(authenticator._session_manager, 'restore', return_value=expired_session), \
             patch.object(authenticator._session_manager, 'save') as mock_save, \
             patch.object(authenticator, '_reauthenticate_token_exchange', wraps=authenticator._reauthenticate_token_exchange) as mock_reauth:
            
            # Set the session info to simulate restored session
            authenticator._session_info = expired_session
            # Call refresh which should detect token exchange and trigger reauthentication
            result = authenticator.refresh(trace_context)
            
            mock_reauth.assert_called_once_with(expired_session, trace_context)
            mock_adapter.exchange_tokens.assert_called_once()
            
            # Verify new session was saved
            mock_save.assert_called_once()
            saved_session = mock_save.call_args[0][1]
            self.assertEqual(saved_session.access_token, 'new_access_token')
            self.assertEqual(result.access_token, 'new_access_token')
    
    def test_reauthenticate_token_exchange_cloud_metadata_fetch(self):
        """Test that reauthentication in cloud environment fetches new identity token"""
        from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
        from dnastack.http.session_info import SessionInfo, SessionInfoHandler
        from dnastack.client.models import ServiceEndpoint
        from dnastack.common.tracing import Span
        
        # Setup auth info for token exchange (no subject_token to force cloud fetch)
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        endpoint = ServiceEndpoint(id='test-endpoint', url='http://localhost:8081')
        authenticator = OAuth2Authenticator(endpoint, auth_info_dict)
        
        # Create expired token exchange session
        expired_session = SessionInfo(
            model_version=4,
            config_hash=authenticator.session_id,
            access_token='expired_token',
            refresh_token=None,
            scope='read write',
            token_type='Bearer',
            issued_at=int(time() - 7200),
            valid_until=int(time() - 3600),
            handler=SessionInfoHandler(auth_info=auth_info_dict)
        )
        
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = self.sample_gcp_id_token
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': 'cloud_refreshed_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }

        trace_context = Span(origin='test')
        mock_adapter = Mock(spec=TokenExchangeAdapter)
        mock_adapter.events = Mock()
        mock_adapter.exchange_tokens.side_effect = mock_exchange_tokens
        
        with patch.object(authenticator._adapter_factory, 'get_from', return_value=mock_adapter), \
             patch.object(authenticator._session_manager, 'restore', return_value=expired_session), \
             patch.object(authenticator._session_manager, 'save') as mock_save:

            authenticator._session_info = expired_session
            result = authenticator.refresh(trace_context)
            
            mock_adapter.exchange_tokens.assert_called_once_with(trace_context)
            self.assertEqual(result.access_token, 'cloud_refreshed_token')
            mock_save.assert_called_once()
            saved_session = mock_save.call_args[0][1]
            self.assertEqual(saved_session.access_token, 'cloud_refreshed_token')

    def test_get_expected_auth_info_fields(self):
        """Test that the expected auth info fields are returned"""
        expected = ['grant_type', 'resource_url', 'token_endpoint']
        self.assertEqual(TokenExchangeAdapter.get_expected_auth_info_fields(), expected)

    def test_exchange_tokens_metadata_fetch_exception(self):
        """Test handling when a network exception occurs during metadata fetch"""
        auth_info = OAuth2Authentication(**self.base_auth_info)
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            # Simulate a network timeout or connection error
            mock_session.get.side_effect = Timeout("Connection to metadata server timed out")
            mock_factory.return_value = mock_session

            with self.assertRaises(AuthException) as context:
                adapter.exchange_tokens(trace_context)

            self.assertIn('No subject token provided', str(context.exception))
            self.assertIn('unable to fetch from cloud', str(context.exception))