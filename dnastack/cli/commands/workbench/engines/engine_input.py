"""Turns the engine CLI arguments into a request, without ever echoing a secret.

Every error raised here is an EngineInputError whose message is safe to print: it names files,
options, field paths and identifiers such as the engine name, never values that may be secret.
A problem with one option's value is an EngineOptionError, which click reports as a bad parameter.
"""
import copy
import json
from typing import Any, Dict, Optional, Tuple

import click
from pydantic import ValidationError

from dnastack.cli.commands.workbench.engines.engine_names import subcommand_for
from dnastack.client.workbench.ewes.engine_models import (
    ENGINE_ID_PATTERN, EngineAdapterType, ExecutionEngineRequest, WesOnCromwellAuthenticationMethod,
    derive_engine_id, drop_placeholder_secrets, get_field, set_field,
)
from dnastack.common.json_argument_parser import ArgumentType, FileOrValue, JsonLike

# Fields the service sets itself; dropped so that `describe` output can be edited and sent back.
SERVER_SET_FIELDS: Tuple[str, ...] = ('internal_id', 'version', 'created_at', 'updated_at', 'state', 'health')

_SERVICE_ACCOUNT_JSON = '--service-account-json'
_CLIENT_SECRET = '--client-secret'
_CLIENT_KEY_AND_CERTIFICATE_CHAIN = '--client-key-and-certificate-chain'
_SECRET_ACCESS_KEY = '--secret-access-key'
# The option each apply_secret_flags parameter stands for.
_SECRET_FLAGS = {
    'service_account_json': _SERVICE_ACCOUNT_JSON,
    'client_secret': _CLIENT_SECRET,
    'client_key_and_certificate_chain': _CLIENT_KEY_AND_CERTIFICATE_CHAIN,
    'secret_access_key': _SECRET_ACCESS_KEY,
}


def _as_sentence(message: str) -> str:
    return message if message.endswith('.') else f'{message}.'


class EngineInputError(Exception):
    """An invalid engine argument. The message never contains secret values, and always ends with a period."""

    def __init__(self, message: str):
        super().__init__(_as_sentence(message))


class EngineOptionError(click.BadParameter, EngineInputError):
    """A bad value in one option. click prints it as "Invalid value for '<option>': <message>" and exits 2."""

    def __init__(self, message: str, option_name: str):
        click.BadParameter.__init__(self, _as_sentence(message), param_hint=f"'{option_name}'")


def _parse_json(value: JsonLike, option_name: str) -> Any:
    try:
        return value.parsed_value()
    except OSError as e:
        if value.argument_type == ArgumentType.FILE:
            raise EngineOptionError(f'cannot read {e.filename}: {e.strerror}', option_name) from None
        # In key=value syntax the "filename" is text the user typed after '@', which may be a secret.
        raise EngineOptionError(f'cannot read a file it refers to: {e.strerror}', option_name) from None
    except json.JSONDecodeError as e:
        raise EngineOptionError(f'invalid JSON at line {e.lineno} column {e.colno}', option_name) from None
    except Exception:
        # Other parse errors (key=value syntax, a "-x" that is not stdin) can quote the input, which may hold
        # a secret, so the message is replaced rather than passed on.
        raise EngineOptionError('could not parse the value', option_name) from None


def load_json_object(value: JsonLike, option_name: str) -> Dict[str, Any]:
    parsed = _parse_json(value, option_name)
    if not isinstance(parsed, dict):
        raise EngineOptionError('must be a JSON object', option_name)
    return parsed


def load_engine_object(value: JsonLike) -> Dict[str, Any]:
    """Load an engine from --config: a JSON object, or the one-element list that `describe` prints."""
    parsed = _parse_json(value, '--config')
    if isinstance(parsed, list):
        if len(parsed) != 1:
            raise EngineOptionError('must be a JSON object, or a list holding exactly one engine', '--config')
        parsed = parsed[0]
    if not isinstance(parsed, dict):
        raise EngineOptionError('must be a JSON object', '--config')
    return parsed


