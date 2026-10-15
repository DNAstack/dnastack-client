"""Unit tests for masking an engine request's secrets in service text."""
import json

import pytest
import requests

from dnastack.cli.commands.workbench.engines.secret_redaction import (
    redact_text, redacted_http_error, request_secret_values,
)
from dnastack.client.workbench.ewes.engine_models import ExecutionEngineRequest
from dnastack.http.session import ClientError, ServerError
from tests.unit.client.workbench.ewes.engine_fixtures import GCP_SERVICE_ACCOUNT, engine


def _gcp_request(key):
    data = engine('gcp')
    data['engine_adapter_configuration']['auth_config']['service_account_json'] = key
    return ExecutionEngineRequest(**data)


def test_service_account_key_parts_are_secrets_too():
    key = {**GCP_SERVICE_ACCOUNT, 'private_key_id': 'SECRET-KEY-ID'}
    secrets = request_secret_values(_gcp_request(key))
    assert 'SECRET-GCP-KEY' in secrets
    assert 'SECRET-KEY-ID' in secrets
    assert json.dumps(key, separators=(',', ':')) in secrets
    assert secrets == sorted(secrets, key=len, reverse=True)


def test_empty_and_missing_values_are_skipped():
    key = {**GCP_SERVICE_ACCOUNT, 'private_key': '', 'private_key_id': None}
    assert request_secret_values(_gcp_request(key)) == [json.dumps(key, separators=(',', ':'))]
    no_secrets = ExecutionEngineRequest(engine_adapter_configuration={'type': 'AWS_HEALTH_OMICS'})
    assert request_secret_values(no_secrets) == []


def test_secret_is_masked_raw_and_json_escaped():
    pem = '-----BEGIN PRIVATE KEY-----\nSECRET\n-----END PRIVATE KEY-----\n'
    text = f'raw {pem} escaped {json.dumps(pem)}'
    assert redact_text(text, [pem]) == 'raw *** escaped "***"'


def _response(status, text):
    response = requests.Response()
    response.status_code = status
    response._content = text.encode('utf-8')
    response.encoding = 'utf-8'
    return response


def test_redacted_http_error_keeps_the_type_and_status():
    for error_type, status in [(ClientError, 409), (ServerError, 503)]:
        redacted = redacted_http_error(error_type(_response(status, 'echo SECRET-Z')), ['SECRET-Z'])
        assert type(redacted) is error_type
        assert str(redacted) == f'HTTP {status}: echo ***'


def test_password_in_the_url_is_a_secret():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['url'] = 'https://user:SECRET-URL@wes.example.com'
    assert 'SECRET-URL' in request_secret_values(ExecutionEngineRequest(**data))


def test_url_without_a_password_adds_no_secret():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['url'] = 'https://user@wes.example.com'
    assert 'user' not in request_secret_values(ExecutionEngineRequest(**data))


@pytest.mark.parametrize('stripped', ['\t', '\n', '\r'])
def test_password_in_the_url_is_a_secret_as_written_when_urlsplit_strips_characters(stripped):
    raw = f'SECRET-URL{stripped}X'
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['url'] = f'https://user:{raw}@wes.example.com'
    assert raw in request_secret_values(ExecutionEngineRequest(**data))
