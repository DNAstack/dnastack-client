"""Request models for creating and updating Workbench engines and their parameter presets.

These mirror the request body the engines service accepts. Reading engines still uses
`ExecutionEngine` from models.py, whose adapter configuration is a plain dict so that engines
of types this client does not model can still be listed and described.
"""
import copy
import json
import re
from enum import Enum
from typing import AbstractSet, Annotated, Any, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import unquote, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dnastack.client.workbench.ewes.models import ExecutionEngine, ExecutionEngineProviderType

SECRET_PLACEHOLDER = '***'

# Dotted paths, relative to engine_adapter_configuration, of every field holding a credential.
# The service never returns these; the CLI redacts them anyway in case that changes.
ENGINE_SECRET_FIELDS: List[str] = [
    'auth_config.service_account_json',
    'oauth_config.clientSecret',
    'client_secret',
    'secret_access_key',
    'ssl_config.client_key_and_certificate_chain',
]

# The Workbench UI's pattern. The service accepts more (e.g. 'ab' or '-x'); the CLI keeps to what the UI creates.
ENGINE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{2,}$')

# Dotted paths, relative to engine_adapter_configuration, of every field holding a URL. A user name or password
# in one is refused on input and masked on output.
ENGINE_URL_FIELDS: List[str] = ['url', 'oauth_config.tokenUri']

_URL_PROBLEM = 'engine_adapter_configuration.url must use https:// (http:// is only allowed for localhost)'
_LOCAL_HOSTS = ('localhost', '127.0.0.1')


class EngineAdapterType(str, Enum):
    WES_ON_CROMWELL = 'WES_ON_CROMWELL'
    GCP_CLOUD_RUN_CROMWELL = 'GCP_CLOUD_RUN_CROMWELL'
    AZURE_CONTAINER_APP_CROMWELL = 'AZURE_CONTAINER_APP_CROMWELL'
    AWS_HEALTH_OMICS = 'AWS_HEALTH_OMICS'


class WesOnCromwellAuthenticationMethod(str, Enum):
    OAUTH = 'OAUTH'
    MTLS = 'MTLS'


class _RequestModel(BaseModel):
    # Unknown fields are rejected so that a misspelled field (a secret especially) fails loudly
    # instead of being dropped, which on an update would silently keep the old value.
    model_config = ConfigDict(extra='forbid')

    def to_request_body(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True, mode='json')


class GcpAuthConfig(_RequestModel):
    service_account_json: Optional[str] = None

    @field_validator('service_account_json', mode='before')
    @classmethod
    def _serialize_key_object(cls, value: Any) -> Any:
        # The service stores the key as a JSON string; accept the parsed key object as well.
        if isinstance(value, dict):
            return json.dumps(value, separators=(',', ':'))
        return value


class GcpCloudRunCromwellEngineAdapterConfiguration(_RequestModel):
    type: Literal['GCP_CLOUD_RUN_CROMWELL']
    url: Optional[str] = None
    project_id: Optional[str] = None
    quota_project_id: Optional[str] = None
    auth_config: Optional[GcpAuthConfig] = None


class WesOnCromwellOAuthConfig(_RequestModel):
    # Unlike the rest of the engine body, the service reads this object in camelCase.
    client_id: Optional[str] = Field(default=None, alias='clientId')
    client_secret: Optional[str] = Field(default=None, alias='clientSecret')
    token_uri: Optional[str] = Field(default=None, alias='tokenUri')
    resource: Optional[str] = None
    scope: Optional[str] = None


class SslConfig(_RequestModel):
    server_certificate_chain: Optional[str] = None
    client_key_and_certificate_chain: Optional[str] = None


class WesOnCromwellEngineAdapterConfiguration(_RequestModel):
    type: Literal['WES_ON_CROMWELL']
    url: Optional[str] = None
    authentication_method: Optional[WesOnCromwellAuthenticationMethod] = None
    oauth_config: Optional[WesOnCromwellOAuthConfig] = None
    ssl_config: Optional[SslConfig] = None


class AzureContainerAppCromwellEngineAdapterConfiguration(_RequestModel):
    type: Literal['AZURE_CONTAINER_APP_CROMWELL']
    url: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scope: Optional[str] = None
    storage_account_name: Optional[str] = None
    storage_container_name: Optional[str] = None


