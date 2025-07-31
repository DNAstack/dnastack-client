from pathlib import Path
from typing import Optional, List

import click
from click import style, Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG, create_sort_arg
from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client, _get_replace_patch, \
    _get_description_patch, _get_author_patch, _get_labels_patch
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.workflow.models import WorkflowCreate, WorkflowSource, \
    WorkflowListOptions
from dnastack.client.workbench.workflow.utils import WorkflowSourceLoader
from dnastack.common.json_argument_parser import FileOrValue


def init_workflows_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            NAMESPACE_ARG,
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            create_sort_arg('--sort "last_updated_at:ASC", --sort "name;source:DESC;"'),
            ArgumentSpec(
                name='order',
                arg_names=['--order'],
                help='This flag is now deprecated, please use --sort instead. '
                     'Define the ordering of the results. '
                     'The value should return to the attribute name to order the results by. '
                     'By default, results are returned in descending order. '
                     'To change the direction of ordering include the "ASC" or "DESC" string after the column. '
                     'e.g.: --O "end_time", --O "end_time ASC"',
            ),
            ArgumentSpec(
                name='source',
                arg_names=['--source'],
                help='Filter the results to only include workflows from the defined source. '
                     'Note: The CUSTOM workflow source has been renamed to Private',
                type=WorkflowSource,
                choices=[e.value for e in WorkflowSource]
            ),
            ArgumentSpec(
                name='search',
                arg_names=['--search'],
                help='Perform a full text search across various fields using the search value',
            ),
            ArgumentSpec(
                name='include_deleted',
                arg_names=['--include-deleted'],
                help='Include deleted workflows in the list',
                type=bool,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_workflows(context: Optional[str],
                       endpoint_id: Optional[str],
                       namespace: Optional[str],
                       max_results: Optional[int],
                       page: Optional[int],
                       page_size: Optional[int],
                       sort: Optional[str],
                       order: Optional[str],
                       search: Optional[str],
                       source: Optional[WorkflowSource],
                       include_deleted: Optional[bool] = False):
        """
        List workflows

        docs: https://docs.omics.ai/docs/workflows-list
        """
        order_direction = None
        if order:
            order_and_direction = order.split()
            if len(order_and_direction) > 1:
                order = order_and_direction[0]
                order_direction = order_and_direction[1]

        ## Migration
        if source and source == WorkflowSource.custom:
            source = WorkflowSource.private

        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        list_options = WorkflowListOptions(
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            direction=order_direction,
            source=source,
            search=search,
            deleted=include_deleted
        )
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=workflows_client.list_workflows(list_options=list_options, max_results=max_results))


    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='workflow_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The id of the workflow to describe.',
                required=True,
                multiple=True,
            ),
            ArgumentSpec(
                name='include_deleted',
                arg_names=['--include-deleted'],
                help='Include deleted workflows in the list',
                type=bool,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_workflows(context: Optional[str],
                           endpoint_id: Optional[str],
                           namespace: Optional[str],
                           workflow_id: List[str],
                           include_deleted: Optional[bool] = False):
        """
        Describe one or more workflows

        docs: https://docs.omics.ai/docs/workflows-describe
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)

        if not workflow_id:
            click.echo(style("You must specify at least one workflow ID", fg='red'), err=True, color=True)
            exit(1)

        described_workflows = [workflows_client.get_workflow(workflow_id, include_deleted=include_deleted) for workflow_id
                               in workflow_id]
        click.echo(to_json(normalize(described_workflows)))


    @formatted_command(
        group=group,
        name='create',
        specs=[
            ArgumentSpec(
                name='workflow_file',
                arg_type=ArgumentType.POSITIONAL,
                help='A WDL or supporting text file that you would like to upload as part of the workflow. '
                     'You can specify multiple files at once. The first WDL file specified will become the entrypoint of the workflow. '
                     'The CLI transparently handles imports for you, inspecting each WDL and resolving/finding relative imports that are defined in the files. '
                     'Because of this, it is typically sufficient to only specify the entrypoint of the workflow, since all other files will be discoverable from that',
                type=FileOrValue,
                required=False,
                multiple=True,
            ),
            ArgumentSpec(
                name='entrypoint',
                arg_names=['--entrypoint'],
                help='A required flag to set the entrypoint for the workflow. '
                     'Needs to be a path of a file in a context of the workflow. E.g. main.wdl',
                required=True,
            ),
            ArgumentSpec(
                name='name',
                arg_names=['--name'],
                help='Set a workflow name. If omitted, the name within the workflow will be used',
            ),
            ArgumentSpec(
                name='version_name',
                arg_names=['--version-name'],
                help='Set the version name. If omitted, v1.0.0 will be used',
            ),
            ArgumentSpec(
                name='description',
                arg_names=['--description'],
                help='Set a description for the workflow'
                     ' You can specify a file by prepending "@" to a path: @<path>',
                type=FileOrValue,
            ),
            ArgumentSpec(
                name='organization',
                arg_names=['--organization'],
                help='Set a organization for the workflow',
            ),
            ArgumentSpec(
                name='labels',
                arg_names=['--label'],
                help='Label for the workflow. This flag can be repeated to specify multiple labels (e.g., --label tag1 --label tag2)',
                multiple=True,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def create_workflow(context: Optional[str],
                        endpoint_id: Optional[str],
                        namespace: Optional[str],
                        name: Optional[str],
                        version_name: Optional[str],
                        description: FileOrValue,
                        organization: Optional[str],
                        entrypoint: str,
                        workflow_file: List[FileOrValue],
                        labels: List[str]):
        """
        Create a new workflow

        To specify the primary descriptor for the workflow,
        use the --entrypoint flag.
        Ensure that this path correctly points to the intended .wdl file,
        as this file serves as the central definition or entrypoint of your workflow.

        Workflow files can encompass a variety of file types, including any standard file or compressed ZIP file.
        The system will recognize and process these files according to their type and content.

        docs: https://docs.omics.ai/docs/workflows-create
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        # Add entrypoint to workflow_files

        workflow_files_list: List[Path] = [Path(f.value()) for f in workflow_file]

        has_zip = any([file.name.endswith("zip") for file in workflow_files_list])
        if has_zip and len(workflow_files_list) > 1:
            raise ValueError("Cannot upload both a zip file and other files at the same time")
        if not has_zip:
            if entrypoint not in workflow_files_list:
                workflow_files_list = [Path(entrypoint)] + workflow_files_list
            loader = WorkflowSourceLoader(entrypoint=entrypoint, source_files=workflow_files_list)
            workflow_files_list = [loader.to_zip()]
            entrypoint = loader.entrypoint

        if labels:
            # Filter out empty labels and strip whitespace
            parsed_labels = [label.strip() for label in labels if label.strip()]
            if parsed_labels:
                label_list = ','.join(parsed_labels)
            else:
                label_list = None
        else:
            label_list = None

        create_request = WorkflowCreate(
            name=name,
            version_name=version_name,
            description=description.value() if description else None,
            organization=organization,
            entrypoint=entrypoint,
            files=workflow_files_list,
            labels=label_list
        )

        result = workflows_client.create_workflow(workflow_create_request=create_request)
        click.echo(to_json(normalize(result)))


    @formatted_command(
        group=group,
        name="delete",
        specs=[
            ArgumentSpec(
                name='workflow_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The id of the workflow to delete.',
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
    def delete_workflow(context: Optional[str],
                        endpoint_id: Optional[str],
                        namespace: Optional[str],
                        workflow_id: str,
                        force: Optional[bool] = False):
        """
        Delete an existing workflow

        docs: https://docs.omics.ai/docs/workflows-delete
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        workflow = workflows_client.get_workflow(workflow_id)
        if not force and not click.confirm(
                f'Do you want to delete "{workflow.name}"?'):
            return

        workflows_client.delete_workflow(workflow.internalId, workflow.etag)
        click.echo("Deleted...")


    @formatted_command(
        group=group,
        name="update",
        specs=[
            ArgumentSpec(
                name='workflow_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The id of the workflow to update.',
                required=True,
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name='name',
                arg_names=['--name'],
                help='The new name of the workflow',
            ),
            ArgumentSpec(
                name='description',
                arg_names=['--description'],
                help='The new description of the workflow in markdown format.'
                     ' You can specify a file by prepending "@" to a path: @<path>. To'
                     ' unset the description the value should be ""',
                type=FileOrValue,
            ),
            ArgumentSpec(
                name='authors',
                arg_names=['--authors'],
                help='A list of authors to update. This value can be a comma separated list, a file or JSON literal',
            ),
            ArgumentSpec(
                name='labels',
                arg_names=['--label'],
                help='Label to apply to the workflow. This flag can be repeated to specify multiple labels (e.g., --label tag1 --label tag2)',
                multiple=True,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def update_workflow(context: Optional[str],
                        endpoint_id: Optional[str],
                        namespace: Optional[str],
                        workflow_id: str,
                        name: Optional[str],
                        description: FileOrValue,
                        authors: Optional[str],
                        labels: List[str]):
        """
        Update an existing workflow

        docs: https://docs.omics.ai/docs/workflows-update
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        workflow = workflows_client.get_workflow(workflow_id)

        patch_list = [
            _get_replace_patch("/name", name),
            _get_description_patch(description),
            _get_author_patch(authors),
            _get_labels_patch(labels)
        ]
        patch_list = [patch for patch in patch_list if patch]

        if patch_list:
            workflow = workflows_client.update_workflow(workflow_id, workflow.etag, patch_list)
            click.echo(to_json(normalize(workflow)))
        else:
            raise ValueError("Must specify at least one attribute to update")





