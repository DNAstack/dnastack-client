from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from dnastack.client.models import ServiceEndpoint
from dnastack.client.tenants.client import TenantClient, UnknownTenantError, WalletEndpointNotDerivableError, \
    WALLET_SERVICE_TYPE_V1_0
from dnastack.client.tenants.models import Tenant, TenantStatus
from dnastack.http.session import ClientError

TENANT_ID = '6f1c1f7e-9a59-4d0c-9a8e-3b6f0f7d6a11'
WALLET_URL = 'https://wallet.example.com/'


def _make_client() -> TenantClient:
    return TenantClient(ServiceEndpoint(id='wallet', url=WALLET_URL, type=WALLET_SERVICE_TYPE_V1_0))


def _mock_session(mock_create_session) -> MagicMock:
    session = MagicMock()
    mock_create_session.return_value.__enter__ = Mock(return_value=session)
    mock_create_session.return_value.__exit__ = Mock(return_value=False)
    return session


def _client_error(status_code: int) -> ClientError:
    response = Mock()
    response.status_code = status_code
    return ClientError(response)


@patch.object(TenantClient, 'create_http_session')
class TestTenantClient:
    def test_list_tenants(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.get.return_value.json.return_value = [
            {'id': TENANT_ID, 'name': 'sickkids', 'status': 'ENABLED', 'created_at': '2026-10-01T00:00:00Z'},
        ]

        tenants = _make_client().list_tenants()

        assert session.get.call_args.args == ('https://wallet.example.com/tenants',)
        assert tenants == [Tenant(id=TENANT_ID, name='sickkids', status=TenantStatus.ENABLED,
                                  created_at=datetime(2026, 10, 1, tzinfo=timezone.utc))]

    def test_get_unknown_tenant_raises_unknown_tenant(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.get.side_effect = _client_error(404)

        with pytest.raises(UnknownTenantError):
            _make_client().get_tenant(TENANT_ID)

    def test_create_tenant_sends_expiry_as_utc_instant(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.post.return_value.json.return_value = {'id': TENANT_ID, 'name': 'sickkids'}

        _make_client().create_tenant('sickkids', expires_at=datetime(2026, 11, 2, 5, 0, 0, tzinfo=timezone.utc))

        assert session.post.call_args.args == ('https://wallet.example.com/tenants',)
        assert session.post.call_args.kwargs['json'] == {'name': 'sickkids', 'expires_at': '2026-11-02T05:00:00Z'}

    def test_create_tenant_without_expiry_omits_it(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.post.return_value.json.return_value = {'id': TENANT_ID, 'name': 'sickkids'}

        _make_client().create_tenant('sickkids')

        assert session.post.call_args.kwargs['json'] == {'name': 'sickkids'}

    def test_delete_tenant(self, mock_create_session):
        session = _mock_session(mock_create_session)

        _make_client().delete_tenant(TENANT_ID)

        assert session.delete.call_args.args == (f'https://wallet.example.com/tenants/{TENANT_ID}',)

    def test_delete_unknown_tenant_raises_unknown_tenant(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.delete.side_effect = _client_error(404)

        with pytest.raises(UnknownTenantError):
            _make_client().delete_tenant(TENANT_ID)

    def test_delete_rethrows_other_client_errors(self, mock_create_session):
        session = _mock_session(mock_create_session)
        session.delete.side_effect = _client_error(400)

        with pytest.raises(ClientError):
            _make_client().delete_tenant(TENANT_ID)

    @pytest.mark.parametrize('method, status', [('disable_tenant', 'DISABLED'), ('enable_tenant', 'ENABLED')])
    def test_set_status(self, mock_create_session, method, status):
        session = _mock_session(mock_create_session)

        getattr(_make_client(), method)(TENANT_ID)

        assert session.put.call_args.args == (f'https://wallet.example.com/tenants/{TENANT_ID}/status',)
        assert session.put.call_args.kwargs['json'] == {'status': status}

    def test_clearing_expiration_sends_null(self, mock_create_session):
        session = _mock_session(mock_create_session)

        _make_client().set_tenant_expiration(TENANT_ID, None)

        assert session.put.call_args.args == (f'https://wallet.example.com/tenants/{TENANT_ID}/expiration',)
        assert session.put.call_args.kwargs['json'] == {'expires_at': None}


class TestMakeFromPublisherEndpoint:
    def test_targets_wallet_that_issues_publisher_tokens(self):
        publisher_endpoint = ServiceEndpoint(
            id='collection-service',
            url='https://publisher.example.com/',
            authentication={
                'type': 'oauth2',
                'client_id': 'publisher-cli',
                'device_code_endpoint': 'https://wallet.example.com/oauth/device/code',
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'resource_url': 'https://publisher.example.com/',
                'token_endpoint': 'https://wallet.example.com/oauth/token',
            },
        )

        client = TenantClient.make_from_publisher_endpoint(publisher_endpoint)

        assert client.url == WALLET_URL
        assert client.endpoint.type == WALLET_SERVICE_TYPE_V1_0
        assert client.endpoint.authentication == {
            'type': 'oauth2',
            'client_id': 'publisher-cli',
            'device_code_endpoint': 'https://wallet.example.com/oauth/device/code',
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'resource_url': WALLET_URL,
            'scope': 'admin:tenants',
            'token_endpoint': 'https://wallet.example.com/oauth/token',
        }
        # The Publisher endpoint itself must not be changed.
        assert publisher_endpoint.authentication['resource_url'] == 'https://publisher.example.com/'

    def test_without_oauth2_authentication_raises(self):
        with pytest.raises(WalletEndpointNotDerivableError):
            TenantClient.make_from_publisher_endpoint(
                ServiceEndpoint(id='collection-service', url='https://publisher.example.com/'))

    def test_with_unrecognized_token_endpoint_raises(self):
        with pytest.raises(WalletEndpointNotDerivableError):
            TenantClient.make_from_publisher_endpoint(ServiceEndpoint(
                id='collection-service',
                url='https://publisher.example.com/',
                authentication={'type': 'oauth2', 'resource_url': 'https://publisher.example.com/',
                                 'token_endpoint': 'https://idp.example.com/token'},
            ))
