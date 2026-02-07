"""Unit tests for EWesClient methods"""
import unittest
from unittest.mock import Mock, patch, MagicMock

from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.ewes.models import SimpleSample, ExtendedRunStatus
from dnastack.client.models import ServiceEndpoint


class TestEWesClientUpdateRunSamples(unittest.TestCase):
    """Unit tests for EWesClient.update_run_samples method"""

    def setUp(self):
        self.endpoint = ServiceEndpoint(url="https://api.example.com/")
        self.namespace = "test-namespace"

    @patch.object(EWesClient, 'create_http_session')
    def test_update_run_samples_sends_correct_request(self, mock_create_session):
        """Test that update_run_samples sends correct PUT request"""
        mock_session = MagicMock()
        mock_create_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_create_session.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.json.return_value = {
            "run_id": "run-123",
            "state": "COMPLETE",
            "start_time": "2026-01-01T00:00:00Z",
            "samples": [
                {"id": "sample-1", "storage_account_id": "sa-1"},
                {"id": "sample-2", "storage_account_id": None},
            ]
        }
        mock_session.submit.return_value = mock_response

        client = EWesClient(self.endpoint, self.namespace)
        samples = [
            SimpleSample(id="sample-1", storage_account_id="sa-1"),
            SimpleSample(id="sample-2", storage_account_id=None),
        ]

        result = client.update_run_samples("run-123", samples)

        # Verify the request was made correctly
        mock_session.submit.assert_called_once()
        call_kwargs = mock_session.submit.call_args
        self.assertEqual(call_kwargs.kwargs['method'], 'put')
        self.assertIn('/runs/run-123/samples', call_kwargs.kwargs['url'])
        self.assertIn('samples', call_kwargs.kwargs['json'])

        # Verify the response is parsed correctly
        self.assertIsInstance(result, ExtendedRunStatus)
        self.assertEqual(result.run_id, "run-123")

    @patch.object(EWesClient, 'create_http_session')
    def test_update_run_samples_with_empty_list(self, mock_create_session):
        """Test that update_run_samples works with empty samples list (clear)"""
        mock_session = MagicMock()
        mock_create_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_create_session.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.json.return_value = {
            "run_id": "run-123",
            "state": "COMPLETE",
            "start_time": "2026-01-01T00:00:00Z",
            "samples": []
        }
        mock_session.submit.return_value = mock_response

        client = EWesClient(self.endpoint, self.namespace)
        result = client.update_run_samples("run-123", [])

        # Verify empty samples list is sent
        call_kwargs = mock_session.submit.call_args
        self.assertEqual(call_kwargs.kwargs['json']['samples'], [])

        # Verify the response
        self.assertIsInstance(result, ExtendedRunStatus)


if __name__ == '__main__':
    unittest.main()
