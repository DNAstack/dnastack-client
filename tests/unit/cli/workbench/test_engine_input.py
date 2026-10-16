"""Unit tests for turning engine CLI arguments into a request, without echoing secrets."""
import io
import json

import pytest

from dnastack.cli.commands.workbench.engines.engine_input import (
    EngineInputError, EngineOptionError, apply_secret_flags, fill_engine_id, follow_default_azure_scope,
    inherit_adapter_type, inherit_authentication_method, load_engine_object, load_json_object, parse_engine_request,
    resolve_if_match, set_config_field,
)
from dnastack.common.json_argument_parser import JsonLike
from tests.unit.client.workbench.ewes.engine_fixtures import GCP_SERVICE_ACCOUNT, as_service_response, engine


def _shown(error):
    """The message click prints for an option error, or the plain message otherwise."""
    if isinstance(error.value, EngineOptionError):
        return error.value.format_message()
    return str(error.value)


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return f'@{path}'


def test_load_json_object_from_file(tmp_path):
    path = _write(tmp_path, 'e.json', json.dumps(engine('gcp')))
    assert load_json_object(JsonLike(path), '--config') == engine('gcp')


def test_load_engine_object_accepts_one_element_list(tmp_path):
    ref = _write(tmp_path, 'e.json', json.dumps([engine('gcp')]))
    assert load_engine_object(JsonLike(ref)) == engine('gcp')


@pytest.mark.parametrize('content', [[], [engine('gcp'), engine('azure')]])
def test_load_engine_object_rejects_other_lists(tmp_path, content):
    ref = _write(tmp_path, 'e.json', json.dumps(content))
    with pytest.raises(EngineOptionError) as error:
        load_engine_object(JsonLike(ref))
    assert _shown(error) == ("Invalid value for '--config': must be a JSON object, or a list holding exactly "
                             "one engine.")


def test_load_json_object_inline():
    assert load_json_object(JsonLike('{"a": 1}'), '--values') == {'a': 1}


def test_missing_file_is_a_clean_error(tmp_path):
    with pytest.raises(EngineOptionError) as error:
        load_json_object(JsonLike(f'@{tmp_path}/nope.json'), '--config')
    assert _shown(error).startswith("Invalid value for '--config': cannot read ")
    assert _shown(error).endswith('nope.json: No such file or directory.')


def test_malformed_json_does_not_echo_content(tmp_path):
    ref = _write(tmp_path, 'bad.json', '{"client_secret": "SECRET-AZURE",,}')
    with pytest.raises(EngineInputError) as error:
        load_json_object(JsonLike(ref), '--config')
    assert 'SECRET-AZURE' not in str(error.value)
    assert 'invalid JSON' in str(error.value)


def test_non_object_rejected(tmp_path):
    with pytest.raises(EngineInputError, match='must be a JSON object'):
        load_json_object(JsonLike(_write(tmp_path, 'a.json', '[1, 2]')), '--config')


def test_service_account_flag(tmp_path):
    data = engine('gcp')
    del data['engine_adapter_configuration']['auth_config']
    result = apply_secret_flags(data, service_account_json=_write(tmp_path, 'sa.json', json.dumps(GCP_SERVICE_ACCOUNT)))
    sent = result['engine_adapter_configuration']['auth_config']['service_account_json']
    assert json.loads(sent) == GCP_SERVICE_ACCOUNT


def test_secret_flag_overrides_file(tmp_path):
    result = apply_secret_flags(engine('azure'), client_secret=_write(tmp_path, 's', 'FROM-FLAG'))
    assert result['engine_adapter_configuration']['client_secret'] == 'FROM-FLAG'


def test_secret_flags_do_not_mutate_input(tmp_path):
    data = engine('azure')
    apply_secret_flags(data, client_secret=_write(tmp_path, 's', 'FROM-FLAG'))
    assert data == engine('azure')


@pytest.mark.parametrize('key, flags, path', [
    ('wes_oauth', {'client_secret': 'NEW'}, 'oauth_config.clientSecret'),
    ('azure', {'client_secret': 'NEW'}, 'client_secret'),
    ('aws', {'secret_access_key': 'NEW'}, 'secret_access_key'),
])
def test_secret_flag_targets(tmp_path, key, flags, path):
    flag_values = {name: _write(tmp_path, name, value) for name, value in flags.items()}
    adapter = apply_secret_flags(engine(key), **flag_values)['engine_adapter_configuration']
    leaf = adapter
    for part in path.split('.'):
        leaf = leaf[part]
    assert leaf == 'NEW'


