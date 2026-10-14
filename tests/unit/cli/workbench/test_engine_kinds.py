"""Unit tests for the per-type engine options and the description they build."""
import copy

import pytest

from dnastack.cli.commands.workbench.engines.engine_input import EngineOptionError
from dnastack.cli.commands.workbench.engines.engine_kinds import (
    ENGINE_KINDS, KINDS_BY_NAME, build_engine_description, has_changes, missing_create_options, option_names,
    option_specs, secret_options_from,
)
from dnastack.cli.commands.workbench.engines.engine_names import subcommand_for, with_article
from dnastack.client.workbench.ewes.engine_models import WesOnCromwellAuthenticationMethod, required_create_fields

ROLE = 'arn:aws:iam::123456789012:role/omics'


def _kind(name):
    return KINDS_BY_NAME[name]


def _spec(kind_name, flag, for_create=True):
    return next(s for s in option_specs(_kind(kind_name), for_create) if flag in s.arg_names)


def test_kinds_in_order():
    assert [k.name for k in ENGINE_KINDS] == ['gcp', 'wes', 'azure', 'aws']


def test_subcommand_for():
    assert subcommand_for('AWS_HEALTH_OMICS') == 'aws'
    assert subcommand_for('SOMETHING_NEW') is None
    assert subcommand_for(['not', 'a', 'type']) is None


@pytest.mark.parametrize('name, values, expected', [
    ('gcp', {'url': 'https://c.example.com', 'project_id': 'p', 'quota_project_id': 'q'},
     {'url': 'https://c.example.com', 'project_id': 'p', 'quota_project_id': 'q'}),
    ('wes', {'url': 'https://w.example.com', 'authentication_method': 'oauth', 'client_id': 'cid',
             'token_uri': 'https://auth.example.com/token', 'resource': 'res', 'scope': 'sc'},
     {'url': 'https://w.example.com', 'authentication_method': 'OAUTH',
      'oauth_config': {'clientId': 'cid', 'tokenUri': 'https://auth.example.com/token', 'resource': 'res',
                       'scope': 'sc'}}),
    ('azure', {'url': 'https://a.example.com', 'tenant_id': 't', 'client_id': 'c', 'scope': 's',
               'storage_account_name': 'acct', 'storage_container_name': 'cont'},
     {'url': 'https://a.example.com', 'tenant_id': 't', 'client_id': 'c', 'scope': 's',
      'storage_account_name': 'acct', 'storage_container_name': 'cont'}),
    ('aws', {'access_key_id': 'AKIA', 'output_bucket': 's3://b', 'role_arn': ROLE},
     {'access_key_id': 'AKIA', 'output_bucket': 's3://b', 'role_arn': ROLE}),
])
def test_options_land_in_their_fields(name, values, expected):
    engine = build_engine_description(_kind(name), None, values, for_create=True)
    assert engine['engine_adapter_configuration'] == {'type': _kind(name).adapter_type.value, **expected}


def test_common_options_and_fixed_provider():
    engine = build_engine_description(_kind('gcp'), None, {'id': 'e-1', 'name': 'E', 'description': 'd',
                                                           'region': 'us-central1'},
                                      for_create=True)
    assert (engine['id'], engine['name'], engine['description'], engine['region']) == (
        'e-1', 'E', 'd', 'us-central1')
    assert engine['provider'] == 'GCP'
    assert 'default' not in engine


def test_wes_takes_provider_option():
    engine = build_engine_description(_kind('wes'), None, {'provider': 'LOCAL'}, for_create=True)
    assert engine['provider'] == 'LOCAL'


def test_options_override_file_and_file_is_not_mutated():
    file = {'name': 'From file', 'engine_adapter_configuration': {
        'type': 'GCP_CLOUD_RUN_CROMWELL', 'url': 'https://old.example.com', 'project_id': 'keep'}}
    snapshot = copy.deepcopy(file)
    engine = build_engine_description(_kind('gcp'), file, {'url': 'https://new.example.com'}, for_create=True)
    assert engine['engine_adapter_configuration']['url'] == 'https://new.example.com'
    assert engine['engine_adapter_configuration']['project_id'] == 'keep'
    assert engine['name'] == 'From file'
    assert file == snapshot


@pytest.mark.parametrize('for_create, message', [
    (True, "Invalid value for '--config': describes an aws engine, but this subcommand creates gcp engines; "
           "use 'omics workbench engines create aws'."),
    (False, "Invalid value for '--config': describes an aws engine; use 'omics workbench engines update aws ...'."),
])
def test_file_of_another_type_rejected(for_create, message):
    file = {'engine_adapter_configuration': {'type': 'AWS_HEALTH_OMICS'}}
    with pytest.raises(EngineOptionError) as error:
        build_engine_description(_kind('gcp'), file, {}, for_create=for_create)
    assert error.value.format_message() == message


