"""Unit tests for the engine create, update, get-default, set-default, delete, list and describe commands."""
import json
import re
from contextlib import ExitStack
from unittest.mock import Mock, patch

import click
import pytest
import requests
from click.testing import CliRunner

from dnastack.cli.commands.workbench.engines import engines_command_group
from dnastack.cli.commands.workbench.engines.engine_kinds import ENGINE_KINDS, KINDS_BY_NAME
from dnastack.client.workbench.ewes.engine_models import ENGINE_SECRET_FIELDS, get_field
from dnastack.client.workbench.ewes.models import ExecutionEngine
from dnastack.http.session import ClientError, ServerError
from tests.unit.client.workbench.ewes.engine_fixtures import (
    ALL_ENGINES, GCP_SERVICE_ACCOUNT, SECRET_VALUES, as_service_response, engine,
)

KIND = {'gcp': 'gcp', 'wes_oauth': 'wes', 'wes_mtls': 'wes', 'azure': 'azure', 'aws': 'aws'}
_ENGINE_MODULES = ('commands', 'create', 'update')


def _patched(client):
    stack = ExitStack()
    for module in _ENGINE_MODULES:
        stack.enter_context(patch(f'dnastack.cli.commands.workbench.engines.{module}.get_ewes_client',
                                  return_value=client))
    return stack


def _not_found():
    return ClientError(Mock(status_code=404, text='not found'))


def _client(existing=None):
    """A mock EWesClient. `existing` is the engine dict get_engine returns, or None for a 404."""
    client = Mock()
    client.namespace = 'demo-ns'
    client.list_engines.return_value = iter([])
    if existing is None:
        client.get_engine.side_effect = _not_found()
    else:
        client.get_engine.return_value = ExecutionEngine(**as_service_response(existing))
    # Echo every secret back, to prove the CLI redacts what the service might return.
    client.create_engine.side_effect = lambda engine: ExecutionEngine(**as_service_response(engine.to_request_body()))
    client.update_engine.side_effect = (
        lambda engine_id, engine, if_match: ExecutionEngine(
            **as_service_response({**(existing or {}), **engine.to_request_body()})))
    client.patch_engine.side_effect = (
        lambda engine_id, patches, if_match: ExecutionEngine(**as_service_response(existing)))
    return client


def _invoke(args):
    return CliRunner(mix_stderr=False).invoke(engines_command_group, args)


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return f'@{path}'


def _assert_no_secrets(result):
    for secret in SECRET_VALUES:
        assert secret not in result.stdout
        assert secret not in result.stderr


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_create_from_single_file_for_every_type(tmp_path, key):
    client = _client()
    with _patched(client):
        result = _invoke(['create', KIND[key], '--config', _write(tmp_path, 'e.json', engine(key))])
    assert result.exit_code == 0, result.stderr
    # "default" in --config is never sent; only set-default makes an engine the default.
    expected = {field: value for field, value in ALL_ENGINES[key].items() if field != 'default'}
    assert client.create_engine.call_args.args[0].to_request_body() == expected
    _assert_no_secrets(result)
    assert json.loads(result.stdout)['id'] == ALL_ENGINES[key]['id']


def test_create_with_service_account_object_in_file(tmp_path):
    data = engine('gcp')
    data['engine_adapter_configuration']['auth_config']['service_account_json'] = GCP_SERVICE_ACCOUNT
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    sent = client.create_engine.call_args.args[0].to_request_body()
    service_account_json = sent['engine_adapter_configuration']['auth_config']['service_account_json']
    assert json.loads(service_account_json) == GCP_SERVICE_ACCOUNT


def test_create_inline_json():
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'aws', '--config', json.dumps(engine('aws'))])
    assert result.exit_code == 0, result.stderr


def test_create_with_service_account_flag(tmp_path):
    data = engine('gcp')
    del data['engine_adapter_configuration']['auth_config']
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data),
                          '--service-account-json', _write(tmp_path, 'sa.json', GCP_SERVICE_ACCOUNT)])
    assert result.exit_code == 0, result.stderr
    _assert_no_secrets(result)


def test_create_existing_engine_fails_without_posting(tmp_path):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 1
    assert "Engine 'hifi-solves-cromwell' already exists in namespace 'demo-ns'" in result.stderr
    assert "Use 'omics workbench engines update gcp hifi-solves-cromwell' to change it." in result.stderr
    client.create_engine.assert_not_called()


def test_create_lookup_error_other_than_404_propagates(tmp_path):
    client = _client()
    client.get_engine.side_effect = ClientError(Mock(status_code=403, text='forbidden'))
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 1
    assert 'already exists' not in result.stderr
    client.create_engine.assert_not_called()


