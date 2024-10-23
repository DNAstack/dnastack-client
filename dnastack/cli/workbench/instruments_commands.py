from typing import Optional

import click

from dnastack.cli.workbench.utils import get_samples_client
from dnastack.cli.helpers.command.decorator import command
from dnastack.cli.helpers.command.spec import ArgumentSpec
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.samples.models import InstrumentListOptions
from dnastack.client.workbench.storage.models import PlatformType


@click.group('instruments')
def instruments_command_group():
    """ Interact with instruments """


@command(
    instruments_command_group,
    'list',
    specs=[
        ArgumentSpec(
            name='namespace',
            arg_names=['--namespace'],
            help='Namespace to connect to. By default, the namespace will be extracted from the user credentials.',
            as_option=True
        ),
        ArgumentSpec(
            name='max_results',
            arg_names=['--max-results'],
            help='Limit the maximum number of results printed to the console.',
            type=int,
            as_option=True
        ),
        ArgumentSpec(
            name='page',
            arg_names=['--page'],
            help='Offset page number for jumping to an arbitrary page of results.',
            type=int,
            as_option=True
        ),
        ArgumentSpec(
            name='page_size',
            arg_names=['--page-size'],
            help='Number of results returned per page (default 100).',
            type=int,
            as_option=True
        ),
        ArgumentSpec(
            name='sort',
            arg_names=['--sort'],
            help='Sort the insturments by properties in the form column(:direction)?(;(column(:direction)?)*.',
            as_option=True
        ),
        ArgumentSpec(
            name='platform_type',
            arg_names=['--platform-type'],
            help='Filter the files by the platform type.',
            type=PlatformType,
            as_option=True
        ),
    ]
)
def list_instruments(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        max_results: Optional[int],
        page: Optional[int],
        page_size: Optional[int],
        sort: Optional[str],
        platform_type: Optional[PlatformType],
):
    """
    List instruments.
    """

    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    options = InstrumentListOptions(
        page=page,
        page_size=page_size,
        sort=sort,
        platform_type=platform_type
    )

    instruments_list = client.list_instruments(
        list_options=options,
        max_results=max_results
    )
    show_iterator(output_format=OutputFormat.JSON, iterator=instruments_list)
