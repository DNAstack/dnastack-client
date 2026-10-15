"""Request models for creating and updating Workbench engines and their parameter presets.

These mirror the request body the engines service accepts. Reading engines still uses
`ExecutionEngine` from models.py, whose adapter configuration is a plain dict so that engines
of types this client does not model can still be listed and described.
"""
import copy
import json
import re
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from urllib.parse import urlsplit, urlunsplit

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

_URL_PROBLEM = 'engine_adapter_configuration.url must use https:// (http:// is only allowed for localhost)'
_URL_USERINFO_PROBLEM = 'engine_adapter_configuration.url must not contain a user name or password'
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


def _is_blank(value: Any) -> bool:
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


def _has_userinfo(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return parts.username is not None or parts.password is not None
    except ValueError:
        return False


# urlsplit silently drops these characters, so what it parses can differ from the raw text.
_URLSPLIT_STRIPPED = ('\t', '\r', '\n')


def _has_stripped_characters(url: str) -> bool:
    return any(char in url for char in _URLSPLIT_STRIPPED)


def _raw_user_info(url: str) -> Optional[str]:
    """The user info of the raw URL text: between the scheme's // and the last @ before the first / ? or #."""
    _, separator, rest = url.partition('//')
    if not separator:
        return None
    authority = re.split(r'[/?#]', rest, maxsplit=1)[0]
    user_info, at, _ = authority.rpartition('@')
    return user_info if at else None


def url_password(url: Any) -> Optional[str]:
    """The password inside a URL's user info, or None when it has none or does not parse."""
    if not isinstance(url, str):
        return None
    try:
        return urlsplit(url).password or None
    except ValueError:
        return None


def raw_url_password(url: Any) -> Optional[str]:
    """The password as written in the URL text, which differs from url_password where urlsplit strips characters."""
    if url_password(url) is None:
        return None
    user_info = _raw_user_info(url)
    if user_info is None or ':' not in user_info:
        return None
    return user_info.partition(':')[2] or None


def _mask_parsed_url_password(url: str) -> str:
    """Rebuild the URL from its parsed form with the password masked, for when the raw user info cannot be found."""
    parts = urlsplit(url)
    user_info, _, host = parts.netloc.rpartition('@')
    return urlunsplit(parts._replace(netloc=f'{user_info.partition(":")[0]}:{SECRET_PLACEHOLDER}@{host}'))


def _mask_url_password(url: Any) -> Any:
    """The URL with the password in its user info replaced by the placeholder; anything else is kept as given."""
    if url_password(url) is None:
        return url
    if _has_stripped_characters(url):
        # The parsed netloc no longer matches the text, so mask the raw user info instead.
        user_info = _raw_user_info(url)
        if user_info is None:
            return _mask_parsed_url_password(url)
        user, colon, _ = user_info.partition(':')
        masked = f'{user}:{SECRET_PLACEHOLDER}' if colon else SECRET_PLACEHOLDER
        return url.replace(f'{user_info}@', f'{masked}@', 1)
    netloc = urlsplit(url).netloc
    user_info, _, host = netloc.rpartition('@')
    user = user_info.partition(':')[0]
    # The netloc first appears right after the scheme, so only the user info changes.
    return url.replace(netloc, f'{user}:{SECRET_PLACEHOLDER}@{host}', 1)


def url_problems(adapter: Dict[str, Any]) -> List[str]:
    """The UI only accepts https engine URLs; plain http is allowed here for engines on this machine.

    A URL holding a user name or password is refused, and never quoted, since the password is a secret.
    """
    url = adapter.get('url')
    if _is_blank(url):
        return []
    if isinstance(url, str) and _has_userinfo(url):
        return [_URL_USERINFO_PROBLEM]
    if _is_allowed_url(url):
        return []
    return [_URL_PROBLEM]


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
    problems = [f'{path} is required' for path in required if _is_blank(get_field(body, path))]

    if not _is_blank(engine.id) and not ENGINE_ID_PATTERN.fullmatch(engine.id):
        problems.append("id must start with a letter or digit, hold only letters, digits and '-', "
                        "and be at least 3 characters")
    problems += method_problems
    problems += url_problems(adapter)

    problems += [
        f"engine_adapter_configuration.{path} must be the real secret, not the '{SECRET_PLACEHOLDER}' placeholder"
        for path in ENGINE_SECRET_FIELDS if get_field(adapter, path) == SECRET_PLACEHOLDER
    ]
    return problems


def validate_engine_for_update(engine: ExecutionEngineRequest, stored: ExecutionEngine) -> List[str]:
    """Check what an update changes. Values equal to the stored ones are not re-checked, so an engine
    saved before a rule existed can still be updated without changing them."""
    adapter = engine.to_request_body()['engine_adapter_configuration']
    stored_adapter = stored.engine_adapter_configuration or {}
    problems = []
    if adapter.get('url') != stored_adapter.get('url'):
        problems += url_problems(adapter)
    return problems


def redact_engine_secrets(engine: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of an engine dict with every present secret, and any password in its URL, replaced by
    the placeholder."""
    redacted = copy.deepcopy(engine)
    adapter = redacted.get('engine_adapter_configuration')
    if isinstance(adapter, dict):
        for path in ENGINE_SECRET_FIELDS:
            if get_field(adapter, path) is not None:
                set_field(adapter, path, SECRET_PLACEHOLDER)
        if 'url' in adapter:
            adapter['url'] = _mask_url_password(adapter['url'])
    return redacted


def drop_placeholder_secrets(engine: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy without placeholder secrets, so an update keeps the stored secret instead of
    overwriting it with the placeholder from redacted output."""
    cleaned = copy.deepcopy(engine)
    adapter = cleaned.get('engine_adapter_configuration')
    if isinstance(adapter, dict):
        for path in ENGINE_SECRET_FIELDS:
            if get_field(adapter, path) == SECRET_PLACEHOLDER:
                delete_field(adapter, path)
    return cleaned