def test_create_invalid_field_does_not_echo_secret(tmp_path):
    data = engine('azure')
    data['engine_adapter_configuration']['client_secret'] = {'nested': 'SECRET-AZURE'}
    with _patched(_client()):
        result = _invoke(['create', 'azure', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 1
    _assert_no_secrets(result)


def test_update_sends_version_and_strips_server_fields(tmp_path):
    client = _client(existing=engine('gcp'))
    edited = as_service_response(engine('gcp'))
    edited['name'] = 'Renamed'
    del edited['engine_adapter_configuration']['auth_config']
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config', _write(tmp_path, 'e.json', edited)])
    assert result.exit_code == 0, result.stderr
    call = client.update_engine.call_args.kwargs
    assert call['engine_id'] == 'hifi-solves-cromwell'
    assert call['if_match'] == 'v-1'
    body = call['engine'].to_request_body()
    assert body['name'] == 'Renamed'
    assert 'version' not in body and 'state' not in body
    assert 'auth_config' not in body['engine_adapter_configuration']
    _assert_no_secrets(result)


def test_update_accepts_describe_output(tmp_path):
    client = _client(existing=engine('gcp'))
    path = _write(tmp_path, 'e.json', [as_service_response(engine('gcp'))])
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config', path])
    assert result.exit_code == 0, result.stderr
    assert client.update_engine.call_args.kwargs['if_match'] == 'v-1'


def test_update_uses_argument_id_when_file_has_none(tmp_path):
    client = _client(existing=engine('gcp'))
    data = engine('gcp')
    del data['id']
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    assert client.update_engine.call_args.kwargs['engine'].id == 'hifi-solves-cromwell'


def test_update_rejects_id_mismatch(tmp_path):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['update', 'gcp', 'other-id', '--config', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 1
    assert "does not match" in result.stderr
    client.update_engine.assert_not_called()


def test_update_drops_placeholder_secret(tmp_path):
    client = _client(existing=engine('azure'))
    data = engine('azure')
    data['engine_adapter_configuration']['client_secret'] = '***'
    with _patched(client):
        result = _invoke(['update', 'azure', 'azure-cromwell', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert 'client_secret' not in body['engine_adapter_configuration']
    _assert_no_secrets(result)


def test_update_keeps_wes_authentication_method(tmp_path):
    client = _client(existing=engine('wes_mtls'))
    data = engine('wes_mtls')
    del data['engine_adapter_configuration']['authentication_method']
    del data['engine_adapter_configuration']['ssl_config']
    with _patched(client):
        result = _invoke(['update', 'wes', 'wes-mtls', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert body['engine_adapter_configuration']['authentication_method'] == 'MTLS'


def test_set_default(tmp_path):
    client = _client(existing=engine('azure'))
    with _patched(client):
        result = _invoke(['set-default', 'azure-cromwell'])
    assert result.exit_code == 0, result.stderr
    call = client.patch_engine.call_args.kwargs
    assert call['engine_id'] == 'azure-cromwell'
    assert call['if_match'] == 'v-1'
    assert [p.model_dump(exclude_none=True) for p in call['patches']] == [
        {'op': 'replace', 'path': '/default', 'value': True}]
    _assert_no_secrets(result)


def _listed(*keys):
    return iter([ExecutionEngine(**as_service_response(engine(key))) for key in keys])


def test_get_default_prints_the_default_engine_redacted():
    client = _client()
    client.list_engines.return_value = _listed('gcp')  # the gcp fixture is the default engine
    with _patched(client):
        result = _invoke(['get-default'])
    assert result.exit_code == 0, result.stderr
    printed = json.loads(result.stdout)
    assert isinstance(printed, dict)
    assert (printed['id'], printed['default']) == ('hifi-solves-cromwell', True)
    assert printed['engine_adapter_configuration']['auth_config']['service_account_json'] == '***'
    _assert_no_secrets(result)


def test_get_default_finds_a_default_listed_after_others():
    # The default is the second engine listed, as when it is on the second page.
    client = _client()
    client.list_engines.return_value = _listed('aws', 'gcp')
    with _patched(client):
        result = _invoke(['get-default', '--id'])
    assert result.exit_code == 0, result.stderr
    assert result.stdout == 'hifi-solves-cromwell\n'
    assert client.list_engines.call_args.kwargs.get('max_results') is None
    assert len(client.list_engines.call_args.args) == 1


def test_get_default_without_a_default_engine_fails():
    client = _client()
    with _patched(client):
        result = _invoke(['get-default'])
    assert result.exit_code == 1
    assert "Namespace 'demo-ns' has no default engine." in result.stderr
    assert result.stdout == ''


def test_get_default_help():
    flat = ' '.join(_help_of(['get-default']).split())
    assert "Get the namespace's default engine" in flat
    assert 'Only output the engine id' in flat
    assert '--namespace' in flat and '--context' in flat and '--endpoint-id' in flat


def test_delete_prompts_and_aborts_on_no():
    client = _client(existing=engine('azure'))
    with _patched(client):
        result = CliRunner(mix_stderr=False).invoke(engines_command_group, ['delete', 'azure-cromwell'],
                                                    input='n\n')
    assert result.exit_code == 0
    client.delete_engine.assert_not_called()


def test_delete_confirmed():
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = CliRunner(mix_stderr=False).invoke(engines_command_group, ['delete', 'hifi-solves-cromwell'],
                                                    input='y\n')
    assert result.exit_code == 0, result.stderr
    client.delete_engine.assert_called_once_with(engine_id='hifi-solves-cromwell')


def test_delete_force_skips_prompt():
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['delete', 'hifi-solves-cromwell', '--force'])
    assert result.exit_code == 0, result.stderr
    client.delete_engine.assert_called_once_with(engine_id='hifi-solves-cromwell')


def test_describe_redacts_secrets():
    client = _client(existing=engine('aws'))
    with _patched(client):
        result = _invoke(['describe', 'aws-omics'])
    assert result.exit_code == 0, result.stderr
    _assert_no_secrets(result)
    assert json.loads(result.stdout)[0]['engine_adapter_configuration']['secret_access_key'] == '***'


def test_list_redacts_secrets():
    client = _client()
    client.list_engines.return_value = iter(
        [ExecutionEngine(**as_service_response(engine(key))) for key in sorted(ALL_ENGINES)])
    with _patched(client):
        result = _invoke(['list'])
    assert result.exit_code == 0, result.stderr
    _assert_no_secrets(result)


def test_delete_default_engine_with_others_is_refused():
    client = _client(existing=engine('gcp'))  # the gcp fixture is the default engine
    client.list_engines.return_value = iter([ExecutionEngine(**as_service_response(engine('gcp'))),
                                             ExecutionEngine(**as_service_response(engine('azure')))])
    with _patched(client):
        result = _invoke(['delete', 'hifi-solves-cromwell', '--force'])
    assert result.exit_code == 1
    assert "Engine 'hifi-solves-cromwell' is the default engine of namespace 'demo-ns'" in result.stderr
    assert 'omics workbench engines set-default' in result.stderr
    client.delete_engine.assert_not_called()


def test_delete_only_engine_even_if_default():
    client = _client(existing=engine('gcp'))
    client.list_engines.return_value = iter([ExecutionEngine(**as_service_response(engine('gcp')))])
    with _patched(client):
        result = _invoke(['delete', 'hifi-solves-cromwell', '--force'])
    assert result.exit_code == 0, result.stderr
    client.delete_engine.assert_called_once_with(engine_id='hifi-solves-cromwell')


def test_create_derives_id_from_name(tmp_path):
    data = engine('gcp')
    del data['id']
    data['name'] = 'GIAB Demo'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    client.get_engine.assert_called_once_with(engine_id='giab-demo')
    assert client.create_engine.call_args.args[0].id == 'giab-demo'


def test_create_rerun_without_id_finds_existing_engine(tmp_path):
    data = engine('gcp')
    del data['id']
    data['name'] = 'GIAB Demo'
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 1
    assert "Engine 'giab-demo' already exists" in result.stderr
    client.create_engine.assert_not_called()


def test_create_name_too_short_for_id(tmp_path):
    data = engine('gcp')
    del data['id']
    data['name'] = 'A1'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 1
    assert 'Cannot derive an engine id' in result.stderr
    client.create_engine.assert_not_called()


def test_create_reads_engine_from_stdin():
    client = _client()
    with _patched(client):
        result = CliRunner(mix_stderr=False).invoke(engines_command_group, ['create', 'azure', '--config', '-'],
                                                    input=json.dumps(engine('azure')))
    assert result.exit_code == 0, result.stderr
    assert client.create_engine.call_args.args[0].to_request_body() == ALL_ENGINES['azure']
    _assert_no_secrets(result)


def _health_check_error():
    response = Mock(status_code=400, text='raw')
    response.json.return_value = {'msg': 'Initial engine health check failed.', 'trace_id': 't-1', 'errors': [
        {'checks': [{'type': 'CREDENTIALS', 'outcome': 'FAILURE', 'error': 'denied'}]}]}
    return ClientError(response)


def test_create_health_check_failure_is_readable(tmp_path):
    client = _client()
    client.create_engine.side_effect = _health_check_error()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 1
    stderr = click.unstyle(result.stderr)
    assert "Engine 'hifi-solves-cromwell' failed its health check and was not created." in stderr
    assert '✗ FAILURE  CREDENTIALS  denied' in stderr
    assert 'raw' not in stderr


def test_create_other_client_error_is_shown_as_before(tmp_path):
    client = _client()
    client.create_engine.side_effect = ClientError(Mock(status_code=400, text='Engine ID must be unique.',
                                                        json=Mock(return_value={'msg': 'Engine ID must be unique.'})))
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 1
    assert 'Engine ID must be unique.' in result.stderr


def test_update_refuses_a_stale_file(tmp_path):
    client = _client(existing=engine('gcp'))  # stored version is v-1
    stale = as_service_response(engine('gcp'))
    stale['version'] = 'v-0'
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config', _write(tmp_path, 'e.json', stale)])
    assert result.exit_code == 1
    assert "Engine 'hifi-solves-cromwell' has changed since that --config was written" in result.stderr
    client.update_engine.assert_not_called()


def test_update_without_version_uses_stored_version(tmp_path):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config',
                          _write(tmp_path, 'e.json', {'name': 'New'})])
    assert result.exit_code == 0, result.stderr
    call = client.update_engine.call_args.kwargs
    assert call['if_match'] == 'v-1'
    assert call['engine'].to_request_body() == {
        'id': 'hifi-solves-cromwell', 'name': 'New', 'engine_adapter_configuration': {'type': 'GCP_CLOUD_RUN_CROMWELL'}}


def test_update_fills_type_into_a_partial_adapter(tmp_path):
    client = _client(existing=engine('aws'))
    data = {'engine_adapter_configuration': {'role_arn': 'arn:aws:iam::123456789012:role/new'}}
    with _patched(client):
        result = _invoke(['update', 'aws', 'aws-omics', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 0, result.stderr
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert body['engine_adapter_configuration'] == {
        'type': 'AWS_HEALTH_OMICS', 'role_arn': 'arn:aws:iam::123456789012:role/new'}


def test_update_refuses_a_type_change(tmp_path):
    client = _client(existing=engine('aws'))
    azure_file = _write(tmp_path, 'e.json', engine('azure') | {'id': 'aws-omics'})
    with _patched(client):
        result = _invoke(['update', 'aws', 'aws-omics', '--config', azure_file])
    assert result.exit_code == 2
    assert ("Error: Invalid value for '--config': describes an azure engine; use "
            "'omics workbench engines update azure ...'.") in result.stderr
    client.update_engine.assert_not_called()


def test_update_keeps_legacy_values_it_does_not_change(tmp_path):
    legacy = engine('wes_oauth')
    legacy['region'] = 'retired-region'
    client = _client(existing=legacy)
    edited = as_service_response(legacy)
    edited['name'] = 'Renamed'
    with _patched(client):
        result = _invoke(['update', 'wes', 'wes-oauth', '--config', _write(tmp_path, 'e.json', edited)])
    assert result.exit_code == 0, result.stderr


def test_update_health_check_failure_is_readable(tmp_path):
    client = _client(existing=engine('gcp'))
    client.update_engine.side_effect = _health_check_error()
    with _patched(client):
        result = _invoke(['update', 'gcp', 'hifi-solves-cromwell', '--config',
                          _write(tmp_path, 'e.json', {'name': 'New'})])
    assert result.exit_code == 1
    assert "failed its health check and was not updated." in click.unstyle(result.stderr)


def test_create_shows_the_services_region_error(tmp_path):
    client = _client()
    body = {'message': 'region is unknown.'}
    client.create_engine.side_effect = ClientError(Mock(status_code=400, text=json.dumps(body),
                                                        json=Mock(return_value=body)))
    data = engine('gcp')
    data['region'] = 'mars-north1'
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 1
    assert 'region is unknown.' in result.stderr


OPTIONS_BY_KIND = {
    'gcp': ['--name', 'GCP Engine', '--region', 'us-central1', '--url', 'https://cromwell.example.com',
            '--project-id', 'demo-project', '--service-account-json', None],
    'wes': ['--name', 'WES Engine', '--region', 'local', '--provider', 'LOCAL', '--url', 'https://wes.example.com',
            '--client-id', 'wes-client', '--token-uri', 'https://auth.example.com/token',
            '--resource', 'https://wes.example.com', '--scope', 'openid', '--client-secret', 'SECRET-OAUTH'],
    'azure': ['--name', 'Azure Engine', '--region', 'eastus', '--url', 'https://cromwell.azure.example.com',
              '--tenant-id', 'tenant', '--client-id', 'azure-client', '--client-secret', 'SECRET-AZURE',
              '--storage-account-name', 'account', '--storage-container-name', 'container'],
    'aws': ['--name', 'AWS Engine', '--region', 'us-east-1', '--access-key-id', 'AKIAEXAMPLE',
            '--secret-access-key', 'SECRET-AWS', '--output-bucket', 's3://omics-output',
            '--role-arn', 'arn:aws:iam::123456789012:role/omics'],
}


@pytest.mark.parametrize('kind', sorted(OPTIONS_BY_KIND))
def test_create_from_options_for_every_type(tmp_path, kind):
    args = list(OPTIONS_BY_KIND[kind])
    if None in args:
        args[args.index(None)] = _write(tmp_path, 'sa.json', GCP_SERVICE_ACCOUNT)
    client = _client()
    with _patched(client):
        result = _invoke(['create', kind, *args])
    assert result.exit_code == 0, result.stderr
    body = client.create_engine.call_args.args[0].to_request_body()
    assert body['engine_adapter_configuration']['type'] == KINDS_BY_NAME[kind].adapter_type.value
    _assert_no_secrets(result)


def test_create_options_override_file(tmp_path):
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', engine('gcp')),
                          '--project-id', 'other-project'])
    assert result.exit_code == 0, result.stderr
    body = client.create_engine.call_args.args[0].to_request_body()
    assert body['engine_adapter_configuration']['project_id'] == 'other-project'


def test_create_with_nothing_names_every_missing_option():
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'aws'])
    assert result.exit_code == 2
    assert 'Usage: ' in result.stderr
    assert ("Error: Missing options '--name', '--region', '--access-key-id', '--secret-access-key', "
            "'--output-bucket', '--role-arn'.") in result.stderr
    client.get_engine.assert_not_called()
    client.create_engine.assert_not_called()


def test_create_with_one_missing_option_uses_the_singular():
    args = OPTIONS_BY_KIND['aws']
    without_role = args[:args.index('--role-arn')]
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'aws', *without_role])
    assert result.exit_code == 2
    assert "Error: Missing option '--role-arn'." in result.stderr
    client.get_engine.assert_not_called()
    client.create_engine.assert_not_called()


