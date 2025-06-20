from typing import Optional

import click
from click import Group

from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, get_samples_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.samples.models import SampleListOptions


def init_samples_commands(group: Group):
    @formatted_command(
        group=group,
        name="list",
        specs=[
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def list_samples(context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str]):
        """
        List samples
        docs: https://docs.dnastack.com/docs/samples-list
        """

        client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        list_options: SampleListOptions = SampleListOptions()
        samples_list = client.list_samples(list_options)
        show_iterator(output_format=OutputFormat.JSON, iterator=samples_list)

    @formatted_command(
        group=group,
        name="describe",
        specs=[
            ArgumentSpec(
                name="sample_id",
                arg_type=ArgumentType.POSITIONAL,
                help="The id of the sample to describe.",
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def describe_samples(context: Optional[str], endpoint_id: Optional[str], namespace: Optional[str], sample_id: str):
        """
        Describe a sample

        docs: https://docs.dnastack.com/docs/samples-describe
        """
        client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        described_sample = client.get_sample(sample_id)
        click.echo(to_json(normalize(described_sample)))
