from unittest.mock import MagicMock, patch

from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.models import ServiceEndpoint


def _make_client(url='http://localhost:8093/'):
    client = CollectionServiceClient.__new__(CollectionServiceClient)
    client._endpoint = MagicMock(spec=ServiceEndpoint)
    client._endpoint.url = url
    return client


class TestSubmitTelemetry:

    def test_posts_to_otlp_traces_endpoint(self):
        client = _make_client()
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.submit_telemetry({'resourceSpans': []})

        mock_session.post.assert_called_once_with(
            'http://localhost:8093/otlp/v1/traces',
            json={'resourceSpans': []},
            trace_context=None
        )

    def test_passes_trace_context_when_provided(self):
        client = _make_client()
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_trace = MagicMock()

        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.submit_telemetry({'resourceSpans': []}, trace=mock_trace)

        mock_session.post.assert_called_once_with(
            'http://localhost:8093/otlp/v1/traces',
            json={'resourceSpans': []},
            trace_context=mock_trace
        )