def test_create_does_not_report_fields_given_in_file(tmp_path):
    data = {'name': 'AWS Engine', 'engine_adapter_configuration': {
        'type': 'AWS_HEALTH_OMICS', 'access_key_id': 'AKIAEXAMPLE', 'secret_access_key': 'SECRET-AWS'}}
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'aws', '--config', _write(tmp_path, 'e.json', data), '--region', 'us-east-1'])
    assert result.exit_code == 2
    assert "Error: Missing options '--output-bucket', '--role-arn'." in result.stderr
    _assert_no_secrets(result)
    client.create_engine.assert_not_called()


def test_create_problem_names_the_option():
    args = list(OPTIONS_BY_KIND['wes'])
    args[args.index('--url') + 1] = 'http://example.com'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', *args])
    assert result.exit_code == 1
    assert '  - --url must use https://' in result.stderr
    assert 'engine_adapter_configuration.url' not in result.stderr
    client.create_engine.assert_not_called()


def test_create_problem_on_a_field_without_an_option_keeps_its_path(tmp_path):
    pem = '-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----\n'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', '--name', 'WES Engine', '--region', 'local', '--provider', 'local',
                          '--url', 'https://wes.example.com', '--authentication-method', 'mtls', '--client-id', 'cid',
                          '--client-key-and-certificate-chain', _write(tmp_path, 'key.pem', pem)])
    assert result.exit_code == 1
    assert ('  - engine_adapter_configuration.oauth_config is only used with OAUTH authentication; remove it'
            in result.stderr)
    client.create_engine.assert_not_called()


