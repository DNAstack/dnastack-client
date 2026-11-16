from time import monotonic, sleep
from typing import Optional, List

import click
from click import style, Group

from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import get_storage_client, NAMESPACE_ARG, create_sort_arg
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import OutputFormat, show_iterator
from dnastack.client.workbench.storage.client import StorageClient
from dnastack.client.workbench.storage.models import StorageAccount, StorageListOptions, Provider

REINDEX_POLL_INTERVAL_SECONDS = 10


def _wait_for_indexing(client: StorageClient,
                       storage_id: str,
                       account: StorageAccount,
                       timeout: int,
                       last_completed_at: Optional[str]) -> StorageAccount:
    """Poll until indexing stops, and fail unless it recorded a completed run after `last_completed_at`."""
    if account.indexing_status is None:
        raise click.ClickException('This Workbench does not report indexing status, so --wait cannot '
                                   'tell when indexing finishes.')
    deadline = monotonic() + timeout
    while account.indexing_status == 'RUNNING':
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise click.ClickException(f'Indexing of storage account {storage_id} is still running after '
                                       f'{timeout} seconds.')
        sleep(min(REINDEX_POLL_INTERVAL_SECONDS, remaining))
        account = client.get_storage_account(storage_id)

    if account.indexing_status != 'IDLE':
        raise click.ClickException(f'Storage account {storage_id} reports indexing status '
                                   f'{account.indexing_status}, which --wait does not recognise.')
    # Workbench records last_indexed_at only when a run completes; a failed run returns to IDLE without it.
    if account.last_indexed_at == last_completed_at:
        raise click.ClickException(f'Indexing of storage account {storage_id} stopped but did not complete. '
                                   f'The last completed indexing is still {last_completed_at or "none"}.')
    return account


def init_storage_commands(group: Group):
    @formatted_command(
        group=group,
        name='delete',
        specs=[
            ArgumentSpec(
                name='storage_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The storage account id',
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
        ],
    )
    def delete_storage_account(context: Optional[str],
                               endpoint_id: Optional[str],
                               namespace: Optional[str],
                               storage_id: str,
                               force: bool = False):
        """Delete a storage account"""
        client = get_storage_client(context, endpoint_id, namespace)

        if not force and not click.confirm(
                f'Confirm deletion of storage account {storage_id}. This action cannot be undone.'):
            return

        client.delete_storage_account(storage_id)
        click.echo(f"Storage account {storage_id} deleted successfully")


    @formatted_command(
        group=group,
        name='list',
        specs=[
            NAMESPACE_ARG,
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            create_sort_arg('--sort "name:ASC", --sort "name;provider:DESC;"'),
            ArgumentSpec(
                name='provider',
                arg_names=['--provider'],
                help='Filter results by provider.',
                type=Provider,
                choices=[e.value for e in Provider],
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_storage_accounts(context: Optional[str],
                              endpoint_id: Optional[str],
                              namespace: Optional[str],
                              max_results: Optional[int],
                              page: Optional[int],
                              page_size: Optional[int],
                              sort: Optional[str],
                              provider: Optional[Provider]):
        """List storage accounts"""
        client = get_storage_client(context, endpoint_id, namespace)
        list_options = StorageListOptions(
            page=page,
            page_size=page_size,
            sort=sort,
            provider=provider
        )
        show_iterator(output_format=OutputFormat.JSON,
                      iterator=client.list_storage_accounts(list_options, max_results))


    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='storage_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The storage account id',
                required=True,
                multiple=True
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def get_storage_accounts(context: Optional[str],
                             endpoint_id: Optional[str],
                             namespace: Optional[str],
                             storage_id: List[str]):
        """Get a storage account"""

        if not storage_id:
            click.echo(style("You must specify at least one storage account ID", fg='red'), err=True, color=True)
            exit(1)

        client = get_storage_client(context, endpoint_id, namespace)
        storage_accounts = [client.get_storage_account(storage_account_id) for storage_account_id in storage_id]
        click.echo(to_json(normalize(storage_accounts)))

    @formatted_command(
        group=group,
        name='reindex',
        specs=[
            ArgumentSpec(
                name='storage_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The storage account id',
                required=True,
            ),
            ArgumentSpec(
                name='wait',
                arg_names=['--wait'],
                help='Wait for indexing to finish, then print the account. Exits non-zero if indexing did not complete.',
                type=bool,
            ),
            ArgumentSpec(
                name='timeout',
                arg_names=['--timeout'],
                help='With --wait, how many seconds to wait before giving up. Indexing keeps running.',
                type=int,
                default=3600,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def reindex_storage_account(context: Optional[str],
                                endpoint_id: Optional[str],
                                namespace: Optional[str],
                                storage_id: str,
                                wait: bool = False,
                                timeout: int = 3600):
        """
        Re-scan a storage account for sample files

        Indexing runs in the background: without --wait the command returns once indexing has started. Indexing
        also removes sample files whose objects are no longer in the bucket. Requires the workbench.storage.update
        permission (namespace admin).
        """
        if timeout < 0:
            raise click.BadParameter('must be zero or more seconds.', param_hint="'--timeout'")
        client = get_storage_client(context, endpoint_id, namespace)
        last_completed_at = client.get_storage_account(storage_id).last_indexed_at if wait else None
        account = client.reindex_storage_account(storage_id)
        if wait:
            account = _wait_for_indexing(client, storage_id, account, timeout, last_completed_at)
        click.echo(to_json(normalize(account)))
