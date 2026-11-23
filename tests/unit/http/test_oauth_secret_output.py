"""Login, refresh, and config listings must not print OAuth tokens or client secrets."""
import json
from http.client import HTTPConnection
from unittest.mock import Mock, patch

from click.testing import CliRunner

from dnastack.cli.commands.config.endpoints import endpoint_command_group
from dnastack.cli.commands.config.registries import registry_command_group
from dnastack.client.models import ServiceEndpoint
from dnastack.common.logger import TraceableLogger
from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
from dnastack.http.authenticators.oauth2_adapter.abstract import AuthException
from dnastack.http.authenticators.oauth2_adapter.client_credential import ClientCredentialAdapter
from dnastack.http.authenticators.oauth2_adapter.device_code_flow import DeviceCodeFlowAdapter
from dnastack.http.authenticators.oauth2_adapter.models import (
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_TOKEN_EXCHANGE,
    OAuth2Authentication,
)
from dnastack.http.authenticators.oauth2_adapter.token_exchange import TokenExchangeAdapter
from dnastack.http.client_factory import HttpClientFactory
from dnastack.http.session_info import SessionInfo, SessionInfoHandler

CLIENT_ID = 'explorer.example.com-public-client'
CLIENT_SECRET = 'CLIENT-SECRET-MARKER'
ACCESS_TOKEN = 'ACCESS-TOKEN-MARKER'
REFRESH_TOKEN = 'REFRESH-TOKEN-MARKER'
DEVICE_CODE = 'DEVICE-CODE-MARKER'
USER_CODE = 'USER-CODE-MARKER'
SUBJECT_TOKEN = 'SUBJECT-TOKEN-MARKER'
SCOPE_MARKER = 'SCOPE-MARKER'
INIT_BODY_MARKER = 'INIT-BODY-MARKER'
TOKEN_URL = 'https://passport.example.com/oauth/token'
RESOURCE_URL = 'https://explorer.example.com/'


def _messages(*loggers) -> str:
    parts = []
    for logger in loggers:
        for call in logger.call_args_list:
            if len(call.args) > 1:
                parts.append(str(call.args[1]))
    return '\n'.join(parts)


def _json_response(body: dict, *, ok: bool = True, status_code: int = 200):
    response = Mock(ok=ok, status_code=status_code, text=json.dumps(body))
    response.json.return_value = body
    response.headers = {}
    return response


def _endpoint_with_secret() -> ServiceEndpoint:
    return ServiceEndpoint(
        id='explorer',
        url=RESOURCE_URL,
        authentication={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'personal_access_token': 'PAT-MARKER',
            'grant_type': 'client_credentials',
            'resource_url': RESOURCE_URL,
            'token_endpoint': TOKEN_URL,
        },
        fallback_authentications=[{'clientId': CLIENT_ID, 'clientSecret': CLIENT_SECRET}],
    )


def _assert_listing_masks_secrets(output: str, endpoint: ServiceEndpoint):
    assert CLIENT_ID in output
    for secret in (CLIENT_SECRET, 'PAT-MARKER'):
        assert secret not in output
    assert '***' in output
    assert endpoint.authentication['client_secret'] == CLIENT_SECRET
    assert endpoint.fallback_authentications[0]['clientSecret'] == CLIENT_SECRET


def test_config_endpoints_list_masks_client_secrets():
    endpoint = _endpoint_with_secret()
    handler = Mock()
    handler.list_endpoints.return_value = [endpoint]
    with patch('dnastack.cli.commands.config.endpoints.EndpointCommandHandler', return_value=handler):
        result = CliRunner().invoke(endpoint_command_group, ['list'])

    assert result.exit_code == 0, result.output
    _assert_listing_masks_secrets(result.output, endpoint)


def test_config_registries_list_masks_client_secrets():
    endpoint = _endpoint_with_secret()
    handler = Mock()
    handler.get_registry_endpoint_iterator.return_value = [endpoint]
    with patch('dnastack.cli.commands.config.registries.ServiceRegistryCommandHandler', return_value=handler):
        result = CliRunner().invoke(registry_command_group, ['list'])

    assert result.exit_code == 0, result.output
    _assert_listing_masks_secrets(result.output, endpoint)


def test_config_registries_list_endpoints_masks_client_secrets():
    endpoint = _endpoint_with_secret()
    handler = Mock()
    handler.list_endpoints_associated_to.return_value = [endpoint]
    with patch('dnastack.cli.commands.config.registries.ServiceRegistryCommandHandler', return_value=handler):
        result = CliRunner().invoke(registry_command_group, ['list-endpoints', 'registry-1'])

    assert result.exit_code == 0, result.output
    _assert_listing_masks_secrets(result.output, endpoint)


