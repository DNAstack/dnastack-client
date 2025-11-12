from typing import Optional

from pydantic import BaseModel

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
    client_secret: Optional[str] = None
    device_code_endpoint: Optional[str] = None
    grant_type: str
    personal_access_endpoint: Optional[str] = None
    personal_access_email: Optional[str] = None
    personal_access_token: Optional[str] = None
    redirect_url: Optional[str] = None
    resource_url: str
    scope: Optional[str] = None
    token_endpoint: Optional[str] = None
    type: str = 'oauth2'
    subject_token: Optional[str] = None
    subject_token_type: Optional[str] = None
    requested_token_type: Optional[str] = None
    audience: Optional[str] = None
    cloud_provider: Optional[str] = None  # Currently supported: 'gcp'