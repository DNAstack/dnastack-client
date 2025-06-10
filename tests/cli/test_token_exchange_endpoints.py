from unittest.mock import patch, Mock, MagicMock

from tests.cli.base import CliTestCase


class TestTokenExchangeEndpoints(CliTestCase):
    """Test cases for token exchange authentication through configured endpoints"""
    
    @staticmethod
    def automatically_authenticate() -> bool:
        return False
    
    def setUp(self):
        super().setUp()
        self.test_endpoint_id = 'test-token-exchange'
        
    def _setup_token_exchange_endpoint(self, with_subject_token=False):
        """Helper method to set up a token exchange endpoint"""
        # Add endpoint
        self.invoke('config', 'endpoints', 'add', '-t', 'oauth2', self.test_endpoint_id)
        
        # Configure endpoint
        config_commands = [
            ('url', 'http://localhost:8185'),
            ('authentication.grant_type', 'urn:ietf:params:oauth:grant-type:token-exchange'),
            ('authentication.token_endpoint', 'http://localhost:8081/oauth/token'),
            ('authentication.resource_url', 'http://localhost:8185'),
        ]
        
        if with_subject_token:
            config_commands.append(('authentication.subject_token', 'test_subject_token_123'))
        
        for key, value in config_commands:
            self.invoke('config', 'endpoints', 'set', self.test_endpoint_id, key, value)
    
    def test_auth_login_with_token_exchange_endpoint(self):
        """Test auth login with a configured token exchange endpoint"""
        self._setup_token_exchange_endpoint(with_subject_token=True)
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'endpoint_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            # Test login
            result = self.invoke('auth', 'login', '--endpoint-id', self.test_endpoint_id)
            
            self.assertEqual(0, result.exit_code, f"Login failed: {result.output}")
            self.assertIn(self.test_endpoint_id, result.output)
            
            # Verify the token exchange was called
            mock_session.post.assert_called()
            call_args = mock_session.post.call_args
            self.assertEqual(call_args[1]['data']['grant_type'], 'urn:ietf:params:oauth:grant-type:token-exchange')
            self.assertEqual(call_args[1]['data']['subject_token'], 'test_subject_token_123')
    
    def test_auth_status_after_token_exchange(self):
        """Test auth status shows correct state after token exchange"""
        self._setup_token_exchange_endpoint(with_subject_token=True)
        
        # First, perform login
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'status_test_token',
            'token_type': 'Bearer',
            'expires_in': 7200
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            self.invoke('auth', 'login', '--endpoint-id', self.test_endpoint_id)
        
        # Check status
        result = self.simple_invoke('auth', 'status', '--endpoint-id', self.test_endpoint_id)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Find our endpoint in the status
        endpoint_status = None
        for status in result:
            if self.test_endpoint_id in status.get('endpoints', []):
                endpoint_status = status
                break
        
        self.assertIsNotNone(endpoint_status, f"Endpoint {self.test_endpoint_id} not found in status")
        self.assertEqual(endpoint_status['status'], 'ready')
        self.assertEqual(endpoint_status['auth_info']['grant_type'], 'urn:ietf:params:oauth:grant-type:token-exchange')
        self.assertEqual(endpoint_status['auth_info']['resource_url'], 'http://localhost:8185')
    
    def test_auth_login_token_exchange_without_subject_token(self):
        """Test auth login with token exchange endpoint that fetches from GCP"""
        self._setup_token_exchange_endpoint(with_subject_token=False)
        
        # Mock both metadata and token exchange responses
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = 'gcp_fetched_token'
        
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': 'gcp_derived_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_metadata_response
            mock_session.post.return_value = mock_token_response
            mock_factory.return_value = mock_session
            
            result = self.invoke('auth', 'login', '--endpoint-id', self.test_endpoint_id)
            
            self.assertEqual(0, result.exit_code, f"Login failed: {result.output}")
            
            # Verify GCP metadata was called
            mock_session.get.assert_called()
            get_call_args = mock_session.get.call_args
            self.assertIn('metadata.google.internal', get_call_args[0][0])
            
            # Verify token exchange was called with the fetched token
            post_call_args = mock_session.post.call_args
            self.assertEqual(post_call_args[1]['data']['subject_token'], 'gcp_fetched_token')
    
    def test_auth_revoke_token_exchange_endpoint(self):
        """Test revoking auth for a token exchange endpoint"""
        self._setup_token_exchange_endpoint(with_subject_token=True)
        
        # First login
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'revoke_test_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            self.invoke('auth', 'login', '--endpoint-id', self.test_endpoint_id)
        
        # Now revoke
        result = self.invoke('auth', 'revoke', '--force', '--endpoint-id', self.test_endpoint_id)
        
        self.assertEqual(0, result.exit_code, f"Revoke failed: {result.output}")
        self.assertIn(self.test_endpoint_id, result.output)
        
        # Check status shows uninitialized
        status_result = self.simple_invoke('auth', 'status', '--endpoint-id', self.test_endpoint_id)
        
        endpoint_status = None
        for status in status_result:
            if self.test_endpoint_id in status.get('endpoints', []):
                endpoint_status = status
                break
        
        self.assertIsNotNone(endpoint_status)
        self.assertEqual(endpoint_status['status'], 'uninitialized')
    
    def test_multiple_token_exchange_endpoints(self):
        """Test handling multiple token exchange endpoints"""
        # Set up two different token exchange endpoints
        endpoint1 = 'token-exchange-1'
        endpoint2 = 'token-exchange-2'
        
        for endpoint_id, resource_url in [(endpoint1, 'http://resource1.example.com'), 
                                          (endpoint2, 'http://resource2.example.com')]:
            self.invoke('config', 'endpoints', 'add', '-t', 'oauth2', endpoint_id)
            self.invoke('config', 'endpoints', 'set', endpoint_id, 'url', resource_url)
            self.invoke('config', 'endpoints', 'set', endpoint_id, 'authentication.grant_type', 
                       'urn:ietf:params:oauth:grant-type:token-exchange')
            self.invoke('config', 'endpoints', 'set', endpoint_id, 'authentication.token_endpoint',
                       'http://localhost:8081/oauth/token')
            self.invoke('config', 'endpoints', 'set', endpoint_id, 'authentication.resource_url', resource_url)
            self.invoke('config', 'endpoints', 'set', endpoint_id, 'authentication.subject_token', 
                       f'token_for_{endpoint_id}')
        
        # Mock responses for both endpoints
        def mock_response_factory(access_token):
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.json.return_value = {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            return mock_resp
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            
            # Configure different responses based on subject token
            def post_side_effect(*args, **kwargs):
                if kwargs['data']['subject_token'] == 'token_for_token-exchange-1':
                    return mock_response_factory('access_token_1')
                else:
                    return mock_response_factory('access_token_2')
            
            mock_session.post.side_effect = post_side_effect
            mock_factory.return_value = mock_session
            
            # Login to all endpoints
            result = self.invoke('auth', 'login')
            
            self.assertEqual(0, result.exit_code)
            
            # Verify both endpoints were authenticated
            self.assertEqual(mock_session.post.call_count, 2)
            
            # Check status shows both are ready
            status_result = self.simple_invoke('auth', 'status')
            
            authenticated_endpoints = set()
            for status in status_result:
                if status['status'] == 'ready':
                    authenticated_endpoints.update(status.get('endpoints', []))
            
            self.assertIn(endpoint1, authenticated_endpoints)
            self.assertIn(endpoint2, authenticated_endpoints)