def test_create_with_an_unreadable_file_is_a_bad_parameter(tmp_path):
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', f'@{tmp_path}/missing.json'])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--config': cannot read" in result.stderr
    client.get_engine.assert_not_called()


def test_create_with_server_certificate_chain_inline_is_a_bad_parameter():
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', *OPTIONS_BY_KIND['wes'],
                          '--server-certificate-chain', '-----BEGIN CERTIFICATE-----'])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--server-certificate-chain'" in result.stderr
    assert 'pass @path' in result.stderr
    client.create_engine.assert_not_called()


def test_create_with_server_certificate_chain_from_file(tmp_path):
    pem = '-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----\n'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', *OPTIONS_BY_KIND['wes'],
                          '--server-certificate-chain', _write(tmp_path, 'server.pem', pem)])
    assert result.exit_code == 0, result.stderr
    adapter = client.create_engine.call_args.args[0].to_request_body()['engine_adapter_configuration']
    assert adapter['ssl_config']['server_certificate_chain'] == pem


def test_update_sends_only_passed_fields():
    client = _client(existing=engine('aws'))
    engine_id = engine('aws')['id']
    with _patched(client):
        result = _invoke(['update', 'aws', engine_id, '--role-arn', 'arn:aws:iam::123456789012:role/new'])
    assert result.exit_code == 0, result.stderr
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert body == {'id': engine_id, 'engine_adapter_configuration': {
        'type': 'AWS_HEALTH_OMICS', 'role_arn': 'arn:aws:iam::123456789012:role/new'}}


def test_update_secret_from_option_is_not_printed():
    client = _client(existing=engine('azure'))
    with _patched(client):
        result = _invoke(['update', 'azure', engine('azure')['id'], '--client-secret', 'SECRET-AZURE'])
    assert result.exit_code == 0, result.stderr
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert body['engine_adapter_configuration']['client_secret'] == 'SECRET-AZURE'
    _assert_no_secrets(result)


def test_update_with_nothing_to_change():
    client = _client(existing=engine('aws'))
    with _patched(client):
        result = _invoke(['update', 'aws', engine('aws')['id']])
    assert result.exit_code == 2
    assert 'Usage:' in result.stderr
    assert 'Error: Nothing to update: pass --config or at least one option.' in result.stderr
    client.get_engine.assert_not_called()