def test_client_secret_trailing_newline_stripped(tmp_path):
    result = apply_secret_flags(engine('azure'), client_secret=_write(tmp_path, 's', 'NEW\n'))
    assert result['engine_adapter_configuration']['client_secret'] == 'NEW'


def test_pem_kept_verbatim(tmp_path):
    pem = '-----BEGIN PRIVATE KEY-----\nNEW\n-----END PRIVATE KEY-----\n'
    result = apply_secret_flags(engine('wes_mtls'), client_key_and_certificate_chain=_write(tmp_path, 'k.pem', pem))
    assert result['engine_adapter_configuration']['ssl_config']['client_key_and_certificate_chain'] == pem


@pytest.mark.parametrize('key, flag, message', [
    ('gcp', 'client_secret', '--client-secret does not apply to gcp engines.'),
    ('aws', 'service_account_json', '--service-account-json does not apply to aws engines.'),
    ('wes_oauth', 'client_key_and_certificate_chain',
     '--client-key-and-certificate-chain does not apply to wes engines using oauth authentication.'),
    ('wes_mtls', 'client_secret', '--client-secret does not apply to wes engines using mtls authentication.'),
])
def test_secret_flag_wrong_type(tmp_path, key, flag, message):
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(engine(key), **{flag: _write(tmp_path, 'f', 'x')})
    option, rest = message.split(' ', 1)
    assert _shown(error) == f"Invalid value for '{option}': {rest}"


def test_empty_secret_file_rejected(tmp_path):
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(engine('aws'), secret_access_key=_write(tmp_path, 's', '\n'))
    assert _shown(error) == "Invalid value for '--secret-access-key': the value is empty."


def test_inherit_authentication_method():
    data = engine('wes_mtls')
    del data['engine_adapter_configuration']['authentication_method']
    result = inherit_authentication_method(data, {'type': 'WES_ON_CROMWELL', 'authentication_method': 'MTLS'})
    assert result['engine_adapter_configuration']['authentication_method'] == 'MTLS'


def test_inherit_authentication_method_keeps_explicit_value():
    result = inherit_authentication_method(engine('wes_oauth'), {'authentication_method': 'MTLS'})
    assert result['engine_adapter_configuration']['authentication_method'] == 'OAUTH'


def test_parse_strips_server_set_fields():
    request = parse_engine_request(as_service_response(engine('gcp')))
    assert 'version' not in request.to_request_body()


def test_parse_requires_adapter_type():
    with pytest.raises(EngineInputError, match='engine_adapter_configuration.type is required'):
        parse_engine_request({'id': 'x', 'engine_adapter_configuration': {}})


def test_validation_error_does_not_echo_secret():
    data = engine('azure')
    data['engine_adapter_configuration']['client_secret'] = {'nested': 'SECRET-AZURE'}
    with pytest.raises(EngineInputError) as error:
        parse_engine_request(data)
    assert 'SECRET-AZURE' not in str(error.value)
    assert 'client_secret' in str(error.value)
    assert 'engine_adapter_configuration.client_secret' in str(error.value)


def test_unknown_adapter_type_does_not_echo_value():
    with pytest.raises(EngineInputError) as error:
        parse_engine_request({'engine_adapter_configuration': {'type': 'SECRET-TYPO'}})
    message = str(error.value)
    assert 'SECRET-TYPO' not in message
    assert ('engine_adapter_configuration.type: must be one of WES_ON_CROMWELL, GCP_CLOUD_RUN_CROMWELL, '
            'AZURE_CONTAINER_APP_CROMWELL, AWS_HEALTH_OMICS' in message)


@pytest.mark.parametrize('raw', ['a[b=SECRET-KV', '-x'])
def test_unparseable_file_value_does_not_echo_it(raw):
    with pytest.raises(EngineOptionError) as error:
        load_engine_object(JsonLike(raw))
    assert _shown(error) == "Invalid value for '--config': could not parse the value."


def test_missing_file_inside_key_value_names_only_the_path(tmp_path):
    with pytest.raises(EngineInputError) as error:
        load_engine_object(JsonLike(f'secret=SECRET-KV,x=@{tmp_path}/missing.txt'))
    assert 'SECRET-KV' not in str(error.value)
    assert 'missing.txt' not in str(error.value)


