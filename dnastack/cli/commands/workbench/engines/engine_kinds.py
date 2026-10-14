"""The engine types `engines create` and `engines update` offer as subcommands, and the options each one takes.

Each subcommand builds an engine description from --config and its options, then hands it to the shared
functions in engine_submission. Secret options are not written into the description: they are passed on
as raw values, so the shared functions read them with the same rules as everywhere else.
"""
import copy
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

import click

from dnastack.cli.commands.workbench.engines.engine_input import EngineOptionError, read_option_text
from dnastack.cli.commands.workbench.engines.engine_names import SUBCOMMAND_NAMES, with_article
from dnastack.cli.core.command_spec import ArgumentSpec
from dnastack.cli.core.constants import TOTAL_WIDTH
from dnastack.cli.core.formatting_utils import wrap_text
from dnastack.client.workbench.ewes.engine_models import (
    EngineAdapterType, WesOnCromwellAuthenticationMethod, get_field, required_create_fields, set_field,
)
from dnastack.common.json_argument_parser import JsonLike

_ADAPTER = 'engine_adapter_configuration'
_AT_PATH_ONLY = 'A value that starts with @ or - must be given as @path.'
_READ_TEXT_HELP = f'the value, @path to a file, or - to read stdin. {_AT_PATH_ONLY}'
_READ_PEM_HELP = f'@path to a PEM file, or - to read stdin. {_AT_PATH_ONLY}'
_DEFAULT_IN_CONFIG_WARNING = 'Ignoring "default" in --config; use `set-default` to make an engine the default.'


def _option_help(text: str, create_hint: str, update_hint: str, for_create: bool) -> str:
    """The help of an option, with its create or update hint appended as its own sentence."""
    hint = create_hint if for_create else update_hint
    if not hint:
        return text
    return f'{text} {hint}' if text.endswith(('.', '!', '?')) else f'{text}. {hint}'


@dataclass(frozen=True)
class EngineOption:
    """An option that sets one field of the engine description."""
    flag: str
    path: str
    help: str
    # Appended on create only: when create requires the option, or what create uses when it is left out. An option
    # create always requires has no hint: create help lists it under the required options heading instead.
    create_hint: str = ''
    # Appended on update only.
    update_hint: str = ''
    choices: Tuple[str, ...] = ()
    upper: bool = False
    case_sensitive: bool = True
    # Read like --client-key-and-certificate-chain: verbatim, inline, as @path, or - for stdin. The help says how
    # to give it.
    reads_text: bool = False

    @property
    def name(self) -> str:
        return self.flag.lstrip('-').replace('-', '_')

    def to_spec(self, for_create: bool, display_required: bool = False) -> ArgumentSpec:
        return ArgumentSpec(name=self.name, arg_names=[self.flag],
                            help=_option_help(self.help, self.create_hint, self.update_hint, for_create),
                            choices=list(self.choices), case_sensitive=self.case_sensitive,
                            display_required=display_required,
                            example_value='@PATH' if self.reads_text else None)

    def value(self, raw: Any) -> Any:
        if self.reads_text:
            return read_option_text(self.flag, raw, verbatim=True)
        return raw.upper() if self.upper else raw


@dataclass(frozen=True)
class SecretOption:
    """A secret option, passed to the shared functions by its apply_secret_flags parameter name.

    path is the full dotted path of the field the secret sets; help includes how to give the value."""
    name: str
    flag: str
    path: str
    help: str
    create_hint: str = ''

    def to_spec(self, for_create: bool, display_required: bool = False) -> ArgumentSpec:
        return ArgumentSpec(name=self.name, arg_names=[self.flag],
                            help=_option_help(self.help, self.create_hint, '', for_create),
                            display_required=display_required, example_value='@PATH')


@dataclass(frozen=True)
class EngineKind:
    adapter_type: EngineAdapterType
    # The engine type line of the create and update help, or None where the summary already says it.
    title: Optional[str]
    summary: str
    provider: Optional[str]
    # Appended to the --region help, if any.
    region_hint: str
    options: Tuple[EngineOption, ...]
    secrets: Tuple[SecretOption, ...]

    @property
    def name(self) -> str:
        """The subcommand name."""
        return SUBCOMMAND_NAMES[self.adapter_type]


