"""`engines update <type> ENGINE_ID`: change only the fields given as options or in --config."""
from typing import Any, Dict, Optional

import click

from dnastack.cli.commands.workbench.engines.commands import ENGINE_ID_ARG, redacted_engine
from dnastack.cli.commands.workbench.engines.engine_input import SERVER_SET_FIELDS, load_engine_object
from dnastack.cli.commands.workbench.engines.engine_kinds import (
    ENGINE_KINDS, EngineKind, build_engine_description, command_help, has_changes, option_names, option_specs,
    secret_options_from,
)
from dnastack.cli.commands.workbench.engines.engine_submission import (
    prepare_engine_update, update_engine_from_description,
)
from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json
from dnastack.common.json_argument_parser import JsonLike


@formatted_group('update')
def update_engine_command_group():
    """Update an engine"""


def _config_has_changes(engine_data: Optional[Dict[str, Any]]) -> bool:
    """Whether --config holds anything to change: the id, default, and server-set fields such as the version do
    not count, since they are never sent."""
    ignored = {'id', 'default', *SERVER_SET_FIELDS}
    return any(key not in ignored for key in (engine_data or {}))


def _help(kind: EngineKind) -> str:
    return command_help(kind, 'Update', "Only the fields given as options or in --config change; everything else, "
                                        "secrets included, keeps its stored value. A field cannot be cleared: an "
                                        "omitted or null field keeps its stored value. If --config has a version "
                                        "and the engine has changed since, the update is refused. The engine's "
                                        "health is checked before the change is saved, so this can take a while. "
                                        "Use `set-default` to make it the default.")


def _add_update_command(kind: EngineKind) -> None:
    def update_engine(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      engine_id: str,
                      engine_config: Optional[JsonLike] = None,
                      **values: Any):
        engine_data = load_engine_object(engine_config) if engine_config else None
        if not _config_has_changes(engine_data) and not has_changes(kind, values, for_create=False):
            raise click.UsageError('Nothing to update: pass --config or at least one option.')
        engine = build_engine_description(kind, engine_data, values, for_create=False)
        # Every check that does not need the stored engine runs before connecting.
        engine, secret_values = prepare_engine_update(engine_id, engine, secret_options_from(kind, values))
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        updated = update_engine_from_description(client, engine_id, engine, secret_values=secret_values,
                                                 adapter_type=kind.adapter_type.value,
                                                 option_names=option_names(kind, for_create=False))
        click.echo(to_json(redacted_engine(updated)))

    update_engine.__doc__ = _help(kind)

    formatted_command(
        group=update_engine_command_group,
        name=kind.name,
        specs=[ENGINE_ID_ARG, *option_specs(kind, for_create=False), NAMESPACE_ARG, CONTEXT_ARG,
               SINGLE_ENDPOINT_ID_ARG],
    )(update_engine)


for _kind in ENGINE_KINDS:
    _add_update_command(_kind)