def test_missing_file_in_key_value_syntax_does_not_echo_the_text_after_the_at_sign():
    with pytest.raises(EngineInputError) as error:
        load_engine_object(JsonLike('a=@SECRET-KV-PATH'))
    assert 'SECRET-KV-PATH' not in _shown(error)
    assert _shown(error).startswith("Invalid value for '--config': cannot read a file it refers to")


def test_secret_option_into_a_non_object_adapter_configuration_is_a_clean_error():
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags({'engine_adapter_configuration': 'x'}, secret_access_key='SECRET-KEY')
    assert 'engine_adapter_configuration must be an object' in str(error.value)
    assert 'SECRET-KEY' not in str(error.value)


def test_secret_option_into_a_non_object_parent_is_a_clean_error():
    data = engine('gcp')
    data['engine_adapter_configuration']['auth_config'] = 'x'
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(data, service_account_json='{"a": "SECRET-SA"}')
    # The same error, naming --config, as a field option writing below a non-object parent.
    assert _shown(error) == ("Invalid value for '--config': "
                             "engine_adapter_configuration.auth_config must be an object.")
    assert 'SECRET-SA' not in str(error.value)


def test_secret_option_with_an_unknown_adapter_type_does_not_echo_it():
    data = {'engine_adapter_configuration': {'type': 'SECRET-TYPO'}}
    with pytest.raises(EngineInputError) as error:
        apply_secret_flags(data, client_secret='SECRET-X')
    message = str(error.value)
    assert 'SECRET-TYPO' not in message
    assert 'engine_adapter_configuration.type must be one of' in message
    assert 'AWS_HEALTH_OMICS' in message


def test_fill_engine_id_derives_from_name():
    assert fill_engine_id({'name': 'GIAB Demo'})['id'] == 'giab-demo'


def test_fill_engine_id_keeps_given_id_and_does_not_mutate():
    data = {'id': 'given', 'name': 'GIAB Demo'}
    assert fill_engine_id(data) == {'id': 'given', 'name': 'GIAB Demo'}
    without_id = {'name': 'GIAB Demo'}
    fill_engine_id(without_id)
    assert without_id == {'name': 'GIAB Demo'}


def test_fill_engine_id_leaves_a_missing_name_to_validation():
    assert fill_engine_id({}) == {}


def test_fill_engine_id_rejects_a_name_too_short_for_an_id():
    with pytest.raises(EngineInputError) as error:
        fill_engine_id({'name': 'A1'})
    assert str(error.value) == ("Cannot derive an engine id from the name 'A1': the id must be at least 3 characters, "
                                "starting with a letter or digit, using only letters, digits and '-'. Pass --id.")


def test_secret_flag_accepts_an_inline_value():
    result = apply_secret_flags(engine('azure'), client_secret='FROM-FLAG')
    assert result['engine_adapter_configuration']['client_secret'] == 'FROM-FLAG'


def test_secret_flag_reads_stdin(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('FROM-STDIN\n'))
    result = apply_secret_flags(engine('aws'), secret_access_key='-')
    assert result['engine_adapter_configuration']['secret_access_key'] == 'FROM-STDIN'


def test_secret_flag_value_starting_with_dash_is_a_clear_error():
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(engine('azure'), client_secret='-SECRET-DASH')
    assert _shown(error) == ("Invalid value for '--client-secret': values starting with \"-\" are read from stdin; "
                             "put the value in a file and pass @path.")
    assert 'SECRET-DASH' not in _shown(error)


def test_missing_secret_file_is_reported_without_the_path(tmp_path):
    with pytest.raises(EngineInputError) as error:
        apply_secret_flags(engine('azure'), client_secret=f'@{tmp_path}/no-such-secret.txt')
    assert _shown(error) == "Invalid value for '--client-secret': cannot read the file: No such file or directory."
    assert 'no-such-secret' not in _shown(error)


def test_inline_secret_starting_with_at_is_not_echoed():
    with pytest.raises(EngineInputError) as error:
        apply_secret_flags(engine('azure'), client_secret='@SECRET-AT')
    assert 'SECRET-AT' not in str(error.value)


def test_secret_file_that_is_not_text_is_reported(tmp_path):
    path = tmp_path / 'binary'
    path.write_bytes(b'\xff\xfe\x00')
    with pytest.raises(EngineInputError) as error:
        apply_secret_flags(engine('azure'), client_secret=f'@{path}')
    assert _shown(error) == "Invalid value for '--client-secret': the file is not text."