_CREATE_COMMON = (
    EngineOption('--id', 'id', 'The engine id, unique within the namespace: at least 3 characters, starting with a '
                               'letter or digit, using only letters, digits and \'-\'. If left out, it is derived '
                               'from --name: lower-cased, each character that is not a letter, digit or \'-\' '
                               'replaced by \'-\', repeated \'-\' collapsed, and \'-\' removed from both ends '
                               '(e.g. "GIAB Demo" becomes giab-demo).'),
    EngineOption('--name', 'name', 'A human readable name for the engine.'),
    EngineOption('--description', 'description', 'A description for the engine.'),
)
_UPDATE_COMMON = tuple(o for o in _CREATE_COMMON if o.flag != '--id')
_PROVIDER = EngineOption('--provider', 'provider', 'Where the WES service runs.',
                         choices=('aws', 'azure', 'gcp', 'local'), upper=True, case_sensitive=False)
_OAUTH_REQUIRED = 'Required with --authentication-method oauth (the default), unless given in --config.'
_CROMWELL_URL = 'The Cromwell URL: https, or http for localhost only.'

ENGINE_KINDS: Tuple[EngineKind, ...] = (
    EngineKind(
        adapter_type=EngineAdapterType.GCP_CLOUD_RUN_CROMWELL, title='Cromwell on Cloud Run',
        summary='a Cromwell engine on GCP', provider='GCP', region_hint='',
        options=(
            EngineOption('--url', f'{_ADAPTER}.url', _CROMWELL_URL),
            EngineOption('--project-id', f'{_ADAPTER}.project_id', 'The id of the GCP project.'),
            EngineOption('--quota-project-id', f'{_ADAPTER}.quota_project_id',
                         'The GCP project billed for API quota, if different from --project-id.'),
        ),
        secrets=(SecretOption('service_account_json', '--service-account-json',
                              f'{_ADAPTER}.auth_config.service_account_json',
                              'The service account JSON key for the engine to use when authenticating with GCP: '
                              f'{_READ_TEXT_HELP}'),),
    ),
    EngineKind(
        adapter_type=EngineAdapterType.WES_ON_CROMWELL, title='Cromwell behind a GA4GH WES API',
        summary='a GA4GH WES engine', provider=None,
        region_hint='Use local with --provider local.',
        options=(
            EngineOption('--url', f'{_ADAPTER}.url', 'The WES service URL: https, or http for localhost only.'),
            EngineOption('--authentication-method', f'{_ADAPTER}.authentication_method',
                         'How Workbench authenticates to the WES service.', 'Defaults to oauth.',
                         choices=('oauth', 'mtls'), upper=True, case_sensitive=False),
            EngineOption('--client-id', f'{_ADAPTER}.oauth_config.clientId', 'The OAuth client id.', _OAUTH_REQUIRED),
            EngineOption('--token-uri', f'{_ADAPTER}.oauth_config.tokenUri', 'The OAuth token URL.',
                         _OAUTH_REQUIRED),
            EngineOption('--resource', f'{_ADAPTER}.oauth_config.resource',
                         'The OAuth resource (audience) to request the token for.', _OAUTH_REQUIRED),
            EngineOption('--scope', f'{_ADAPTER}.oauth_config.scope', 'The OAuth scope to request.', _OAUTH_REQUIRED),
            EngineOption('--server-certificate-chain', f'{_ADAPTER}.ssl_config.server_certificate_chain',
                         "The WES server's PEM certificate chain, for a server whose certificate is not publicly "
                         f'trusted: {_READ_PEM_HELP}', reads_text=True),
        ),
        secrets=(
            SecretOption('client_secret', '--client-secret', f'{_ADAPTER}.oauth_config.clientSecret',
                         f'The OAuth client secret: {_READ_TEXT_HELP}', _OAUTH_REQUIRED),
            SecretOption('client_key_and_certificate_chain', '--client-key-and-certificate-chain',
                         f'{_ADAPTER}.ssl_config.client_key_and_certificate_chain',
                         f'The PEM client private key and certificate chain: {_READ_PEM_HELP}',
                         'Required with --authentication-method mtls, unless given in --config.'),
        ),
    ),
    EngineKind(
        adapter_type=EngineAdapterType.AZURE_CONTAINER_APP_CROMWELL,
        title='Cromwell on Container Apps',
        summary='a Cromwell engine on Azure', provider='AZURE', region_hint='',
        options=(
            EngineOption('--url', f'{_ADAPTER}.url', _CROMWELL_URL),
            EngineOption('--tenant-id', f'{_ADAPTER}.tenant_id',
                         'Refers to the Azure Active Directory (AAD) tenant associated with the engine. '
                         'The tenant ID uniquely identifies your organization’s AAD instance.'),
            EngineOption('--client-id', f'{_ADAPTER}.client_id',
                         'The application (client) ID of the Azure AD service principal that Workbench uses to '
                         'call Cromwell.'),
            EngineOption('--scope', f'{_ADAPTER}.scope', 'The OAuth scope to request.',
                         'Defaults to <client id>/.default.',
                         update_hint='When --client-id changes and the stored scope is the default '
                                     '<client id>/.default, it follows the new client id; otherwise the stored '
                                     'scope is kept.'),
            EngineOption('--storage-account-name', f'{_ADAPTER}.storage_account_name',
                         'The Azure storage account name.'),
            EngineOption('--storage-container-name', f'{_ADAPTER}.storage_container_name',
                         'The Azure storage container name.'),
        ),
        secrets=(SecretOption('client_secret', '--client-secret', f'{_ADAPTER}.client_secret',
                              'Refers to the password or secret key for the service principal: '
                              f'{_READ_TEXT_HELP}'),),
    ),
    EngineKind(
        adapter_type=EngineAdapterType.AWS_HEALTH_OMICS, title=None,
        summary='an AWS HealthOmics engine', provider='AWS', region_hint='',
        options=(
            EngineOption('--access-key-id', f'{_ADAPTER}.access_key_id',
                         'The access key id for the engine to use when authenticating with AWS.'),
            EngineOption('--output-bucket', f'{_ADAPTER}.output_bucket',
                         'The S3 bucket for workflow outputs (s3:// is added if left out).'),
            EngineOption('--role-arn', f'{_ADAPTER}.role_arn', 'The IAM role ARN HealthOmics runs as.'),
        ),
        secrets=(SecretOption('secret_access_key', '--secret-access-key', f'{_ADAPTER}.secret_access_key',
                              'The secret access key for the engine to use when authenticating with AWS: '
                              f'{_READ_TEXT_HELP}'),),
    ),
)
KINDS_BY_NAME: Dict[str, EngineKind] = {kind.name: kind for kind in ENGINE_KINDS}
_KINDS_BY_ADAPTER_TYPE: Dict[str, EngineKind] = {kind.adapter_type.value: kind for kind in ENGINE_KINDS}