def fill_engine_id(engine: Dict[str, Any]) -> Dict[str, Any]:
    """Derive a missing id from the name the way the Workbench UI does.

    Sending the id ourselves means a re-run create finds the engine it made and stops, where the
    service would generate a new random id and create a duplicate.
    """
    name = engine.get('name')
    if engine.get('id') or not isinstance(name, str):
        return engine
    engine_id = derive_engine_id(name)
    if not ENGINE_ID_PATTERN.fullmatch(engine_id):
        raise EngineInputError(f"Cannot derive an engine id from the name '{name}': the id must be at least 3 "
                               "characters, starting with a letter or digit, using only letters, digits and '-'. "
                               "Pass --id.")
    return {**engine, 'id': engine_id}


def _secret_targets(adapter_type: str, authentication_method: str) -> Dict[str, str]:
    """Which secret options apply to an adapter type, and the field each one sets."""
    if adapter_type == EngineAdapterType.GCP_CLOUD_RUN_CROMWELL.value:
        return {_SERVICE_ACCOUNT_JSON: 'auth_config.service_account_json'}
    if adapter_type == EngineAdapterType.AZURE_CONTAINER_APP_CROMWELL.value:
        return {_CLIENT_SECRET: 'client_secret'}
    if adapter_type == EngineAdapterType.AWS_HEALTH_OMICS.value:
        return {_SECRET_ACCESS_KEY: 'secret_access_key'}
    if adapter_type == EngineAdapterType.WES_ON_CROMWELL.value:
        if authentication_method == WesOnCromwellAuthenticationMethod.MTLS.value:
            return {_CLIENT_KEY_AND_CERTIFICATE_CHAIN: 'ssl_config.client_key_and_certificate_chain'}
        return {_CLIENT_SECRET: 'oauth_config.clientSecret'}
    return {}


def _service_account_json(content: str) -> str:
    try:
        key = json.loads(content)
    except json.JSONDecodeError as e:
        raise EngineOptionError(f'invalid JSON at line {e.lineno} column {e.colno}', _SERVICE_ACCOUNT_JSON) from None
    if not isinstance(key, dict):
        raise EngineOptionError('must be a JSON object', _SERVICE_ACCOUNT_JSON)
    return json.dumps(key)


def read_option_text(option_name: str, raw: str, verbatim: bool) -> str:
    """An option's text, given inline, as @path to a file, or as - to read stdin. The value may be a secret,
    so it never appears in an error.

    A verbatim value (a PEM bundle, which is multi-line) is kept as it is; otherwise trailing whitespace,
    such as the newline an editor or `echo` adds, is removed.
    """
    try:
        content = FileOrValue(raw).value()
    except OSError as e:
        # An inline value may itself start with '@', so the unreadable "path" is not echoed.
        raise EngineOptionError(f'cannot read the file: {e.strerror}', option_name) from None
    except UnicodeDecodeError:
        raise EngineOptionError('the file is not text', option_name) from None
    except ValueError:
        # FileOrValue raises this when asked to read stdin from a terminal.
        raise EngineOptionError('nothing to read from stdin', option_name) from None
    if content is None:
        # FileOrValue treats anything starting with '-' as stdin, and reads only a bare '-'.
        raise EngineOptionError('values starting with "-" are read from stdin; put the value in a file and '
                                'pass @path', option_name)
    value = content if verbatim else content.rstrip()
    if not value.strip():
        raise EngineOptionError('the value is empty', option_name)
    return value


def _read_secret(option_name: str, raw: str) -> str:
    """A secret option's value, given inline, as @path to a file, or as - to read stdin."""
    if option_name == _SERVICE_ACCOUNT_JSON:
        return _service_account_json(read_option_text(option_name, raw, verbatim=True))
    return read_option_text(option_name, raw, verbatim=option_name == _CLIENT_KEY_AND_CERTIFICATE_CHAIN)


def read_secret_options(secret_options: Dict[str, Optional[str]]) -> Dict[str, str]:
    """Read each given secret option (inline, @path, or -), keyed by its apply_secret_flags parameter name.

    This only reads the values, so an unreadable one is reported before anything is fetched from the service;
    pass the result to apply_secret_flags with already_read=True.
    """
    return {name: _read_secret(_SECRET_FLAGS[name], raw) for name, raw in secret_options.items() if raw is not None}


