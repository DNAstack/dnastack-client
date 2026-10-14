from typing import Optional, List

import click
from click import style, Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG
from dnastack.cli.commands.workbench.engines.engine_input import EngineInputError
from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.ewes.engine_models import redact_engine_secrets
from dnastack.client.workbench.ewes.models import ExecutionEngine, ExecutionEngineListOptions
from dnastack.http.session import JsonPatch

ENGINE_ID_ARG = ArgumentSpec(
    name='engine_id',
    arg_type=ArgumentType.POSITIONAL,
    help='The engine id.',
    required=True,
)


def redacted_engine(engine: ExecutionEngine) -> dict:
    return redact_engine_secrets(normalize(engine))


def init_engines_commands(group: Group):
    """Initialize engine commands"""

    @formatted_command(
        group=group,
        name='list',
        specs=[
            MAX_RESULTS_ARG,
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_engines(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     max_results: Optional[int]):
        """List engines"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        list_options: ExecutionEngineListOptions = ExecutionEngineListOptions()
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=client.list_engines(list_options, max_results),
                      transform=redacted_engine)

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='engine_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The engine id.',
                required=True,
                multiple=True
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_engines(context: Optional[str],
                         endpoint_id: Optional[str],
                         namespace: Optional[str],
                         engine_id: List[str]):
        """Describe one or more engines"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

        if not engine_id:
            click.echo(style("You must specify at least one engine ID", fg='red'), err=True, color=True)
            exit(1)

        described_engines = [redacted_engine(client.get_engine(engine_id=engine)) for engine in engine_id]
        click.echo(to_json(described_engines))

    @formatted_command(
        group=group,
        name='get-default',
        specs=[
            ArgumentSpec(
                name='id_only',
                arg_names=['--id'],
                help='Only output the engine id',
                type=bool,
                required=False,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def get_default_engine(context: Optional[str],
                           endpoint_id: Optional[str],
                           namespace: Optional[str],
                           id_only: bool = False):
        """Get the namespace's default engine"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        # The service has no default-engine endpoint, so look through every engine for it.
        default_engine = next((e for e in client.list_engines(ExecutionEngineListOptions()) if e.default), None)
        if default_engine is None:
            raise EngineInputError(f"Namespace '{client.namespace}' has no default engine.")
        click.echo(default_engine.id if id_only else to_json(redacted_engine(default_engine)))

    @formatted_command(
        group=group,
        name='set-default',
        specs=[
            ENGINE_ID_ARG,
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def set_default_engine(context: Optional[str],
                           endpoint_id: Optional[str],
                           namespace: Optional[str],
                           engine_id: str):
        """Make an engine the namespace's default engine"""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        existing = client.get_engine(engine_id=engine_id)
        updated = client.patch_engine(engine_id=engine_id,
                                      patches=[JsonPatch(op='replace', path='/default', value=True)],
                                      if_match=existing.version)
        click.echo(to_json(redacted_engine(updated)))

    @formatted_command(
        group=group,
        name='delete',
        specs=[
            ENGINE_ID_ARG,
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
    def delete_engine(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      engine_id: str,
                      force: Optional[bool] = False):
        """
        Delete an engine

        The namespace's default engine cannot be deleted while other engines exist; make another engine the default
        first.
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        if client.get_engine(engine_id=engine_id).default:
            # Two are enough to tell whether any other engine exists.
            engines = client.list_engines(ExecutionEngineListOptions(), max_results=2)
            if any(e.id != engine_id for e in engines):
                raise EngineInputError(f"Engine '{engine_id}' is the default engine of namespace '{client.namespace}'. "
                                       f"Make another engine the default with "
                                       f"'omics workbench engines set-default' first.")
        if not force and not click.confirm(
                f"Are you sure you want to delete engine '{engine_id}' in namespace '{client.namespace}'?"):
            return
        client.delete_engine(engine_id=engine_id)
        click.echo(f"Deleted engine '{engine_id}'.")