_CONFIG_SPEC = ArgumentSpec(
    name='engine_config', arg_names=['--config'], type=JsonLike,
    help='The engine configuration as JSON, instead of individual options: @path/to/engine.json, inline JSON, '
         'or - to read stdin. Uses the same fields as `omics workbench engines describe` output. Any options '
         'also given override the matching fields.',
)


def command_help(kind: EngineKind, verb: str, body: str) -> str:
    """The help of `engines <verb> <kind>`: the summary, the engine type where it adds to the summary, then body.

    Built without indentation and wrapped to the help width, since the help formatter prints it as it is.
    """
    paragraphs = [f'{verb} {kind.summary}']
    if kind.title:
        paragraphs.append(f'Engine type: {kind.title}.')
    paragraphs.append('\n'.join(wrap_text(body, TOTAL_WIDTH)))
    return '\n\n'.join(paragraphs)


def _region_option(kind: EngineKind) -> EngineOption:
    region_help = ' '.join(filter(None, ['The region for the engine.', kind.region_hint]))
    return EngineOption('--region', 'region', region_help)


def _field_options(kind: EngineKind, for_create: bool) -> Tuple[EngineOption, ...]:
    common = _CREATE_COMMON if for_create else _UPDATE_COMMON
    provider = () if kind.provider else (_PROVIDER,)
    return common + (_region_option(kind),) + provider + kind.options


def always_required_create_fields(kind: EngineKind) -> FrozenSet[str]:
    """The fields create requires whatever the authentication method, as full dotted paths."""
    adapter_type = kind.adapter_type.value
    return frozenset.intersection(*(frozenset(required_create_fields(adapter_type, method.value))
                                    for method in WesOnCromwellAuthenticationMethod))


def option_specs(kind: EngineKind, for_create: bool) -> List[ArgumentSpec]:
    """The specs of --config and each field and secret option.

    On create, the options of the fields create always requires are listed as required in help. Click does not
    enforce them, since --config may supply the fields; missing_create_options reports any left unset.
    """
    required = always_required_create_fields(kind) if for_create else frozenset()
    options = [*_field_options(kind, for_create), *kind.secrets]
    return [_CONFIG_SPEC, *(o.to_spec(for_create, display_required=o.path in required) for o in options)]