def test_client_credential_success_logs_status_without_tokens():
    body = {
        'access_token': ACCESS_TOKEN,
        'refresh_token': REFRESH_TOKEN,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': SCOPE_MARKER,
    }
    seen = []

    def post(*args, **kwargs):
        seen.append(HTTPConnection.debuglevel)
        assert kwargs['data']['client_secret'] == CLIENT_SECRET
        return _json_response(body)

    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.post.side_effect = post
    auth = OAuth2Authentication(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, grant_type='client_credentials',
                                resource_url=RESOURCE_URL, token_endpoint=TOKEN_URL)
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1
    try:
        with patch.object(TraceableLogger, 'debug', autospec=True) as debug, \
                patch.object(TraceableLogger, 'warning', autospec=True) as warning, \
                patch.object(TraceableLogger, 'error', autospec=True) as error, \
                patch.object(HttpClientFactory, 'make', return_value=session):
            result = ClientCredentialAdapter(auth).exchange_tokens(Span(origin='test'))
        log = _messages(debug, warning, error)
        assert HTTPConnection.debuglevel == 1
    finally:
        HTTPConnection.debuglevel = saved
    assert result['access_token'] == ACCESS_TOKEN
    assert 'HTTP 200' in log
    for secret in (ACCESS_TOKEN, REFRESH_TOKEN, CLIENT_SECRET, SCOPE_MARKER):
        assert secret not in log
    assert seen == [0]


def test_client_credential_error_redacts_token_fields():
    body = {
        'error': 'invalid_client',
        'error_description': 'nope',
        'access_token': ACCESS_TOKEN,
        'client_secret': CLIENT_SECRET,
    }
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.post.return_value = _json_response(body, ok=False, status_code=401)
    auth = OAuth2Authentication(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, grant_type='client_credentials',
                                resource_url=RESOURCE_URL, token_endpoint=TOKEN_URL)
    with patch.object(HttpClientFactory, 'make', return_value=session):
        try:
            ClientCredentialAdapter(auth).exchange_tokens(Span(origin='test'))
        except AuthException as exc:
            message = str(exc)
        else:
            raise AssertionError('expected AuthException')

    assert 'nope' in message
    assert '***' in message
    assert ACCESS_TOKEN not in message
    assert CLIENT_SECRET not in message


def test_device_code_login_logs_status_without_codes_or_tokens():
    init_body = {
        'device_code': DEVICE_CODE,
        'user_code': USER_CODE,
        'verification_uri_complete': f'https://example.com/device?user_code={USER_CODE}',
        'interval': 1,
        'expires_in': 600,
        'extra': INIT_BODY_MARKER,
    }
    token_body = {
        'access_token': ACCESS_TOKEN,
        'refresh_token': REFRESH_TOKEN,
        'token_type': 'Bearer',
        'scope': SCOPE_MARKER,
    }
    responses = [_json_response(init_body), _json_response(token_body)]
    seen = []

    def post(*args, **kwargs):
        seen.append(HTTPConnection.debuglevel)
        return responses.pop(0)

    session = Mock()
    session.post.side_effect = post
    auth = OAuth2Authentication(client_id=CLIENT_ID, grant_type=GRANT_TYPE_DEVICE_CODE, resource_url=RESOURCE_URL,
                                token_endpoint=TOKEN_URL, device_code_endpoint='https://passport.example.com/device')
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1
    try:
        with patch.object(TraceableLogger, 'debug', autospec=True) as debug, \
                patch.object(TraceableLogger, 'warning', autospec=True) as warning, \
                patch.object(TraceableLogger, 'error', autospec=True) as error, \
                patch.object(HttpClientFactory, 'make', return_value=session):
            result = DeviceCodeFlowAdapter(auth).exchange_tokens(Span(origin='test'))
        log = _messages(debug, warning, error)
        assert HTTPConnection.debuglevel == 1
    finally:
        HTTPConnection.debuglevel = saved
    assert result['access_token'] == ACCESS_TOKEN
    assert 'HTTP 200' in log
    for secret in (DEVICE_CODE, USER_CODE, ACCESS_TOKEN, REFRESH_TOKEN, INIT_BODY_MARKER, SCOPE_MARKER):
        assert secret not in log
    assert seen == [0, 0]