def test_service_account_inline_json():
    data = engine('gcp')
    del data['engine_adapter_configuration']['auth_config']
    result = apply_secret_flags(data, service_account_json=json.dumps(GCP_SERVICE_ACCOUNT))
    sent = result['engine_adapter_configuration']['auth_config']['service_account_json']
    assert json.loads(sent) == GCP_SERVICE_ACCOUNT


def test_service_account_invalid_json_does_not_echo_it():
    with pytest.raises(EngineInputError) as error:
        apply_secret_flags(engine('gcp'), service_account_json='{"private_key": "SECRET-GCP-KEY"')
    assert 'SECRET-GCP-KEY' not in _shown(error)
    assert _shown(error).startswith("Invalid value for '--service-account-json': invalid JSON")


def test_service_account_must_be_an_object():
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(engine('gcp'), service_account_json='["SECRET-GCP-KEY"]')
    assert _shown(error) == "Invalid value for '--service-account-json': must be a JSON object."


def test_inherit_adapter_type_when_adapter_missing():
    assert inherit_adapter_type({'name': 'n'}, 'AWS_HEALTH_OMICS') == {
        'name': 'n', 'engine_adapter_configuration': {'type': 'AWS_HEALTH_OMICS'}}


def test_inherit_adapter_type_when_type_missing():
    result = inherit_adapter_type({'engine_adapter_configuration': {'role_arn': 'r'}}, 'AWS_HEALTH_OMICS')
    assert result['engine_adapter_configuration'] == {'role_arn': 'r', 'type': 'AWS_HEALTH_OMICS'}


def test_inherit_adapter_type_rejects_a_change():
    with pytest.raises(EngineInputError, match=r'engine_adapter_configuration.type cannot be changed '
                                               r'\(stored: AWS_HEALTH_OMICS, --config: GCP_CLOUD_RUN_CROMWELL\)'):
        inherit_adapter_type({'engine_adapter_configuration': {'type': 'GCP_CLOUD_RUN_CROMWELL'}}, 'AWS_HEALTH_OMICS')


def test_inherit_adapter_type_does_not_echo_an_unknown_type():
    with pytest.raises(EngineInputError) as error:
        inherit_adapter_type({'engine_adapter_configuration': {'type': 'SECRET-PASTED'}}, 'AWS_HEALTH_OMICS')
    assert str(error.value) == 'engine_adapter_configuration.type cannot be changed (stored: AWS_HEALTH_OMICS).'


def test_set_config_field_replaces_missing_and_null_parents():
    data = {'a': None}
    set_config_field(data, 'a.b.c', 1)
    assert data == {'a': {'b': {'c': 1}}}


def test_set_config_field_keeps_existing_parents():
    data = {'a': {'b': {'keep': 1}}}
    set_config_field(data, 'a.b.c', 2)
    assert data == {'a': {'b': {'keep': 1, 'c': 2}}}


@pytest.mark.parametrize('parent', ['text', 5, ['x']])
def test_set_config_field_names_the_first_parent_that_is_not_an_object(parent):
    with pytest.raises(EngineOptionError) as error:
        set_config_field({'a': {'b': parent}}, 'a.b.c', 'SECRET-VALUE')
    assert _shown(error) == "Invalid value for '--config': a.b must be an object."


def test_inherit_adapter_type_does_not_mutate():
    data = {'engine_adapter_configuration': {'role_arn': 'r'}}
    inherit_adapter_type(data, 'AWS_HEALTH_OMICS')
    assert data == {'engine_adapter_configuration': {'role_arn': 'r'}}


def test_resolve_if_match():
    assert resolve_if_match('e', 'v-2', 'V-2') == 'v-2'
    assert resolve_if_match('e', None, 'v-2') == 'v-2'
    with pytest.raises(EngineInputError, match="Engine 'e' has changed since that --config was written"):
        resolve_if_match('e', 'v-1', 'v-2')


def test_option_errors_are_still_engine_input_errors():
    with pytest.raises(EngineInputError):
        load_engine_object(JsonLike('[1, 2]'))


def test_secret_flag_needs_adapter_type_names_the_option(tmp_path):
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags({'id': 'x'}, client_secret=_write(tmp_path, 's', 'x'))
    assert _shown(error) == ("Invalid value for '--client-secret': engine_adapter_configuration.type must be set "
                             "in --config to use this option.")


