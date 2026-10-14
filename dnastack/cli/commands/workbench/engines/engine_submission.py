"""Creates or updates an engine from its description, however the description was given.

The per-type subcommands in create.py and update.py build the description from --config, their own options and
the secret options, then call these, so every route gets the same id handling, validation,
duplicate and version checks, and health-check report. Each operation has a prepare step that needs no service,
so a command runs every local check before it connects.
"""
from typing import Any, Dict, List, Optional, Tuple

from dnastack.cli.commands.workbench.engines.engine_input import (
    EngineInputError, apply_secret_flags, fill_engine_id, follow_default_azure_scope, inherit_adapter_type,
    inherit_authentication_method, parse_engine_request, read_secret_options, resolve_if_match,
)
from dnastack.cli.commands.workbench.engines.engine_names import subcommand_for, with_article
from dnastack.cli.commands.workbench.engines.health_check_failure import exit_on_failed_health_check
from dnastack.cli.commands.workbench.engines.secret_redaction import redacted_http_error, request_secret_values
from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.ewes.engine_models import (
    ExecutionEngineRequest, validate_engine_for_create, validate_engine_for_update,
)
from dnastack.client.workbench.ewes.models import ExecutionEngine
from dnastack.http.session import ClientError, HttpError


def _engine_exists(client: EWesClient, engine_id: str) -> bool:
    try:
        client.get_engine(engine_id=engine_id)
    except ClientError as e:
        if e.response.status_code == 404:
            return False
        raise
    return True


def _raise_without_secrets(error: HttpError, request: ExecutionEngineRequest, engine_id: str, action: str) -> None:
    """Report a failed create or update with every secret the request sent masked in the service's text.

    A failed health check is printed as a report and exits; any other error is raised again as the same type.
    """
    secrets = request_secret_values(request)
    if isinstance(error, ClientError):
        exit_on_failed_health_check(error, engine_id, action, secrets)
    # Not chained: the original error's text still holds the secrets.
    raise redacted_http_error(error, secrets) from None


def _describe_problems(heading: str, problems: List[str], option_names: Optional[Dict[str, str]]) -> str:
    """List the problems, naming the option that sets a field instead of the field's path where there is one.

    A dotted path is replaced wherever it appears; a single-segment path such as `region` only where it starts
    the problem, since it could be part of other words. Longer paths go first so a path is never replaced
    inside a longer one.
    """
    named = []
    for problem in problems:
        for path in sorted(option_names or {}, key=len, reverse=True):
            flag = option_names[path]
            if '.' in path:
                problem = problem.replace(path, flag)
            elif problem.startswith(f'{path} '):
                problem = flag + problem[len(path):]
        named.append(problem if problem.endswith('.') else f'{problem}.')
    return heading + '\n' + '\n'.join(f'  - {p}' for p in named)


def prepare_engine_create(engine: Dict[str, Any],
                          secret_options: Optional[Dict[str, Optional[str]]] = None,
                          option_names: Optional[Dict[str, str]] = None) -> ExecutionEngineRequest:
    """Turn an engine description, in the engines service's JSON shape, into a create request, without the service.

    Raises on any problem found locally. A missing id is derived from the name the way the Workbench UI does it.
    Secret options must be passed through secret_options, as raw option values (inline, @path, or -) keyed by
    apply_secret_flags' parameter names, so they get the same reading and no-echo rules as the CLI options; the
    description itself may also hold secrets. option_names maps a field's full dotted path to the option that
    sets it, so problems name the option.
    """
    engine = apply_secret_flags(engine, **(secret_options or {}))
    request = parse_engine_request(fill_engine_id(engine), for_update=False)
    problems = validate_engine_for_create(request)
    if problems:
        raise EngineInputError(_describe_problems('The engine cannot be created:', problems, option_names))
    return request


def create_engine_from_description(client: EWesClient, request: ExecutionEngineRequest) -> ExecutionEngine:
    """Create an engine from a request made by prepare_engine_create, unless one with its id already exists."""
    if _engine_exists(client, request.id):
        subcommand = subcommand_for(request.engine_adapter_configuration.type)
        raise EngineInputError(f"Engine '{request.id}' already exists in namespace '{client.namespace}'. "
                               f"Use 'omics workbench engines update {subcommand} {request.id}' to change it.")
    try:
        return client.create_engine(request)
    except HttpError as e:
        _raise_without_secrets(e, request, request.id, 'created')


def prepare_engine_update(engine_id: str,
                          engine: Dict[str, Any],
                          secret_options: Optional[Dict[str, Optional[str]]] = None
                          ) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Check what an update can check without the stored engine, and read the secret options.

    Returns the description with its id set, and the secret values to pass to update_engine_from_description.
    secret_options are raw option values, as for prepare_engine_create.
    """
    description_id = engine.get('id')
    if description_id is not None and description_id != engine_id:
        raise EngineInputError(f"The id in --config ('{description_id}') does not match "
                               f"the engine id ('{engine_id}')")
    return {**engine, 'id': engine_id}, read_secret_options(secret_options or {})


def update_engine_from_description(client: EWesClient,
                                   engine_id: str,
                                   engine: Dict[str, Any],
                                   secret_values: Optional[Dict[str, str]] = None,
                                   adapter_type: Optional[str] = None,
                                   option_names: Optional[Dict[str, str]] = None) -> ExecutionEngine:
    """Update an engine from a description of the fields to change; every field left out keeps its value.

    engine and secret_values come from prepare_engine_update. The secrets are applied after the stored
    authentication method is known, since that decides where a WES secret goes. adapter_type is the adapter type
    the caller expects; a stored engine of another type is refused with the subcommand to use instead.
    option_names is as for prepare_engine_create.
    """
    existing = client.get_engine(engine_id=engine_id)
    if_match = resolve_if_match(engine_id, engine.get('version'), existing.version)
    stored_adapter = existing.engine_adapter_configuration or {}
    stored_type = stored_adapter.get('type')
    if adapter_type and stored_type and stored_type != adapter_type:
        stored_subcommand = subcommand_for(stored_type)
        if stored_subcommand is None:
            raise EngineInputError(f"Engine '{engine_id}' is not {with_article(subcommand_for(adapter_type))} engine")
        raise EngineInputError(f"Engine '{engine_id}' is {with_article(stored_subcommand)} engine; "
                               f"use 'omics workbench engines update {stored_subcommand} {engine_id}'.")
    engine = inherit_adapter_type(engine, stored_type)
    engine = inherit_authentication_method(engine, stored_adapter)
    engine = follow_default_azure_scope(engine, stored_adapter)
    engine = apply_secret_flags(engine, **(secret_values or {}), already_read=True)
    request = parse_engine_request(engine, for_update=True)

    problems = validate_engine_for_update(request, existing)
    if problems:
        raise EngineInputError(_describe_problems('The engine cannot be updated:', problems, option_names))
    try:
        return client.update_engine(engine_id=engine_id, engine=request, if_match=if_match)
    except HttpError as e:
        _raise_without_secrets(e, request, engine_id, 'updated')
