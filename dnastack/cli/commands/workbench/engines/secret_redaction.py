"""Masks the secrets of an engine request in text the engines service sent back.

A service error can echo the request, so every error that carries service text is passed through here
before it is printed.
"""
import copy
import json
from typing import Any, List

from dnastack.client.workbench.ewes.engine_models import (
    ENGINE_SECRET_FIELDS, SECRET_PLACEHOLDER, ExecutionEngineRequest, get_field, raw_url_password, url_password,
)
from dnastack.http.session import HttpError

_SERVICE_ACCOUNT_PATH = 'auth_config.service_account_json'
# A service may echo only part of the key, so these values inside a service account key are masked on their own.
_SERVICE_ACCOUNT_SECRET_KEYS = ('private_key', 'private_key_id')


def _is_present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def request_secret_values(request: ExecutionEngineRequest) -> List[str]:
    """Every secret value the request sends, longest first so a secret is never masked inside a longer one."""
    adapter = request.to_request_body().get('engine_adapter_configuration') or {}
    values = [get_field(adapter, path) for path in ENGINE_SECRET_FIELDS] + [
        url_password(adapter.get('url')), raw_url_password(adapter.get('url'))]
    service_account = get_field(adapter, _SERVICE_ACCOUNT_PATH)
    if _is_present(service_account):
        try:
            key = json.loads(service_account)
        except json.JSONDecodeError:
            key = None
        if isinstance(key, dict):
            values += [key.get(name) for name in _SERVICE_ACCOUNT_SECRET_KEYS]
    secrets = [value for value in values if _is_present(value) and value != SECRET_PLACEHOLDER]
    return sorted(set(secrets), key=len, reverse=True)


def redact_text(text: str, secrets: List[str]) -> str:
    """Replace each secret in the text with the placeholder, also where it appears escaped inside a JSON string."""
    for secret in secrets:
        text = text.replace(secret, SECRET_PLACEHOLDER)
        # A JSON response holds the secret escaped, e.g. a PEM key's newlines as \n, with or without
        # non-ASCII characters escaped as well.
        for ensure_ascii in (True, False):
            text = text.replace(json.dumps(secret, ensure_ascii=ensure_ascii)[1:-1], SECRET_PLACEHOLDER)
    return text


def redacted_http_error(error: HttpError, secrets: List[str]) -> HttpError:
    """A copy of the error, of the same type, whose response text and message have the secrets masked."""
    if not secrets:
        return error
    response = copy.copy(error.response)
    # requests reads Response.text from _content; this is the only way to give a Response other text.
    response._content = redact_text(error.response.text, secrets).encode('utf-8')
    response.encoding = 'utf-8'
    message = redact_text(error.message, secrets) if error.message else error.message
    return type(error)(response, trace_context=error.trace, message=message)