def _check_config_matches(kind: EngineKind, engine: Dict[str, Any], for_create: bool) -> None:
    adapter = engine.get(_ADAPTER)
    if adapter is not None and not isinstance(adapter, dict):
        raise EngineOptionError(f'{_ADAPTER} must be an object', '--config')
    config_type = (adapter or {}).get('type')
    if config_type is not None and config_type != kind.adapter_type.value:
        config_kind = _KINDS_BY_ADAPTER_TYPE.get(config_type) if isinstance(config_type, str) else None
        if config_kind is None:
            # A type this CLI does not know is not echoed: the field may hold anything, a pasted secret included.
            raise EngineOptionError(f'{_ADAPTER}.type must be {kind.adapter_type.value} for this subcommand, '
                                    f'or left out', '--config')
        described = with_article(config_kind.name)
        if for_create:
            raise EngineOptionError(f'describes {described} engine, but this subcommand creates {kind.name} engines; '
                                    f"use 'omics workbench engines create {config_kind.name}'", '--config')
        raise EngineOptionError(f"describes {described} engine; use 'omics workbench engines update "
                                f"{config_kind.name} ...'", '--config')
    config_provider = engine.get('provider')
    if kind.provider and config_provider is not None and config_provider != kind.provider:
        raise EngineOptionError(f'provider must be {kind.provider} for {kind.name} engines, or left out', '--config')


def _prepare_parents(engine: Dict[str, Any], path: str) -> None:
    """Make every object above the last path segment exist, so a null one in --config does not crash set_field."""
    parts = path.split('.')[:-1]
    node = engine
    for index, key in enumerate(parts):
        if node.get(key) is None:
            node[key] = {}
        if not isinstance(node[key], dict):
            raise EngineOptionError(f"{'.'.join(parts[:index + 1])} must be an object", '--config')
        node = node[key]


def build_engine_description(kind: EngineKind,
                             engine_config: Optional[Dict[str, Any]],
                             values: Dict[str, Any],
                             for_create: bool) -> Dict[str, Any]:
    """Start from --config and write each option that was passed into its field.

    Create also sets the adapter type and any fixed provider. Update leaves the type out, since the shared update
    inherits it from the stored engine.
    """
    engine = copy.deepcopy(engine_config or {})
    _check_config_matches(kind, engine, for_create)
    # Like the server-set fields, "default" in --config (as `describe` prints it) is never sent:
    # `engines set-default` is the only way to make an engine the default.
    if engine.pop('default', None) is True:
        click.echo(_DEFAULT_IN_CONFIG_WARNING, err=True)
    for option in _field_options(kind, for_create):
        raw = values.get(option.name)
        if raw is not None:
            _prepare_parents(engine, option.path)
            set_field(engine, option.path, option.value(raw))
    if for_create:
        set_field(engine, f'{_ADAPTER}.type', kind.adapter_type.value)
        if kind.provider:
            engine['provider'] = kind.provider
    return engine


def secret_options_from(kind: EngineKind, values: Dict[str, Any]) -> Dict[str, Optional[str]]:
    return {secret.name: values.get(secret.name) for secret in kind.secrets}


def option_names(kind: EngineKind, for_create: bool) -> Dict[str, str]:
    """The option that sets each field, keyed by the field's full dotted path."""
    names = {option.path: option.flag for option in _field_options(kind, for_create)}
    names.update({secret.path: secret.flag for secret in kind.secrets})
    return names


def missing_create_options(kind: EngineKind, engine: Dict[str, Any], values: Dict[str, Any]) -> List[str]:
    """The options of the fields create requires that neither --config nor an option supplies, in required order.

    A required field no option sets is left for the shared validation to report.
    """
    flags = option_names(kind, for_create=True)
    secret_names = {secret.path: secret.name for secret in kind.secrets}
    method = get_field(engine, f'{_ADAPTER}.authentication_method')
    missing = []
    for path in required_create_fields(kind.adapter_type.value, method if isinstance(method, str) else None):
        value = get_field(engine, path)
        if value is not None and not (isinstance(value, str) and not value.strip()):
            continue
        if path in secret_names and values.get(secret_names[path]) is not None:
            continue
        if path in flags:
            missing.append(flags[path])
    return missing


def has_changes(kind: EngineKind, values: Dict[str, Any], for_create: bool) -> bool:
    """Whether any field or secret option was passed."""
    names = [o.name for o in _field_options(kind, for_create)] + [s.name for s in kind.secrets]
    return any(values.get(name) is not None for name in names)
