"""Tests that WorkflowClient methods inject X-Admin-Only-Action header when admin_only_action=True."""
from unittest.mock import MagicMock, patch

from dnastack.client.models import ServiceEndpoint
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.workflow.client import WorkflowClient
from dnastack.client.workbench.workflow.models import (
    WorkflowCreate,
    WorkflowDefaultsCreateRequest,
    WorkflowTransformationCreate,
    WorkflowVersionCreate,
)
from dnastack.http.session import JsonPatch


def _create_workflow_client(namespace='test-ns'):
    """Create a WorkflowClient with a mocked endpoint."""
    endpoint = ServiceEndpoint(
        id='test-endpoint',
        url='http://localhost:8080/',
        type=ServiceType(group='com.dnastack.workbench', artifact='workflow-service', version='1.0.0'),
    )
    return WorkflowClient.make(endpoint=endpoint, namespace=namespace)


_WORKFLOW_JSON = {
    'internalId': 'test-id',
    'source': 'dnastack',
    'name': 'test-workflow',
    'latestVersion': '1.0',
}

_WORKFLOW_VERSION_JSON = {
    'id': 'test-version-id',
    'versionName': '1.0',
    'workflowName': 'test-workflow',
    'descriptorType': 'WDL',
}


def _mock_session(response_json=None):
    """Create a mock HTTP session context manager.

    Args:
        response_json: Optional dict to return from response.json(). Defaults to an empty dict.
    """
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)

    mock_response = MagicMock()
    mock_response.json.return_value = response_json or {}
    mock_response.headers = {'Etag': '"test-etag"'}

    session.post.return_value = mock_response
    session.submit.return_value = mock_response
    session.delete.return_value = mock_response
    session.json_patch.return_value = mock_response
    session.get.return_value = mock_response
    return session


class TestAdminOnlyActionHeader:
    """Verify that admin_only_action=True adds the X-Admin-Only-Action header."""

    def _assert_header_present(self, call_kwargs):
        headers = call_kwargs.get('headers', {})
        assert 'X-Admin-Only-Action' in headers, f"Expected X-Admin-Only-Action header, got: {headers}"
        assert headers['X-Admin-Only-Action'] == 'true'

    def _assert_header_absent(self, call_kwargs):
        headers = call_kwargs.get('headers', {})
        assert 'X-Admin-Only-Action' not in headers, f"Unexpected X-Admin-Only-Action header in: {headers}"

    def test_create_workflow_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_JSON)
        workflow_create = WorkflowCreate(
            name='test-workflow',
            version_name='1.0',
            entrypoint='main.wdl',
            files=[],
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.create_workflow(workflow_create, admin_only_action=True)

        mock_session.post.assert_called_once()
        self._assert_header_present(mock_session.post.call_args.kwargs)

    def test_create_workflow_no_admin_header_by_default(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_JSON)
        workflow_create = WorkflowCreate(
            name='test-workflow',
            version_name='1.0',
            entrypoint='main.wdl',
            files=[],
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.create_workflow(workflow_create)

        mock_session.post.assert_called_once()
        self._assert_header_absent(mock_session.post.call_args.kwargs)

    def test_delete_workflow_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_JSON)
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.delete_workflow('wf-id', etag='test-etag', admin_only_action=True)

        mock_session.delete.assert_called_once()
        call_kwargs = mock_session.delete.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_delete_workflow_no_admin_header_by_default(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_JSON)
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.delete_workflow('wf-id', etag='test-etag')

        mock_session.delete.assert_called_once()
        self._assert_header_absent(mock_session.delete.call_args.kwargs)

    def test_update_workflow_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_JSON)
        patches = [JsonPatch(op='replace', path='/name', value='new-name')]
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.update_workflow('wf-id', etag='test-etag', updates=patches, admin_only_action=True)

        mock_session.json_patch.assert_called_once()
        call_kwargs = mock_session.json_patch.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_create_version_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_VERSION_JSON)
        version_create = WorkflowVersionCreate(
            version_name='2.0',
            entrypoint='main.wdl',
            files=[],
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.create_version('wf-id', version_create, admin_only_action=True)

        mock_session.post.assert_called_once()
        self._assert_header_present(mock_session.post.call_args.kwargs)

    def test_delete_workflow_version_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_VERSION_JSON)
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.delete_workflow_version('wf-id', 'v-id', etag='test-etag', admin_only_action=True)

        mock_session.delete.assert_called_once()
        call_kwargs = mock_session.delete.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_update_workflow_version_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session(response_json=_WORKFLOW_VERSION_JSON)
        patches = [JsonPatch(op='replace', path='/version_name', value='2.1')]
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.update_workflow_version('wf-id', 'v-id', etag='test-etag', updates=patches, admin_only_action=True)

        mock_session.json_patch.assert_called_once()
        call_kwargs = mock_session.json_patch.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_create_workflow_defaults_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session()
        defaults_create = WorkflowDefaultsCreateRequest(
            name='test-defaults',
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.create_workflow_defaults('wf-id', 'v-id', defaults_create, admin_only_action=True)

        mock_session.post.assert_called_once()
        self._assert_header_present(mock_session.post.call_args.kwargs)

    def test_delete_workflow_defaults_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session()
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.delete_workflow_defaults('wf-id', 'v-id', 'def-id', if_match='test-etag', admin_only_action=True)

        mock_session.delete.assert_called_once()
        call_kwargs = mock_session.delete.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_update_workflow_defaults_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session()
        from dnastack.client.workbench.workflow.models import WorkflowDefaultsUpdateRequest
        defaults_update = WorkflowDefaultsUpdateRequest(
            name='updated-defaults',
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.update_workflow_defaults('wf-id', 'v-id', 'def-id', if_match='test-etag',
                                            workflow_defaults=defaults_update, admin_only_action=True)

        mock_session.submit.assert_called_once()
        call_kwargs = mock_session.submit.call_args.kwargs
        self._assert_header_present(call_kwargs)
        # Also verify the If-Match header is preserved
        assert call_kwargs['headers']['If-Match'] == 'test-etag'

    def test_create_workflow_transformation_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session()
        transformation_create = WorkflowTransformationCreate(
            script='echo hello',
        )
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.create_workflow_transformation('wf-id', 'v-id', transformation_create, admin_only_action=True)

        mock_session.post.assert_called_once()
        self._assert_header_present(mock_session.post.call_args.kwargs)

    def test_delete_workflow_transformation_sends_admin_header(self):
        client = _create_workflow_client()
        mock_session = _mock_session()
        with patch.object(client, 'create_http_session', return_value=mock_session):
            client.delete_workflow_transformation('wf-id', 'v-id', 'trans-id', admin_only_action=True)

        mock_session.delete.assert_called_once()
        self._assert_header_present(mock_session.delete.call_args.kwargs)
