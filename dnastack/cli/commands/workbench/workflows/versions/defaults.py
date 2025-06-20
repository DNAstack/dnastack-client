from typing import List, Optional

import click

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, create_sort_arg
from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.workflow.models import (
    WorkflowDefaultsCreateRequest,
    WorkflowDefaultsListOptions,
    WorkflowDefaultsSelector,
    WorkflowDefaultsUpdateRequest,
)
from dnastack.common.json_argument_parser import JsonLike


@formatted_group("defaults")
def workflows_versions_defaults_command_group():
    """Interact with workflow versions defaults"""


@formatted_command(
    group=workflows_versions_defaults_command_group,
    name="create",
    specs=[
        ArgumentSpec(
            name="default_id",
            arg_type=ArgumentType.POSITIONAL,
            help="The id of the default.",
            required=False,
        ),
        ArgumentSpec(
            name="workflow_id",
            arg_names=["--workflow"],
            help="The id of the workflow",
            required=True,
        ),
        ArgumentSpec(
            name="version_id",
            arg_names=["--version"],
            help="The id of the workflow version",
            required=True,
        ),
        ArgumentSpec(
            name="engine",
            arg_names=["--engine"],
            help="The selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="provider",
            arg_names=["--provider"],
            help="The provider selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="region",
            arg_names=["--region"],
            help="The region selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="values",
            arg_names=["--values"],
            help="The values to use when creating the defaults",
            type=JsonLike,
        ),
        ArgumentSpec(
            name="name",
            arg_names=["--name"],
            help="The human readable name of the defaults",
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def create_workflow_defaults(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    workflow_id: str,
    version_id: str,
    provider: Optional[str],
    region: Optional[str],
    engine: Optional[str],
    values: JsonLike,
    name: str,
    default_id: Optional[str],
):
    """
    Create a default for a workflow
    """
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    parsed = values.parsed_value()
    selector = WorkflowDefaultsSelector(engine=engine, provider=provider, region=region)
    workflow_defaults = WorkflowDefaultsCreateRequest(id=default_id, name=name, selector=selector, values=parsed)
    click.echo(
        to_json(
            normalize(
                client.create_workflow_defaults(
                    workflow_id=workflow_id, version_id=version_id, workflow_defaults=workflow_defaults
                )
            )
        )
    )


@formatted_command(
    group=workflows_versions_defaults_command_group,
    name="list",
    specs=[
        ArgumentSpec(
            name="workflow_id",
            arg_names=["--workflow"],
            help="The id of the workflow",
            required=True,
        ),
        ArgumentSpec(
            name="version_id",
            arg_names=["--version"],
            help="The id of the workflow version",
            required=True,
        ),
        NAMESPACE_ARG,
        MAX_RESULTS_ARG,
        PAGINATION_PAGE_ARG,
        PAGINATION_PAGE_SIZE_ARG,
        create_sort_arg('--sort "name:ASC", --sort "name;created_on:DESC;"'),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def list_workflow_defaults(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    max_results: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    sort: Optional[str],
    workflow_id: str,
    version_id: str,
):
    """
    List the defaults available for a workflow
    """
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

    show_iterator(
        output_format=OutputFormat.JSON,
        iterator=client.list_workflow_defaults(
            workflow_id=workflow_id,
            version_id=version_id,
            max_results=max_results,
            list_options=WorkflowDefaultsListOptions(page=page, page_size=page_size, sort=sort),
        ),
    )


@formatted_command(
    group=workflows_versions_defaults_command_group,
    name="describe",
    specs=[
        ArgumentSpec(
            name="default_id",
            arg_type=ArgumentType.POSITIONAL,
            help="The id of the default.",
            required=True,
            multiple=True,
        ),
        ArgumentSpec(
            name="workflow_id",
            arg_names=["--workflow"],
            help="The id of the workflow",
            required=True,
        ),
        ArgumentSpec(
            name="version_id",
            arg_names=["--version"],
            help="The id of the workflow version",
            required=True,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def describe_workflow_defaults(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    workflow_id: str,
    version_id: str,
    default_id: List[str],
):
    """
    Describe one or more default values for a workflow
    """

    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

    if not default_id:
        click.echo("You must specify at least one default id")
        exit(1)

    workflow_defaults = [
        client.get_workflow_defaults(workflow_id=workflow_id, version_id=version_id, default_id=default_id)
        for default_id in default_id
    ]
    click.echo(to_json(normalize(workflow_defaults)))


@formatted_command(
    group=workflows_versions_defaults_command_group,
    name="update",
    specs=[
        ArgumentSpec(
            name="default_id",
            arg_type=ArgumentType.POSITIONAL,
            help="The id of the default.",
            required=True,
        ),
        ArgumentSpec(
            name="workflow_id",
            arg_names=["--workflow"],
            help="The id of the workflow",
            required=True,
        ),
        ArgumentSpec(
            name="version_id",
            arg_names=["--version"],
            help="The id of the workflow version",
            required=True,
        ),
        ArgumentSpec(
            name="engine",
            arg_names=["--engine"],
            help="The selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="provider",
            arg_names=["--provider"],
            help="The provider selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="region",
            arg_names=["--region"],
            help="The region selector to use when creating the defaults",
        ),
        ArgumentSpec(
            name="values",
            arg_names=["--values"],
            help="The values to use when creating the defaults",
            type=JsonLike,
        ),
        ArgumentSpec(
            name="name",
            arg_names=["--name"],
            help="The human readable name of the defaults",
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def update_workflow_defaults(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    workflow_id: str,
    version_id: str,
    name: str,
    provider: Optional[str],
    region: Optional[str],
    engine: Optional[str],
    values: JsonLike,
    default_id: str,
):
    """
    Update a default for a workflow
    """
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    parsed = values.parsed_value()
    selector = WorkflowDefaultsSelector(engine=engine, provider=provider, region=region)
    workflow_defaults = WorkflowDefaultsUpdateRequest(name=name, selector=selector, values=parsed)
    existing = client.get_workflow_defaults(workflow_id=workflow_id, version_id=version_id, default_id=default_id)
    click.echo(
        to_json(
            normalize(
                client.update_workflow_defaults(
                    workflow_id=workflow_id,
                    version_id=version_id,
                    default_id=default_id,
                    if_match=existing.etag,
                    workflow_defaults=workflow_defaults,
                )
            )
        )
    )


@formatted_command(
    group=workflows_versions_defaults_command_group,
    name="delete",
    specs=[
        ArgumentSpec(
            name="default_id",
            arg_type=ArgumentType.POSITIONAL,
            help="The id of the default.",
            required=True,
        ),
        ArgumentSpec(
            name="workflow_id",
            arg_names=["--workflow"],
            help="The id of the workflow",
            required=True,
        ),
        ArgumentSpec(
            name="version_id",
            arg_names=["--version"],
            help="The id of the workflow version",
            required=True,
        ),
        NAMESPACE_ARG,
        ArgumentSpec(
            name="force",
            arg_names=["--force", "-f"],
            help="Force the deletion of the workflow defaults",
            type=bool,
        ),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def delete_workflow_defaults(
    context: Optional[str],
    endpoint_id: Optional[str],
    namespace: Optional[str],
    workflow_id: str,
    version_id: str,
    default_id: str,
    force: Optional[bool],
):
    """
    Delete a default for a workflow
    """
    client = get_workflow_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    if not force:
        click.confirm(f"Are you sure you want to delete the workflow defaults with id {default_id}?", abort=True)
    existing = client.get_workflow_defaults(workflow_id=workflow_id, version_id=version_id, default_id=default_id)
    client.delete_workflow_defaults(
        workflow_id=workflow_id, version_id=version_id, default_id=default_id, if_match=existing.etag
    )
    click.echo("Deleted...")
