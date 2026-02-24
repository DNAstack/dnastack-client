from unittest.mock import Mock, patch, MagicMock
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient
from dnastack.client.workbench.workbench_user_service.models import Namespace
from dnastack.client.models import ServiceEndpoint


class TestGetActiveNamespace:
    """Tests for WorkbenchUserClient.get_active_namespace"""

    def _make_client(self):
        endpoint = ServiceEndpoint(
            id='test',
            url='https://user-service.example.com/',
            type=WorkbenchUserClient.get_default_service_type(),
        )
        return WorkbenchUserClient(endpoint)

    @patch.object(WorkbenchUserClient, 'create_http_session')
    def test_calls_correct_endpoint(self, mock_create_session):
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = {
            "id": "ns-123",
            "name": "My Workspace",
            "description": "Test workspace",
            "created_at": "2026-01-01T00:00:00Z",
            "created_by": "system",
            "updated_at": "2026-01-01T00:00:00Z",
            "updated_by": "system",
        }
        mock_create_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_create_session.return_value.__exit__ = Mock(return_value=False)

        client = self._make_client()
        result = client.get_active_namespace()

        mock_session.get.assert_called_once_with(
            'https://user-service.example.com/users/me/active-namespace'
        )
        assert isinstance(result, Namespace)
        assert result.id == "ns-123"
        assert result.name == "My Workspace"

    @patch.object(WorkbenchUserClient, 'create_http_session')
    def test_returns_namespace_with_minimal_fields(self, mock_create_session):
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = {
            "id": "ns-456",
            "name": "Minimal",
        }
        mock_create_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_create_session.return_value.__exit__ = Mock(return_value=False)

        client = self._make_client()
        result = client.get_active_namespace()

        assert result.id == "ns-456"
        assert result.description is None


class TestSetActiveNamespace:
    """Tests for WorkbenchUserClient.set_active_namespace"""

    def _make_client(self):
        endpoint = ServiceEndpoint(
            id='test',
            url='https://user-service.example.com/',
            type=WorkbenchUserClient.get_default_service_type(),
        )
        return WorkbenchUserClient(endpoint)

    @patch.object(WorkbenchUserClient, 'create_http_session')
    def test_calls_correct_endpoint_with_payload(self, mock_create_session):
        mock_session = MagicMock()
        mock_session.put.return_value.json.return_value = {
            "id": "ns-789",
            "name": "Switched Workspace",
        }
        mock_create_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_create_session.return_value.__exit__ = Mock(return_value=False)

        client = self._make_client()
        result = client.set_active_namespace("ns-789")

        mock_session.put.assert_called_once_with(
            'https://user-service.example.com/users/me/active-namespace',
            json={"namespace_id": "ns-789"},
        )
        assert isinstance(result, Namespace)
        assert result.id == "ns-789"
        assert result.name == "Switched Workspace"
