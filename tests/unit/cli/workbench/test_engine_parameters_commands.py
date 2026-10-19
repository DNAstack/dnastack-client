"""Unit tests for the engine parameter preset create, update, get-default, set-default and delete commands."""
import json
from unittest.mock import Mock, patch

from click.testing import CliRunner

from dnastack.cli.commands.workbench.engines import engines_command_group
from dnastack.client.workbench.ewes.models import EngineParamPreset

GET_CLIENT = 'dnastack.cli.commands.workbench.engines.parameters.get_ewes_client'
EXISTING = EngineParamPreset(id='p1', name='original', default=True, preset_values={'a': 1},
                             engine_id='eng', etag='e-1')


def _client():
    client = Mock()
    client.namespace = 'demo-ns'
    client.get_engine_param_preset.return_value = EXISTING
    client.create_engine_param_preset.return_value = EXISTING
    client.update_engine_param_preset.return_value = EXISTING
    client.patch_engine_param_preset.return_value = EXISTING
    client.list_engine_param_presets.return_value = iter([EXISTING])
    return client


def _invoke(args, input=None):
    return CliRunner(mix_stderr=False).invoke(engines_command_group, ['parameters'] + args, input=input)


def test_create(tmp_path):
    values = tmp_path / 'v.json'
    values.write_text(json.dumps({'cpu': 2}))
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['create', '--engine', 'eng', '--name', 'p', '--values', f'@{values}'])
    assert result.exit_code == 0, result.stderr
    call = client.create_engine_param_preset.call_args.kwargs
    assert call['engine_id'] == 'eng'
    assert call['preset'].to_request_body() == {'name': 'p', 'default': False, 'preset_values': {'cpu': 2}}


def test_create_rejects_the_default_flag():
    with patch(GET_CLIENT) as get_client:
        result = _invoke(['create', '--engine', 'eng', '--name', 'p', '--values', '{"a": 1}', '--default'])
    assert result.exit_code == 2
    assert 'No such option: --default' in result.stderr
    get_client.assert_not_called()


def test_create_values_must_be_object():
    with patch(GET_CLIENT, return_value=_client()):
        result = _invoke(['create', '--engine', 'eng', '--name', 'p', '--values', '[1]'])
    assert result.exit_code == 2
    assert 'Usage:' in result.stderr
    assert "Error: Invalid value for '--values': must be a JSON object" in result.stderr


def test_update_fills_unspecified_fields():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['update', 'p1', '--engine', 'eng', '--name', 'renamed'])
    assert result.exit_code == 0, result.stderr
    call = client.update_engine_param_preset.call_args.kwargs
    assert call['param_preset_id'] == 'p1'
    assert call['if_match'] == 'e-1'
    assert call['preset'].to_request_body() == {'name': 'renamed', 'default': True, 'preset_values': {'a': 1}}


def test_update_values():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['update', 'p1', '--engine', 'eng', '--values', '{"b": 2}'])
    assert result.exit_code == 0, result.stderr
    assert client.update_engine_param_preset.call_args.kwargs['preset'].preset_values == {'b': 2}


def test_set_default():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['set-default', 'p1', '--engine', 'eng'])
    assert result.exit_code == 0, result.stderr
    call = client.patch_engine_param_preset.call_args.kwargs
    assert call['if_match'] == 'e-1'
    assert [p.model_dump(exclude_none=True) for p in call['patches']] == [
        {'op': 'replace', 'path': '/default', 'value': True}]


def test_delete_aborts_on_no():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['delete', 'p1', '--engine', 'eng'], input='n\n')
    assert result.exit_code == 0
    client.delete_engine_param_preset.assert_not_called()


def test_delete_force():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['delete', 'p1', '--engine', 'eng', '--force'])
    assert result.exit_code == 0, result.stderr
    client.delete_engine_param_preset.assert_called_once_with(engine_id='eng', param_preset_id='p1')


OTHER = EngineParamPreset(id='p2', name='other', default=False, preset_values={'b': 2}, engine_id='eng', etag='e-2')


def test_delete_default_preset_with_others_is_refused():
    client = _client()
    client.list_engine_param_presets.return_value = iter([EXISTING, OTHER])
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['delete', 'p1', '--engine', 'eng', '--force'])
    assert result.exit_code == 1
    assert "Preset 'p1' is the default for engine 'eng'" in result.stderr
    assert 'omics workbench engines parameters set-default' in result.stderr
    client.delete_engine_param_preset.assert_not_called()


def test_delete_non_default_preset():
    client = _client()
    client.get_engine_param_preset.return_value = OTHER
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['delete', 'p2', '--engine', 'eng', '--force'])
    assert result.exit_code == 0, result.stderr
    client.list_engine_param_presets.assert_not_called()


def test_create_rejects_empty_values():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['create', '--engine', 'eng', '--name', 'p', '--values', '{}'])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--values': must not be empty" in result.stderr
    client.create_engine_param_preset.assert_not_called()