def test_refresh_logs_status_without_tokens():
    auth_info = {
        'grant_type': 'classified',
        'resource_url': RESOURCE_URL,
        'token_endpoint': TOKEN_URL,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    body = {
        'access_token': ACCESS_TOKEN,
        'refresh_token': 'NEW-REFRESH-MARKER',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': SCOPE_MARKER,
    }
    seen = []

    def post(*args, **kwargs):
        seen.append(HTTPConnection.debuglevel)
        assert kwargs['data']['refresh_token'] == REFRESH_TOKEN
        assert kwargs['auth'] == (CLIENT_ID, CLIENT_SECRET)
        return _json_response(body)

    http_session = Mock()
    http_session.post.side_effect = post
    http_client_factory = Mock(spec=HttpClientFactory)
    http_client_factory.make.return_value = http_session
    session_info = SessionInfo(access_token='OLD-ACCESS-MARKER', refresh_token=REFRESH_TOKEN, token_type='Bearer',
                               issued_at=0, valid_until=1, handler=SessionInfoHandler(auth_info=auth_info))
    authenticator = OAuth2Authenticator(endpoint=ServiceEndpoint(url=RESOURCE_URL), auth_info=auth_info,
                                        session_manager=Mock(), adapter_factory=Mock(),
                                        http_client_factory=http_client_factory)
    authenticator._session_info = session_info
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1
    try:
        with patch.object(TraceableLogger, 'debug', autospec=True) as debug, \
                patch.object(TraceableLogger, 'warning', autospec=True) as warning, \
                patch.object(TraceableLogger, 'error', autospec=True) as error:
            refreshed = authenticator.refresh()
        log = _messages(debug, warning, error)
        assert HTTPConnection.debuglevel == 1
    finally:
        HTTPConnection.debuglevel = saved
    assert refreshed.access_token == ACCESS_TOKEN
    assert 'HTTP 200' in log
    for secret in (ACCESS_TOKEN, REFRESH_TOKEN, 'NEW-REFRESH-MARKER', CLIENT_SECRET, 'OLD-ACCESS-MARKER', SCOPE_MARKER):
        assert secret not in log
    assert seen == [0]


def test_unexpected_token_response_does_not_include_the_refresh_token():
    authenticator = OAuth2Authenticator(endpoint=ServiceEndpoint(url=RESOURCE_URL),
                                        auth_info={'grant_type': 'classified', 'resource_url': RESOURCE_URL},
                                        session_manager=Mock(), adapter_factory=Mock(), http_client_factory=Mock())
    try:
        authenticator._convert_token_response_to_session(
            {'client_id': CLIENT_ID},
            {'refresh_token': REFRESH_TOKEN, 'client_secret': CLIENT_SECRET, 'token_type': 'Bearer'},
        )
    except AssertionError as exc:
        message = str(exc)
    else:
        raise AssertionError('expected AssertionError')

    assert REFRESH_TOKEN not in message
    assert CLIENT_SECRET not in message
    assert '***' in message
    assert 'Bearer' in message


def test_debug_mode_does_not_log_bearer_token_claims():
    access_token = f'header.{ACCESS_TOKEN}.sig'
    session = SessionInfo(access_token=access_token, token_type='Bearer', issued_at=0, valid_until=1)
    authenticator = OAuth2Authenticator(endpoint=ServiceEndpoint(url=RESOURCE_URL),
                                        auth_info={'grant_type': 'classified', 'resource_url': RESOURCE_URL},
                                        session_manager=Mock(), adapter_factory=Mock(), http_client_factory=Mock())
    request = Mock()
    request.headers = {}
    with patch('dnastack.http.authenticators.oauth2.currently_in_debug_mode', return_value=True), \
            patch.object(TraceableLogger, 'debug', autospec=True) as debug:
        authenticator.update_request(session, request)

    assert request.headers['Authorization'] == f'Bearer {access_token}'
    assert ACCESS_TOKEN not in _messages(debug)


def test_token_exchange_error_redacts_tokens_and_skips_wire_debugging():
    body = {'error': 'invalid_grant', 'error_description': 'nope', 'access_token': ACCESS_TOKEN}
    seen = []

    def post(*args, **kwargs):
        seen.append(HTTPConnection.debuglevel)
        assert kwargs['data']['subject_token'] == SUBJECT_TOKEN
        return _json_response(body, ok=False, status_code=400)

    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.post.side_effect = post
    auth = OAuth2Authentication(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, grant_type=GRANT_TYPE_TOKEN_EXCHANGE,
                                resource_url=RESOURCE_URL, token_endpoint=TOKEN_URL, subject_token=SUBJECT_TOKEN)
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1
    try:
        with patch.object(TraceableLogger, 'debug', autospec=True) as debug, \
                patch.object(TraceableLogger, 'error', autospec=True) as error, \
                patch.object(HttpClientFactory, 'make', return_value=session):
            try:
                TokenExchangeAdapter(auth).exchange_tokens(Span(origin='test'))
            except AuthException as exc:
                message = str(exc)
            else:
                raise AssertionError('expected AuthException')
        assert HTTPConnection.debuglevel == 1
    finally:
        HTTPConnection.debuglevel = saved

    assert 'nope' in message
    assert ACCESS_TOKEN not in message
    assert SUBJECT_TOKEN not in message
    assert CLIENT_SECRET not in message
    assert SUBJECT_TOKEN not in _messages(debug, error)
    assert CLIENT_SECRET not in _messages(debug, error)
    assert seen == [0]
