from datetime import datetime
from typing import Optional

import click
from click import Group

from dnastack.cli.commands.publisher.tenants.utils import TENANT_ARG, _get_tenant_client, _resolve_tenant_id
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, RESOURCE_OUTPUT_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.client.tenants.models import TenantStatus
from dnastack.common.iso_time import InvalidPointInTimeError, parse_point_in_time
from dnastack.common.tracing import Span

EXPIRES_HELP = ('When the tenant expires and is deleted, as an ISO 8601 duration from now (e.g. P30D, PT12H), '
                'a date (e.g. 2026-11-01, meaning the end of that day in your local timezone) or a date-time '
                '(e.g. 2026-11-01T17:00:00Z).')


def init_tenants_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
        ]
    )
    def list_tenants(output: Optional[str] = None, context: Optional[str] = None):
        """ List all tenants, including disabled ones """
        client = _get_tenant_client(context)
        show_iterator(output, [normalize(tenant) for tenant in client.list_tenants(trace=Span())])

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            TENANT_ARG,
            CONTEXT_ARG,
        ]
    )
    def describe_tenant(tenant: str, context: Optional[str] = None):
        """ Show a tenant """
        client = _get_tenant_client(context)
        click.echo(to_json(normalize(client.get_tenant(_resolve_tenant_id(client, tenant)))))

    @formatted_command(
        group=group,
        name='create',
        specs=[
            ArgumentSpec(
                name='name',
                arg_names=['--name'],
                help='The tenant name. It must be a DNS label: at most 63 lowercase letters, digits and "-", '
                     'not starting or ending with "-".',
                required=True,
            ),
            ArgumentSpec(
                name='expires',
                arg_names=['--expires'],
                help=f'{EXPIRES_HELP} The tenant never expires if this is not given.',
                required=False,
            ),
            CONTEXT_ARG,
        ]
    )
    def create_tenant(name: str, expires: Optional[str] = None, context: Optional[str] = None):
        """ Create a tenant """
        expires_at = _parse_expiry(expires) if expires else None
        client = _get_tenant_client(context)
        click.echo(to_json(normalize(client.create_tenant(name, expires_at=expires_at))))

    @formatted_command(
        group=group,
        name='delete',
        specs=[
            TENANT_ARG,
            ArgumentSpec(
                name='force',
                arg_names=['--force', '-f'],
                help='Delete without prompting for confirmation.',
                type=bool,
            ),
            CONTEXT_ARG,
        ]
    )
    def delete_tenant(tenant: str, force: bool = False, context: Optional[str] = None):
        """
        Delete a tenant

        The tenant becomes inaccessible immediately, and it is permanently deleted along with all of its resources
        shortly after.
        """
        client = _get_tenant_client(context)
        tenant_id = _resolve_tenant_id(client, tenant)

        if not force and not click.confirm(
                f'Confirm deletion of tenant {tenant}. The tenant and all of its resources will be permanently '
                f'deleted. This action cannot be undone.'):
            return

        client.delete_tenant(tenant_id)
        click.echo(f'Tenant {tenant} deleted')

    @formatted_command(
        group=group,
        name='disable',
        specs=[
            TENANT_ARG,
            CONTEXT_ARG,
        ]
    )
    def disable_tenant(tenant: str, context: Optional[str] = None):
        """
        Disable a tenant

        Nobody can sign in to a disabled tenant or reach its resources, but nothing is deleted. Use "enable" to undo.
        """
        _set_status(tenant, TenantStatus.DISABLED, context)

    @formatted_command(
        group=group,
        name='enable',
        specs=[
            TENANT_ARG,
            CONTEXT_ARG,
        ]
    )
    def enable_tenant(tenant: str, context: Optional[str] = None):
        """ Enable a disabled tenant """
        _set_status(tenant, TenantStatus.ENABLED, context)

    @formatted_command(
        group=group,
        name='set-expiration',
        specs=[
            TENANT_ARG,
            ArgumentSpec(
                name='expires',
                arg_type=ArgumentType.POSITIONAL,
                help=EXPIRES_HELP,
                required=True,
            ),
            CONTEXT_ARG,
        ]
    )
    def set_tenant_expiration(tenant: str, expires: str, context: Optional[str] = None):
        """
        Set when a tenant expires

        Once a tenant expires, it becomes inaccessible and is permanently deleted along with all of its resources.
        """
        expires_at = _parse_expiry(expires)
        client = _get_tenant_client(context)
        client.set_tenant_expiration(_resolve_tenant_id(client, tenant), expires_at)
        click.echo(f'Tenant {tenant} expires at {expires_at.isoformat()}')

    @formatted_command(
        group=group,
        name='clear-expiration',
        specs=[
            TENANT_ARG,
            CONTEXT_ARG,
        ]
    )
    def clear_tenant_expiration(tenant: str, context: Optional[str] = None):
        """ Make a tenant never expire """
        client = _get_tenant_client(context)
        client.set_tenant_expiration(_resolve_tenant_id(client, tenant), None)
        click.echo(f'Tenant {tenant} no longer expires')


def _parse_expiry(expires: str) -> datetime:
    try:
        return parse_point_in_time(expires)
    except InvalidPointInTimeError as e:
        raise click.BadParameter(str(e)) from e


def _set_status(tenant: str, status: TenantStatus, context: Optional[str]):
    client = _get_tenant_client(context)
    client.set_tenant_status(_resolve_tenant_id(client, tenant), status)
    click.echo(f'Tenant {tenant} {status.value.lower()}')