def test_update_rejects_empty_values():
    client = _client()
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['update', 'p1', '--engine', 'eng', '--values', '{}'])
    assert result.exit_code == 2
    assert "Error: Invalid value for '--values': must not be empty" in result.stderr
    client.update_engine_param_preset.assert_not_called()


def test_create_rejects_the_old_set_default_flag():
    result = _invoke(['create', '--engine', 'eng', '--name', 'p', '--values', '{"a": 1}', '--set-default'])
    assert result.exit_code == 2
    assert 'No such option' in result.stderr


def _flat_help(args):
    result = CliRunner().invoke(engines_command_group, args + ['--help'])
    assert result.exit_code == 0, result.output
    return ' '.join(result.output.split())


def test_parameters_group_summaries():
    flat = _flat_help(['parameters'])
    for summary in ("list List an engine's parameter presets", 'describe Describe one or more parameter presets',
                    "get-default Get an engine's default parameter preset",
                    "set-default Set an engine's default parameter preset"):
        assert summary in flat


def test_values_help():
    values_help = ('The parameter values the preset supplies, as a non-empty JSON object of parameter name to value: '
                   '@path/to/values.json, inline JSON, or - to read stdin.')
    assert values_help in _flat_help(['parameters', 'create'])
    assert (f"{values_help} Defaults to the current values. Replaces all of the preset's values."
            in _flat_help(['parameters', 'update']))


def test_delete_help_explains_the_default_preset():
    output = CliRunner().invoke(engines_command_group, ['parameters', 'delete', '--help']).output
    assert ("\n\nDelete an engine parameter preset\n\nThe engine's default preset cannot be deleted while other "
            'presets exist.\n') in output
    listing = _flat_help(['parameters'])
    assert 'delete Delete an engine parameter preset ' in listing
    assert 'Delete an engine parameter preset.' not in listing


def test_update_with_nothing_to_change_is_a_usage_error():
    with patch(GET_CLIENT) as get_client:
        result = _invoke(['update', 'p1', '--engine', 'eng'])
    assert result.exit_code == 2
    assert 'Usage:' in result.stderr
    assert 'Error: Nothing to update: pass --name or --values.' in result.stderr
    get_client.assert_not_called()


def test_create_help_says_the_first_preset_becomes_the_default():
    output = CliRunner().invoke(engines_command_group, ['parameters', 'create', '--help']).output
    assert ('\n\nCreate an engine parameter preset\n\nThe first preset of an engine always becomes the default. '
            'Use `set-default` to change it.\n' in output)
    assert '--default' not in output


def test_list_and_describe_engine_option_names_parameter_presets():
    assert 'Specify the engine whose parameter presets should be listed.' in _flat_help(['parameters', 'list'])
    assert 'Specify the engine whose parameter presets should be described.' in _flat_help(['parameters', 'describe'])


def test_parameters_group_help_has_no_surrounding_spaces():
    assert 'parameters Manage engine parameter presets' in _flat_help([])
    assert engines_command_group.commands['parameters'].help == 'Manage engine parameter presets'


# get-default


def _preset(preset_id, default):
    return EngineParamPreset(id=preset_id, name=preset_id, default=default, preset_values={'a': 1},
                             engine_id='eng', etag='e-1')


def _client_listing(*presets):
    client = _client()
    client.list_engine_param_presets.return_value = iter(presets)
    return client


def test_get_default_prints_the_default_preset():
    # The default is the second preset listed, as when it is on the second page.
    client = _client_listing(_preset('p0', False), _preset('p1', True))
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['get-default', '--engine', 'eng'])
    assert result.exit_code == 0, result.stderr
    printed = json.loads(result.stdout)
    assert isinstance(printed, dict)
    assert (printed['id'], printed['default'], printed['preset_values']) == ('p1', True, {'a': 1})
    assert client.list_engine_param_presets.call_args.args[0] == 'eng'


def test_get_default_id_prints_only_the_id():
    client = _client_listing(_preset('p0', False), _preset('p1', True))
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['get-default', '--engine', 'eng', '--id'])
    assert result.exit_code == 0, result.stderr
    assert result.stdout == 'p1\n'


def test_get_default_without_a_default_preset_fails():
    client = _client_listing(_preset('p0', False))
    with patch(GET_CLIENT, return_value=client):
        result = _invoke(['get-default', '--engine', 'eng'])
    assert result.exit_code == 1
    assert "Engine 'eng' has no default parameter preset." in result.stderr
    assert result.stdout == ''


def test_get_default_requires_the_engine():
    result = _invoke(['get-default'])
    assert result.exit_code == 2
    assert "Missing option '--engine'" in result.stderr


def test_get_default_help():
    flat = _flat_help(['parameters', 'get-default'])
    assert "Get an engine's default parameter preset" in flat
    assert 'Specify the engine whose default parameter preset should be shown.' in flat
    assert 'Only output the preset id' in flat
