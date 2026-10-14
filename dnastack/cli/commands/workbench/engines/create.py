"""`engines create <type>`: create an engine of one type from options, --config, or both."""
from typing import Any, List, Optional

import click

from dnastack.cli.commands.workbench.engines.commands import redacted_engine
from dnastack.cli.commands.workbench.engines.engine_input import load_engine_object
from dnastack.cli.commands.workbench.engines.engine_kinds import (
    ENGINE_KINDS, EngineKind, build_engine_description, command_help, missing_create_options, option_names,
    option_specs, secret_options_from,
)
from dnastack.cli.commands.workbench.engines.engine_submission import (
    create_engine_from_description, prepare_engine_create,
)
from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json
from dnastack.common.json_argument_parser import JsonLike


@formatted_group('create')
def create_engine_command_group():
    """Create an engine"""


def _missing_options_message(flags: List[str]) -> str:
    quoted = ', '.join(f"'{flag}'" for flag in flags)
    return f'Missing option {quoted}.' if len(flags) == 1 else f'Missing options {quoted}.'


def _help(kind: EngineKind) -> str:
    return command_help(kind, 'Create', f"Creating an engine whose id already exists fails; use `update {kind.name}` "
                                        "to change it. The service checks the engine's health before it is saved, "
                                        "so this can take a while. The first engine in a namespace always "
                                        "becomes the default. Use `set-default` to change it.")


def _add_create_command(kind: EngineKind) -> None:
    def create_engine(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      engine_config: Optional[JsonLike] = None,
                      **values: Any):
        engine_data = load_engine_object(engine_config) if engine_config else None
        engine = build_engine_description(kind, engine_data, values, for_create=True)
        missing = missing_create_options(kind, engine, values)
        if missing:
            raise click.UsageError(_missing_options_message(missing))
        # Every local check runs before connecting, so a mistake is reported without a sign-in or a request.
        request = prepare_engine_create(engine, secret_options=secret_options_from(kind, values),
                                        option_names=option_names(kind, for_create=True))
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        created = create_engine_from_description(client, request)
        click.echo(to_json(redacted_engine(created)))

    create_engine.__doc__ = _help(kind)

    formatted_command(
        group=create_engine_command_group,
        name=kind.name,
        specs=[*option_specs(kind, for_create=True), NAMESPACE_ARG, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG],
        required_section_title='Required Options (unless given in --config):',
    )(create_engine)


for _kind in ENGINE_KINDS:
    _add_create_command(_kind)