class AwsHealthOmicsEngineAdapterConfiguration(_RequestModel):
    type: Literal['AWS_HEALTH_OMICS']
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    output_bucket: Optional[str] = None
    role_arn: Optional[str] = None


EngineAdapterConfiguration = Annotated[
    Union[
        GcpCloudRunCromwellEngineAdapterConfiguration,
        WesOnCromwellEngineAdapterConfiguration,
        AzureContainerAppCromwellEngineAdapterConfiguration,
        AwsHealthOmicsEngineAdapterConfiguration,
    ],
    Field(discriminator='type'),
]


class ExecutionEngineRequest(_RequestModel):
    """An engine as sent to create or update. Everything but the adapter type may be omitted,
    because an update keeps the stored value of every field left out."""
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[ExecutionEngineProviderType] = None
    region: Optional[str] = None
    default: Optional[bool] = None
    engine_adapter_configuration: EngineAdapterConfiguration


class EngineParamPresetRequest(_RequestModel):
    name: str
    default: bool = False
    preset_values: Dict[str, Any]


# Fields the service requires when creating each adapter type, as dotted paths in the request body.
_REQUIRED_ADAPTER_FIELDS: Dict[str, List[str]] = {
    EngineAdapterType.GCP_CLOUD_RUN_CROMWELL.value: ['url', 'project_id', 'auth_config.service_account_json'],
    EngineAdapterType.WES_ON_CROMWELL.value: ['url'],
    EngineAdapterType.AZURE_CONTAINER_APP_CROMWELL.value: [
        'url', 'tenant_id', 'client_id', 'client_secret', 'storage_account_name', 'storage_container_name',
    ],
    EngineAdapterType.AWS_HEALTH_OMICS.value: ['access_key_id', 'secret_access_key', 'output_bucket', 'role_arn'],
}

_REQUIRED_WES_AUTH_FIELDS: Dict[str, List[str]] = {
    WesOnCromwellAuthenticationMethod.OAUTH.value: [
        'oauth_config.clientId', 'oauth_config.clientSecret', 'oauth_config.tokenUri', 'oauth_config.resource',
        'oauth_config.scope',
    ],
    WesOnCromwellAuthenticationMethod.MTLS.value: ['ssl_config.client_key_and_certificate_chain'],
}


def required_create_fields(adapter_type: str, authentication_method: Optional[str]) -> List[str]:
    """The fields creating an engine of this adapter type requires, as dotted paths in the request body.

    authentication_method only matters for WES engines, where it defaults to OAUTH.
    """
    required = ['name', 'provider', 'region']
    adapter_fields = list(_REQUIRED_ADAPTER_FIELDS.get(adapter_type, []))
    if adapter_type == EngineAdapterType.WES_ON_CROMWELL.value:
        method = authentication_method or WesOnCromwellAuthenticationMethod.OAUTH.value
        adapter_fields += _REQUIRED_WES_AUTH_FIELDS.get(method, [])
    return required + [f'engine_adapter_configuration.{path}' for path in adapter_fields]


def get_field(data: Dict[str, Any], path: str) -> Any:
    value: Any = data
    for key in path.split('.'):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def set_field(data: Dict[str, Any], path: str, value: Any) -> None:
    *parents, leaf = path.split('.')
    for key in parents:
        data = data.setdefault(key, {})
    data[leaf] = value


def delete_field(data: Dict[str, Any], path: str) -> None:
    *parents, leaf = path.split('.')
    for key in parents:
        data = data.get(key)
        if not isinstance(data, dict):
            return
    data.pop(leaf, None)


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def derive_engine_id(name: str) -> str:
    """Derive an engine id from its name exactly as the Workbench UI does (convertNameToId).

    The service would instead append random letters, so a re-run create would make a new engine each time.
    """
    engine_id = re.sub(r'[^a-zA-Z0-9-]', '-', name.strip().lower())
    # After collapsing, at most one '-' is left at each end, which is all the UI removes.
    return re.sub(r'--+', '-', engine_id).strip('-')


def _is_allowed_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        # urlsplit rejects some malformed URLs (e.g. an unbalanced IPv6 bracket) outright.
        return False
    if parts.scheme == 'https':
        return bool(hostname)
    return parts.scheme == 'http' and hostname in _LOCAL_HOSTS


