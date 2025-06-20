import os
from pathlib import Path
from typing import List, Optional

import click
from click import Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG
from dnastack.cli.commands.workbench.utils import NAMESPACE_ARG
from dnastack.cli.commands.workbench.workflows.utils import (
    _get_author_patch,
    _get_description_patch,
    _get_replace_patch,
    create_missing_directories,
    decode_base64_content,
    decode_readable_file,
    find_file,
    get_workflow_client,
    handle_files_output,
    handle_zip_output,
    write_to_file,
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.workflow.models import WorkflowVersionCreate, WorkflowVersionListOptions
from dnastack.client.workbench.workflow.utils import WorkflowSourceLoader
from dnastack.common.json_argument_parser import FileOrValue


def init_workflows_versions_commands(group: Group):
    @formatted_command(
        group=group,
        name="list",
        specs=[
            ArgumentSpec(
                name="workflow",
                arg_names=["--workflow"],
                help="The workflow id to add the version to.",
                required=True,
            ),
            NAMESPACE_ARG,
            MAX_RESULTS_ARG,
            ArgumentSpec(
                name="include_deleted",
                arg_names=["--include-deleted"],
                help="An optional flag to include deleted workflows in the list",
                type=bool,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def list_versions(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        workflow: str,
        max_results: Optional[int],
        include_deleted: Optional[bool] = False,
    ):
        """
        List the available versions for the given workflow

        docs: https://docs.omics.ai/docs/workflows-versions-list
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        list_options = WorkflowVersionListOptions(deleted=include_deleted)
        show_iterator(
            output_format=OutputFormat.JSON,
            iterator=workflows_client.list_workflow_versions(
                workflow_id=workflow, list_options=list_options, max_results=max_results
            ),
        )

    @formatted_command(
        group=group,
        name="describe",
        specs=[
            ArgumentSpec(
                name="version_id",
                arg_type=ArgumentType.POSITIONAL,
                help="The id of the workflow version to describe.",
                required=True,
                multiple=True,
            ),
            ArgumentSpec(
                name="workflow",
                arg_names=["--workflow"],
                help="The workflow id to add the version to.",
                required=True,
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name="include_deleted",
                arg_names=["--include-deleted"],
                help="An optional flag to include deleted workflows in the list",
                type=bool,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def describe_version(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        workflow: str,
        version_id: List[str],
        include_deleted: Optional[bool] = False,
    ):
        """
        Describe one or more workflow versions for the given workflow

        docs: https://docs.omics.ai/docs/workflows-versions-describe
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        click.echo(
            to_json(
                normalize(
                    [
                        workflows_client.get_workflow_version(
                            workflow_id=workflow, version_id=version_id, include_deleted=include_deleted
                        )
                        for version_id in version_id
                    ]
                )
            )
        )

    @formatted_command(
        group=group,
        name="delete",
        specs=[
            ArgumentSpec(
                name="version_id",
                arg_type=ArgumentType.POSITIONAL,
                help="The id of the workflow version to delete.",
                required=True,
            ),
            ArgumentSpec(
                name="workflow_id",
                arg_names=["--workflow"],
                help="The id of the workflow",
                required=True,
            ),
            ArgumentSpec(
                name="force",
                arg_names=["--force", "-f"],
                help="Force the deletion without prompting for confirmation.",
                type=bool,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def delete_workflow_version(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        workflow_id: str,
        version_id: str,
        force: Optional[bool] = False,
    ):
        """
        Delete an existing workflow version

        docs: https://docs.omics.ai/docs/workflows-versions-delete
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        workflow = workflows_client.get_workflow(workflow_id)
        version = workflows_client.get_workflow_version(workflow_id, version_id)
        if not force and not click.confirm(
            f'Do you want to delete "{version.versionName}" from workflow "{workflow.name}"?'
        ):
            return

        workflows_client.delete_workflow_version(workflow_id, version_id, version.etag)
        click.echo("Deleted...")

    @formatted_command(
        group=group,
        name="create",
        specs=[
            ArgumentSpec(
                name="workflow_file",
                arg_type=ArgumentType.POSITIONAL,
                help="A WDL or supporting text file that you would like to include as part of the new version. "
                "You can specify multiple files at once. The first WDL file specified will become the entry point of the new version.",
                type=FileOrValue,
                required=False,
                multiple=True,
            ),
            ArgumentSpec(
                name="workflow",
                arg_names=["--workflow"],
                help="The workflow id to add the version to.",
                required=True,
            ),
            ArgumentSpec(
                name="name",
                arg_names=["--name"],
                help="The version name to create",
                required=True,
            ),
            ArgumentSpec(
                name="entrypoint",
                arg_names=["--entrypoint"],
                help="A required flag to set the entrypoint for the workflow. "
                "Needs to be a path of a file in a context of the workflow. E.g. main.wdl",
                required=True,
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name="description",
                arg_names=["--description"],
                help="An optional description for the workflow version in markdown format."
                ' You can specify a file by prepending "@" to a path: @<path>',
                type=FileOrValue,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def add_version(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        workflow: str,
        name: str,
        description: FileOrValue,
        entrypoint: str,
        workflow_file: List[FileOrValue],
    ):
        """
        Add a new version to an existing workflow

        To specify the primary descriptor for the workflow,
        use the --entrypoint flag.
        Ensure that this path correctly points to the intended .wdl file,
        as this file serves as the central definition or entrypoint of your workflow.

        Workflow files can encompass a variety of file types, including any standard file or compressed ZIP file.
        The system will recognize and process these files according to their type and content.

        docs: https://docs.omics.ai/docs/workflows-versions-create
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)

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

        create_request = WorkflowVersionCreate(
            version_name=name,
            description=description.value() if description else None,
            entrypoint=entrypoint,
            files=workflow_files_list,
        )

        result = workflows_client.create_version(workflow_id=workflow, workflow_version_create_request=create_request)
        click.echo(to_json(normalize(result)))

    @formatted_command(
        group=group,
        name="update",
        specs=[
            ArgumentSpec(
                name="version_id",
                arg_type=ArgumentType.POSITIONAL,
                help="The id of the workflow version to update.",
                required=True,
            ),
            ArgumentSpec(
                name="workflow_id",
                arg_names=["--workflow"],
                help="The id of the workflow",
                required=True,
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name="version_name",
                arg_names=["--name"],
                help="The new name of the workflow version",
            ),
            ArgumentSpec(
                name="description",
                arg_names=["--description"],
                help="The new description of the workflow version in markdown format."
                ' You can specify a file by prepending "@" to a path: @<path>. To'
                ' unset the description the value should be ""',
                type=FileOrValue,
            ),
            ArgumentSpec(
                name="authors",
                arg_names=["--authors"],
                help="List of authors to update. This value can be a comma separated list",
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def update_workflow_version(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        workflow_id: str,
        version_id: str,
        version_name: Optional[str],
        description: FileOrValue,
        authors: Optional[str],
    ):
        """
        Update an existing workflow version

        docs: https://docs.omics.ai/docs/workflows-versions-update
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)
        workflow_version = workflows_client.get_workflow_version(workflow_id, version_id)

        patch_list = [
            _get_replace_patch("/versionName", version_name),
            _get_description_patch(description),
            _get_author_patch(authors),
        ]
        patch_list = [patch for patch in patch_list if patch]

        if patch_list:
            workflow_version = workflows_client.update_workflow_version(
                workflow_id, version_id, workflow_version.etag, patch_list
            )
            click.echo(to_json(normalize(workflow_version)))
        else:
            raise ValueError("Must specify at least one attribute to update")

    @formatted_command(
        group=group,
        name="files",
        specs=[
            ArgumentSpec(
                name="version_id",
                arg_type=ArgumentType.POSITIONAL,
                help="The id of the workflow version to list files.",
                required=True,
            ),
            ArgumentSpec(
                name="workflow_id",
                arg_names=["--workflow"],
                help="The id of the workflow",
                required=True,
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name="path",
                arg_names=["--path"],
                help="An optional flag to define a path to print the specific file",
            ),
            ArgumentSpec(
                name="output",
                arg_names=["--output"],
                help="An optional flag to define the path where the content should"
                "be saved instead of being printed to the screen",
            ),
            ArgumentSpec(
                name="zip",
                arg_names=["--zip"],
                help="An optional flag that specifies whether the files should be downloaded in a zip folder.",
                type=bool,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def retrieve_workflow_files(
        context: Optional[str],
        endpoint_id: Optional[str],
        namespace: Optional[str],
        path: str = None,
        output: str = None,
        zip: bool = False,
        workflow_id: str = None,
        version_id: str = None,
    ):
        """
        Output the workflow's files
        """
        workflows_client = get_workflow_client(context, endpoint_id, namespace)

        if not workflow_id:
            raise NameError("You must specify workflow ID")

        if not version_id:
            raise NameError("You must specify version ID")

        # get files
        files = workflows_client.get_workflow_files(workflow_id=workflow_id, version_id=version_id)
        if path:
            output_file = find_file(path, files)

            # --path and --zip are defined (--output is checked in the function)
            if zip:
                handle_zip_output(output, [output_file], workflow_id, version_id)

            # --path and --output are defined without --zip
            else:
                if output:
                    content = decode_base64_content(output_file.base64_content)
                    directory = os.path.dirname(output)
                    create_missing_directories(directory)
                    write_to_file(output, content)

                # only --path is defined
                else:
                    content = decode_readable_file(output_file)
                    click.echo(content)
        else:
            # --zip is defined without --path
            if zip:
                handle_zip_output(output, files, workflow_id, version_id)

            # --path and --zip are not defined (--output is checked in the function)
            else:
                handle_files_output(output, files)