def test_update_wes_mtls_secret_option_uses_stored_method(tmp_path):
    client = _client(existing=engine('wes_mtls'))
    pem = '-----BEGIN PRIVATE KEY-----\nNEW\n-----END PRIVATE KEY-----\n'
    with _patched(client):
        result = _invoke(['update', 'wes', engine('wes_mtls')['id'], '--client-key-and-certificate-chain',
                          _write(tmp_path, 'key.pem', pem)])
    assert result.exit_code == 0, result.stderr
    adapter = client.update_engine.call_args.kwargs['engine'].to_request_body()['engine_adapter_configuration']
    assert adapter['authentication_method'] == 'MTLS'
    assert adapter['ssl_config']['client_key_and_certificate_chain'] == pem


def test_old_file_only_forms_are_gone(tmp_path):
    path = _write(tmp_path, 'e.json', engine('gcp'))
    with _patched(_client()):
        for args, message in ((['create', '--file', path], 'No such option: --file'),
                              (['update', 'some-id', '--file', path], 'No such command')):
            result = _invoke(args)
            assert result.exit_code == 2
            assert message in result.stdout + result.stderr


@pytest.mark.parametrize('verb, args', [('create', ['gcp']), ('update', ['gcp', 'hifi-solves-cromwell'])])
def test_file_option_is_now_config(tmp_path, verb, args):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke([verb, *args, '--file', _write(tmp_path, 'e.json', engine('gcp'))])
    assert result.exit_code == 2
    assert 'No such option: --file' in result.stderr
    client.get_engine.assert_not_called()


@pytest.mark.parametrize('file', ['{}', '{"id": "x", "version": "v"}', '{"id": "x", "state": "READY"}'])
def test_update_with_a_file_of_nothing_to_change_and_no_options(file):
    client = _client(existing=engine('aws'))
    with _patched(client):
        result = _invoke(['update', 'aws', engine('aws')['id'], '--config', file])
    assert result.exit_code == 2
    assert 'Usage:' in result.stderr
    assert 'Error: Nothing to update: pass --config or at least one option.' in result.stderr
    client.get_engine.assert_not_called()
    client.update_engine.assert_not_called()


@pytest.mark.parametrize('group, verb', [('create', 'Create'), ('update', 'Update')])
def test_group_help_shows_full_summaries(group, verb):
    output = click.unstyle(_invoke([group, '--help']).stdout)
    for kind in ENGINE_KINDS:
        assert f'{verb} {kind.summary}' in output
    commands = output.split('Commands:')[1].split('Examples:')[0]
    assert not [line for line in commands.splitlines() if line.rstrip().endswith('...')]


@pytest.mark.parametrize('provider', ['GCP', 'gcp', 'Gcp'])
def test_provider_accepts_any_case_and_sends_upper_case(provider):
    args = list(OPTIONS_BY_KIND['wes'])
    args[args.index('--provider') + 1] = provider
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', *args])
    assert result.exit_code == 0, result.stderr
    assert client.create_engine.call_args.args[0].to_request_body()['provider'] == 'GCP'


def test_auth_method_accepts_upper_case(tmp_path):
    pem = '-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----\n'
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'wes', '--name', 'WES Engine', '--region', 'local', '--provider', 'local',
                          '--url', 'https://wes.example.com', '--authentication-method', 'MTLS',
                          '--client-key-and-certificate-chain', _write(tmp_path, 'key.pem', pem)])
    assert result.exit_code == 0, result.stderr
    adapter = client.create_engine.call_args.args[0].to_request_body()['engine_adapter_configuration']
    assert adapter['authentication_method'] == 'MTLS'


def test_choice_help_lists_lower_case():
    output = click.unstyle(_invoke(['create', 'wes', '--help']).stdout)
    assert '(Choices: aws, azure, gcp, local)' in output
    assert '(Choices: oauth, mtls)' in output


def _help_of(args):
    result = CliRunner().invoke(engines_command_group, args + ['--help'])
    assert result.exit_code == 0, result.output
    return result.output


_CREATE_REQUIRED_HEADING = 'Required Options (unless given in --config):'


def _help_sections(args):
    """The help's sections by heading, each as the list of its option flags."""
    output = click.unstyle(_help_of(args))
    sections = {}
    for block in re.split(r'\n(?=[A-Z][^\n]*:\n-+\n)', output)[1:]:
        heading, _, body = block.split('\n', 2)
        sections[heading] = re.findall(r'^  (--[a-z-]+)', body, flags=re.MULTILINE)
    return sections


def test_create_aws_help_lists_the_always_required_options_first():
    sections = _help_sections(['create', 'aws'])
    assert sections[_CREATE_REQUIRED_HEADING] == ['--name', '--region', '--access-key-id', '--output-bucket',
                                                  '--role-arn', '--secret-access-key']
    assert not set(sections[_CREATE_REQUIRED_HEADING]) & set(sections['Options:'])
    assert 'Required Options:' not in sections
    output = click.unstyle(_help_of(['create', 'aws']))
    assert output.splitlines()[0].endswith('create aws REQUIRED_OPTIONS [OPTIONS]')
    assert '(Required)' not in output
    assert 'Required unless given in --config' not in output


def test_create_wes_help_lists_only_the_options_every_method_requires():
    sections = _help_sections(['create', 'wes'])
    assert sections[_CREATE_REQUIRED_HEADING] == ['--name', '--region', '--provider', '--url']
    assert {'--client-id', '--client-secret', '--client-key-and-certificate-chain'} <= set(sections['Options:'])


@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_update_help_has_no_required_options_section(kind):
    output = click.unstyle(_help_of(['update', kind]))
    assert 'Required Options' not in output
    assert 'REQUIRED_OPTIONS' not in output


@pytest.mark.parametrize('path', [['get-default'], ['parameters', 'get-default']], ids=' '.join)
def test_get_default_id_flag_shows_no_default(path):
    output = click.unstyle(_help_of(path))
    assert '--id' in output
    assert '(default: False)' not in output


