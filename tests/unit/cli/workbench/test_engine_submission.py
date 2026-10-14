"""Unit tests for creating an engine from a description, the path every create command shares."""
from unittest.mock import Mock

import pytest

from dnastack.cli.commands.workbench.engines.engine_input import EngineInputError
from dnastack.cli.commands.workbench.engines.engine_submission import (
    create_engine_from_description, prepare_engine_create, prepare_engine_update, update_engine_from_description,
)
from dnastack.client.workbench.ewes.models import ExecutionEngine
from dnastack.http.session import ClientError
from tests.unit.client.workbench.ewes.engine_fixtures import as_service_response, engine


def _client():
    client = Mock()
    client.namespace = 'demo-ns'
    client.get_engine.side_effect = ClientError(Mock(status_code=404, text='not found'))
    client.create_engine.side_effect = lambda request: ExecutionEngine(**as_service_response(request.to_request_body()))
    return client


def test_creates_from_a_description_without_the_cli():
    client = _client()
    data = engine('aws')
    del data['id']
    created = create_engine_from_description(client, prepare_engine_create(data))
    assert client.create_engine.call_args.args[0].id == 'aws-healthomics'
    assert created.id == 'aws-healthomics'


def test_create_sends_the_prepared_request():
    client = _client()
    request = prepare_engine_create(engine('aws'))
    create_engine_from_description(client, request)
    assert client.create_engine.call_args.args[0] is request


def test_prepare_create_refuses_placeholder_secrets():
    data = engine('aws')
    data['engine_adapter_configuration']['secret_access_key'] = '***'
    with pytest.raises(EngineInputError) as error:
        prepare_engine_create(data, option_names={
            'engine_adapter_configuration.secret_access_key': '--secret-access-key'})
    assert "  - --secret-access-key must be the real secret, not the '***' placeholder." in str(error.value)


def test_create_secret_option_lands_in_the_request():
    client = _client()
    data = engine('aws')
    del data['engine_adapter_configuration']['secret_access_key']
    create_engine_from_description(client, prepare_engine_create(data, {'secret_access_key': 'FROM-OPTION'}))
    body = client.create_engine.call_args.args[0].to_request_body()
    assert body['engine_adapter_configuration']['secret_access_key'] == 'FROM-OPTION'


def test_reports_every_problem_and_sends_nothing():
    client = _client()
    data = engine('aws')
    del data['engine_adapter_configuration']['role_arn']
    with pytest.raises(EngineInputError) as error:
        prepare_engine_create(data)
    assert 'engine_adapter_configuration.role_arn is required.' in str(error.value)
    client.get_engine.assert_not_called()


def _client_with_stored(stored):
    client = _client()
    client.get_engine.side_effect = None
    client.get_engine.return_value = ExecutionEngine(**as_service_response(stored))
    client.update_engine.side_effect = (
        lambda engine_id, engine, if_match: ExecutionEngine(
            **as_service_response({**stored, **engine.to_request_body()})))
    return client


def test_update_puts_a_wes_secret_where_the_stored_method_needs_it():
    client = _client_with_stored(engine('wes_mtls'))
    description, secret_values = prepare_engine_update('wes-mtls', {'name': 'Renamed'},
                                                       {'client_key_and_certificate_chain': 'NEW-PEM'})
    update_engine_from_description(client, 'wes-mtls', description, secret_values=secret_values)
    body = client.update_engine.call_args.kwargs['engine'].to_request_body()
    assert body['engine_adapter_configuration']['authentication_method'] == 'MTLS'
    assert body['engine_adapter_configuration']['ssl_config']['client_key_and_certificate_chain'] == 'NEW-PEM'


def test_update_rejects_a_different_type_with_the_right_subcommand():
    client = _client_with_stored(engine('gcp'))
    engine_id = engine('gcp')['id']
    with pytest.raises(EngineInputError) as error:
        update_engine_from_description(client, engine_id, {'name': 'Renamed'}, adapter_type='AWS_HEALTH_OMICS')
    assert str(error.value) == (f"Engine '{engine_id}' is a gcp engine; "
                                f"use 'omics workbench engines update gcp {engine_id}'.")
    client.update_engine.assert_not_called()