def _require_object_parents(adapter: Dict[str, Any], path: str) -> None:
    parents = path.split('.')[:-1]
    node: Any = adapter
    for i, key in enumerate(parents):
        node = node.get(key)
        if node is None:
            return
        if not isinstance(node, dict):
            raise EngineInputError(f"engine_adapter_configuration.{'.'.join(parents[:i + 1])} must be an object")


def apply_secret_flags(engine: Dict[str, Any],
                       service_account_json: Optional[str] = None,
                       client_secret: Optional[str] = None,
                       client_key_and_certificate_chain: Optional[str] = None,
                       secret_access_key: Optional[str] = None,
                       already_read: bool = False) -> Dict[str, Any]:
    """Return a copy of the engine with each given secret option written into its field.

    The values are raw option values (inline, @path, or -), or the output of read_secret_options with
    already_read=True.
    """
    options = {
        _SERVICE_ACCOUNT_JSON: service_account_json,
        _CLIENT_SECRET: client_secret,
        _CLIENT_KEY_AND_CERTIFICATE_CHAIN: client_key_and_certificate_chain,
        _SECRET_ACCESS_KEY: secret_access_key,
    }
    given = {name: raw for name, raw in options.items() if raw is not None}
    if not given:
        return engine

    if not isinstance(engine.get('engine_adapter_configuration', {}), dict):
        raise EngineInputError('engine_adapter_configuration must be an object')
    adapter_type = get_field(engine, 'engine_adapter_configuration.type')
    if not adapter_type:
        raise EngineOptionError('engine_adapter_configuration.type must be set in --config to use this option',
                                next(iter(given)))
    authentication_method = (get_field(engine, 'engine_adapter_configuration.authentication_method')
                             or WesOnCromwellAuthenticationMethod.OAUTH.value)
    # Only a valid method is named in a message: anything else in --config may be a pasted secret.
    method_is_valid = (isinstance(authentication_method, str)
                       and authentication_method in {m.value for m in WesOnCromwellAuthenticationMethod})
    if not isinstance(adapter_type, str) or adapter_type not in {t.value for t in EngineAdapterType}:
        raise EngineInputError('engine_adapter_configuration.type must be one of '
                               + ', '.join(t.value for t in EngineAdapterType))
    targets = _secret_targets(adapter_type, authentication_method)

    result = copy.deepcopy(engine)
    adapter = result['engine_adapter_configuration']
    for option_name, raw in given.items():
        if option_name not in targets:
            engine_kind = f'{subcommand_for(adapter_type)} engines'
            if adapter_type == EngineAdapterType.WES_ON_CROMWELL.value:
                engine_kind += (f' using {authentication_method.lower()} authentication' if method_is_valid
                                else ' using the authentication_method in --config')
            raise EngineOptionError(f'does not apply to {engine_kind}', option_name)
        _require_object_parents(adapter, targets[option_name])
        set_field(adapter, targets[option_name], raw if already_read else _read_secret(option_name, raw))
    return result


