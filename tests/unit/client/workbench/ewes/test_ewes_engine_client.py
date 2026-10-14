"""Unit tests for the EWesClient engine and parameter preset write methods."""
import traceback
from http.client import HTTPConnection
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from dnastack.client.models import ServiceEndpoint
from dnastack.client.workbench.ewes.client import EWesClient, UnreadableEngineResponseError
from dnastack.client.workbench.ewes.engine_models import EngineParamPresetRequest, ExecutionEngineRequest
from dnastack.client.workbench.ewes.models import (
    EngineHealthCheckListOptions, EngineParamPreset, EngineParamPresetListOptions, ExecutionEngine,
    ExecutionEngineListOptions,
)
from dnastack.http.session import JsonPatch
from tests.unit.client.workbench.ewes.engine_fixtures import (
    GCP_ENGINE, as_service_response, engine,
)

BASE = 'https://api.example.com/'
NS = 'demo-ns'
PRESET_RESPONSE = {'id': 'p1', 'name': 'preset', 'default': False, 'preset_values': {'a': 1},
                   'engine_id': 'hifi-solves-cromwell', 'etag': 'e-1'}


@pytest.fixture
def session():
    with patch.object(EWesClient, 'create_http_session') as create_session:
        mock_session = MagicMock()
        create_session.return_value.__enter__ = Mock(return_value=mock_session)
        create_session.return_value.__exit__ = Mock(return_value=False)
        yield mock_session


@pytest.fixture
def client():
    return EWesClient(ServiceEndpoint(url=BASE), NS)


def _respond(method_mock, body):
    method_mock.return_value = Mock(json=Mock(return_value=body))


def test_create_engine(session, client):
    _respond(session.post, as_service_response(engine('gcp')))
    result = client.create_engine(ExecutionEngineRequest(**engine('gcp')))
    assert session.post.call_args.args[0] == f'{BASE}{NS}/engines'
    assert session.post.call_args.kwargs['json'] == GCP_ENGINE
    assert isinstance(result, ExecutionEngine)
    assert result.version == 'v-1'


def test_update_engine(session, client):
    _respond(session.put, as_service_response(engine('gcp')))
    client.update_engine('hifi-solves-cromwell', ExecutionEngineRequest(**engine('gcp')), if_match='v-1')
    assert session.put.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell'
    assert session.put.call_args.kwargs['headers'] == {'If-Match': 'v-1'}
    assert session.put.call_args.kwargs['json'] == GCP_ENGINE


def test_patch_engine(session, client):
    _respond(session.json_patch, as_service_response(engine('gcp')))
    client.patch_engine('hifi-solves-cromwell', [JsonPatch(op='replace', path='/default', value=True)], if_match='v-1')
    assert session.json_patch.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell'
    assert session.json_patch.call_args.kwargs['headers'] == {'If-Match': 'v-1'}
    assert session.json_patch.call_args.kwargs['json'] == [{'op': 'replace', 'path': '/default', 'value': True}]


def test_delete_engine(session, client):
    client.delete_engine('hifi-solves-cromwell')
    assert session.delete.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell'


def test_create_engine_param_preset(session, client):
    _respond(session.post, PRESET_RESPONSE)
    result = client.create_engine_param_preset('hifi-solves-cromwell',
                                               EngineParamPresetRequest(name='preset', preset_values={'a': 1}))
    assert session.post.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell/param-presets'
    assert session.post.call_args.kwargs['json'] == {'name': 'preset', 'default': False, 'preset_values': {'a': 1}}
    assert isinstance(result, EngineParamPreset)


def test_update_engine_param_preset(session, client):
    _respond(session.put, PRESET_RESPONSE)
    client.update_engine_param_preset('hifi-solves-cromwell', 'p1',
                                      EngineParamPresetRequest(name='preset', preset_values={'a': 1}), if_match='e-1')
    assert session.put.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell/param-presets/p1'
    assert session.put.call_args.kwargs['headers'] == {'If-Match': 'e-1'}


def test_patch_engine_param_preset(session, client):
    _respond(session.json_patch, PRESET_RESPONSE)
    client.patch_engine_param_preset('hifi-solves-cromwell', 'p1',
                                     [JsonPatch(op='replace', path='/default', value=True)], if_match='e-1')
    assert session.json_patch.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell/param-presets/p1'
    assert session.json_patch.call_args.kwargs['headers'] == {'If-Match': 'e-1'}


def test_delete_engine_param_preset(session, client):
    client.delete_engine_param_preset('hifi-solves-cromwell', 'p1')
    assert session.delete.call_args.args[0] == f'{BASE}{NS}/engines/hifi-solves-cromwell/param-presets/p1'


