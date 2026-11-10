from typing import Optional
from uuid import UUID

from dnastack.cli.commands.publisher.collections.utils import _get_collection_service_client, _get_context
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType
from dnastack.client.tenants.client import TenantClient, UnknownTenantError

TENANT_ARG = ArgumentSpec(
    name='tenant',
    arg_type=ArgumentType.POSITIONAL,
    help='The ID or name of the tenant.',
    required=True,
)


def _get_tenant_client(context_name: Optional[str] = None) -> TenantClient:
    """
    Get a client for the wallet of the current context.

    A wallet endpoint configured in the context takes precedence. Otherwise the wallet is the one that issues tokens
    for the context's Publisher collection service.
    """
    context = _get_context(context_name)
    for endpoint in context.endpoints:
        if endpoint.type in TenantClient.get_supported_service_types():
            return TenantClient.make(endpoint.model_copy(deep=True))

    publisher_endpoint = _get_collection_service_client(context_name).endpoint
    return TenantClient.make_from_publisher_endpoint(publisher_endpoint)


def _resolve_tenant_id(client: TenantClient, id_or_name: str) -> str:
    """ Wallet addresses tenants by ID only, so a name is looked up among all tenants """
    try:
        return str(UUID(id_or_name))
    except ValueError:
        pass

    for tenant in client.list_tenants():
        if tenant.name == id_or_name:
            return tenant.id
    raise UnknownTenantError(id_or_name)
