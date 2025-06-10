import json
from unittest.mock import patch, Mock, MagicMock
from click.testing import Result

from tests.cli.base import CliTestCase
from dnastack.common.environments import env


class TestTokenExchange(CliTestCase):
    """Test cases for the token exchange CLI command"""
    
    @staticmethod
    def automatically_authenticate() -> bool:
        return False
    
    def test_token_exchange_with_provided_subject_token(self):
        """Test token exchange with explicitly provided subject token"""
        # Mock the HTTP client factory to avoid actual network calls
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'mock_access_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': 'mock_refresh_token_456'
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'http://localhost:8081/oauth/token',
                '--resource', 'http://localhost:8185',
                '--subject-token', 'mock_jwt_token_abc123'
            )
            
            self.assertEqual(0, result.exit_code, f"Command failed with output: {result.output}")
            self.assertIn('Token exchange successful!', result.output)
            self.assertIn('Access token: mock_access_token_123', result.output)
            self.assertIn('Token type: Bearer', result.output)
            self.assertIn('Expires in: 3600 seconds', result.output)
            self.assertIn('Refresh token: mock_refresh_token_456', result.output)
            
            # Verify the HTTP call was made correctly
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            self.assertEqual(call_args[0][0], 'http://localhost:8081/oauth/token')
            self.assertEqual(call_args[1]['data']['grant_type'], 'urn:ietf:params:oauth:grant-type:token-exchange')
            self.assertEqual(call_args[1]['data']['subject_token'], 'mock_jwt_token_abc123')
            self.assertEqual(call_args[1]['data']['resource'], 'http://localhost:8185')
    
    def test_token_exchange_with_gcp_metadata_fetch(self):
        """Test token exchange when fetching ID token from GCP metadata service"""
        # Mock the metadata service response
        mock_metadata_response = Mock()
        mock_metadata_response.ok = True
        mock_metadata_response.text = 'gcp_id_token_from_metadata'
        
        # Mock the token exchange response
        mock_token_response = Mock()
        mock_token_response.ok = True
        mock_token_response.json.return_value = {
            'access_token': 'gcp_access_token_789',
            'token_type': 'Bearer',
            'expires_in': 7200
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            
            # Configure responses based on URL
            def side_effect(url, *args, **kwargs):
                if 'metadata.google.internal' in url:
                    return mock_metadata_response
                else:
                    return mock_token_response
            
            mock_session.get.side_effect = lambda *args, **kwargs: side_effect(*args, **kwargs)
            mock_session.post.return_value = mock_token_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'https://example.com/oauth/token',
                '--resource', 'https://example.com/api',
                '--audience', 'https://custom-audience.example.com'
            )
            
            self.assertEqual(0, result.exit_code, f"Command failed with output: {result.output}")
            self.assertIn('Fetching ID token from cloud environment', result.output)
            self.assertIn('Token exchange successful!', result.output)
            self.assertIn('Access token: gcp_access_token_789', result.output)
            self.assertIn('Expires in: 7200 seconds', result.output)
            
            # Verify metadata service was called
            metadata_call = mock_session.get.call_args
            self.assertIn('metadata.google.internal', metadata_call[0][0])
            self.assertIn('audience=https://custom-audience.example.com', metadata_call[0][0])
            self.assertEqual(metadata_call[1]['headers']['Metadata-Flavor'], 'Google')
    
    def test_token_exchange_missing_required_parameters(self):
        """Test that missing required parameters are properly handled"""
        # Test missing token endpoint
        result = self.invoke(
            'auth', 'token-exchange',
            '--resource', 'http://localhost:8185',
            bypass_error=True
        )
        self.assertNotEqual(0, result.exit_code)
        self.assertIn('--token-endpoint', result.stderr)
        
        # Test missing resource
        result = self.invoke(
            'auth', 'token-exchange',
            '--token-endpoint', 'http://localhost:8081/oauth/token',
            bypass_error=True
        )
        self.assertNotEqual(0, result.exit_code)
        self.assertIn('--resource', result.stderr)
    
    def test_token_exchange_failed_metadata_fetch(self):
        """Test handling when GCP metadata service is unavailable"""
        # Mock failed metadata service response
        mock_metadata_response = Mock()
        mock_metadata_response.ok = False
        mock_metadata_response.status_code = 404
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_metadata_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'http://localhost:8081/oauth/token',
                '--resource', 'http://localhost:8185',
                bypass_error=True
            )
            
            self.assertNotEqual(0, result.exit_code)
            # The error should indicate that no subject token was provided
            self.assertIn('No subject token provided', str(result.exception))
    
    def test_token_exchange_failed_token_exchange(self):
        """Test handling when token exchange request fails"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = 'Invalid subject token'
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'http://localhost:8081/oauth/token',
                '--resource', 'http://localhost:8185',
                '--subject-token', 'invalid_token',
                bypass_error=True
            )
            
            self.assertNotEqual(0, result.exit_code)
            self.assertIn('Failed to perform token exchange', str(result.exception))
            self.assertIn('401', str(result.exception))
    
    def test_token_exchange_with_minimal_response(self):
        """Test token exchange with minimal response (no refresh token)"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'minimal_token',
            'token_type': 'Bearer',
            'expires_in': 1800
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'http://localhost:8081/oauth/token',
                '--resource', 'http://localhost:8185',
                '--subject-token', 'test_token'
            )
            
            self.assertEqual(0, result.exit_code)
            self.assertIn('Token exchange successful!', result.output)
            self.assertIn('Access token: minimal_token', result.output)
            # Should not show refresh token line when not present
            self.assertNotIn('Refresh token:', result.output)
    
    def test_token_exchange_uses_explorer_credentials(self):
        """Test that token exchange uses explorer client credentials by default"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.post.return_value = mock_response
            mock_factory.return_value = mock_session
            
            result = self.invoke(
                'auth', 'token-exchange',
                '--token-endpoint', 'http://localhost:8081/oauth/token',
                '--resource', 'http://localhost:8185',
                '--subject-token', 'test_subject_token'
            )
            
            self.assertEqual(0, result.exit_code)
            
            # Verify explorer credentials were used
            call_args = mock_session.post.call_args
            auth_tuple = call_args[1]['auth']
            self.assertEqual(auth_tuple[0], 'dnastack-client')  # Explorer client ID
            self.assertEqual(auth_tuple[1], 'dev-secret-never-use-in-prod')  # Explorer client secret
