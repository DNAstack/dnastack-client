from datetime import datetime
from typing import List, Optional

import click
from click import Group

from dnastack.cli.commands.dataconnect.utils import DECIMAL_POINT_OUTPUT_ARG, handle_query
from dnastack.cli.commands.publisher.collections.utils import (
    COLLECTION_ID_ARG,
    _filter_collection_fields,
    _get_collection_service_client,
    _get_context,
    _switch_to_data_connect,
    _transform_to_public_collection,
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import DATA_OUTPUT_ARG, RESOURCE_OUTPUT_ARG, ArgumentSpec, ArgumentType
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.client.collections.model import Collection, CollectionStatus, CollectionValidationStatus, Tag
from dnastack.common.json_argument_parser import FileOrValue
from dnastack.common.tracing import Span
from dnastack.http.session import ClientError


def init_collections_commands(group: Group):
    @formatted_command(
        group=group,
        name="list",
        specs=[
            RESOURCE_OUTPUT_ARG,
        ],
    )
    def list_collections(output: Optional[str] = None):
        """List collections"""
        span = Span()
        show_iterator(
            output,
            [
                _filter_collection_fields(collection=collection)
                for collection in _get_collection_service_client().list_collections(trace=span)
            ],
            transform=_transform_to_public_collection,
        )

    @formatted_command(
        group=group,
        name="query",
        specs=[
            ArgumentSpec(
                name="query",
                arg_type=ArgumentType.POSITIONAL,
                help="The SQL query.",
                required=True,
            ),
            COLLECTION_ID_ARG,
            DECIMAL_POINT_OUTPUT_ARG,
            DATA_OUTPUT_ARG,
        ],
    )
    def query_collection(
        collection: str, query: str, decimal_as: str = "string", no_auth: bool = False, output: Optional[str] = None
    ):
        """Query data"""
        trace = Span(origin="cli.collections.query")
        client = _switch_to_data_connect(_get_context(), _get_collection_service_client(), collection, no_auth=no_auth)
        return handle_query(client, query, decimal_as=decimal_as, no_auth=no_auth, output_format=output, trace=trace)

    @formatted_command(
        group=group,
        name="create",
        specs=[
            ArgumentSpec(
                name="name",
                arg_names=["--name"],
                help="The name of the collection you want to create or manage.",
                required=True,
            ),
            ArgumentSpec(
                name="description",
                arg_names=["--description"],
                help="A short summary or explanation of the purpose or contents of the collection. "
                "Use @<path> to load from file.",
                type=FileOrValue,
                required=True,
            ),
            ArgumentSpec(
                name="slug",
                arg_names=["--slug"],
                help="A unique identifier for the collection, often used in URLs for easy reference.",
                required=True,
            ),
            ArgumentSpec(
                name="tags",
                arg_names=["--tags"],
                help="A comma-separated list of tags to categorize and organize the collection.",
                required=False,
            ),
        ],
    )
    def create_collection(name: str, description: FileOrValue, slug: str, tags: Optional[str] = None):
        """Create a new collection"""

        def parse_tags(tags: Optional[str]) -> Optional[List[Tag]]:
            if not tags:
                return None
            return [Tag(label=tag.strip()) for tag in tags.split(",")]

        def handle_collection_error(error: ClientError, name: str, slug: str) -> str:
            if error.response.status_code == 409:
                return f'Error: A collection with the name "{name}" or slug "{slug}" already exists. Please use different values.'

            elif error.response.status_code == 400:
                error_body = error.response.json()
                error_message = error_body.get("message", "")
                return f"Error: Invalid input - {error_message}"

            elif error.response.status_code == 401:
                return "Error: Authentication required. Please check your credentials."

            elif error.response.status_code == 403:
                return "Error: You do not have permission to create collections."

            return f"Error: Failed to create collection. Server returned status {error.response.status_code}"

        collection = Collection(name=name, description=description.value(), slugName=slug, tags=parse_tags(tags))

        try:
            client = _get_collection_service_client()
            response = client.create_collection(collection)
            click.echo(to_json(normalize(response)))
        except ClientError as e:
            error_message = handle_collection_error(e, name, slug)
            click.echo(click.style(error_message, fg="red"), err=True)
            exit(1)

    @formatted_command(
        group=group,
        name="describe",
        specs=[
            ArgumentSpec(
                name="id_or_slugs",
                arg_type=ArgumentType.POSITIONAL,
                help="The ID or slug name of the target collection",
                required=True,
                multiple=True,
            ),
        ],
    )
    def describe_collection(id_or_slugs: List[str]):
        """View details of a specific collection"""
        client = _get_collection_service_client()
        # Get unique collections by id, with the last occurrence taking precedence
        unique_collections = {
            collection.id: collection
            for id_or_slug in id_or_slugs
            for collection in [client.get(id_or_slug_name=id_or_slug)]
        }

        click.echo(to_json(normalize(list(unique_collections.values()))))

    @formatted_command(
        group=group,
        name="status",
        specs=[
            COLLECTION_ID_ARG,
            ArgumentSpec(
                name="missing_items",
                arg_names=["--missing-items"],
                help="To find missing files and/or folders while adding or removing to the collection.",
                type=bool,
                required=False,
            ),
        ],
    )
    def get_collection_status(collection: str, missing_items: Optional[bool] = False):
        """Check status of a collection"""

        def format_datetime(dt: Optional[datetime]) -> str:
            """Format datetime in the required format"""
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return "N/A"

        def format_validation_status(status: CollectionValidationStatus) -> str:
            """Convert enum status to user-friendly message"""
            status_messages = {
                CollectionValidationStatus.VALIDATED: "Validation Complete. All items added/removed.",
                CollectionValidationStatus.VALIDATION_STOPPED: "Validation Stopped",
                CollectionValidationStatus.VALIDATION_IN_PROGRESS: "Validation in Progress",
                CollectionValidationStatus.MISSING_ITEMS: "Some items are missing",
            }
            return status_messages.get(status, str(status))

        def print_missing_items_hint(collection_id: str):
            """Print hint about missing items to stderr"""
            hint = (
                "# Run the following command to see details.\n"
                f"omics publisher collections status --collection {collection_id} --missing-items"
            )
            click.echo(hint, err=True)

        def format_collection_status(status: CollectionStatus, collection_id: str) -> None:
            """Format and print collection status according to requirements"""
            # Print main status
            click.echo(f"Validation Status: {format_validation_status(status.validationsStatus)}")

            if status.lastChecked:
                click.echo(f"Last Checked: {format_datetime(status.lastChecked)}")

            # Print missing items if any
            if status.validationsStatus == CollectionValidationStatus.MISSING_ITEMS and status.missingItems:
                click.echo("\nMissing Items:")
                if status.missingItems.tables:
                    click.echo(f"  Tables: {status.missingItems.tables}")
                if status.missingItems.files:
                    click.echo(f"  Files: {status.missingItems.files}")
                click.echo()  # Add empty line before stderr message
                print_missing_items_hint(collection_id)

        client = _get_collection_service_client()
        status = client.get_collection_status(collection_id_or_slug_name_or_db_schema_name=collection)

        format_collection_status(status, collection)
