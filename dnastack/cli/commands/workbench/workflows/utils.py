import base64
import binascii
import os
import re
import zipfile as zf
from typing import Optional, List, Union

import click
from imagination import container

from dnastack.cli.commands.workbench.utils import _populate_workbench_endpoint
from dnastack.cli.commands.workbench.utils import get_user_client
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory
from dnastack.client.workbench.workflow.client import WorkflowClient
from dnastack.client.workbench.workflow.models import WorkflowFile, WorkflowFileType
from dnastack.common.json_argument_parser import FileOrValue
from dnastack.http.session import JsonPatch


class UnableToFindFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UnableToDecodeFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnableToDisplayFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UnableToCreateFilePathError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnableToWriteToFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class IncorrectFlagError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def get_workflow_client(context_name: Optional[str] = None,
                        endpoint_id: Optional[str] = None,
                        namespace: Optional[str] = None) -> WorkflowClient:
    if not namespace:
        user_client = get_user_client(context_name=context_name, endpoint_id=endpoint_id)
        namespace = user_client.get_user_config().default_namespace

    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(WorkflowClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(WorkflowClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)

def get_descriptor_file(files_list: List[WorkflowFile]):
    for file in files_list:
        if file.file_type == WorkflowFileType.primary:
            return file
    raise UnableToFindFileError("No primary descriptor file found for the workflow. Must specify a file's "
                                "path using --path flag.")


def find_file(file_path: str, files_list: List[WorkflowFile]):
    for file in files_list:
        if file_path == file.path:
            return file
    raise UnableToFindFileError(f'File not found at {file_path}')


def decode_base64_content(base64_content: str):
    try:
        return base64.b64decode(base64_content)
    except binascii.Error as e:
        raise UnableToDecodeFileError(f"Failed to decode base64 content: {e}")


def decode_readable_file(file: WorkflowFile):
    if file.content_type == "application/json" or file.content_type.startswith("text/"):
        return decode_base64_content(file.base64_content)
    else:
        raise UnableToDisplayFileError(f"File cannot be displayed due to unsupported content type: {file.content_type}")


def is_folder(path):
    base, extension = os.path.splitext(path)
    return extension == ""


def is_zip_file(path):
    base, extension = os.path.splitext(path)
    return extension.lower() == ".zip"


def create_missing_directories(path):
    if not os.path.exists(path) and path != "":
        try:
            os.makedirs(path)
        except Exception:
            raise UnableToCreateFilePathError(f"Could not create file path: {path}")


def handle_zip_output(output: str, files: List[WorkflowFile], workflow_name, workflow_version):
    output_path = None
    if not output:
        output = os.getcwd()
        output_path = os.path.join(output, f'{workflow_name}-{workflow_version}-files.zip')
        click.secho(f"No --output flag specified. Downloading zip file as "
                    f"{workflow_name}-{workflow_version}-files.zip into current directory", fg='green')

    # checks if output is a directory
    elif is_folder(output):
        create_missing_directories(output)
        output_path = os.path.join(output, f'{workflow_name}-{workflow_version}-files.zip')
        click.secho(f"--output flag specified a folder instead of a zip file path. "
                    f"Downloading zip file into {output_path}", fg='green')

    # check if output is a zip file
    elif is_zip_file(output):
        zip_file_dir_path = os.path.dirname(output)
        create_missing_directories(zip_file_dir_path)
        output_path = output

    # if output ends with an existing file that is a zip file then raise error
    else:
        raise IncorrectFlagError("The path specified with --output ends with a file. Must either specify --output "
                                 "to end with a .zip extension or to end with a folder")

    with zf.ZipFile(output_path, mode='w') as z:
        for file in files:
            content = decode_base64_content(file.base64_content)
            # must decode bytes to string to write to a zip file
            if file.content_type == "application/json" or file.content_type.startswith("text/"):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError as e:
                    raise UnableToDecodeFileError(f"Failed to decode binary content: {e}")
            z.writestr(file.path, content)


def write_to_file(output, content):
    try:
        with open(output, mode='w') as file_path:
            click.echo(content, file=file_path, nl=False)
    # fails when writing specific file and output has trailing separator or is directory
    except Exception:
        raise UnableToWriteToFileError(f"Unable to write to file specified by --output: {output} Please ensure that "
                                       f"if you are writing to a specific file that your path specified by "
                                       f"--output does not have a trailing separator and does not point to a directory")


def handle_files_output(output: str, files: List[WorkflowFile]):
    # if --path, --output and --zip flags are NOT specified, print the descriptor file contents
    if not output:
        output_file = get_descriptor_file(files)
        content = decode_readable_file(output_file)
        click.echo(content)

    # if only --output then write the entire hierarchy of files to output location
    else:
        create_missing_directories(output)
        if os.path.isdir(output):
            for file in files:
                content = decode_base64_content(file.base64_content)
                appended_path = os.path.join(output, file.path)
                # if file.path contains more nested directories, we create them
                directory = os.path.dirname(appended_path)
                create_missing_directories(directory)
                write_to_file(appended_path, content)
        else:
            raise IncorrectFlagError("The path specified with --output ends with a file. Must either specify "
                                     "a specific file with --path flag to be copied into the location specified "
                                     "by --output or change the path specified by --output to end with a folder.")


def _get_author_patch(authors: str) -> Union[JsonPatch, None]:
    if authors == "":
        return JsonPatch(path="/authors", op="remove")
    elif authors:
        return JsonPatch(path="/authors", op="replace", value=authors.split(","))
    return None


def _get_description_patch(description: Optional[FileOrValue]) -> Union[JsonPatch, None]:
    if not description:
        return None
    if description.raw_value == "":
        return JsonPatch(path="/description", op="remove")
    elif description:
        return JsonPatch(path="/description", op="replace", value=description.value())
    return None


def _get_replace_patch(path: str, value: str) -> Union[JsonPatch, None]:
    if value:
        return JsonPatch(path=path, op="replace", value=value)
    return None


def _get_labels_patch(labels: Optional[str]) -> Union[JsonPatch, None]:
    if labels is None:
        return None
    if labels.strip() == "":
        return JsonPatch(path="/labels", op="remove")

    # Clean and validate labels
    cleaned_labels = [label.strip() for label in labels.split(",") if label.strip()]
    if not cleaned_labels:
        return JsonPatch(path="/labels", op="remove")

    return JsonPatch(path="/labels", op="replace", value=cleaned_labels)


class JavaScriptFunctionExtractor:
    FUNCTION_PATTERN = re.compile(r'(?:let|const)\s*\w+\s*=\s*(\(.*\)\s*=>\s*\{.*\})', re.DOTALL)

    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_first_function(self) -> Optional[str]:
        with open(self.file_path, 'r') as file:
            content = file.read()
        match = self.FUNCTION_PATTERN.search(content)
        if match:
            return match.group(1)
        return None


class WorkflowDependencyParseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def parse_workflow_dependency(dependency_str: str) -> tuple[str, Optional[str]]:
    """
    Parse a workflow dependency string in the format 'workflow-id/version-id' or 'workflow-id'.
    
    Args:
        dependency_str: The dependency string to parse
        
    Returns:
        A tuple of (workflow_id, version_id) where version_id may be None
        
    Raises:
        WorkflowDependencyParseError: If the dependency string is invalid
    """
    if not dependency_str or not dependency_str.strip():
        raise WorkflowDependencyParseError("Dependency string cannot be empty")
    
    dependency_str = dependency_str.strip()
    
    # Check for invalid characters or patterns
    if dependency_str.startswith('/') or dependency_str.endswith('/'):
        raise WorkflowDependencyParseError("Dependency string cannot start or end with '/'")
    
    if '//' in dependency_str:
        raise WorkflowDependencyParseError("Dependency string cannot contain consecutive '/' characters")
    
    parts = dependency_str.split('/')
    
    if len(parts) == 1:
        # Only workflow ID provided
        workflow_id = parts[0]
        if not workflow_id:
            raise WorkflowDependencyParseError("Workflow ID cannot be empty")
        return workflow_id, None
    elif len(parts) == 2:
        # Both workflow ID and version ID provided
        workflow_id, version_id = parts
        if not workflow_id:
            raise WorkflowDependencyParseError("Workflow ID cannot be empty")
        if not version_id:
            raise WorkflowDependencyParseError("Version ID cannot be empty when specified")
        return workflow_id, version_id
    else:
        raise WorkflowDependencyParseError("Invalid dependency format. Expected 'workflow-id' or 'workflow-id/version-id'")


def get_latest_workflow_version(workflow_client: WorkflowClient, workflow_id: str) -> str:
    """
    Get the latest version ID for a workflow.
    
    Args:
        workflow_client: The workflow client to use
        workflow_id: The workflow ID to get the latest version for
        
    Returns:
        The latest version ID
        
    Raises:
        Exception: If the workflow is not found or has no versions
    """
    try:
        workflow = workflow_client.get_workflow(workflow_id)
        if not workflow.latestVersion:
            raise Exception(f"Workflow {workflow_id} has no versions")
        return workflow.latestVersion
    except Exception as e:
        raise Exception(f"Failed to get latest version for workflow {workflow_id}: {str(e)}")


def resolve_workflow_dependency(workflow_client: WorkflowClient, dependency_str: str) -> tuple[str, str]:
    """
    Resolve a workflow dependency string to a (workflow_id, version_id) tuple.
    If version_id is not provided, fetches the latest version.
    
    Args:
        workflow_client: The workflow client to use
        dependency_str: The dependency string to resolve
        
    Returns:
        A tuple of (workflow_id, version_id)
        
    Raises:
        WorkflowDependencyParseError: If the dependency string is invalid
        Exception: If the workflow is not found or has no versions
    """
    workflow_id, version_id = parse_workflow_dependency(dependency_str)
    return workflow_id, version_id
