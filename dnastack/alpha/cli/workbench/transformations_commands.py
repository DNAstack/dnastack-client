import click
from typing import Optional, List

from dnastack.alpha.cli.workbench.utils import get_alpha_workflow_client
from dnastack.alpha.client.workbench.workflow.models import WorkflowTransformationListOptions, \
    WorkflowTransformationCreate
from dnastack.cli.helpers.command.decorator import command
from dnastack.cli.helpers.command.spec import ArgumentSpec
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat


@click.group('transformations')
def alpha_transformations_command_group():
    """ Interact with workflow transformations """


@command(alpha_transformations_command_group,
         'list',
         specs=[
             ArgumentSpec(
                 name='namespace',
                 arg_names=['--namespace', '-n'],
                 help='An optional flag to define the namespace to connect to. By default, the namespace will be '
                      'extracted from the users credentials.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='workflow_id',
                 arg_names=['--workflow'],
                 help='The id of the workflow.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='version_id',
                 arg_names=['--version'],
                 help='The id of the version.',
                 as_option=True
             ),
         ])
def list_workflow_transformations(context: Optional[str],
                         endpoint_id: Optional[str],
                         namespace: Optional[str],
                         workflow_id: str,
                         version_id: str,
                         ):
    """
    List workflow transformations
    """

    client = get_alpha_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    list_options: WorkflowTransformationListOptions = WorkflowTransformationListOptions()
    transformations_list = client.list_workflow_transformations(workflow_id=workflow_id, workflow_version_id=version_id, list_options=list_options)
    show_iterator(output_format=OutputFormat.JSON, iterator=transformations_list)


@command(alpha_transformations_command_group,
         'describe',
         specs=[
             ArgumentSpec(
                 name='namespace',
                 arg_names=['--namespace', '-n'],
                 help='An optional flag to define the namespace to connect to. By default, the namespace will be '
                      'extracted from the users credentials.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='workflow_id',
                 arg_names=['--workflow'],
                 help='The id of the workflow.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='version_id',
                 arg_names=['--version'],
                 help='The id of the version.',
                 as_option=True
             ),
         ])
def describe_workflow_transformation(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     workflow_id: str,
                     version_id: str,
                     transformation_id: str):
    """
    Describe a workflow transformation
    """
    client = get_alpha_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    described_transformation = client.get_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, transformation_id=transformation_id)
    click.echo(to_json(normalize(described_transformation)))


@command(alpha_transformations_command_group,
         "delete",
         specs=[
             ArgumentSpec(
                 name='namespace',
                 arg_names=['--namespace', '-n'],
                 help='An optional flag to define the namespace to connect to. By default, the namespace will be '
                      'extracted from the users credentials.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='force',
                 arg_names=['--force'],
                 help='Force the deletion without prompting for confirmation.',
                 as_option=True,
                 default=False
             ),
             ArgumentSpec(
                 name='workflow_id',
                 arg_names=['--workflow'],
                 help='The id of the workflow.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='version_id',
                 arg_names=['--version'],
                 help='The id of the version.',
                 as_option=True
             ),
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
    client = get_alpha_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    if not force and not click.confirm(
            f'Are you sure you want to delete the transformation with ID "{transformation_id}" '
            f'This action cannot be undone.'):
        return

    transformation = client.get_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, transformation_id=transformation_id)
    if any(label.lower() == "public" for label in transformation.labels):
        click.echo("Public transformations can be deleted only by admin.")
        return

    client.delete_workflow_transformation(workflow_id, version_id, transformation_id)
    click.echo("Deleted...")


@command(alpha_transformations_command_group,
         'create',
         specs=[
             ArgumentSpec(
                 name='namespace',
                 arg_names=['--namespace', '-n'],
                 help='An optional flag to define the namespace to connect to. By default, the namespace will be '
                      'extracted from the users credentials.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='workflow_id',
                 arg_names=['--workflow'],
                 help='The id of the workflow.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='version_id',
                 arg_names=['--version'],
                 help='The id of the version.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='transformation_id',
                 arg_names=['--id'],
                 help='The human readable id of the transformation',
                 as_option=True
             ),
             ArgumentSpec(
                 name='next_transformation_id',
                 arg_names=['--next-transformation'],
                 help='The id of the next transformation. If provided, '
                      'the transformation will have a set order in which transformations are applied.',
                 as_option=True
             ),
             ArgumentSpec(
                 name='labels',
                 arg_names=['--label'],
                 help='A label to apply to the transformation',
                 as_option=True
             ),
         ]
         )
def add_workflow_transformation(context: Optional[str],
                                endpoint_id: Optional[str],
                                namespace: Optional[str],
                                workflow_id: str,
                                version_id: str,
                                script: str,
                                transformation_id: Optional[str],
                                next_transformation_id: Optional[str],
                                labels: List[str]):
    """Create a new workflow transformation"""
    client = get_alpha_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

    workflow_transformation = WorkflowTransformationCreate(
        id=transformation_id,
        next_transformation_id=next_transformation_id,
        script=script,
        labels=labels
    )

    response = client.create_workflow_transformation(workflow_id=workflow_id, workflow_version_id=version_id, workflow_transformation_create_request=workflow_transformation)
    click.echo(to_json(normalize(response)))
