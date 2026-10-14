"""Unit tests for the engine request models, create validation and secret redaction."""
import json

import pytest
from pydantic import ValidationError

from dnastack.client.workbench.ewes.engine_models import (
    ENGINE_ID_PATTERN, ENGINE_SECRET_FIELDS, SECRET_PLACEHOLDER, EngineParamPresetRequest, ExecutionEngineRequest,
    derive_engine_id, drop_placeholder_secrets, get_field, redact_engine_secrets,
    required_create_fields, url_problems, validate_engine_for_create, validate_engine_for_update,
)
from dnastack.client.workbench.ewes.models import ExecutionEngine
from tests.unit.client.workbench.ewes.engine_fixtures import (
    ALL_ENGINES, GCP_SERVICE_ACCOUNT, SECRET_VALUES, as_service_response, engine,
)


def _validate(data):
    return validate_engine_for_create(ExecutionEngineRequest(**data))


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_every_type_round_trips(key):
    body = ExecutionEngineRequest(**engine(key)).to_request_body()
    assert body == ALL_ENGINES[key]


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_every_type_is_valid_for_create(key):
    assert _validate(engine(key)) == []


def test_service_account_object_becomes_string():
    data = engine('gcp')
    data['engine_adapter_configuration']['auth_config']['service_account_json'] = GCP_SERVICE_ACCOUNT
    body = ExecutionEngineRequest(**data).to_request_body()
    sent = body['engine_adapter_configuration']['auth_config']['service_account_json']
    assert isinstance(sent, str)
    assert json.loads(sent) == GCP_SERVICE_ACCOUNT


def test_unknown_field_rejected():
    data = engine('gcp')
    data['engine_adapter_configuration']['serviceAccountJson'] = 'x'
    with pytest.raises(ValidationError):
        ExecutionEngineRequest(**data)


def test_oauth_config_requires_camel_case():
    data = engine('wes_oauth')
    oauth = data['engine_adapter_configuration']['oauth_config']
    oauth['client_secret'] = oauth.pop('clientSecret')
    with pytest.raises(ValidationError):
        ExecutionEngineRequest(**data)


def test_unknown_adapter_type_rejected():
    data = engine('gcp')
    data['engine_adapter_configuration']['type'] = 'NOT_A_TYPE'
    with pytest.raises(ValidationError):
        ExecutionEngineRequest(**data)


@pytest.mark.parametrize('key, path, message', [
    ('gcp', 'auth_config', 'engine_adapter_configuration.auth_config.service_account_json is required'),
    ('gcp', 'project_id', 'engine_adapter_configuration.project_id is required'),
    ('wes_oauth', 'oauth_config', 'engine_adapter_configuration.oauth_config.clientSecret is required'),
    ('wes_mtls', 'ssl_config', 'engine_adapter_configuration.ssl_config.client_key_and_certificate_chain is required'),
    ('azure', 'client_secret', 'engine_adapter_configuration.client_secret is required'),
    ('azure', 'storage_container_name', 'engine_adapter_configuration.storage_container_name is required'),
    ('aws', 'secret_access_key', 'engine_adapter_configuration.secret_access_key is required'),
    ('aws', 'role_arn', 'engine_adapter_configuration.role_arn is required'),
])
def test_missing_required_adapter_field(key, path, message):
    data = engine(key)
    del data['engine_adapter_configuration'][path]
    assert message in _validate(data)


def test_azure_scope_is_optional():
    data = engine('azure')
    del data['engine_adapter_configuration']['scope']
    assert _validate(data) == []


def test_wes_defaults_to_oauth_when_method_omitted():
    data = engine('wes_mtls')
    del data['engine_adapter_configuration']['authentication_method']
    problems = _validate(data)
    assert 'engine_adapter_configuration.oauth_config.clientId is required' in problems


@pytest.mark.parametrize('field', ['name', 'provider', 'region'])
def test_missing_core_field(field):
    data = engine('gcp')
    del data[field]
    assert f'{field} is required' in _validate(data)


def test_id_is_optional():
    data = engine('gcp')
    del data['id']
    assert _validate(data) == []


