from typing import List, Optional

import click

from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_ewes_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.ewes.models import EngineParamPresetListOptions


@formatted_group("parameters")
def engine_parameters_command_group():
    """List and describe engine parameters"""


@formatted_command(
    group=engine_parameters_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="engine_id",
            arg_names=["--engine"],
            help="Specify the engine whose parameters should be listed.",
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_engine_parameters(
    context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str], engine_id: str = None
):
    """
    Lists engine parameter preset values
    """
    if engine_id is None:
        raise NameError("You must specify engine ID after --engine flag")

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options: EngineParamPresetListOptions = EngineParamPresetListOptions()
    show_iterator(output_format=OutputFormat.JSON, iterator=client.list_engine_param_presets(engine_id, list_options))


@formatted_command(
    group=engine_parameters_command_group,
    name="describe",
    specs=[
        ArgumentSpec(
            name="preset_id",
            arg_type=ArgumentType.POSITIONAL,
            help="The specific preset parameter ID to retrieve information for.",
            required=True,
            multiple=True,
        ),
        ArgumentSpec(
            name="engine_id",
            arg_names=["--engine"],
            help="Specify the engine whose parameters should be described.",
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def describe_engine_parameters(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    engine_id: str = None,
    preset_id: List[str] = None,
):
    """
    Describes an engine's parameter preset values
    """
    if engine_id is None:
        raise NameError("You must specify engine ID after --engine flag")
    if preset_id is None:
        raise NameError("You must specify a preset ID")

    client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    described_param_presets = [
        client.get_engine_param_preset(engine_id=engine_id, param_preset_id=param_preset_id)
        for param_preset_id in preset_id
    ]
    click.echo(to_json(normalize(described_param_presets)))