def test_file_of_an_unknown_type_is_not_echoed():
    file = {'engine_adapter_configuration': {'type': 'SECRET-TYPO'}}
    with pytest.raises(EngineOptionError) as error:
        build_engine_description(_kind('gcp'), file, {}, for_create=True)
    assert error.value.format_message() == ("Invalid value for '--config': engine_adapter_configuration.type must be "
                                            "GCP_CLOUD_RUN_CROMWELL for this subcommand, or left out.")


def test_file_with_another_provider_rejected_for_fixed_kinds():
    with pytest.raises(EngineOptionError) as error:
        build_engine_description(_kind('gcp'), {'provider': 'SECRET-AZURE'}, {}, for_create=True)
    assert error.value.format_message() == ("Invalid value for '--config': provider must be GCP for gcp engines, "
                                            "or left out.")


def test_file_adapter_must_be_an_object():
    with pytest.raises(EngineOptionError, match='engine_adapter_configuration must be an object'):
        build_engine_description(_kind('gcp'), {'engine_adapter_configuration': 'x'}, {}, for_create=True)


def test_update_leaves_type_and_provider_out():
    engine = build_engine_description(_kind('aws'), None, {'role_arn': ROLE}, for_create=False)
    assert engine == {'engine_adapter_configuration': {'role_arn': ROLE}}


def test_server_certificate_chain_read_from_file(tmp_path):
    pem = '-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----\n'
    path = tmp_path / 'server.pem'
    path.write_text(pem)
    engine = build_engine_description(_kind('wes'), None, {'server_certificate_chain': f'@{path}'},
                                      for_create=True)
    assert engine['engine_adapter_configuration']['ssl_config']['server_certificate_chain'] == pem


def test_server_certificate_chain_given_inline_is_refused_with_the_path_hint():
    with pytest.raises(EngineOptionError) as error:
        build_engine_description(_kind('wes'), None,
                                 {'server_certificate_chain': '-----BEGIN CERTIFICATE-----\nSERVER'}, for_create=True)
    assert error.value.format_message() == (
        "Invalid value for '--server-certificate-chain': values starting with \"-\" are read from stdin; put the "
        "value in a file and pass @path.")


def test_server_certificate_chain_missing_file(tmp_path):
    with pytest.raises(EngineOptionError) as error:
        build_engine_description(_kind('wes'), None, {'server_certificate_chain': f'@{tmp_path}/missing.pem'},
                                 for_create=True)
    assert error.value.format_message() == ("Invalid value for '--server-certificate-chain': cannot read the "
                                            "file: No such file or directory.")


@pytest.mark.parametrize('flag', ['--server-certificate-chain', '--client-key-and-certificate-chain'])
def test_pem_options_are_read_from_a_file_or_stdin_only(flag):
    help_text = _spec('wes', flag, for_create=False).help
    assert ': @path to a PEM file, or - to read stdin.' in help_text
    assert help_text.endswith(' A value that starts with @ or - must be given as @path.')
    assert 'the value' not in help_text
    assert 'shell history' not in help_text


def test_auth_method_default_is_named_on_create_only():
    flag = '--authentication-method'
    assert _spec('wes', flag).help == 'How Workbench authenticates to the WES service. Defaults to oauth.'
    assert _spec('wes', flag, for_create=False).help == 'How Workbench authenticates to the WES service.'


@pytest.mark.parametrize('for_create', [True, False], ids=['create', 'update'])
@pytest.mark.parametrize('kind', ENGINE_KINDS, ids=lambda k: k.name)
def test_every_engine_option_help_ends_with_a_period(kind, for_create):
    assert [s.arg_names[0] for s in option_specs(kind, for_create) if not s.help.endswith('.')] == []


@pytest.mark.parametrize('for_create', [True, False], ids=['create', 'update'])
@pytest.mark.parametrize('kind', ENGINE_KINDS, ids=lambda k: k.name)
def test_no_option_sets_the_default(kind, for_create):
    assert [s for s in option_specs(kind, for_create) if s.name == 'default'] == []


def test_config_help_is_the_same_for_create_and_update():
    assert _spec('gcp', '--config').help == _spec('gcp', '--config', for_create=False).help
    assert 'Fields left out' not in _spec('gcp', '--config', for_create=False).help


@pytest.mark.parametrize('kind', ENGINE_KINDS, ids=lambda k: k.name)
def test_summaries_fit_the_command_list(kind):
    assert len(f'Create {kind.summary}') <= 45
    assert len(f'Update {kind.summary}') <= 45