@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_create_help_describes_the_id(kind):
    assert 'The engine id, unique within the namespace' in _help_of(['create', kind])


def _all_engine_command_paths():
    paths = [[verb, kind.name] for verb in ('create', 'update') for kind in ENGINE_KINDS]
    paths += [[cmd] for cmd in ('list', 'describe', 'get-default', 'set-default', 'delete')]
    paths += [['parameters', cmd]
              for cmd in ('list', 'describe', 'create', 'update', 'get-default', 'set-default', 'delete')]
    return paths


@pytest.mark.parametrize('path', _all_engine_command_paths(), ids=' '.join)
def test_engine_help_has_no_ui_or_shell_history_mentions(path):
    output = _help_of(path)
    assert 'Workbench UI' not in output
    assert 'shell history' not in output


def test_create_rejects_the_old_set_default_flag():
    result = CliRunner().invoke(engines_command_group, ['create', 'aws', '--set-default'])
    assert result.exit_code == 2
    assert 'No such option' in result.output


@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_create_rejects_the_default_flag(kind):
    with patch('dnastack.cli.commands.workbench.engines.create.get_ewes_client') as get_client:
        result = _invoke(['create', kind, '--default'])
    assert result.exit_code == 2
    assert 'No such option: --default' in result.stderr
    get_client.assert_not_called()


@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_create_help_has_no_default_option(kind):
    assert '--default' not in _help_of(['create', kind])


@pytest.mark.parametrize('args, old', [
    (['create', 'azure', '--container', 'c'], '--container'),
    (['update', 'azure', 'some-id', '--container', 'c'], '--container'),
    (['create', 'gcp', '--service-account', 'x'], '--service-account'),
    (['update', 'gcp', 'some-id', '--service-account', 'x'], '--service-account'),
    (['create', 'wes', '--auth-method', 'mtls'], '--auth-method'),
    (['update', 'wes', 'some-id', '--auth-method', 'mtls'], '--auth-method'),
    (['create', 'wes', '--client-key-and-cert', 'x'], '--client-key-and-cert'),
    (['update', 'wes', 'some-id', '--client-key-and-cert', 'x'], '--client-key-and-cert'),
])
def test_old_option_names_are_rejected(args, old):
    result = CliRunner().invoke(engines_command_group, args)
    assert result.exit_code == 2
    assert f'No such option: {old}' in result.output


@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_create_required_hints_start_a_new_sentence(kind):
    flat = ' '.join(_help_of(['create', kind]).split())
    assert not re.search(r'[a-z] Required', flat)


def test_aws_help_has_no_engine_type_line():
    assert 'Engine type:' not in _help_of(['create', 'aws'])
    assert 'Engine type: Cromwell on Cloud Run.' in _help_of(['create', 'gcp'])


@pytest.mark.parametrize('verb', ['create', 'update'])
@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_create_and_update_help_print_flush(verb, kind):
    output = _help_of([verb, kind])
    description = output[:output.index('--------')].split('\n\n')[1:-1]
    assert description[0] == f'{verb.capitalize()} {KINDS_BY_NAME[kind].summary}'
    assert all(not line.startswith(' ') and len(line) <= 120 for part in description for line in part.splitlines())


def test_create_help_body():
    flat = ' '.join(_help_of(['create', 'wes']).split())
    assert ('Creating an engine whose id already exists fails; use `update wes` to change it. The service checks '
            "the engine's health before it is saved, so this can take a while.") in flat
    assert 'Give each field as an option' not in flat


def test_delete_help_explains_the_default_engine():
    output = _help_of(['delete'])
    assert '\n\nDelete an engine\n\nThe namespace' in output
    assert ("The namespace's default engine cannot be deleted while other engines exist; make another engine the "
            'default first.') in ' '.join(output.split())
    listing = ' '.join(_help_of([]).split())
    assert 'delete Delete an engine ' in listing
    assert 'Delete an engine.' not in listing


def _invoke_without_connecting(module, args):
    """Run args with get_ewes_client mocked, and return the result and that mock."""
    with patch(f'dnastack.cli.commands.workbench.engines.{module}.get_ewes_client') as get_client:
        return _invoke(args), get_client


def test_create_name_too_short_fails_before_connecting():
    args = list(OPTIONS_BY_KIND['aws'])
    args[args.index('--name') + 1] = 'ab'
    result, get_client = _invoke_without_connecting('create', ['create', 'aws', *args])
    assert result.exit_code == 1
    assert ("Cannot derive an engine id from the name 'ab': the id must be at least 3 characters, starting with a "
            "letter or digit, using only letters, digits and '-'. Pass --id.") in result.stderr
    get_client.assert_not_called()


def test_create_placeholder_secret_fails_before_connecting():
    args = list(OPTIONS_BY_KIND['aws'])
    args[args.index('--secret-access-key') + 1] = '***'
    result, get_client = _invoke_without_connecting('create', ['create', 'aws', *args])
    assert result.exit_code == 1
    assert "  - --secret-access-key must be the real secret, not the '***' placeholder." in result.stderr
    get_client.assert_not_called()


def test_create_problem_fails_before_connecting():
    args = list(OPTIONS_BY_KIND['wes'])
    args[args.index('--url') + 1] = 'http://example.com'
    result, get_client = _invoke_without_connecting('create', ['create', 'wes', *args])
    assert result.exit_code == 1
    assert 'The engine cannot be created:' in result.stderr
    get_client.assert_not_called()


def test_create_unreadable_secret_fails_before_connecting(tmp_path):
    args = list(OPTIONS_BY_KIND['aws'])
    args[args.index('--secret-access-key') + 1] = f'@{tmp_path}/missing'
    result, get_client = _invoke_without_connecting('create', ['create', 'aws', *args])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--secret-access-key': cannot read the file" in result.stderr
    get_client.assert_not_called()


def test_update_unreadable_secret_fails_before_connecting(tmp_path):
    result, get_client = _invoke_without_connecting(
        'update', ['update', 'aws', 'aws-omics', '--secret-access-key', f'@{tmp_path}/missing'])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--secret-access-key': cannot read the file" in result.stderr
    get_client.assert_not_called()


