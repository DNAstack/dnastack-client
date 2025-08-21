from typing import Optional, List

import click
from click import Group

from dnastack.cli.commands.workbench.utils import get_samples_client, NAMESPACE_ARG, parse_to_datetime_iso_format
from dnastack.cli.core.command import formatted_command
from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.common.models import State
from dnastack.client.workbench.samples.models import SampleListOptions, Sex, PerspectiveType
from dnastack.client.workbench.storage.models import PlatformType


def init_samples_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            ArgumentSpec(
                name='storage_id',
                arg_names=['--storage-id'],
                help='Returns samples associated with the specified storage id.',
                required=False
            ),
            ArgumentSpec(
                name='platform_type',
                arg_names=['--platform-type'],
                help='Returns samples associated with the specified platform type.',
                required=False,
                type=PlatformType
            ),
            ArgumentSpec(
                name='instrument_id',
                arg_names=['--instrument-id'],
                help='Returns samples associated with the specified instrument',
                required=False
            ),
            ArgumentSpec(
                name='workflow_id',
                arg_names=['--workflow'],
                help="Returns samples that were processed by the specified workflow. "
                     "If the workflow version is not specified returns all workflow versions. " 
                     "If the --perspective option is set to 'WORKFLOW', then the workflow-id is required",
                required=False
            ),
            ArgumentSpec(
                name='workflow_version_id',
                arg_names=['--workflow-version'],
                help="Returns samples that were processed by the specified workflow version. "
                     "If the workflow is not specified returns all workflows. "
                     "If the --perspective option is set to 'WORKFLOW', then the workflow-version-id is required",
                required=False
            ),
            ArgumentSpec(
                name='states',
                arg_names=['--state'],
                help='Returns samples with workflows in the specified states',
                required=False,
                type=State,
                multiple=True
            ),
            ArgumentSpec(
                name='family_ids',
                arg_names=['--family-id'],
                help='Returns samples that are part of the specified families',
                required=False,
                multiple=True
            ),
            ArgumentSpec(
                name='sample_ids',
                arg_names=['--sample'],
                help='Returns samples with the specified id',
                required=False,
                multiple=True
            ),
            ArgumentSpec(
                name='sexes',
                arg_names=['--sex'],
                help='Returns samples with the specified sex',
                required=False,
                multiple=True
            ),
            ArgumentSpec(
                name='perspective',
                arg_names=['--perspective'],
                help='Returns samples from the specified perspective. '
                     'If not specified, returns samples from the default perspective. '
                     'If perspective is set to "WORKFLOW", then the workflow-id is required. '
                     'When the perspective is set to "WORKFLOW", all samples are returned with a flag indicating '
                     'whether they were processed by the specified workflow or not.',
                required=False,
                type=PerspectiveType
            ),
            ArgumentSpec(
                name='search',
                arg_names=['--search'],
                help='Searches samples by the specified search term. The search term is matched against sample id',
                required=False
            ),
            ArgumentSpec(
                name='since',
                arg_names=['--created-since'],
                help='Returns samples created after the specified date. '
                     'The timestamp can be in iso date, or datetime format. '
                     'e.g.: -t "2022-11-23", -t "2022-11-23T23:59:59.999Z"',
                required=False
            ),
            ArgumentSpec(
                name='until',
                arg_names=['--created-until'],
                help='Returns samples created before the specified date. '
                     'The timestamp can be in iso date, or datetime format. '
                     'e.g.: -t "2022-11-23", -t "2022-11-23T23:59:59.999Z"',
                required=False
            ),
            ArgumentSpec(
                name='analyzed',
                arg_names=['--analyzed'],
                help='Returns samples that have been analyzed.',
                required=False,
                type=bool
            ),
            ArgumentSpec(
                name='not_analyzed',
                arg_names=['--not-analyzed'],
                help='Returns samples that have not been analyzed.',
                required=False,
                type=bool
            )

        ]
    )
    def list_samples(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     max_results: Optional[int] = None,
                     page: Optional[int] = None,
                     page_size: Optional[int] = None,
                     storage_id: Optional[str] = None,
                     platform_type: Optional[PlatformType] = None,
                     instrument_id: Optional[str] = None,
                     workflow_id: Optional[str] = None,
                     workflow_version_id: Optional[str] = None,
                     states: Optional[List[State]] = None,
                     family_ids: Optional[List[str]] = None,
                     sample_ids: Optional[List[str]] = None,
                     sexes: Optional[List[Sex]] = None,
                     perspective: Optional[PerspectiveType] = None,
                     search: Optional[str] = None,
                     since: Optional[str] = None,
                     until: Optional[str] = None,
                     analyzed: Optional[bool] = None,
                     not_analyzed: Optional[bool] = None
                     ):
        """
        List samples
        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/samples-list
        """

        if not states:
            if analyzed:
                states = [State.QUEUED, State.INITIALIZING, State.RUNNING, State.COMPLETE]
            elif not_analyzed:
                states = [State.NOT_PROCESSED]

        if perspective == PerspectiveType.workflow and not workflow_id:
            raise click.UsageError('When perspective is set to "WORKFLOW", the workflow-id is required.')
        client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        list_options: SampleListOptions = SampleListOptions(
            page=page,
            page_size=page_size,
            storage_id=storage_id,
            platform_type=platform_type,
            instrument_id=instrument_id,
            workflow_id=workflow_id,
            workflow_version_id=workflow_version_id,
            states=states,
            family_id=family_ids,
            id=sample_ids,
            sexes=sexes,
            perspective=perspective,
            search=search,
            since=parse_to_datetime_iso_format(since, start_of_day=True),
            until=parse_to_datetime_iso_format(until, end_of_day=True)
        )
        samples_list = client.list_samples(list_options,max_results)
        show_iterator(output_format=OutputFormat.JSON, iterator=samples_list)

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='sample_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The id of the sample to describe.',
                required=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_samples(context: Optional[str],
                         endpoint_id: Optional[str],
                         namespace: Optional[str],
                         sample_id: str):
        """
        Describe a sample

        docs: https://docs.dnastack.com/docs/samples-describe
        """
        client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        described_sample = client.get_sample(sample_id)
        click.echo(to_json(normalize(described_sample)))