ODD_ID = 'a/../b#c?d'
ODD_SEGMENT = 'a%2F..%2Fb%23c%3Fd'


def test_engine_id_is_one_path_segment(session, client):
    client.delete_engine(ODD_ID)
    assert session.delete.call_args.args[0] == f'{BASE}{NS}/engines/{ODD_SEGMENT}'


@pytest.mark.parametrize('bad_id', ['', '.', '..'])
def test_engine_id_that_cannot_be_one_segment_is_rejected(session, client, bad_id):
    with pytest.raises(ValueError):
        client.delete_engine(bad_id)
    session.delete.assert_not_called()


def test_preset_id_that_cannot_be_one_segment_is_rejected(session, client):
    with pytest.raises(ValueError):
        client.delete_engine_param_preset('eng', '..')
    session.delete.assert_not_called()


def test_escaped_engine_url_survives_requests_requoting(client):
    url = client._engine_url(ODD_ID)
    assert requests.Request('DELETE', url).prepare().url.endswith(f'/engines/{ODD_SEGMENT}')


def test_get_engine_escapes_id(session, client):
    _respond(session.get, as_service_response(engine('gcp')))
    client.get_engine(ODD_ID)
    assert session.get.call_args.args[0] == f'{BASE}{NS}/engines/{ODD_SEGMENT}'


def test_update_and_patch_engine_escape_id(session, client):
    _respond(session.put, as_service_response(engine('gcp')))
    _respond(session.json_patch, as_service_response(engine('gcp')))
    client.update_engine(ODD_ID, ExecutionEngineRequest(**engine('gcp')), if_match='v-1')
    client.patch_engine(ODD_ID, [JsonPatch(op='replace', path='/default', value=True)], if_match='v-1')
    assert session.put.call_args.args[0] == f'{BASE}{NS}/engines/{ODD_SEGMENT}'
    assert session.json_patch.call_args.args[0] == f'{BASE}{NS}/engines/{ODD_SEGMENT}'


def test_preset_methods_escape_both_ids(session, client):
    expected = f'{BASE}{NS}/engines/{ODD_SEGMENT}/param-presets/{ODD_SEGMENT}'
    _respond(session.get, PRESET_RESPONSE)
    _respond(session.put, PRESET_RESPONSE)
    _respond(session.json_patch, PRESET_RESPONSE)
    _respond(session.post, PRESET_RESPONSE)
    client.get_engine_param_preset(ODD_ID, ODD_ID)
    client.update_engine_param_preset(ODD_ID, ODD_ID, EngineParamPresetRequest(name='p', preset_values={'a': 1}),
                                      if_match='e-1')
    client.patch_engine_param_preset(ODD_ID, ODD_ID, [JsonPatch(op='replace', path='/default', value=True)],
                                     if_match='e-1')
    client.delete_engine_param_preset(ODD_ID, ODD_ID)
    client.create_engine_param_preset(ODD_ID, EngineParamPresetRequest(name='p', preset_values={'a': 1}))
    assert session.get.call_args.args[0] == expected
    assert session.put.call_args.args[0] == expected
    assert session.json_patch.call_args.args[0] == expected
    assert session.delete.call_args.args[0] == expected
    assert session.post.call_args.args[0] == f'{BASE}{NS}/engines/{ODD_SEGMENT}/param-presets'


def test_list_loaders_escape_engine_id(client):
    with patch.object(EWesClient, 'create_http_session'), \
            patch('dnastack.client.workbench.ewes.client.EngineParamPresetListResultLoader') as presets, \
            patch('dnastack.client.workbench.ewes.client.EngineHealthCheckListResultLoader') as checks:
        client.list_engine_param_presets(ODD_ID, EngineParamPresetListOptions())
        client.list_engine_health_checks(ODD_ID, EngineHealthCheckListOptions())
    assert presets.call_args.kwargs['service_url'] == f'{BASE}{NS}/engines/{ODD_SEGMENT}/param-presets'
    assert checks.call_args.kwargs['service_url'] == f'{BASE}{NS}/engines/{ODD_SEGMENT}/health-checks'


@pytest.mark.parametrize('call', [
    lambda c: c.get_engine('e'),
    lambda c: c.create_engine(ExecutionEngineRequest(**engine('gcp'))),
    lambda c: c.update_engine('e', ExecutionEngineRequest(**engine('gcp')), if_match='v-1'),
    lambda c: c.patch_engine('e', [JsonPatch(op='replace', path='/default', value=True)], if_match='v-1'),
    lambda c: c.list_engines(ExecutionEngineListOptions()),
])
def test_engine_calls_do_not_log_response_bodies(client, call):
    with patch.object(EWesClient, 'create_http_session') as create_session:
        mock_session = MagicMock()
        mock_session.get.return_value.json.return_value = as_service_response(engine('gcp'))
        mock_session.post.return_value.json.return_value = as_service_response(engine('gcp'))
        mock_session.put.return_value.json.return_value = as_service_response(engine('gcp'))
        mock_session.json_patch.return_value.json.return_value = as_service_response(engine('gcp'))
        create_session.return_value.__enter__ = Mock(return_value=mock_session)
        create_session.return_value.__exit__ = Mock(return_value=False)
        call(client)
    assert create_session.call_args.kwargs == {'log_response_body': False}