def test_secrets_stay_out_of_the_description():
    values = {'secret_access_key': 'SECRET-AWS', 'role_arn': ROLE}
    engine = build_engine_description(_kind('aws'), None, values, for_create=True)
    assert 'secret_access_key' not in engine['engine_adapter_configuration']
    assert secret_options_from(_kind('aws'), values) == {'secret_access_key': 'SECRET-AWS'}


@pytest.mark.parametrize('name, secrets', [
    ('gcp', ['--service-account-json']),
    ('wes', ['--client-secret', '--client-key-and-certificate-chain']),
    ('azure', ['--client-secret']),
    ('aws', ['--secret-access-key']),
])
def test_each_kind_offers_only_its_secrets(name, secrets):
    flags = {f for s in option_specs(_kind(name), True) for f in s.arg_names}
    all_secrets = {'--service-account-json', '--client-secret', '--client-key-and-certificate-chain',
                   '--secret-access-key'}
    assert flags & all_secrets == set(secrets)


def test_only_wes_has_a_provider_option():
    for kind in ENGINE_KINDS:
        flags = {f for s in option_specs(kind, True) for f in s.arg_names}
        assert ('--provider' in flags) == (kind.name == 'wes')


def test_create_and_update_option_sets():
    create_flags = {f for s in option_specs(_kind('gcp'), True) for f in s.arg_names}
    update_flags = {f for s in option_specs(_kind('gcp'), False) for f in s.arg_names}
    assert {'--config', '--id', '--name', '--region', '--url'} <= create_flags
    assert '--id' not in update_flags
    assert {'--config', '--name', '--region', '--url'} <= update_flags


def test_always_required_options_are_display_required_on_create_only():
    assert _spec('gcp', '--project-id').display_required
    assert not _spec('gcp', '--project-id', for_create=False).display_required
    assert 'Required' not in _spec('gcp', '--project-id').help
    assert 'Required' not in _spec('gcp', '--project-id', for_create=False).help
    assert not _spec('gcp', '--config').display_required


def test_has_changes():
    assert not has_changes(_kind('aws'), {'role_arn': None, 'secret_access_key': None}, for_create=False)
    assert has_changes(_kind('aws'), {'secret_access_key': 'x'}, for_create=False)
    assert has_changes(_kind('aws'), {'role_arn': ROLE}, for_create=False)


def test_null_nested_object_in_file_is_replaced():
    file = {'engine_adapter_configuration': {'type': 'WES_ON_CROMWELL', 'oauth_config': None}}
    engine = build_engine_description(_kind('wes'), file, {'client_id': 'x'}, for_create=True)
    assert engine['engine_adapter_configuration']['oauth_config'] == {'clientId': 'x'}


def test_non_object_nested_setting_in_file_rejected():
    file = {'engine_adapter_configuration': {'type': 'WES_ON_CROMWELL', 'ssl_config': 'x'}}
    values = {'server_certificate_chain': 'PEM'}
    with pytest.raises(EngineOptionError, match='engine_adapter_configuration.ssl_config must be an object'):
        build_engine_description(_kind('wes'), file, values, for_create=True)


@pytest.mark.parametrize('kind_name, secret_name, path', [
    ('gcp', 'service_account_json', 'engine_adapter_configuration.auth_config.service_account_json'),
    ('wes', 'client_secret', 'engine_adapter_configuration.oauth_config.clientSecret'),
    ('wes', 'client_key_and_certificate_chain',
     'engine_adapter_configuration.ssl_config.client_key_and_certificate_chain'),
    ('azure', 'client_secret', 'engine_adapter_configuration.client_secret'),
    ('aws', 'secret_access_key', 'engine_adapter_configuration.secret_access_key'),
])
def test_secret_paths(kind_name, secret_name, path):
    assert next(s.path for s in _kind(kind_name).secrets if s.name == secret_name) == path


def _create_specs_by_path(kind):
    flags = option_names(kind, for_create=True)
    specs = {flag: spec for spec in option_specs(kind, for_create=True) for flag in spec.arg_names}
    return {path: specs[flag] for path, flag in flags.items()}


@pytest.mark.parametrize('kind', ENGINE_KINDS, ids=lambda k: k.name)
def test_every_required_field_is_display_required_or_has_a_required_with_hint(kind):
    specs = _create_specs_by_path(kind)
    for method in WesOnCromwellAuthenticationMethod:
        for path in required_create_fields(kind.adapter_type.value, method.value):
            if path not in specs:
                # Fixed by the subcommand, like the provider of every type but wes.
                assert path == 'provider' and kind.provider
                continue
            spec = specs[path]
            assert spec.display_required or 'Required with' in spec.help, path


