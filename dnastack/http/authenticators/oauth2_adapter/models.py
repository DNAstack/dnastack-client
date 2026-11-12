from typing import Any, FrozenSet, Optional

from pydantic import BaseModel, Field

from dnastack.common.model_mixin import JsonModelMixin as HashableModel


GRANT_TYPE_TOKEN_EXCHANGE = 'urn:ietf:params:oauth:grant-type:token-exchange'
GRANT_TYPE_DEVICE_CODE = 'urn:ietf:params:oauth:grant-type:device_code'
GRANT_TYPE_CLIENT_CREDENTIALS = 'client_credentials'

# List of grant types supported by the CLI
SUPPORTED_GRANT_TYPES = [
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_TOKEN_EXCHANGE,
]


class OAuth2Authentication(BaseModel, HashableModel):
    """OAuth2 Authentication Information"""
    authorization_endpoint: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = Field(default=None, repr=False)
    device_code_endpoint: Optional[str] = None
    grant_type: str
    personal_access_endpoint: Optional[str] = None
    personal_access_email: Optional[str] = None
    personal_access_token: Optional[str] = Field(default=None, repr=False)
    redirect_url: Optional[str] = None
    resource_url: str
    scope: Optional[str] = None
    token_endpoint: Optional[str] = None
    type: str = 'oauth2'
    subject_token: Optional[str] = Field(default=None, repr=False)
    subject_token_type: Optional[str] = None
    requested_token_type: Optional[str] = None
    audience: Optional[str] = None
    cloud_provider: Optional[str] = None  # Currently supported: 'gcp'


REDACTED_VALUE = '***'


def _snake_to_camel(name: str) -> str:
    head, *tail = name.split('_')
    return head + ''.join(part.capitalize() for part in tail)


def _secret_property_names() -> FrozenSet[str]:
    names = {name for name, field in OAuth2Authentication.model_fields.items() if not field.repr}
    return frozenset(names | {_snake_to_camel(name) for name in names})


SECRET_PROPERTY_NAMES = _secret_property_names()
""" Authentication property names whose values must never appear in logs or error messages

    Derived from the OAuth2Authentication fields excluded from repr, in both snake_case and camelCase
    (the latter is how the service registry spells them).
"""


def redact_secrets(value: Any) -> Any:
    """ Return a copy of an authentication config (dict, list or nested) with secret values masked """
    if isinstance(value, dict):
        return {
            k: REDACTED_VALUE if k in SECRET_PROPERTY_NAMES and v else redact_secrets(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value