def test_update_id_mismatch_fails_before_connecting():
    result, get_client = _invoke_without_connecting(
        'update', ['update', 'aws', 'aws-omics', '--config', '{"id": "other", "name": "N"}'])
    assert result.exit_code == 1
    assert "The id in --config ('other') does not match the engine id ('aws-omics')." in result.stderr
    get_client.assert_not_called()


def test_update_wrong_type_message_uses_subcommand_names():
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['update', 'aws', 'hifi-solves-cromwell', '--name', 'Renamed'])
    assert result.exit_code == 1
    assert ("Engine 'hifi-solves-cromwell' is a gcp engine; "
            "use 'omics workbench engines update gcp hifi-solves-cromwell'.") in result.stderr
    client.update_engine.assert_not_called()


def test_create_config_of_another_type_names_the_subcommands():
    result, get_client = _invoke_without_connecting('create', ['create', 'gcp', '--config', json.dumps(engine('aws'))])
    assert result.exit_code == 2
    assert ("Error: Invalid value for '--config': describes an aws engine, but this subcommand creates gcp engines; "
            "use 'omics workbench engines create aws'.") in result.stderr
    get_client.assert_not_called()


# "default" in --config


def _describe_output(key):
    """What `engines describe` prints for an engine, as a one-element list."""
    return [as_service_response(engine(key))]


_DEFAULT_WARNING = 'Ignoring "default" in --config; use `set-default` to make an engine the default.'


def test_create_from_describe_output_of_a_default_engine_does_not_send_default(tmp_path):
    described = _describe_output('gcp')
    assert described[0]['default'] is True
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', described)])
    assert result.exit_code == 0, result.stderr
    assert 'default' not in client.create_engine.call_args.args[0].to_request_body()
    assert _DEFAULT_WARNING in result.stderr


def test_create_with_default_false_in_config_neither_sends_it_nor_warns(tmp_path):
    described = _describe_output('aws')
    assert described[0]['default'] is False
    client = _client()
    with _patched(client):
        result = _invoke(['create', 'aws', '--config', _write(tmp_path, 'e.json', described)])
    assert result.exit_code == 0, result.stderr
    assert 'default' not in client.create_engine.call_args.args[0].to_request_body()
    assert 'Ignoring "default"' not in result.stderr


def test_update_with_default_false_in_config_neither_sends_it_nor_warns(tmp_path):
    client = _client(existing=engine('aws'))
    with _patched(client):
        result = _invoke(['update', 'aws', engine('aws')['id'], '--config',
                          _write(tmp_path, 'e.json', _describe_output('aws'))])
    assert result.exit_code == 0, result.stderr
    assert 'default' not in client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert 'Ignoring "default"' not in result.stderr


def test_update_from_describe_output_of_a_default_engine_does_not_send_default(tmp_path):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['update', 'gcp', engine('gcp')['id'], '--config',
                          _write(tmp_path, 'e.json', _describe_output('gcp'))])
    assert result.exit_code == 0, result.stderr
    assert 'default' not in client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert _DEFAULT_WARNING in result.stderr


def test_update_with_only_default_in_config_has_nothing_to_change(tmp_path):
    client = _client(existing=engine('gcp'))
    with _patched(client):
        result = _invoke(['update', 'gcp', engine('gcp')['id'], '--config',
                          _write(tmp_path, 'e.json', {'default': True})])
    assert result.exit_code == 2
    assert 'Nothing to update' in result.stderr
    client.update_engine.assert_not_called()


# Azure scope following a changed client id


def _azure_update_body(stored_changes, args):
    stored = engine('azure')
    stored['engine_adapter_configuration'].update(stored_changes)
    client = _client(existing=stored)
    with _patched(client):
        result = _invoke(['update', 'azure', stored['id'], *args])
    assert result.exit_code == 0, result.stderr
    return client.update_engine.call_args.kwargs['engine'].to_request_body()['engine_adapter_configuration']


def test_update_azure_client_id_moves_a_default_scope_along():
    adapter = _azure_update_body({}, ['--client-id', 'new-client'])
    assert adapter['client_id'] == 'new-client'
    assert adapter['scope'] == 'new-client/.default'


def test_update_azure_client_id_keeps_a_custom_scope():
    adapter = _azure_update_body({'scope': 'api://custom/.default'}, ['--client-id', 'new-client'])
    assert 'scope' not in adapter


def test_update_azure_client_id_keeps_a_scope_that_is_given():
    adapter = _azure_update_body({}, ['--client-id', 'new-client', '--scope', 'chosen'])
    assert adapter['scope'] == 'chosen'


def test_update_azure_without_client_id_change_leaves_scope_alone():
    assert 'scope' not in _azure_update_body({}, ['--client-id', 'azure-client'])
    assert 'scope' not in _azure_update_body({}, ['--url', 'https://other.azure.example.com'])


def test_azure_scope_help_differs_between_create_and_update():
    create = ' '.join(_help_of(['create', 'azure']).split())
    update = ' '.join(_help_of(['update', 'azure']).split())
    assert 'The OAuth scope to request. Defaults to <client id>/.default.' in create
    assert ('The OAuth scope to request. When --client-id changes and the stored scope is the default '
            '<client id>/.default, it follows the new client id; otherwise the stored scope is kept.') in update


# Service errors that echo the request's secrets


def _response(status, text):
    response = requests.Response()
    response.status_code = status
    response._content = text.encode('utf-8')
    response.encoding = 'utf-8'
    return response


def _echoing_error(error_type, status, body):
    """An error whose text echoes the whole request body, every secret in it JSON-escaped as a service would."""
    return error_type(_response(status, json.dumps({'msg': 'rejected', 'request': body})))