@pytest.mark.parametrize('kind', ENGINE_KINDS, ids=lambda k: k.name)
def test_display_required_options_are_the_fields_every_method_requires(kind):
    adapter_type = kind.adapter_type.value
    if kind.name == 'wes':
        expected = (set(required_create_fields(adapter_type, 'OAUTH'))
                    & set(required_create_fields(adapter_type, 'MTLS')))
    else:
        expected = set(required_create_fields(adapter_type, None))
    if kind.provider:
        expected.discard('provider')
    specs = _create_specs_by_path(kind)
    assert {path for path, spec in specs.items() if spec.display_required} == expected


@pytest.mark.parametrize('kind_name, flags', [
    ('gcp', ['--name', '--region', '--url', '--project-id', '--service-account-json']),
    ('azure', ['--name', '--region', '--url', '--tenant-id', '--client-id', '--client-secret',
               '--storage-account-name', '--storage-container-name']),
    ('aws', ['--name', '--region', '--access-key-id', '--secret-access-key', '--output-bucket', '--role-arn']),
    ('wes', ['--name', '--region', '--provider', '--url']),
])
def test_display_required_flags(kind_name, flags):
    specs = option_specs(_kind(kind_name), for_create=True)
    assert {s.arg_names[0] for s in specs if s.display_required} == set(flags)
    assert not any(s.display_required for s in option_specs(_kind(kind_name), for_create=False))


def _missing(kind_name, file=None, values=None):
    values = values or {}
    engine = build_engine_description(_kind(kind_name), file, values, for_create=True)
    return missing_create_options(_kind(kind_name), engine, values)


def test_missing_create_options_in_required_order():
    assert _missing('aws') == ['--name', '--region', '--access-key-id', '--secret-access-key', '--output-bucket',
                               '--role-arn']


def test_missing_create_options_counts_file_fields_and_secret_options():
    file = {'name': 'From file', 'engine_adapter_configuration': {'access_key_id': 'AKIA', 'role_arn': ROLE}}
    values = {'region': 'us-east-1', 'secret_access_key': 'SECRET-AWS'}
    assert _missing('aws', file, values) == ['--output-bucket']


def test_missing_create_options_treats_blank_values_as_missing():
    assert '--name' in _missing('aws', {'name': '  '})


def test_missing_create_options_wes_depends_on_the_auth_method():
    assert _missing('wes') == ['--name', '--provider', '--region', '--url', '--client-id', '--client-secret',
                               '--token-uri', '--resource', '--scope']
    assert _missing('wes', values={'authentication_method': 'mtls'}) == [
        '--name', '--provider', '--region', '--url', '--client-key-and-certificate-chain']


def test_option_names():
    names = option_names(_kind('aws'), for_create=True)
    assert names['id'] == '--id'
    assert names['engine_adapter_configuration.role_arn'] == '--role-arn'
    assert names['engine_adapter_configuration.secret_access_key'] == '--secret-access-key'
    assert 'id' not in option_names(_kind('aws'), for_create=False)


def test_with_article():
    assert with_article('aws') == 'an aws'
    assert with_article('gcp') == 'a gcp'


@pytest.mark.parametrize('kind_name, region_help', [
    ('gcp', 'The region for the engine.'),
    ('azure', 'The region for the engine.'),
    ('aws', 'The region for the engine.'),
    ('wes', 'The region for the engine. Use local with --provider local.'),
])
def test_region_help(kind_name, region_help):
    assert _spec(kind_name, '--region', for_create=False).help == region_help
    assert _spec(kind_name, '--region').help == region_help


def test_create_hint_follows_the_at_path_note():
    help_text = _spec('wes', '--client-key-and-certificate-chain').help
    assert help_text.endswith('A value that starts with @ or - must be given as @path. Required with '
                              '--authentication-method mtls, unless given in --config.')


def test_azure_container_option_sets_the_storage_container_name():
    engine = build_engine_description(_kind('azure'), None, {'storage_container_name': 'c'}, for_create=False)
    assert engine == {'engine_adapter_configuration': {'storage_container_name': 'c'}}


def test_default_in_config_is_dropped_and_warned_about_only_when_true(capsys):
    for value, warned in [(True, True), (False, False)]:
        for for_create in (True, False):
            engine = build_engine_description(_kind('aws'), {'default': value}, {}, for_create=for_create)
            assert 'default' not in engine
            assert ('Ignoring "default" in --config; use `set-default` to make an engine the default.'
                    in capsys.readouterr().err) == warned