# A scheme and its '//', exactly as written. Anything else before the user info is masked along with it.
_SCHEME_AND_SLASHES = re.compile(r'[A-Za-z][A-Za-z0-9+.-]*://')


def _credentials_span(url: Any) -> Optional[Tuple[int, int]]:
    """Where the user info of a URL may be: from after the scheme's '//' up to the last '@'.

    Ending at the last '@' rather than at the first '/', '?' or '#' covers a password holding one of those, which
    urlsplit would read as the end of the host. When the URL does not start with a scheme and '//' (it may hold a
    character urlsplit strips, such as a tab), the span starts at the beginning of the text.
    """
    if not isinstance(url, str) or '@' not in url:
        return None
    scheme = _SCHEME_AND_SLASHES.match(url)
    return (scheme.end() if scheme else 0), url.rindex('@')


def mask_url_credentials(url: Any) -> Any:
    """The URL with everything between its scheme's '//' and its last '@' replaced by the placeholder, so no
    reading of the URL can find a password in what is shown. Anything else is kept as given."""
    span = _credentials_span(url)
    if span is None:
        return url
    start, end = span
    return url[:start] + SECRET_PLACEHOLDER + url[end:]


def url_credential_values(url: Any) -> List[str]:
    """Every form of a URL's user info and password that a service could echo: as written, as urlsplit reads it,
    and percent-decoded."""
    span = _credentials_span(url)
    if span is None:
        return []
    user_info = url[span[0]:span[1]]
    # When the last '@' is not the end of the user info, the part after ':' is some other piece of the URL, and
    # masking it only garbles the text; it is still masked, since it may be a password holding '/', '?' or '#'.
    values = [user_info, user_info.partition(':')[2]]
    try:
        values.append(urlsplit(url).password)
    except ValueError:
        pass
    values += [unquote(value) for value in values if value]
    return [value for value in dict.fromkeys(values) if value and value != SECRET_PLACEHOLDER]


def _userinfo_problem(path: str) -> str:
    return f"engine_adapter_configuration.{path} must not contain '@': a user name or password is not allowed"


def url_problems(adapter: Dict[str, Any], paths: Optional[AbstractSet[str]] = None) -> List[str]:
    """Check the URL fields: the UI only accepts https engine URLs, and plain http is allowed here for engines on
    this machine. paths limits the check to those fields (relative to engine_adapter_configuration).

    Any '@' is refused, since it may end a user name and password that urlsplit cannot see (one holding '/', '?'
    or '#', say), and the URL is never quoted.
    """
    problems = []
    for path in ENGINE_URL_FIELDS:
        url = get_field(adapter, path)
        if (paths is not None and path not in paths) or is_blank(url) or not isinstance(url, str):
            continue
        if '@' in url:
            problems.append(_userinfo_problem(path))
        elif path == 'url' and not _is_allowed_url(url):
            problems.append(_URL_PROBLEM)
    return problems


def _wes_method_problems(adapter: Dict[str, Any], method: str) -> List[str]:
    # The UI never sends the other method's credentials, so the service never stores a secret it will not use.
    if method == WesOnCromwellAuthenticationMethod.OAUTH.value:
        if get_field(adapter, 'ssl_config.client_key_and_certificate_chain') is not None:
            return ['engine_adapter_configuration.ssl_config.client_key_and_certificate_chain is only used with '
                    'MTLS authentication; remove it']
    elif adapter.get('oauth_config') is not None:
        return ['engine_adapter_configuration.oauth_config is only used with OAUTH authentication; remove it']
    return []