@pytest.mark.parametrize('error_type, status', [(ClientError, 400), (ClientError, 409), (ServerError, 500)])
@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_create_error_echoing_the_request_masks_every_secret(tmp_path, key, error_type, status):
    client = _client()
    client.create_engine.side_effect = lambda request: (_ for _ in ()).throw(
        _echoing_error(error_type, status, request.to_request_body()))
    with _patched(client):
        result = _invoke(['create', KIND[key], '--config', _write(tmp_path, 'e.json', engine(key))])
    assert result.exit_code == 1
    assert f'{error_type.__name__}: ' in result.stderr
    assert f'HTTP {status}' in result.stderr
    assert '***' in result.stderr
    _assert_no_secrets(result)


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_update_error_echoing_the_request_masks_every_secret(tmp_path, key):
    client = _client(existing=engine(key))
    client.update_engine.side_effect = lambda engine_id, engine, if_match: (_ for _ in ()).throw(
        _echoing_error(ClientError, 400, engine.to_request_body()))
    with _patched(client):
        result = _invoke(['update', KIND[key], engine(key)['id'], '--config', _write(tmp_path, 'e.json', engine(key))])
    assert result.exit_code == 1
    assert 'ClientError: ' in result.stderr
    _assert_no_secrets(result)


def test_update_error_masks_a_secret_given_as_an_option():
    client = _client(existing=engine('aws'))
    client.update_engine.side_effect = ClientError(_response(400, 'secret_access_key NEW-SECRET-KEY is invalid'))
    with _patched(client):
        result = _invoke(['update', 'aws', engine('aws')['id'], '--secret-access-key', 'NEW-SECRET-KEY'])
    assert result.exit_code == 1
    assert 'ClientError: HTTP 400: secret_access_key *** is invalid' in result.stderr
    assert 'NEW-SECRET-KEY' not in result.stderr + result.stdout


def test_error_echoing_part_of_the_service_account_key_masks_it(tmp_path):
    key = {**GCP_SERVICE_ACCOUNT, 'private_key_id': 'SECRET-KEY-ID'}
    data = engine('gcp')
    data['engine_adapter_configuration']['auth_config']['service_account_json'] = key
    client = _client()
    client.create_engine.side_effect = ClientError(_response(
        400, 'key SECRET-KEY-ID could not sign with SECRET-GCP-KEY'))
    with _patched(client):
        result = _invoke(['create', 'gcp', '--config', _write(tmp_path, 'e.json', data)])
    assert result.exit_code == 1
    assert 'key *** could not sign with ***' in result.stderr
    assert 'SECRET-KEY-ID' not in result.stderr
    _assert_no_secrets(result)


@pytest.mark.parametrize('key', sorted(ALL_ENGINES))
def test_health_check_errors_echoing_a_secret_are_masked(tmp_path, key):
    adapter = ALL_ENGINES[key]['engine_adapter_configuration']
    secrets = [get_field(adapter, path) for path in ENGINE_SECRET_FIELDS if get_field(adapter, path)]
    assert secrets
    body = {'msg': 'Initial engine health check failed.', 'errors': [{'checks': [
        {'type': 'CREDENTIALS', 'outcome': 'FAILURE', 'error': f'credential {secret} was refused'}
        for secret in secrets]}]}
    client = _client()
    client.create_engine.side_effect = ClientError(_response(400, json.dumps(body)))
    with _patched(client):
        result = _invoke(['create', KIND[key], '--config', _write(tmp_path, 'e.json', engine(key))])
    assert result.exit_code == 1
    assert 'failed its health check' in result.stderr
    assert 'credential *** was refused' in click.unstyle(result.stderr)
    _assert_no_secrets(result)


def test_unparsable_error_body_echoing_a_secret_is_masked(tmp_path):
    client = _client()
    client.create_engine.side_effect = ClientError(_response(400, '<html>SECRET-AWS not accepted'))
    with _patched(client):
        result = _invoke(['create', 'aws', '--config', _write(tmp_path, 'e.json', engine('aws'))])
    assert result.exit_code == 1
    assert 'ClientError: HTTP 400: <html>*** not accepted' in result.stderr
    _assert_no_secrets(result)


# Help texts


@pytest.mark.parametrize('verb', ['create', 'update'])
@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_region_help_has_no_example_regions(verb, kind):
    flat = ' '.join(_help_of([verb, kind]).split())
    assert 'The region for the engine.' in flat
    assert 'For example' not in flat
    assert ('Use local with --provider local.' in flat) == (kind == 'wes')


@pytest.mark.parametrize('verb', ['create', 'update'])
@pytest.mark.parametrize('kind', [k.name for k in ENGINE_KINDS])
def test_secret_option_help_says_how_to_pass_an_at_or_dash_value(verb, kind):
    flat = ' '.join(_help_of([verb, kind]).split())
    for secret in KINDS_BY_NAME[kind].secrets:
        option_help = flat[flat.index(secret.flag):]
        assert 'A value that starts with @ or - must be given as @path.' in option_help[:400]


def test_update_help_says_a_field_cannot_be_cleared():
    flat = ' '.join(_help_of(['update', 'aws']).split())
    assert 'A field cannot be cleared: an omitted or null field keeps its stored value.' in flat


def test_create_help_says_the_first_engine_becomes_the_default():
    flat = ' '.join(_help_of(['create', 'aws']).split())
    assert 'The first engine in a namespace always becomes the default. Use `set-default` to change it.' in flat


def test_azure_container_option():
    output = _help_of(['create', 'azure'])
    assert '--storage-container-name' in output
    assert '--container' not in output.replace('--storage-container-name', '')
    flat = ' '.join(output.split())
    assert 'The Azure storage container name.' in flat
    assert ('The application (client) ID of the Azure AD service principal that Workbench uses to call '
            'Cromwell.') in flat


def test_engine_group_help_has_no_surrounding_spaces():
    output = CliRunner().invoke(click.Group(commands={'engines': engines_command_group}), ['--help']).output
    assert 'Interact with engines' in output
    assert ' Interact with engines ' not in output
    assert engines_command_group.help == 'Interact with engines'


def test_create_help_examples_show_secret_options_as_at_path():
    examples = _help_of(['create', 'aws']).split('Examples:')[1]
    assert '--secret-access-key @PATH' in examples
    assert '--secret-access-key VALUE' not in examples
    assert '--service-account-json @PATH' in _help_of(['create', 'gcp']).split('Examples:')[1]
    assert '--client-secret @PATH' in _help_of(['create', 'azure']).split('Examples:')[1]