def _unreadable_engine():
    """An engine response that fails validation: no name, an unknown provider, and a secret in its body."""
    body = as_service_response(engine('aws'))
    del body['name']
    body['provider'] = 'SECRET-PROVIDER'
    return body


def _unreadable_preset():
    body = {k: v for k, v in PRESET_RESPONSE.items() if k != 'name'}
    body['preset_values'] = {'token': 'SECRET-PRESET'}
    body['default'] = 'SECRET-DEFAULT'
    return body


@pytest.mark.parametrize('method, call, response', [
    ('post', lambda c: c.create_engine(ExecutionEngineRequest(**engine('aws'))), _unreadable_engine),
    ('put', lambda c: c.update_engine('aws-engine', ExecutionEngineRequest(**engine('aws')), if_match='v-1'),
     _unreadable_engine),
    ('json_patch', lambda c: c.patch_engine('aws-engine', [], if_match='v-1'), _unreadable_engine),
    ('post', lambda c: c.create_engine_param_preset(
        'e', EngineParamPresetRequest(name='p', preset_values={})), _unreadable_preset),
    ('put', lambda c: c.update_engine_param_preset(
        'e', 'p1', EngineParamPresetRequest(name='p', preset_values={}), if_match='e-1'), _unreadable_preset),
    ('json_patch', lambda c: c.patch_engine_param_preset('e', 'p1', [], if_match='e-1'), _unreadable_preset),
])
def test_unreadable_write_response_is_reported_without_its_values(session, client, method, call, response):
    _respond(getattr(session, method), response())
    with pytest.raises(UnreadableEngineResponseError) as raised:
        call(client)
    message = str(raised.value)
    assert message.startswith('The engines service returned ')
    assert 'this CLI cannot read: ' in message
    assert 'name: Field required' in message
    rendered = ''.join(traceback.format_exception(raised.value))
    for secret in ['SECRET-AWS', 'SECRET-PROVIDER', 'SECRET-PRESET', 'SECRET-DEFAULT']:
        assert secret not in rendered


def test_unreadable_engine_response_names_each_field(session, client):
    _respond(session.post, _unreadable_engine())
    with pytest.raises(UnreadableEngineResponseError) as raised:
        client.create_engine(ExecutionEngineRequest(**engine('aws')))
    message = str(raised.value)
    assert message.startswith('The engines service returned an engine this CLI cannot read: ')
    assert 'name: ' in message and 'provider: ' in message


@pytest.fixture
def wire_debugging():
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1
    yield
    HTTPConnection.debuglevel = saved


def _record_debuglevel(method_mock, body):
    seen = []

    def side_effect(*args, **kwargs):
        seen.append(HTTPConnection.debuglevel)
        return Mock(json=Mock(return_value=body))

    method_mock.side_effect = side_effect
    return seen


def test_create_engine_turns_wire_debugging_off_for_the_request(session, client, wire_debugging):
    seen = _record_debuglevel(session.post, as_service_response(engine('gcp')))
    client.create_engine(ExecutionEngineRequest(**engine('gcp')))
    assert seen == [0]
    assert HTTPConnection.debuglevel == 1


def test_update_engine_turns_wire_debugging_off_for_the_request(session, client, wire_debugging):
    seen = _record_debuglevel(session.put, as_service_response(engine('gcp')))
    client.update_engine('hifi-solves-cromwell', ExecutionEngineRequest(**engine('gcp')), if_match='v-1')
    assert seen == [0]
    assert HTTPConnection.debuglevel == 1


def test_wire_debugging_is_restored_when_the_request_fails(session, client, wire_debugging):
    session.post.side_effect = RuntimeError('boom')
    session.put.side_effect = RuntimeError('boom')
    with pytest.raises(RuntimeError):
        client.create_engine(ExecutionEngineRequest(**engine('gcp')))
    assert HTTPConnection.debuglevel == 1
    with pytest.raises(RuntimeError):
        client.update_engine('hifi-solves-cromwell', ExecutionEngineRequest(**engine('gcp')), if_match='v-1')
    assert HTTPConnection.debuglevel == 1