def validate_engine_for_create(engine: ExecutionEngineRequest) -> List[str]:
    """Return what stops this engine from being created, mirroring the checks of the service and the UI.

    Provider and region are left to the service, which reports a combination it does not offer.
    """
    body = engine.to_request_body()
    adapter = body['engine_adapter_configuration']
    adapter_type = adapter['type']
    method = adapter.get('authentication_method')
    required = required_create_fields(adapter_type, method)
    method_problems = []
    if adapter_type == EngineAdapterType.WES_ON_CROMWELL.value:
        method = method or WesOnCromwellAuthenticationMethod.OAUTH.value
        # In the UI, SSL settings on an OAuth engine exist only to supply a custom server certificate.
        if method == WesOnCromwellAuthenticationMethod.OAUTH.value and 'ssl_config' in adapter:
            required.append('engine_adapter_configuration.ssl_config.server_certificate_chain')
        method_problems = _wes_method_problems(adapter, method)
    problems = [f'{path} is required' for path in required if is_blank(get_field(body, path))]

    if not is_blank(engine.id) and not ENGINE_ID_PATTERN.fullmatch(engine.id):
        problems.append("id must start with a letter or digit, hold only letters, digits and '-', "
                        "and be at least 3 characters")
    problems += method_problems
    problems += url_problems(adapter)

    problems += [
        f"engine_adapter_configuration.{path} must be the real secret, not the '{SECRET_PLACEHOLDER}' placeholder"
        for path in ENGINE_SECRET_FIELDS if get_field(adapter, path) == SECRET_PLACEHOLDER
    ]
    return problems


def _wes_update_method_problems(adapter: Dict[str, Any], stored_adapter: Dict[str, Any]) -> List[str]:
    method = adapter.get('authentication_method') or WesOnCromwellAuthenticationMethod.OAUTH.value
    stored_method = stored_adapter.get('authentication_method') or WesOnCromwellAuthenticationMethod.OAUTH.value
    if method == stored_method and adapter.get('oauth_config') == stored_adapter.get('oauth_config'):
        # An MTLS engine saved with OAuth settings can still be updated from its describe output.
        adapter = {key: value for key, value in adapter.items() if key != 'oauth_config'}
    return _wes_method_problems(adapter, method)


def validate_engine_for_update(engine: ExecutionEngineRequest,
                               stored: ExecutionEngine,
                               given_by_option: AbstractSet[str] = frozenset()) -> List[str]:
    """Check what an update changes. Values equal to the stored ones are not re-checked, so an engine
    saved before a rule existed can still be updated without changing them, unless an option gave them:
    given_by_option holds those fields' paths, relative to engine_adapter_configuration."""
    adapter = engine.to_request_body()['engine_adapter_configuration']
    stored_adapter = stored.engine_adapter_configuration or {}
    changed = {path for path in ENGINE_URL_FIELDS
               if path in given_by_option or get_field(adapter, path) != get_field(stored_adapter, path)}
    problems = url_problems(adapter, changed)
    if adapter.get('type') == EngineAdapterType.WES_ON_CROMWELL.value:
        problems += _wes_update_method_problems(adapter, stored_adapter)
    return problems


def redact_engine_secrets(engine: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of an engine dict with every present secret, and the user info of every URL, replaced by
    the placeholder."""
    redacted = copy.deepcopy(engine)
    adapter = redacted.get('engine_adapter_configuration')
    if isinstance(adapter, dict):
        for path in ENGINE_SECRET_FIELDS:
            if get_field(adapter, path) is not None:
                set_field(adapter, path, SECRET_PLACEHOLDER)
        for path in ENGINE_URL_FIELDS:
            url = get_field(adapter, path)
            if isinstance(url, str):
                set_field(adapter, path, mask_url_credentials(url))
    return redacted


def drop_redacted_values(engine: Dict[str, Any],
                         stored_adapter: Optional[Dict[str, Any]],
                         given_by_option: AbstractSet[str] = frozenset()) -> Dict[str, Any]:
    """Undo redact_engine_secrets for an update, so redacted describe output sent back keeps the stored values.

    Placeholder secrets are always dropped. A URL is dropped when it is the stored URL as redacted output shows it,
    unless an option gave it (given_by_option holds those paths, relative to engine_adapter_configuration): a
    masked URL that was typed, or edited, is kept and refused by validation.
    """
    cleaned = copy.deepcopy(engine)
    adapter = cleaned.get('engine_adapter_configuration')
    if not isinstance(adapter, dict):
        return cleaned
    for path in ENGINE_SECRET_FIELDS:
        if get_field(adapter, path) == SECRET_PLACEHOLDER:
            delete_field(adapter, path)
    for path in ENGINE_URL_FIELDS:
        stored_url = get_field(stored_adapter or {}, path)
        masked = mask_url_credentials(stored_url)
        if path not in given_by_option and masked != stored_url and get_field(adapter, path) == masked:
            delete_field(adapter, path)
    return cleaned
