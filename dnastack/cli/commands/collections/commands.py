import re
from typing import Optional, Any, Dict, List
from urllib.parse import urlparse

import click
from click import Group

from dnastack.cli.commands.collections.utils import _filter_collection_fields, _simplify_collection, _get, \
    _transform_to_public_collection, COLLECTION_ID_CLI_ARG, _abort_with_collection_list, _switch_to_data_connect, \
    _get_context
from dnastack.cli.commands.dataconnect.utils import DECIMAL_POINT_OUTPUT_ARG, handle_query
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, RESOURCE_OUTPUT_ARG, DATA_OUTPUT_ARG, CONTEXT_ARG, \
    SINGLE_ENDPOINT_ID_ARG, ArgumentType
from dnastack.cli.helpers.exporter import to_json
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span


def init_collections_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            ArgumentSpec(
                name='simplified',
                arg_names=['--simplified'],
                help='Use the simplified representation (experimental)',
                type=bool,
            ),
            ArgumentSpec(
                name='selected_fields',
                arg_names=['--select'],
                nargs='*',
                help='Select a certain field (experimental)',
            ),
            ArgumentSpec(
                name='no_auth',
                arg_names=['--no-auth'],
                help='Skip automatic authentication if set',
                type=bool,
                required=False,
                hidden=True,
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_collections(context: Optional[str],
                         endpoint_id: Optional[str],
                         selected_fields: Optional[str] = None,
                         simplified: Optional[bool] = False,
                         no_auth: bool = False,
                         output: Optional[str] = None):
        """ List collections """
        span = Span()
        show_iterator(output,
                      [
                          _filter_collection_fields(_simplify_collection(collection) if simplified else collection, selected_fields)
                          for collection in _get(context, endpoint_id).list_collections(no_auth=no_auth, trace=span)
                      ],
                      transform=_transform_to_public_collection)
    
    
    @formatted_command(
        group=group,
        name='list-items',
        specs=[
            COLLECTION_ID_CLI_ARG,
            ArgumentSpec(
                name='limit',
                arg_names=['--limit', '-l'],
                help='The maximum number of items to display',
                type=int,
                default=50
            ),
            ArgumentSpec(
                name='no_auth',
                arg_names=['--no-auth'],
                help='Skip automatic authentication if set',
                type=bool,
                required=False,
                hidden=True,
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_items(context: Optional[str],
                   endpoint_id: Optional[str],
                   collection: Optional[str],
                   limit: Optional[int] = 50,
                   no_auth: bool = False,
                   output: Optional[str] = None):
        """ List items of the given collection """
        logger = get_logger('CLI/list-items')
        limit_override = False
    
        # This is for Python 3.7. In newer Python, the wrapper code automatically
        # will provide the value as annotated in type hints.
        limit = int(limit)
    
        assert limit >= 0, 'The limit (--limit) should be either ZERO (item query WITHOUT limit) '\
                          'or at least ONE (item query WITH limit).'
    
        click.secho(f'Retrieving upto {limit} item{"s" if limit == 1 else ""}...' if limit else 'Retrieving all items...',
                    dim=True,
                    err=True)
    
        collection_service_client = _get(context, endpoint_id)
    
        collection_id = collection.strip() if collection else None
        if not collection_id:
            _abort_with_collection_list(collection_service_client, collection, no_auth=no_auth)
    
        actual_collection = collection_service_client.get(collection_id, no_auth=no_auth)
        data_connect_client = _switch_to_data_connect(_get_context(context), collection_service_client,
                                                      actual_collection.slugName, no_auth)
    
        def __simplify_item(row: Dict[str, Any]) -> Dict[str, Any]:
            # NOTE: It is implemented this way to guarantee that "id" and "name" are more likely to show first.
            property_names = ['type', 'size', 'size_unit', 'version', 'item_updated_at']
    
            logger.debug(f'Item Simplifier: given: {to_json(row)}')
    
            item = dict(
                id=row['id'],
                name=row.get('qualified_table_name') or row.get('preferred_name') or row.get('display_name') or row['name'],
            )
    
            if row['type'] == 'blob':
                property_names.extend([
                    'checksums',
                    'metadata_url',
                    'mime_type',
                ])
            elif row['type'] == 'table':
                property_names.extend([
                    'json_schema',
                ])
    
            item.update({
                k: v
                for k, v in row.items()
                if k in property_names
            })
    
            # FIXME: Remove this logic when https://www.pivotaltracker.com/story/show/182309558 is resolved.
            if 'metadata_url' in item:
                parsed_url = urlparse(item['metadata_url'])
                item['metadata_url'] = f'{parsed_url.scheme}://{parsed_url.netloc}/{item["id"]}'
    
            return item
    
        items: List[Dict[str, Any]] = []
    
        items_query = actual_collection.itemsQuery.strip()
    
        if re.search(r' limit\s*\d+$', items_query, re.IGNORECASE):
            logger.warning('The items query already has the limit defined and the CLI will not override that limit.')
        else:
            logger.debug(f'Only shows {limit} row(s)')
            limit_override = True
            items_query = f'{items_query} LIMIT {limit + 1}'  # We use +1 as an indicator whether there are more results.
    
        items.extend([i for i in data_connect_client.query(items_query, no_auth=no_auth)])
    
        row_count = len(items)
    
        displayed_item_count = show_iterator(
            output or RESOURCE_OUTPUT_ARG.default,
            items,
            __simplify_item,
            limit
        )
    
        click.secho(f'Displayed {displayed_item_count} item{"s" if displayed_item_count != 1 else ""} from this collection',
                    fg='green',
                    err=True)
    
        if limit_override and row_count > limit:
            click.secho(f'There exists more than {limit} item{"s" if limit != 1 else ""} in this collection. You may use '
                        '"--limit 0" to get all items in this collection.\n\n'
                        f'    dnastack collections list-items -c {actual_collection.slugName} --limit=0 '
                        f'{"--no-auth" if no_auth else ""}'
                        '\n',
                        fg='yellow',
                        err=True)
    
    
    @formatted_command(
        group=group,
        name='query',
        specs=[
            ArgumentSpec(
                name='query',
                arg_type=ArgumentType.POSITIONAL,
                help='The SQL query.',
                required=True,
            ),
            COLLECTION_ID_CLI_ARG,
            DECIMAL_POINT_OUTPUT_ARG,
            DATA_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def query_collection(context: Optional[str],
                         endpoint_id: Optional[str],
                         collection: Optional[str],
                         query: str,
                         decimal_as: str = 'string',
                         no_auth: bool = False,
                         output: Optional[str] = None):
        """ Query data """
        trace = Span(origin='cli.collections.query')
        client = _switch_to_data_connect(_get_context(context), _get(context, endpoint_id), collection, no_auth=no_auth)
        return handle_query(client, query,
                            decimal_as=decimal_as,
                            no_auth=no_auth,
                            output_format=output,
                            trace=trace)

