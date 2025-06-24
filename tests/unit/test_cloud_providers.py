import unittest
from unittest.mock import Mock, patch, MagicMock
from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.cloud_providers import (
    CloudProvider, CloudProviderFactory, GCPMetadataProvider, CloudMetadataConfig
)


class TestCloudProviders(unittest.TestCase):

    def setUp(self):
        self.trace_context = Span(origin='test')
        self.test_audience = 'https://api.example.com'
        self.config = CloudMetadataConfig(timeout=5)

    def test_gcp_metadata_provider_is_available_success(self):
        """Test GCP provider availability check when metadata service is accessible."""
        provider = GCPMetadataProvider(timeout=self.config.timeout)

        mock_response = Mock()
        mock_response.ok = True

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session

            self.assertTrue(provider.is_available())

            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            self.assertIn('metadata.google.internal', call_args[0][0])
            self.assertEqual(call_args[1]['headers']['Metadata-Flavor'], 'Google')
            self.assertEqual(call_args[1]['timeout'], 1)

    def test_gcp_metadata_provider_is_available_failure(self):
        """Test GCP provider availability check when metadata service is not accessible."""
        provider = GCPMetadataProvider(timeout=self.config.timeout)

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.side_effect = Exception('Connection timeout')
            mock_factory.return_value = mock_session

            self.assertFalse(provider.is_available())

    def test_gcp_get_identity_token_success(self):
        """Test successful GCP identity token fetch."""
        provider = GCPMetadataProvider(timeout=self.config.timeout)
        expected_token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.signature'

        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = expected_token

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session
            token = provider.get_identity_token(self.test_audience, self.trace_context)

            self.assertEqual(token, expected_token)

            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            url = call_args[0][0]
            self.assertIn('metadata.google.internal', url)
            self.assertIn(f'audience={self.test_audience}', url)
            self.assertIn('format=full', url)

    def test_gcp_get_identity_token_failure(self):
        """Test GCP identity token fetch when service returns error."""
        provider = GCPMetadataProvider(timeout=self.config.timeout)

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

            token = provider.get_identity_token(self.test_audience, self.trace_context)

            self.assertIsNone(token)

    def test_gcp_get_identity_token_exception(self):
        """Test GCP identity token fetch when exception occurs."""
        provider = GCPMetadataProvider(timeout=self.config.timeout)

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.side_effect = Exception('Network error')
            mock_factory.return_value = mock_session

            token = provider.get_identity_token(self.test_audience, self.trace_context)

            self.assertIsNone(token)

    def test_cloud_provider_factory_create_gcp(self):
        """Test factory creates GCP provider instance."""
        gcp_provider = CloudProviderFactory.create(CloudProvider.GCP, self.config)
        self.assertIsInstance(gcp_provider, GCPMetadataProvider)

    def test_cloud_provider_factory_create_unsupported(self):
        """Test factory raises error for unsupported provider."""
        with self.assertRaises(ValueError) as context:
            CloudProviderFactory.create('unsupported', self.config)

        self.assertIn('Unsupported cloud provider', str(context.exception))

    def test_detect_provider_returns_gcp(self):
        mock_response = Mock()
        mock_response.ok = True

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session

            detected = CloudProviderFactory.detect_provider(self.config)
            self.assertIsInstance(detected, GCPMetadataProvider)

    def test_detect_provider_returns_none_if_metadata_unavailable(self):
        """Test detect_provider returns None when metadata service is unavailable."""
        mock_response = Mock()
        mock_response.ok = False

        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.return_value = mock_response
            mock_factory.return_value = mock_session

            detected = CloudProviderFactory.detect_provider(self.config)
            self.assertIsNone(detected)

    def test_detect_provider_returns_none_if_metadata_exception(self):
        """Test detect_provider returns None when an exception occurs during metadata fetch."""
        with patch('dnastack.http.client_factory.HttpClientFactory.make') as mock_factory:
            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_session.__exit__.return_value = None
            mock_session.get.side_effect = Exception("Simulated network error")
            mock_factory.return_value = mock_session

            detected = CloudProviderFactory.detect_provider(self.config)
            self.assertIsNone(detected)

    def test_detect_provider_handles_create_exception(self):
        """Test detect_provider handles exceptions during provider creation."""
        with patch.object(CloudProviderFactory, 'create', side_effect=Exception("Provider creation failed")):
            detected = CloudProviderFactory.detect_provider(self.config)
            self.assertIsNone(detected)



if __name__ == '__main__':
    unittest.main()
