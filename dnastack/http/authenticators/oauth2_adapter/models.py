from functools import cache
from json import JSONDecodeError
from typing import Any, FrozenSet, Optional

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel

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


@cache
def secret_property_names() -> FrozenSet[str]:
    """ Property names whose values must never appear in logs or error messages

        Derived from the OAuth2Authentication and SessionInfo fields excluded from repr, in both snake_case and
        camelCase (the latter is how the service registry spells them).
    """
    # Imported here because dnastack.http.session_info imports this module.
    from dnastack.http.session_info import SessionInfo

    names = {
        name
        for model in (OAuth2Authentication, SessionInfo)
        for name, field in model.model_fields.items()
        if not field.repr
    }
    return frozenset(names | {to_camel(name) for name in names})


def redact_secrets(value: Any) -> Any:
    """ Return a copy of an authentication config or session (dict, list or nested) with secret values masked """
    if isinstance(value, dict):
        return {
            k: REDACTED_VALUE if k in secret_property_names() and v else redact_secrets(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


# Server error text is not safe to print. Wallet and other token endpoints put the submitted secret back in
# error_description, and a JSON string body is the secret itself. These codes are the OAuth error tokens from
# RFC 6749 section 5.2 and RFC 8628 section 3.5. Anything else stays out of the message. The HTTP status still
# separates a rejection from an outage.
_OAUTH_ERROR_CODES = frozenset({
    'invalid_request',
    'invalid_client',
    'invalid_grant',
    'unauthorized_client',
    'unsupported_grant_type',
    'invalid_scope',
    'server_error',
    'temporarily_unavailable',
    'authorization_pending',
    'slow_down',
    'access_denied',
    'expired_token',
})


def oauth_error_code(response: Any) -> Optional[str]:
    try:
        parsed = response.json()
    except JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    code = parsed.get('error')
    if isinstance(code, str) and code in _OAUTH_ERROR_CODES:
        return code
    return None


def oauth_failure_detail(response: Any) -> str:
    detail = f'HTTP {response.status_code}'
    code = oauth_error_code(response)
    if code:
        detail += f' ({code})'
    return detail


class RedactedReprMixin:
    """ Masks secrets inside dict and list fields when the model is rendered with repr() or str() """

    def __repr_args__(self):
        for name, value in super().__repr_args__():
            yield name, redact_secrets(value)