ID_PROBLEM = "id must start with a letter or digit, hold only letters, digits and '-', and be at least 3 characters"


@pytest.mark.parametrize('engine_id', ['has spaces', 'ab', '-ab', 'abc\n', 'a_b'])
def test_invalid_id(engine_id):
    data = engine('gcp')
    data['id'] = engine_id
    assert ID_PROBLEM in _validate(data)


@pytest.mark.parametrize('engine_id', ['abc', 'a-b-c', 'GIAB-demo-2', '9ab'])
def test_valid_id(engine_id):
    assert ENGINE_ID_PATTERN.fullmatch(engine_id)


@pytest.mark.parametrize('name, expected', [
    ('GIAB Demo', 'giab-demo'),
    ('  GIAB  Demo  ', 'giab-demo'),
    ('giab_demo (v2)!', 'giab-demo-v2'),
    ('--x--y--', 'x-y'),
    ('Ünïcode name', 'n-code-name'),
    ('A1', 'a1'),
])
def test_derive_engine_id_matches_the_ui(name, expected):
    # Expected values worked out by hand from the UI's convertNameToId regexes.
    assert derive_engine_id(name) == expected


@pytest.mark.parametrize('url, allowed', [
    ('https://cromwell.example.com', True),
    ('https://cromwell.example.com:8443/api', True),
    ('http://localhost:8080', True),
    ('http://127.0.0.1', True),
    ('http://cromwell.example.com', False),
    ('http://localhost.evil.com', False),
    ('ftp://cromwell.example.com', False),
    ('https://', False),
    ('cromwell.example.com', False),
    ('https://[bad', False),
    ('http://localhost:notaport', True),
])
def test_url_rule(url, allowed):
    problems = url_problems({'type': 'WES_ON_CROMWELL', 'url': url})
    assert (problems == []) is allowed


def test_url_rule_applies_on_create():
    data = engine('azure')
    data['engine_adapter_configuration']['url'] = 'http://cromwell.example.com'
    assert ('engine_adapter_configuration.url must use https:// (http:// is only allowed for localhost)'
            in _validate(data))


def test_wes_oauth_requires_scope():
    data = engine('wes_oauth')
    del data['engine_adapter_configuration']['oauth_config']['scope']
    assert 'engine_adapter_configuration.oauth_config.scope is required' in _validate(data)


def test_wes_oauth_with_ssl_config_requires_server_certificate():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['ssl_config'] = {}
    assert ('engine_adapter_configuration.ssl_config.server_certificate_chain is required'
            in _validate(data))


def test_wes_oauth_rejects_mtls_client_key():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['ssl_config'] = {
        'server_certificate_chain': 'CERT', 'client_key_and_certificate_chain': 'SECRET-MTLS'}
    assert ('engine_adapter_configuration.ssl_config.client_key_and_certificate_chain is only used with MTLS '
            'authentication; remove it' in _validate(data))


def test_wes_mtls_rejects_oauth_config():
    data = engine('wes_mtls')
    data['engine_adapter_configuration']['oauth_config'] = {'clientId': 'x', 'clientSecret': 'SECRET-OAUTH'}
    assert ('engine_adapter_configuration.oauth_config is only used with OAUTH authentication; remove it'
            in _validate(data))


def test_placeholder_secret_rejected_on_create():
    data = engine('azure')
    data['engine_adapter_configuration']['client_secret'] = SECRET_PLACEHOLDER
    assert ("engine_adapter_configuration.client_secret must be the real secret, not the '***' placeholder"
            in _validate(data))


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_redaction_hides_every_secret(key):
    redacted = redact_engine_secrets(as_service_response(engine(key)))
    rendered = json.dumps(redacted)
    for secret in SECRET_VALUES:
        assert secret not in rendered
    assert SECRET_PLACEHOLDER in rendered


def test_redaction_does_not_mutate_input_or_add_fields():
    original = engine('aws')
    del original['engine_adapter_configuration']['secret_access_key']
    snapshot = json.dumps(original, sort_keys=True)
    redacted = redact_engine_secrets(original)
    assert json.dumps(original, sort_keys=True) == snapshot
    assert 'secret_access_key' not in redacted['engine_adapter_configuration']


