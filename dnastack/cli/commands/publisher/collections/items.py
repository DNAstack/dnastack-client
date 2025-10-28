import re
from typing import Optional

import click

from dnastack.cli.commands.publisher.collections.utils import _get_collection_service_client, \
    COLLECTION_ID_ARG
from dnastack.cli.commands.utils import MAX_RESULTS_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, RESOURCE_OUTPUT_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.collections.model import CreateCollectionItemsRequest, DeleteCollectionItemRequest, \
    CollectionItemListOptions
from dnastack.common.json_argument_parser import FileOrValue
from dnastack.http.session import ClientError


@formatted_group("items")
def items_command_group():
    """Interact with a collection's items"""


@formatted_command(
    group=items_command_group,
    name='list',
    specs=[
        COLLECTION_ID_ARG,
        ArgumentSpec(
            name='limit',
            arg_names=['--limit', '-l'],
            help='Set the page size returned by the server.',
            type=int,
            default=50,
            required=False,
        ),
        ArgumentSpec(
            name='item_type',
            arg_names=['--type'],
            help='The type of items to list.',
            required=False,
        ),
        ArgumentSpec(
            name='missing_items',
            arg_names=['--missing-items'],
            help='List only missing items from the collection.',
            type=bool,
            required=False,
        ),
        MAX_RESULTS_ARG,
        RESOURCE_OUTPUT_ARG
    ]
)
def list(collection: str,
         limit: Optional[int],
         max_results: Optional[int],
         item_type: Optional[str],
         missing_items: Optional[bool] = False,
         output: Optional[str] = None):
    """ List items of the given collection """
    assert limit >= 0, 'The limit (--limit) should be either ZERO (item query WITHOUT limit) ' \
                       'or at least ONE (item query WITH limit).'

    list_options = CollectionItemListOptions(
        type=item_type,
        limit=limit,
        onlyMissing=missing_items if missing_items else None,
    )

    collection_service_client = _get_collection_service_client()
    show_iterator(output_format=OutputFormat.JSON,
                  iterator=collection_service_client.list_collection_items(
                      collection_id_or_slug_name_or_db_schema_name=collection,
                      list_options=list_options,
                      max_results=max_results
                  ))


@formatted_command(
    group=items_command_group,
    name='add',
    specs=[
        COLLECTION_ID_ARG,
        ArgumentSpec(
            name='datasource',
            arg_names=['--datasource'],
            help='The ID or Name of the data source where the files or folders reside, such as a bucket or storage location.',
            required=True,
        ),
        ArgumentSpec(
            name='files',
            arg_names=['--files'],
            help='Specifies the files to be added. '
                 'Accepts a comma-separated list of file URLs, a file path (@files.txt), or files piped via stdin.',
            type=FileOrValue,
            required=True,
        ),
    ]
)
def add_files_to_collection(collection: str,
                            datasource: str,
                            files: FileOrValue):
    """ Add files to a collection """
    parsed_files = set(item.strip() for item in re.split(r'[,\n]', files.value()) if item.strip())
    if not parsed_files:
        click.echo("Error: No valid files provided. Please specify at least one file.", err=True)
        return

    request = CreateCollectionItemsRequest(
        dataSourceId=datasource,
        sourceKeys=parsed_files,
    )

    try:
        client = _get_collection_service_client()
        client.create_collection_items(
            collection_id_or_slug_name_or_db_schema_name=collection,
            create_items_request=request
        )

        click.echo("Adding items to collection...")
        click.echo(f"Validation in progress. Run 'status --collection {collection}' for updates.")
    except ClientError as error:
        error_message = f"Error: Failed to add items to collection. Server returned status {error.response.status_code}"
        click.echo(click.style(error_message, fg='red'), err=True)
        exit(1)


@formatted_command(
    group=items_command_group,
    name='remove',
    specs=[
        COLLECTION_ID_ARG,
        ArgumentSpec(
            name='datasource',
            arg_names=['--datasource'],
            help='The ID of the data source where the files or folders reside, such as a bucket or storage location.',
            required=True,
        ),
        ArgumentSpec(
            name='files',
            arg_names=['--files'],
            help='Specifies the files to be removed. '
                 'Accepts a comma-separated list of file URLs, a file path (@files.txt), or files piped via stdin.',
            type=FileOrValue,
            required=True,
        ),
    ]
)
def remove_files_from_collection(collection: str,
                                 datasource: str,
                                 files: FileOrValue):
    """ Remove files from a collection """
    parsed_files = set(item.strip() for item in re.split(r'[,\n]', files.value()) if item.strip())
    if not parsed_files:
        click.echo("Error: No valid files provided. Please specify at least one file.", err=True)
        return

    client = _get_collection_service_client()
    for file in parsed_files:
        request = DeleteCollectionItemRequest(
            dataSourceId=datasource,
            sourceKey=file,
        )

        try:
            client.delete_collection_items(
                collection_id_or_slug_name_or_db_schema_name=collection,
                delete_items_request=request
            )
        except ClientError as error:
            error_message = f"Error: Failed to remove item '{file}' from collection. Server returned status {error.response.status_code}"
            click.echo(click.style(error_message, fg='red'), err=True)
            return

    click.echo("Removing items from collection...")
    click.echo(f"Validation in progress. Run 'status --collection {collection}' for updates.")
