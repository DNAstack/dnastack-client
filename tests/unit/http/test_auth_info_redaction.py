"""Unit tests for keeping OAuth client secrets and tokens out of model repr/str (and so out of log messages)."""
from dnastack.client.models import ServiceEndpoint
from dnastack.client.service_registry.helper import parse_ga4gh_service_info
from dnastack.client.service_registry.models import Service, ServiceType
from dnastack.http.authenticators.oauth2_adapter.models import (
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_TOKEN_EXCHANGE,
    OAuth2Authentication,
    redact_secrets,
)
from dnastack.http.session_info import SessionInfo, SessionInfoHandler

CLIENT_ID = 'explorer.example.com-public-client'
CLIENT_SECRET = 'CLIENT-SECRET-MARKER'
ACCESS_TOKEN = 'ACCESS-TOKEN-MARKER'
REFRESH_TOKEN = 'REFRESH-TOKEN-MARKER'
PERSONAL_ACCESS_TOKEN = 'PAT-MARKER'
SUBJECT_TOKEN = 'SUBJECT-TOKEN-MARKER'
SECRETS = (CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, PERSONAL_ACCESS_TOKEN, SUBJECT_TOKEN)


def _registry_service() -> Service:
    auth = {'clientId': CLIENT_ID, 'clientSecret': CLIENT_SECRET, 'resource': 'https://explorer.example.com/',
            'accessTokenUrl': 'https://passport.example.com/oauth/token'}
    return Service(
        id='data-connect-example',
        name='Example',
        type=ServiceType(group='org.ga4gh', artifact='data-connect', version='1.0.0'),
        url='https://explorer.example.com/data-connect/',
        authentication=[dict(auth, grantType=GRANT_TYPE_DEVICE_CODE),
                        dict(auth, grantType=GRANT_TYPE_TOKEN_EXCHANGE)],
    )


def _assert_no_secrets(model) -> str:
    rendered = f'{model!r}\n{model}'
    for secret in SECRETS:
        assert secret not in rendered
    return rendered


def test_service_endpoint_from_registry_hides_client_secret_but_keeps_client_id():
    endpoint = parse_ga4gh_service_info(_registry_service())

    rendered = _assert_no_secrets(endpoint)

    assert CLIENT_ID in rendered
    assert 'fallback_authentications' in rendered
    assert endpoint.authentication['client_secret'] == CLIENT_SECRET
    assert endpoint.model_dump()['fallback_authentications'][0]['client_secret'] == CLIENT_SECRET


def test_service_endpoint_with_legacy_nested_auth_hides_client_secret():
    endpoint = ServiceEndpoint(url='https://example.com/',
                               authentication={'oauth2': {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}})

    assert CLIENT_ID in _assert_no_secrets(endpoint)


def test_service_endpoint_without_secret_shows_none():
    endpoint = ServiceEndpoint(url='https://example.com/', authentication={'client_id': CLIENT_ID,
                                                                          'client_secret': None})

    assert "'client_secret': None" in repr(endpoint)


def test_registry_service_hides_client_secret():
    assert CLIENT_ID in _assert_no_secrets(_registry_service())


def test_oauth2_authentication_hides_secret_fields():
    auth_info = OAuth2Authentication(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                     personal_access_token=PERSONAL_ACCESS_TOKEN, subject_token=SUBJECT_TOKEN,
                                     grant_type=GRANT_TYPE_DEVICE_CODE, resource_url='https://example.com/')

    assert CLIENT_ID in _assert_no_secrets(auth_info)
    assert auth_info.model_dump()['client_secret'] == CLIENT_SECRET


def test_session_info_hides_tokens_and_handler_client_secret():
    session = SessionInfo(access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN, token_type='Bearer',
                          issued_at=0, valid_until=1,
                          handler=SessionInfoHandler(auth_info={'client_id': CLIENT_ID,
                                                                'client_secret': CLIENT_SECRET}))

    assert CLIENT_ID in _assert_no_secrets(session)
    assert session.model_dump()['access_token'] == ACCESS_TOKEN


def test_redact_secrets_leaves_input_unchanged():
    auth = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}

    redacted = redact_secrets([auth])

    assert redacted == [{'client_id': CLIENT_ID, 'client_secret': '***'}]
    assert auth['client_secret'] == CLIENT_SECRET