@pytest.mark.parametrize('method', ['SECRET-METHOD', 7, ['MTLS'], {'nested': 'SECRET-METHOD'}])
def test_secret_flag_with_an_invalid_authentication_method_does_not_echo_it(tmp_path, method):
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['authentication_method'] = method
    with pytest.raises(EngineOptionError) as error:
        apply_secret_flags(data, client_key_and_certificate_chain=_write(tmp_path, 'k.pem', 'pem'))
    assert _shown(error) == ("Invalid value for '--client-key-and-certificate-chain': does not apply to wes engines "
                             "using the authentication_method in --config.")


@pytest.mark.parametrize('method', [7, ['MTLS'], {'nested': 'SECRET-METHOD'}])
def test_secret_flag_that_applies_with_a_non_string_method_fails_only_as_input_errors(tmp_path, method):
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['authentication_method'] = method
    with pytest.raises(EngineInputError) as error:
        parse_engine_request(apply_secret_flags(data, client_secret=_write(tmp_path, 's', 'NEW')))
    assert 'SECRET-METHOD' not in str(error.value)


def test_unknown_field_names_its_parent_but_not_the_key():
    data = engine('aws')
    data['engine_adapter_configuration']['SECRET-PASTED-KEY'] = 'x'
    data['engine_adapter_configuration']['another-SECRET'] = 'y'
    with pytest.raises(EngineInputError) as error:
        parse_engine_request(data)
    message = str(error.value)
    assert 'SECRET' not in message
    assert message.count('engine_adapter_configuration has a field this engine type does not use.') == 1


def test_unknown_nested_and_top_level_fields_name_their_parent():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['oauth_config']['SECRET-A'] = 'x'
    data['SECRET-B'] = 'y'
    with pytest.raises(EngineInputError) as error:
        parse_engine_request(data)
    message = str(error.value)
    assert 'SECRET' not in message
    assert 'engine_adapter_configuration.oauth_config has a field this engine type does not use.' in message
    assert 'The engine description has a field this engine type does not use.' in message


def _azure_update(adapter_changes):
    return {'engine_adapter_configuration': {'type': 'AZURE_CONTAINER_APP_CROMWELL', **adapter_changes}}


def _stored_azure(**changes):
    return {**engine('azure')['engine_adapter_configuration'], **changes}


def test_default_azure_scope_follows_a_new_client_id():
    result = follow_default_azure_scope(_azure_update({'client_id': 'new'}), _stored_azure())
    assert result['engine_adapter_configuration']['scope'] == 'new/.default'


@pytest.mark.parametrize('update, stored', [
    ({'client_id': 'new'}, _stored_azure(scope='api://custom/.default')),
    ({'client_id': 'new', 'scope': 'chosen'}, _stored_azure()),
    ({'client_id': 'azure-client'}, _stored_azure()),
    ({'url': 'https://x.example.com'}, _stored_azure()),
    ({'client_id': 'new'}, _stored_azure(scope=None)),
])
def test_azure_scope_is_otherwise_left_alone(update, stored):
    engine_update = _azure_update(update)
    assert follow_default_azure_scope(engine_update, stored) == engine_update


def test_default_azure_scope_ignores_other_adapter_types():
    data = {'engine_adapter_configuration': {'type': 'AWS_HEALTH_OMICS', 'client_id': 'new'}}
    assert follow_default_azure_scope(data, _stored_azure()) == data


def test_inherit_authentication_method_treats_null_as_omitted():
    data = {'engine_adapter_configuration': {'type': 'WES_ON_CROMWELL', 'authentication_method': None}}
    result = inherit_authentication_method(data, {'authentication_method': 'MTLS'})
    assert result['engine_adapter_configuration']['authentication_method'] == 'MTLS'
    assert data['engine_adapter_configuration']['authentication_method'] is None


@pytest.mark.parametrize('key, parent, option', [
    ('wes_oauth', 'oauth_config', 'client_secret'),
    ('gcp', 'auth_config', 'service_account_json'),
    ('wes_mtls', 'ssl_config', 'client_key_and_certificate_chain'),
])
def test_secret_option_into_a_null_parent_creates_it(tmp_path, key, parent, option):
    data = engine(key)
    data['engine_adapter_configuration'][parent] = None
    value = json.dumps(GCP_SERVICE_ACCOUNT) if option == 'service_account_json' else 'SECRET-NULL-PARENT'
    result = apply_secret_flags(data, **{option: _write(tmp_path, 's', value)})
    assert isinstance(result['engine_adapter_configuration'][parent], dict)
    assert data['engine_adapter_configuration'][parent] is None