def inherit_authentication_method(engine: Dict[str, Any],
                                  existing_adapter: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Copy a WES engine's stored authentication_method into an update that omits it.

    The service treats an omitted authentication_method as OAUTH rather than keeping the stored
    value, so an update of an MTLS engine would otherwise switch it to OAUTH.
    """
    adapter = engine.get('engine_adapter_configuration')
    stored_method = (existing_adapter or {}).get('authentication_method')
    if (not isinstance(adapter, dict)
            or adapter.get('type') != EngineAdapterType.WES_ON_CROMWELL.value
            or 'authentication_method' in adapter
            or not stored_method):
        return engine
    result = copy.deepcopy(engine)
    result['engine_adapter_configuration']['authentication_method'] = stored_method
    return result


def inherit_adapter_type(engine: Dict[str, Any], stored_type: Optional[str]) -> Dict[str, Any]:
    """Fill engine_adapter_configuration.type from the stored engine when an update leaves it out.

    The service cannot read an adapter configuration without its type, and refuses to change it.
    """
    adapter = engine.get('engine_adapter_configuration')
    if not stored_type or (adapter is not None and not isinstance(adapter, dict)):
        return engine
    config_type = (adapter or {}).get('type')
    if config_type and config_type != stored_type:
        raise EngineInputError(f'engine_adapter_configuration.type cannot be changed '
                               f'(stored: {stored_type}, --config: {config_type})')
    return {**engine, 'engine_adapter_configuration': {**(adapter or {}), 'type': stored_type}}


def follow_default_azure_scope(engine: Dict[str, Any], existing_adapter: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Keep an Azure engine's scope in step with a changed client_id when the scope is the default one.

    The stored scope is only replaced when it is exactly <stored client_id>/.default and the update gives a new
    client_id but no scope; any other scope is the user's choice and is kept.
    """
    adapter = engine.get('engine_adapter_configuration')
    stored = existing_adapter or {}
    if not isinstance(adapter, dict) or adapter.get('type') != EngineAdapterType.AZURE_CONTAINER_APP_CROMWELL.value:
        return engine
    new_client_id = adapter.get('client_id')
    stored_client_id = stored.get('client_id')
    if (not isinstance(new_client_id, str) or not new_client_id.strip() or new_client_id == stored_client_id
            or adapter.get('scope') is not None
            or not isinstance(stored_client_id, str) or stored.get('scope') != f'{stored_client_id}/.default'):
        return engine
    result = copy.deepcopy(engine)
    result['engine_adapter_configuration']['scope'] = f'{new_client_id}/.default'
    return result


def resolve_if_match(engine_id: str, config_version: Optional[str], stored_version: Optional[str]) -> Optional[str]:
    """The version an update is based on: --config's, so an edit of stale `describe` output is refused
    rather than overwriting a change made since. Without one, the stored version is used."""
    if config_version is None:
        return stored_version
    if str(config_version).lower() != str(stored_version).lower():
        raise EngineInputError(f"Engine '{engine_id}' has changed since that --config was written. "
                               f"Run 'omics workbench engines describe {engine_id}' again and reapply your edits.")
    return config_version


def _describe_loc(loc: Tuple[Any, ...]) -> str:
    # The adapter union adds its discriminator tag after the field name; it is noise in a path.
    tags = {t.value for t in EngineAdapterType}
    parts = [str(part) for i, part in enumerate(loc)
             if not (i > 0 and loc[i - 1] == 'engine_adapter_configuration' and part in tags)]
    return '.'.join(parts)


def _describe_error(error: Dict[str, Any]) -> str:
    if error['type'] == 'extra_forbidden':
        # The unknown key is not named: it may be a secret pasted in the wrong place.
        parent = _describe_loc(error['loc'][:-1]) or 'The engine description'
        return f'{parent} has a field this engine type does not use'
    loc = _describe_loc(error['loc'])
    if error['type'] == 'union_tag_invalid':
        # pydantic's message quotes the rejected type, so name the valid ones instead.
        return f"{loc}.type: must be one of {', '.join(t.value for t in EngineAdapterType)}"
    return f"{loc}: {error['msg']}"


def _describe_validation_error(error: ValidationError) -> str:
    # Built from loc and msg only: pydantic's own message includes the rejected input values.
    # Several unknown keys under one parent describe the same way, so each line is listed once.
    lines = [f'  - {line}' for line in dict.fromkeys(_as_sentence(_describe_error(e)) for e in error.errors())]
    return 'The engine description is not valid:\n' + '\n'.join(lines)


def parse_engine_request(engine: Dict[str, Any], for_update: bool) -> ExecutionEngineRequest:
    body = {key: value for key, value in engine.items() if key not in SERVER_SET_FIELDS}
    if for_update:
        body = drop_placeholder_secrets(body)
    if not get_field(body, 'engine_adapter_configuration.type'):
        raise EngineInputError('engine_adapter_configuration.type is required')
    try:
        return ExecutionEngineRequest(**body)
    except ValidationError as e:
        raise EngineInputError(_describe_validation_error(e)) from None
