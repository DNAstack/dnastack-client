from typing import Optional, List

import click
from click import style

from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG
from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.workflow.models import WorkflowTransformationListOptions, \
    WorkflowTransformationCreate
from dnastack.common.json_argument_parser import FileOrValue


@formatted_group('transformations')
def workflows_versions_transformations_command_group():
    """ Interact with transformations """


@formatted_command(
    group=workflows_versions_transformations_command_group,
    name='list',
    specs=[
        ArgumentSpec(
            name='workflow_id',
            arg_names=['--workflow'],
            help='The id of the workflow',
            required=True,
        ),
        ArgumentSpec(
            name='version_id',
            arg_names=['--version'],
            help='The id of the workflow version',
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def list_workflow_transformations(context: Optional[str],
                         endpoint_id: Optional[str],
                         namespace: Optional[str],
                         workflow_id: str,
                         version_id: str):
    """
    List workflow transformations
    """

    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options: WorkflowTransformationListOptions = WorkflowTransformationListOptions()
    transformations_list = client.list_workflow_transformations(workflow_id=workflow_id, workflow_version_id=version_id, list_options=list_options)
    show_iterator(output_format=OutputFormat.JSON, iterator=transformations_list)


@formatted_command(
    group=workflows_versions_transformations_command_group,
    name='describe',
    specs=[
        ArgumentSpec(
            name='transformation_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The id of the transformation.',
            required=True,
            multiple=True,
        ),
        ArgumentSpec(
            name='workflow_id',
            arg_names=['--workflow'],
            help='The id of the workflow',
            required=True,
        ),
        ArgumentSpec(
            name='version_id',
            arg_names=['--version'],
            help='The id of the workflow version',
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def describe_workflow_transformation(context: Optional[str],
                                     endpoint_id: Optional[str],
                                     namespace: Optional[str],
                                     workflow_id: str,
                                     version_id: str,
                                     transformation_id: List[str]):
    """
    Describe one or more workflow transformations
    """
    if not transformation_id:
        click.echo(style("You must specify at least one transformation ID", fg='red'), err=True, color=True)
        exit(1)

    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    described_transformations = [client.get_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, transformation_id=transformation_id)
                                 for transformation_id in transformation_id]
    click.echo(to_json(normalize(described_transformations)))


@formatted_command(
    group=workflows_versions_transformations_command_group,
    name="delete",
    specs=[
        ArgumentSpec(
            name='transformation_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The id of the transformation.',
            required=True,
        ),
        ArgumentSpec(
            name='workflow_id',
            arg_names=['--workflow'],
            help='The id of the workflow',
            required=True,
        ),
        ArgumentSpec(
            name='version_id',
            arg_names=['--version'],
            help='The id of the workflow version',
            required=True,
        ),
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
def delete_workflow_transformation(context: Optional[str],
                                   endpoint_id: Optional[str],
                                   namespace: Optional[str],
                                   workflow_id: str,
                                   version_id: str,
                                   transformation_id: str,
                                   force: Optional[bool] = False):
    """
    Delete an existing workflow transformation
    """
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    if not force and not click.confirm(
            f'Are you sure you want to delete the transformation with ID "{transformation_id}" '
            f'This action cannot be undone.'):
        return

    transformation = client.get_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, transformation_id=transformation_id)
    if any(label.lower() == "public" for label in transformation.labels):
        click.echo("You are not allowed to delete public transformations.")
        exit(1)

    client.delete_workflow_transformation(workflow_id, version_id, transformation_id)
    click.echo("Deleted...")


@formatted_command(
    group=workflows_versions_transformations_command_group,
    name='create',
    specs=[
        ArgumentSpec(
            name='script',
            arg_type=ArgumentType.POSITIONAL,
            help='The transformation script to execute. '
                 'The script can be provided as a string or a path to a JavaScript file (needs to be prefixed with @).'
                 ' The script should be a function that takes a single argument, context, and returns a modified context object.'
                 ' You do not need to return the entire context object, only the parts that you want to modify. '
                 'Results of transformations are merged into the final context object. '
                 'The context object is a JSON object that contains the workflow parameters and other metadata.',
            type=FileOrValue,
            required=True,
        ),
        ArgumentSpec(
            name='workflow_id',
            arg_names=['--workflow'],
            help='The id of the workflow',
            required=True,
        ),
        ArgumentSpec(
            name='version_id',
            arg_names=['--version'],
            help='The id of the workflow version',
            required=True,
        ),
        NAMESPACE_ARG,
        ArgumentSpec(
            name='transformation_id',
            arg_names=['--id'],
            help='The human readable id of the transformation',
        ),
        ArgumentSpec(
            name='next_transformation_id',
            arg_names=['--next-transformation'],
            help='The id of the next transformation. If provided, '
                 'the transformation will have a set order in which transformations are applied.',
        ),
        ArgumentSpec(
            name='labels',
            arg_names=['--label'],
            help='A label to apply to the transformation',
            multiple=True
        ),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def add_workflow_transformation(context: Optional[str],
                                endpoint_id: Optional[str],
                                namespace: Optional[str],
                                workflow_id: str,
                                version_id: str,
                                script: FileOrValue,
                                transformation_id: Optional[str],
                                next_transformation_id: Optional[str],
                                labels: List[str]):
    """Create a new workflow transformation"""
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

    workflow_transformation = WorkflowTransformationCreate(
        id=transformation_id,
        next_transformation_id=next_transformation_id,
        script=script.value(),
        labels=labels
    )

    response = client.create_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, workflow_transformation_create_request=workflow_transformation)
    click.echo(to_json(normalize(response)))