def test_redaction_tolerates_missing_adapter_configuration():
    assert redact_engine_secrets({'id': 'x'}) == {'id': 'x'}


def test_drop_placeholder_secrets():
    data = redact_engine_secrets(engine('wes_oauth'))
    cleaned = drop_placeholder_secrets(data)
    assert get_field(cleaned['engine_adapter_configuration'], 'oauth_config.clientSecret') is None
    assert get_field(cleaned['engine_adapter_configuration'], 'oauth_config.clientId') == 'wes-client'
    ExecutionEngineRequest(**cleaned)  # still parses


def test_secret_field_list_covers_fixtures():
    for key, data in ALL_ENGINES.items():
        adapter = data['engine_adapter_configuration']
        assert any(get_field(adapter, path) for path in ENGINE_SECRET_FIELDS), key


def test_execution_engine_keeps_version():
    parsed = ExecutionEngine(**as_service_response(engine('gcp')))
    assert parsed.version == 'v-1'


def test_preset_request_body():
    body = EngineParamPresetRequest(name='p', preset_values={'a': 1}).to_request_body()
    assert body == {'name': 'p', 'default': False, 'preset_values': {'a': 1}}


def test_region_for_a_provider_is_left_to_the_service():
    data = engine('aws')
    data['provider'] = 'GCP'
    data['region'] = 'nowhere'
    assert validate_engine_for_create(ExecutionEngineRequest(**data)) == []


def _stored(key, **changes):
    data = as_service_response(engine(key))
    data.update(changes)
    return ExecutionEngine(**data)


def test_update_with_unchanged_legacy_values_is_valid():
    stored = _stored('wes_oauth', region='retired-region')
    stored.engine_adapter_configuration['url'] = 'http://legacy.example.com'
    data = engine('wes_oauth')
    data['region'] = 'retired-region'
    data['engine_adapter_configuration']['url'] = 'http://legacy.example.com'
    request = ExecutionEngineRequest(**data)
    assert validate_engine_for_update(request, stored) == []


def test_update_leaves_a_changed_region_to_the_service():
    request = ExecutionEngineRequest(region='eu-north-9', engine_adapter_configuration={'type': 'AWS_HEALTH_OMICS'})
    assert validate_engine_for_update(request, _stored('aws')) == []


def test_update_checks_a_changed_url():
    data = {'engine_adapter_configuration': {'type': 'AZURE_CONTAINER_APP_CROMWELL', 'url': 'http://x.example.com'}}
    assert validate_engine_for_update(ExecutionEngineRequest(**data), _stored('azure')) == [
        'engine_adapter_configuration.url must use https:// (http:// is only allowed for localhost)']


@pytest.mark.parametrize('adapter_type, method, expected', [
    ('AWS_HEALTH_OMICS', None, ['access_key_id', 'secret_access_key', 'output_bucket', 'role_arn']),
    ('WES_ON_CROMWELL', None, ['url', 'oauth_config.clientId', 'oauth_config.clientSecret',
                               'oauth_config.tokenUri', 'oauth_config.resource', 'oauth_config.scope']),
    ('WES_ON_CROMWELL', 'MTLS', ['url', 'ssl_config.client_key_and_certificate_chain']),
    ('AWS_HEALTH_OMICS', 'MTLS', ['access_key_id', 'secret_access_key', 'output_bucket', 'role_arn']),
])
def test_required_create_fields(adapter_type, method, expected):
    assert required_create_fields(adapter_type, method) == (
        ['name', 'provider', 'region'] + [f'engine_adapter_configuration.{path}' for path in expected])


def test_create_validation_reports_each_required_field_by_its_full_path():
    data = {'engine_adapter_configuration': {'type': 'WES_ON_CROMWELL', 'authentication_method': 'MTLS'}}
    problems = validate_engine_for_create(ExecutionEngineRequest(**data))
    assert problems == [f'{path} is required' for path in required_create_fields('WES_ON_CROMWELL', 'MTLS')]
