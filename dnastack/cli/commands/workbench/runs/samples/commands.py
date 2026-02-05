from typing import Optional

import click

from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.client.workbench.ewes.models import SimpleSample


def init_samples_commands(group):

    @formatted_command(
        group=group,
        name='add',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_names=['--run-id'],
                help='The ID of the run to add samples to',
                required=True,
            ),
            ArgumentSpec(
                name='samples',
                arg_names=['--sample'],
                help='Sample ID to add to the run. Can be specified multiple times.',
                as_option=True,
                multiple=True,
                required=True,
            ),
            ArgumentSpec(
                name='storage_account_id',
                arg_names=['--storage-account'],
                help='The storage account ID to associate with the samples.',
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def add_samples(context: Optional[str] = None,
                    endpoint_id: Optional[str] = None,
                    namespace: Optional[str] = None,
                    run_id: str = None,
                    samples: tuple = (),
                    storage_account_id: Optional[str] = None):
        """Add samples to a run. Existing samples are preserved."""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        run = client.get_run(run_id)
        existing = run.request.samples if run.request and run.request.samples else []

        existing_ids = {s.id for s in existing}
        new_samples = list(existing)
        for sample_id in samples:
            if sample_id not in existing_ids:
                new_samples.append(SimpleSample(id=sample_id, storage_account_id=storage_account_id))

        result = client.update_run_samples(run_id, new_samples)
        click.echo(to_json(normalize(result)))

    @formatted_command(
        group=group,
        name='remove',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_names=['--run-id'],
                help='The ID of the run to remove samples from',
                required=True,
            ),
            ArgumentSpec(
                name='samples',
                arg_names=['--sample'],
                help='Sample ID to remove from the run. Can be specified multiple times.',
                as_option=True,
                multiple=True,
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def remove_samples(context: Optional[str] = None,
                       endpoint_id: Optional[str] = None,
                       namespace: Optional[str] = None,
                       run_id: str = None,
                       samples: tuple = ()):
        """Remove samples from a run."""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        run = client.get_run(run_id)
        existing = run.request.samples if run.request and run.request.samples else []

        remove_ids = set(samples)
        remaining = [s for s in existing if s.id not in remove_ids]

        result = client.update_run_samples(run_id, remaining)
        click.echo(to_json(normalize(result)))

    @formatted_command(
        group=group,
        name='clear',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_names=['--run-id'],
                help='The ID of the run to clear all samples from',
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def clear_samples(context: Optional[str] = None,
                      endpoint_id: Optional[str] = None,
                      namespace: Optional[str] = None,
                      run_id: str = None):
        """Remove all samples from a run."""
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        result = client.update_run_samples(run_id, [])
        click.echo(to_json(normalize(result)))