def test_update_of_an_engine_of_an_unknown_type_does_not_echo_it():
    stored = engine('gcp')
    stored['engine_adapter_configuration']['type'] = 'SECRET-TYPE'
    client = _client_with_stored(stored)
    with pytest.raises(EngineInputError) as error:
        update_engine_from_description(client, stored['id'], {'name': 'Renamed'}, adapter_type='AWS_HEALTH_OMICS')
    assert str(error.value) == f"Engine '{stored['id']}' is not an aws engine."


def test_prepare_update_rejects_an_id_mismatch():
    with pytest.raises(EngineInputError) as error:
        prepare_engine_update('engine-a', {'id': 'engine-b'})
    assert str(error.value) == "The id in --config ('engine-b') does not match the engine id ('engine-a')."


def test_prepare_update_reads_secrets_and_sets_the_id():
    description, secret_values = prepare_engine_update('engine-a', {'name': 'N'},
                                                       {'client_secret': 'S', 'service_account_json': None})
    assert description == {'name': 'N', 'id': 'engine-a'}
    assert secret_values == {'client_secret': 'S'}


def test_update_with_matching_type_proceeds():
    client = _client_with_stored(engine('gcp'))
    update_engine_from_description(client, engine('gcp')['id'], {'name': 'Renamed'},
                                   adapter_type='GCP_CLOUD_RUN_CROMWELL')
    client.update_engine.assert_called_once()


def test_problems_name_the_option_that_sets_the_field():
    data = engine('aws')
    del data['engine_adapter_configuration']['role_arn']
    data['region'] = ' '
    data['id'] = 'x'
    names = {'id': '--id', 'region': '--region', 'engine_adapter_configuration.role_arn': '--role-arn'}
    with pytest.raises(EngineInputError) as error:
        prepare_engine_create(data, option_names=names)
    message = str(error.value)
    assert '  - --region is required.' in message
    assert '  - --role-arn is required.' in message
    assert "  - --id must start with a letter or digit" in message
    assert 'engine_adapter_configuration.role_arn' not in message


def test_single_segment_paths_are_replaced_only_at_the_start():
    data = engine('aws')
    data['id'] = 'x'
    with pytest.raises(EngineInputError) as error:
        prepare_engine_create(data, option_names={'id': '--id', 'digit': '--digit'})
    assert "--id must start with a letter or digit, hold only letters, digits and '-'" in str(error.value)


def test_longer_paths_are_replaced_first():
    data = engine('wes_oauth')
    data['engine_adapter_configuration']['ssl_config'] = {}
    names = {'engine_adapter_configuration.ssl_config': '--wrong',
             'engine_adapter_configuration.ssl_config.server_certificate_chain': '--server-certificate-chain'}
    with pytest.raises(EngineInputError) as error:
        prepare_engine_create(data, option_names=names)
    assert '  - --server-certificate-chain is required.' in str(error.value)


def test_already_exists_names_the_update_subcommand():
    client = _client_with_stored(engine('azure'))
    with pytest.raises(EngineInputError) as error:
        create_engine_from_description(client, prepare_engine_create(engine('azure')))
    assert str(error.value) == ("Engine 'azure-cromwell' already exists in namespace 'demo-ns'. "
                                "Use 'omics workbench engines update azure azure-cromwell' to change it.")
    client.create_engine.assert_not_called()


def test_update_problem_names_the_option():
    client = _client_with_stored(engine('gcp'))
    with pytest.raises(EngineInputError) as error:
        update_engine_from_description(client, engine('gcp')['id'],
                                       {'engine_adapter_configuration': {'url': 'http://example.com'}},
                                       option_names={'engine_adapter_configuration.url': '--url'})
    assert '  - --url must use https://' in str(error.value)
    client.update_engine.assert_not_called()
