from itertools import islice
from typing import Any, Dict, Optional, List

import click

from dnastack.cli.commands.workbench.engines.engine_input import (
    EngineInputError, EngineOptionError, load_json_object,
)
from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.ewes.engine_models import EngineParamPresetRequest
from dnastack.client.workbench.ewes.models import EngineParamPresetListOptions
from dnastack.common.json_argument_parser import JsonLike
from dnastack.http.session import JsonPatch


@formatted_group('parameters')
def engine_parameters_command_group():
    """Manage engine parameter presets"""


@formatted_command(
    group=engine_parameters_command_group,
    name='list',
    specs=[
        ArgumentSpec(
            name='engine_id',
            arg_names=['--engine'],
            help='Specify the engine whose parameter presets should be listed.',
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def list_engine_parameters(context: Optional[str],
                           endpoint_id: Optional[str],
                           namespace: Optional[str],
                           engine_id: str = None):
    """List an engine's parameter presets"""
    if engine_id is None:
        raise NameError('You must specify engine ID after --engine flag')

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options: EngineParamPresetListOptions = EngineParamPresetListOptions()
    show_iterator(output_format=OutputFormat.JSON, iterator=client.list_engine_param_presets(engine_id, list_options))


@formatted_command(
    group=engine_parameters_command_group,
    name='describe',
    specs=[
        ArgumentSpec(
            name='preset_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The preset id.',
            required=True,
            multiple=True,
        ),
        ArgumentSpec(
            name='engine_id',
            arg_names=['--engine'],
            help='Specify the engine whose parameter presets should be described.',
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def describe_engine_parameters(context: Optional[str],
                               endpoint_id: Optional[str],
                               namespace: Optional[str],
                               engine_id: str = None,
                               preset_id: List[str] = None):
    """Describe one or more parameter presets"""
    if engine_id is None:
        raise NameError('You must specify engine ID after --engine flag')
    if preset_id is None:
        raise NameError('You must specify a preset ID')

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    described_param_presets = [client.get_engine_param_preset(engine_id=engine_id, param_preset_id=param_preset_id)
                               for param_preset_id in preset_id]
    click.echo(to_json(normalize(described_param_presets)))


@formatted_command(
    group=engine_parameters_command_group,
    name='get-default',
    specs=[
        ArgumentSpec(
            name='engine_id',
            arg_names=['--engine'],
            help='Specify the engine whose default parameter preset should be shown.',
            required=True,
        ),
        ArgumentSpec(
            name='id_only',
            arg_names=['--id'],
            help='Only output the preset id',
            type=bool,
            required=False,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def get_default_engine_parameters(context: Optional[str],
                                  endpoint_id: Optional[str],
                                  namespace: Optional[str],
                                  engine_id: str,
                                  id_only: bool = False):
    """Get an engine's default parameter preset"""
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    presets = client.list_engine_param_presets(engine_id, EngineParamPresetListOptions())
    default_preset = next((p for p in presets if p.default), None)
    if default_preset is None:
        raise EngineInputError(f"Engine '{engine_id}' has no default parameter preset.")
    click.echo(default_preset.id if id_only else to_json(normalize(default_preset)))


def _engine_arg(outcome: str) -> ArgumentSpec:
    return ArgumentSpec(
        name='engine_id',
        arg_names=['--engine'],
        help=f'Specify the engine whose parameter preset should be {outcome}.',
        required=True,
    )


_VALUES_HELP = ('The parameter values the preset supplies, as a non-empty JSON object of parameter name to value: '
                '@path/to/values.json, inline JSON, or - to read stdin.')

PRESET_ID_ARG = ArgumentSpec(
    name='preset_id',
    arg_type=ArgumentType.POSITIONAL,
    help='The preset id.',
    required=True,
)


def _preset_values(values: JsonLike) -> Dict[str, Any]:
    # The UI does not allow a preset without values either.
    preset_values = load_json_object(values, '--values')
    if not preset_values:
        raise EngineOptionError('must not be empty', '--values')
    return preset_values


@formatted_command(
    group=engine_parameters_command_group,
    name='create',
    specs=[
        _engine_arg('created'),
        ArgumentSpec(
            name='name',
            arg_names=['--name'],
            help='The preset name. Names are unique within an engine.',
            required=True,
        ),
        ArgumentSpec(
            name='values',
            arg_names=['--values'],
            help=_VALUES_HELP,
            type=JsonLike,
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def create_engine_parameters(context: Optional[str],
                             endpoint_id: Optional[str],
                             namespace: Optional[str],
                             engine_id: str,
                             name: str,
                             values: JsonLike):
    """
    Create an engine parameter preset

    The first preset of an engine always becomes the default. Use `set-default` to change it.
    """
    preset = EngineParamPresetRequest(name=name, preset_values=_preset_values(values))
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    click.echo(to_json(normalize(client.create_engine_param_preset(engine_id=engine_id, preset=preset))))


@formatted_command(
    group=engine_parameters_command_group,
    name='update',
    specs=[
        PRESET_ID_ARG,
        _engine_arg('updated'),
        ArgumentSpec(
            name='name',
            arg_names=['--name'],
            help='The new preset name. Defaults to the current name.',
        ),
        ArgumentSpec(
            name='values',
            arg_names=['--values'],
            help=f"{_VALUES_HELP} Defaults to the current values. Replaces all of the preset's values.",
            type=JsonLike,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def update_engine_parameters(context: Optional[str],
                             endpoint_id: Optional[str],
                             namespace: Optional[str],
                             preset_id: str,
                             engine_id: str,
                             name: Optional[str] = None,
                             values: Optional[JsonLike] = None):
    """
    Update an engine parameter preset
    """
    if name is None and values is None:
        raise click.UsageError('Nothing to update: pass --name or --values.')
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    existing = client.get_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id)
    preset = EngineParamPresetRequest(
        name=name or existing.name,
        default=bool(existing.default),
        preset_values=_preset_values(values) if values else existing.preset_values,
    )
    updated = client.update_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id,
                                                preset=preset, if_match=existing.etag)
    click.echo(to_json(normalize(updated)))


@formatted_command(
    group=engine_parameters_command_group,
    name='set-default',
    specs=[
        PRESET_ID_ARG,
        _engine_arg('set as the default'),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def set_default_engine_parameters(context: Optional[str],
                                  endpoint_id: Optional[str],
                                  namespace: Optional[str],
                                  preset_id: str,
                                  engine_id: str):
    """Set an engine's default parameter preset"""
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    existing = client.get_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id)
    updated = client.patch_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id,
                                               patches=[JsonPatch(op='replace', path='/default', value=True)],
                                               if_match=existing.etag)
    click.echo(to_json(normalize(updated)))


@formatted_command(
    group=engine_parameters_command_group,
    name='delete',
    specs=[
        PRESET_ID_ARG,
        _engine_arg('deleted'),
        ArgumentSpec(
            name='force',
            arg_names=['--force', '-f'],
            help='Force the deletion without prompting for confirmation.',
            type=bool,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def delete_engine_parameters(context: Optional[str],
                             endpoint_id: Optional[str],
                             namespace: Optional[str],
                             preset_id: str,
                             engine_id: str,
                             force: Optional[bool] = False):
    """
    Delete an engine parameter preset

    The engine's default preset cannot be deleted while other presets exist.
    """
    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    if client.get_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id).default:
        # Two are enough to tell whether any other preset exists.
        presets = islice(client.list_engine_param_presets(engine_id, EngineParamPresetListOptions()), 2)
        if any(p.id != preset_id for p in presets):
            raise EngineInputError(f"Preset '{preset_id}' is the default for engine '{engine_id}'. "
                                   f"Make another preset the default with "
                                   f"'omics workbench engines parameters set-default' first.")
    if not force and not click.confirm(
            f"Are you sure you want to delete preset '{preset_id}' of engine '{engine_id}'?"):
        return
    client.delete_engine_param_preset(engine_id=engine_id, param_preset_id=preset_id)
    click.echo(f"Deleted preset '{preset_id}'.")
