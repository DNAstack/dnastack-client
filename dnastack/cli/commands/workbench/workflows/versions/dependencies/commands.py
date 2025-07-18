import json
from typing import Optional, List

import click

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG
from dnastack.cli.commands.workbench.workflows.utils import (
    get_workflow_client,
    resolve_workflow_dependency,
    WorkflowDependencyParseError
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.workflow.models import (
    WorkflowDependencyCreateRequest,
    WorkflowDependencyUpdateRequest,
    WorkflowDependencyPrerequisite,
    WorkflowDependencyListOptions
)
from dnastack.common.logger import get_logger

logger = get_logger(__name__)


def _resolve_dependencies(workflow_client, dependency_strings: List[str]) -> List[WorkflowDependencyPrerequisite]:
    """
    Parse and resolve a list of dependency strings into WorkflowDependencyPrerequisite objects.
    
    Args:
        workflow_client: The workflow client for resolving latest versions
        dependency_strings: List of dependency strings in format "workflow-id/version-id" or "workflow-id"
        
    Returns:
        List of resolved WorkflowDependencyPrerequisite objects
        
    Raises:
        click.ClickException: If any dependency string is invalid or cannot be resolved
    """
    resolved_dependencies = []
    for dep_str in dependency_strings:
        try:
            dep_workflow_id, dep_version_id = resolve_workflow_dependency(workflow_client, dep_str)
            resolved_dependencies.append(WorkflowDependencyPrerequisite(
                workflow_id=dep_workflow_id,
                workflow_version_id=dep_version_id
            ))
        except WorkflowDependencyParseError as e:
            raise click.ClickException(f"Invalid dependency format '{dep_str}': {e}")
        except Exception as e:
            raise click.ClickException(f"Error resolving dependency '{dep_str}': {e}")
    
    return resolved_dependencies

WORKFLOW_ID_ARG = ArgumentSpec(
    name='workflow_id',
    arg_names=['--workflow'],
    help='The workflow ID',
    required=True
)

VERSION_ID_ARG = ArgumentSpec(
    name='version_id',
    arg_names=['--version'],
    help='The workflow version ID',
    required=True
)

DEPENDENCY_NAME_ARG = ArgumentSpec(
    name='name',
    arg_names=['--name'],
    help='The dependency name',
    required=True
)

DEPENDENCY_ARG = ArgumentSpec(
    name='dependencies',
    arg_names=['--dependency'],
    help='Workflow dependency in format "workflow-id/version-id" or "workflow-id" (can be specified multiple times)',
    multiple=True,
    required=True
)

GLOBAL_ARG = ArgumentSpec(
    name='global_action',
    arg_names=['--global'],
    help='Create a global dependency (admin only)',
    type=bool
)

FORCE_ARG = ArgumentSpec(
    name='force',
    arg_names=['--force'],
    help='Skip confirmation prompt',
    type=bool
)


@formatted_group(name='dependencies')
def dependencies():
    """Manage workflow version dependencies"""
    pass


@formatted_command(
    group=dependencies,
    name='create',
    specs=[
        CONTEXT_ARG,
        NAMESPACE_ARG,
        SINGLE_ENDPOINT_ID_ARG,
        WORKFLOW_ID_ARG,
        VERSION_ID_ARG,
        DEPENDENCY_NAME_ARG,
        DEPENDENCY_ARG,
        GLOBAL_ARG
    ]
)
def create(context: Optional[str] = None,
           namespace: Optional[str] = None,
           endpoint_id: Optional[str] = None,
           workflow_id: str = None,
           version_id: str = None,
           name: str = None,
           dependencies: List[str] = None,
           global_action: bool = False):
    """Create a new workflow version dependency"""

    workflow_client = get_workflow_client(
        context_name=context,
        endpoint_id=endpoint_id,
        namespace=namespace
    )

    # Parse and resolve dependencies
    resolved_dependencies = _resolve_dependencies(workflow_client, dependencies)

    # Create the dependency request
    create_request = WorkflowDependencyCreateRequest(
        name=name,
        dependencies=resolved_dependencies
    )

    # Create the dependency
    dependency = workflow_client.create_workflow_dependency(
        workflow_id=workflow_id,
        workflow_version_id=version_id,
        workflow_dependency_create_request=create_request,
        admin_only_action=global_action
    )

    click.echo(json.dumps(dependency.dict(), indent=2))


@formatted_command(
    group=dependencies,
    name='list',
    specs=[
        CONTEXT_ARG,
        NAMESPACE_ARG,
        SINGLE_ENDPOINT_ID_ARG,
        WORKFLOW_ID_ARG,
        VERSION_ID_ARG,
        MAX_RESULTS_ARG,
        PAGINATION_PAGE_ARG,
        PAGINATION_PAGE_SIZE_ARG
    ]
)
def list(context: Optional[str] = None,
         namespace: Optional[str] = None,
         endpoint_id: Optional[str] = None,
         workflow_id: str = None,
         version_id: str = None,
         max_results: Optional[int] = None,
         page: Optional[int] = None,
         page_size: Optional[int] = None):
    """List workflow version dependencies"""

    try:
        workflow_client = get_workflow_client(
            context_name=context,
            endpoint_id=endpoint_id,
            namespace=namespace
        )

        # Set up list options
        list_options = WorkflowDependencyListOptions()
        if page is not None:
            list_options.page = page
        if page_size is not None:
            list_options.page_size = page_size

        # Get dependencies
        dependencies_iterator = workflow_client.list_workflow_dependencies(
            workflow_id=workflow_id,
            workflow_version_id=version_id,
            list_options=list_options,
            max_results=max_results
        )

        show_iterator(output_format=OutputFormat.JSON, iterator=dependencies_iterator)

    except Exception as e:
        logger.error(f"Failed to list workflow dependencies: {e}")
        raise click.ClickException(f"Failed to list workflow dependencies: {e}")


@formatted_command(
    group=dependencies,
    name='describe',
    specs=[
        CONTEXT_ARG,
        NAMESPACE_ARG,
        SINGLE_ENDPOINT_ID_ARG,
        WORKFLOW_ID_ARG,
        VERSION_ID_ARG,
        ArgumentSpec(
            name='dependency_ids',
            arg_type=ArgumentType.POSITIONAL,
            help='The dependency IDs to describe',
            multiple=True,
            required=True
        )
    ]
)
def describe(context: Optional[str] = None,
             namespace: Optional[str] = None,
             endpoint_id: Optional[str] = None,
             workflow_id: str = None,
             version_id: str = None,
             dependency_ids: List[str] = None):
    """Describe workflow version dependencies"""

    try:
        workflow_client = get_workflow_client(
            context_name=context,
            endpoint_id=endpoint_id,
            namespace=namespace
        )

        # Get each dependency
        dependencies = []
        for dependency_id in dependency_ids:
            try:
                dependency = workflow_client.get_workflow_dependency(
                    workflow_id=workflow_id,
                    workflow_version_id=version_id,
                    dependency_id=dependency_id
                )
                dependencies.append(dependency.dict())
            except Exception as e:
                logger.error(f"Failed to get dependency {dependency_id}: {e}")
                raise click.ClickException(f"Failed to get dependency {dependency_id}: {e}")

        # Output as JSON array
        click.echo(json.dumps(dependencies, indent=2))

    except Exception as e:
        logger.error(f"Failed to describe workflow dependencies: {e}")
        raise click.ClickException(f"Failed to describe workflow dependencies: {e}")


@formatted_command(
    group=dependencies,
    name='update',
    specs=[
        CONTEXT_ARG,
        NAMESPACE_ARG,
        SINGLE_ENDPOINT_ID_ARG,
        WORKFLOW_ID_ARG,
        VERSION_ID_ARG,
        DEPENDENCY_NAME_ARG,
        DEPENDENCY_ARG,
        GLOBAL_ARG,
        ArgumentSpec(
            name='dependency_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The dependency ID to update',
            required=True
        )
    ]
)
def update(context: Optional[str] = None,
           namespace: Optional[str] = None,
           endpoint_id: Optional[str] = None,
           workflow_id: str = None,
           version_id: str = None,
           name: str = None,
           dependencies: List[str] = None,
           global_action: bool = False,
           dependency_id: str = None):
    """Update a workflow version dependency"""

    try:
        workflow_client = get_workflow_client(
            context_name=context,
            endpoint_id=endpoint_id,
            namespace=namespace
        )

        # Parse and resolve dependencies
        resolved_dependencies = _resolve_dependencies(workflow_client, dependencies)

        # Create the update request
        update_request = WorkflowDependencyUpdateRequest(
            name=name,
            dependencies=resolved_dependencies
        )

        # Update the dependency
        dependency = workflow_client.update_workflow_dependency(
            workflow_id=workflow_id,
            workflow_version_id=version_id,
            dependency_id=dependency_id,
            workflow_dependency_update_request=update_request,
            admin_only_action=global_action
        )

        click.echo(json.dumps(dependency.dict(), indent=2))

    except Exception as e:
        logger.error(f"Failed to update workflow dependency: {e}")
        raise click.ClickException(f"Failed to update workflow dependency: {e}")


@formatted_command(
    group=dependencies,
    name='delete',
    specs=[
        CONTEXT_ARG,
        NAMESPACE_ARG,
        SINGLE_ENDPOINT_ID_ARG,
        WORKFLOW_ID_ARG,
        VERSION_ID_ARG,
        GLOBAL_ARG,
        FORCE_ARG,
        ArgumentSpec(
            name='dependency_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The dependency ID to delete',
            required=True
        )
    ]
)
def delete(context: Optional[str] = None,
           namespace: Optional[str] = None,
           endpoint_id: Optional[str] = None,
           workflow_id: str = None,
           version_id: str = None,
           global_action: bool = False,
           force: bool = False,
           dependency_id: str = None):
    """Delete a workflow version dependency"""

    try:
        workflow_client = get_workflow_client(
            context_name=context,
            endpoint_id=endpoint_id,
            namespace=namespace
        )

        # Confirm deletion unless --force is used
        if not force:
            if not click.confirm(
                    f"Are you sure you want to delete dependency '{dependency_id}' "
                    f"for workflow '{workflow_id}' version '{version_id}'?"
            ):
                click.echo("Deletion cancelled.")
                return

        # Delete the dependency
        workflow_client.delete_workflow_dependency(
            workflow_id=workflow_id,
            workflow_version_id=version_id,
            dependency_id=dependency_id,
            admin_only_action=global_action
        )

        click.echo(f"Dependency '{dependency_id}' deleted successfully.")

    except Exception as e:
        logger.error(f"Failed to delete workflow dependency: {e}")
        raise click.ClickException(f"Failed to delete workflow dependency: {e}")
