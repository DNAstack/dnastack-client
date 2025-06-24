import json
import base64
import secrets
import string
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
from time import time

from dnastack.http.authenticators.oauth2_adapter.token_exchange import TokenExchangeAdapter
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication, GRANT_TYPE_TOKEN_EXCHANGE
from dnastack.http.authenticators.oauth2_adapter.cloud_providers import (
    GCPMetadataProvider, CloudProviderFactory, CloudMetadataConfig, CloudProvider
)
from dnastack.common.tracing import Span
from dnastack.context.models import Context




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
            'grant_type': GRANT_TYPE_TOKEN_EXCHANGE,
            'token_endpoint': 'http://localhost:8081/oauth/token',
            'resource_url': 'http://localhost:8185',
            'type': 'oauth2'
        }


    def test_get_and_clear_context_subject_token(self):
        """Test that context subject token is retrieved and cleared after use"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        
        # Mock a context with a subject token
        mock_context = Context()
        mock_context.platform_subject_token = self.sample_gcp_id_token
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = mock_context
        mock_context_manager.contexts.current_context_name = 'test-context'
        mock_context_manager.contexts.set = Mock()
        
        with patch('dnastack.http.authenticators.oauth2_adapter.token_exchange.container.get', 
                   return_value=mock_context_manager):
            
            # First call should return the token
            token = adapter._get_and_clear_context_subject_token()
            self.assertEqual(token, self.sample_gcp_id_token)
            
            # Verify the context was updated (token cleared)
            self.assertIsNone(mock_context.platform_subject_token)
            mock_context_manager.contexts.set.assert_called_once_with('test-context', mock_context)
            
            # Second call should return None since token was cleared
            token2 = adapter._get_and_clear_context_subject_token()
            self.assertIsNone(token2)

    def test_get_and_clear_context_subject_token_no_context(self):
        """Test context subject token retrieval when no context exists"""
        auth_info = OAuth2Authentication(**self.base_auth_info)
        adapter = TokenExchangeAdapter(auth_info)
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = None
        
        with patch('dnastack.http.authenticators.oauth2_adapter.token_exchange.container.get', 
                   return_value=mock_context_manager):
            
            token = adapter._get_and_clear_context_subject_token()
            self.assertIsNone(token)

    def test_subject_token_priority_auth_info_first(self):
        """Test that auth_info subject token takes priority over context token"""
        auth_info_dict = self.base_auth_info.copy()
        auth_info_dict['subject_token'] = 'auth_info_token'
        auth_info_dict['client_id'] = 'dnastack-client'
        auth_info_dict['client_secret'] = generate_dummy_secret()
        auth_info = OAuth2Authentication(**auth_info_dict)
        
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='test')
        
        # Mock context with different token
        mock_context = Context()
        mock_context.platform_subject_token = 'context_token'
        
        mock_context_manager = Mock()
        mock_context_manager.contexts.current_context = mock_context
        
        with patch('dnastack.http.authenticators.oauth2_adapter.token_exchange.container.get', 
                   return_value=mock_context_manager):
            
            # Should use auth_info token, not call context method
            token = adapter._get_subject_token(trace_context)
            self.assertEqual(token, 'auth_info_token')
            
            # Context token should not be touched
            self.assertEqual(mock_context.platform_subject_token, 'context_token')



class TestCloudProviders(TestCase):
    """Test cloud provider functionality for better coverage"""

    def test_gcp_metadata_provider_name(self):
        """Test GCP provider name"""
        provider = GCPMetadataProvider()
        self.assertEqual(provider.name, 'gcp')

    def test_gcp_metadata_provider_is_available_success(self):
        """Test GCP availability check when metadata service is available"""
        provider = GCPMetadataProvider()
        
        mock_response = Mock()
        mock_response.ok = True
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = provider.is_available()
            self.assertTrue(result)
            
            # Verify correct URL and headers
            mock_session.get.assert_called_once_with(
                'http://metadata.google.internal/computeMetadata/v1/project/project-id',
                headers={'Metadata-Flavor': 'Google'},
                timeout=1
            )

    def test_gcp_metadata_provider_is_available_failure(self):
        """Test GCP availability check when metadata service is not available"""
        provider = GCPMetadataProvider()
        
        mock_response = Mock()
        mock_response.ok = False
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = provider.is_available()
            self.assertFalse(result)

    def test_gcp_metadata_provider_is_available_exception(self):
        """Test GCP availability check when an exception occurs"""
        provider = GCPMetadataProvider()
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_factory.side_effect = Exception("Network error")
            
            result = provider.is_available()
            self.assertFalse(result)

    def test_gcp_metadata_provider_get_identity_token_success(self):
        """Test successful identity token retrieval"""
        provider = GCPMetadataProvider(timeout=10)
        trace_context = Span(origin='test')
        audience = 'http://localhost:8081'
        expected_token = 'gcp_identity_token'
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = f'  {expected_token}  '  # Include whitespace to test stripping
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = provider.get_identity_token(audience, trace_context)
            self.assertEqual(result, expected_token)
            
            # Verify correct URL and headers
            expected_url = f'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience={audience}&format=full'
            mock_session.get.assert_called_once_with(
                expected_url,
                headers={'Metadata-Flavor': 'Google'},
                timeout=10
            )

    def test_gcp_metadata_provider_get_identity_token_failure(self):
        """Test identity token retrieval when service returns error"""
        provider = GCPMetadataProvider()
        trace_context = Span(origin='test')
        audience = 'http://localhost:8081'
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = provider.get_identity_token(audience, trace_context)
            self.assertIsNone(result)

    def test_gcp_metadata_provider_get_identity_token_exception(self):
        """Test identity token retrieval when an exception occurs"""
        provider = GCPMetadataProvider()
        trace_context = Span(origin='test')
        audience = 'http://localhost:8081'
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_factory.side_effect = Exception("Network error")
            
            result = provider.get_identity_token(audience, trace_context)
            self.assertIsNone(result)

    def test_cloud_metadata_config_validation(self):
        """Test CloudMetadataConfig validation"""
        # Valid config
        config = CloudMetadataConfig(timeout=15)
        self.assertEqual(config.timeout, 15)
        
        # Default timeout
        config_default = CloudMetadataConfig()
        self.assertEqual(config_default.timeout, 5)
        
        # Invalid timeout values should be handled by Pydantic validation
        # (We'd need to test this differently depending on Pydantic version)

    def test_cloud_provider_factory_create_gcp(self):
        """Test creating GCP provider through factory"""
        config = CloudMetadataConfig(timeout=20)
        provider = CloudProviderFactory.create(CloudProvider.GCP, config)
        
        self.assertIsInstance(provider, GCPMetadataProvider)
        self.assertEqual(provider.timeout, 20)
        self.assertEqual(provider.name, 'gcp')

    def test_cloud_provider_factory_create_unsupported(self):
        """Test creating unsupported provider raises error"""
        config = CloudMetadataConfig()
        
        with self.assertRaises(ValueError) as context:
            CloudProviderFactory.create('aws', config)  # Unsupported provider
        
        self.assertIn('Unsupported cloud provider', str(context.exception))

    def test_cloud_provider_factory_detect_provider_success(self):
        """Test auto-detection when GCP is available"""
        config = CloudMetadataConfig()
        
        with patch.object(GCPMetadataProvider, 'is_available', return_value=True):
            provider = CloudProviderFactory.detect_provider(config)
            
            self.assertIsInstance(provider, GCPMetadataProvider)
            self.assertEqual(provider.name, 'gcp')

    def test_cloud_provider_factory_detect_provider_none(self):
        """Test auto-detection when no providers are available"""
        config = CloudMetadataConfig()
        
        with patch.object(GCPMetadataProvider, 'is_available', return_value=False):
            provider = CloudProviderFactory.detect_provider(config)
            
            self.assertIsNone(provider)


class TestContextManager(TestCase):
    """Test context manager functionality related to token exchange"""

    def test_filter_endpoints_for_token_exchange(self):
        """Test filtering endpoints to only include token exchange authentication"""
        from dnastack.context.manager import BaseContextManager
        from dnastack.context.models import Context
        from dnastack.client.models import ServiceEndpoint, ServiceType
        from dnastack.client.service_registry.client import STANDARD_SERVICE_REGISTRY_TYPE_V1_0
        
        context = Context()
        
        # Add a service registry endpoint (should be skipped)
        registry_endpoint = ServiceEndpoint(
            id='registry',
            url='http://localhost:8185/service-registry',
            type=STANDARD_SERVICE_REGISTRY_TYPE_V1_0
        )
        context.endpoints.append(registry_endpoint)
        
        # Add endpoint with mixed authentication methods
        mixed_endpoint = ServiceEndpoint(
            id='mixed-service',
            url='http://localhost:8185/api',
            type=ServiceType(group='com.dnastack', artifact='test-service', version='1.0.0'),
            authentication={
                'type': 'oauth2',
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': 'test-client'
            },
            fallback_authentications=[
                {
                    'type': 'oauth2',
                    'grant_type': GRANT_TYPE_TOKEN_EXCHANGE,
                    'client_id': 'test-client'
                },
                {
                    'type': 'oauth2', 
                    'grant_type': 'client_credentials',
                    'client_id': 'test-client'
                }
            ]
        )
        context.endpoints.append(mixed_endpoint)
        
        # Add endpoint with only token exchange
        token_exchange_endpoint = ServiceEndpoint(
            id='token-exchange-service',
            url='http://localhost:8186/api',
            type=ServiceType(group='com.dnastack', artifact='test-service2', version='1.0.0'),
            authentication={
                'type': 'oauth2',
                'grant_type': GRANT_TYPE_TOKEN_EXCHANGE,
                'client_id': 'test-client'
            }
        )
        context.endpoints.append(token_exchange_endpoint)
        
        # Add endpoint with no token exchange
        no_token_exchange_endpoint = ServiceEndpoint(
            id='no-token-exchange-service',
            url='http://localhost:8187/api',
            type=ServiceType(group='com.dnastack', artifact='test-service3', version='1.0.0'),
            authentication={
                'type': 'oauth2',
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': 'test-client'
            }
        )
        context.endpoints.append(no_token_exchange_endpoint)
        
        # Apply filtering
        manager = BaseContextManager(context_map=None)
        manager._filter_endpoints_for_token_exchange(context)
        
        # Verify results
        # Registry endpoint should be unchanged
        self.assertEqual(registry_endpoint.authentication, None)
        
        # Mixed endpoint should only have token exchange auth
        self.assertEqual(mixed_endpoint.authentication['grant_type'], GRANT_TYPE_TOKEN_EXCHANGE)
        self.assertIsNone(mixed_endpoint.fallback_authentications)
        
        # Token exchange endpoint should be unchanged
        self.assertEqual(token_exchange_endpoint.authentication['grant_type'], GRANT_TYPE_TOKEN_EXCHANGE)
        
        # No token exchange endpoint should have auth cleared
        self.assertIsNone(no_token_exchange_endpoint.authentication)
        self.assertIsNone(no_token_exchange_endpoint.fallback_authentications)


class TestServiceRegistryHelper(TestCase):
    """Test service registry helper functionality"""

    def test_parse_authentication_info_token_exchange(self):
        """Test parsing token exchange authentication info"""
        from dnastack.client.service_registry.helper import _parse_authentication_info
        
        auth_info = {
            'authorizationUrl': 'http://localhost:8081/oauth/authorize',
            'accessTokenUrl': 'http://localhost:8081/oauth/token',
            'clientId': 'test-client',
            'clientSecret': 'test-secret',
            'grantType': GRANT_TYPE_TOKEN_EXCHANGE,
            'resource': 'http://localhost:8185/',
            'scope': 'read write'
        }
        
        result = _parse_authentication_info(auth_info)
        
        self.assertEqual(result['type'], 'oauth2')
        self.assertEqual(result['authorization_endpoint'], 'http://localhost:8081/oauth/authorize')
        self.assertEqual(result['token_endpoint'], 'http://localhost:8081/oauth/token')
        self.assertEqual(result['client_id'], 'test-client')
        self.assertEqual(result['client_secret'], 'test-secret')
        self.assertEqual(result['grant_type'], GRANT_TYPE_TOKEN_EXCHANGE)
        self.assertEqual(result['resource_url'], 'http://localhost:8185/')
        self.assertEqual(result['scope'], 'read write')
        self.assertTrue(result['platform_credentials'])

    def test_parse_authentication_info_device_code(self):
        """Test parsing device code authentication info"""
        from dnastack.client.service_registry.helper import _parse_authentication_info
        
        auth_info = {
            'authorizationUrl': 'http://localhost:8081/oauth/authorize',
            'accessTokenUrl': 'http://localhost:8081/oauth/token',
            'deviceCodeUrl': 'http://localhost:8081/oauth/device/code',
            'clientId': 'test-client',
            'clientSecret': 'test-secret',
            'grantType': 'urn:ietf:params:oauth:grant-type:device_code',
            'resource': 'http://localhost:8185/',
            'scope': 'read write'
        }
        
        result = _parse_authentication_info(auth_info)
        
        self.assertEqual(result['type'], 'oauth2')
        self.assertEqual(result['device_code_endpoint'], 'http://localhost:8081/oauth/device/code')
        self.assertEqual(result['grant_type'], 'urn:ietf:params:oauth:grant-type:device_code')
        self.assertFalse(result['platform_credentials'])