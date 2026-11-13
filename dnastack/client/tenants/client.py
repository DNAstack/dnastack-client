from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.models import ServiceEndpoint
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.tenants.models import Tenant, TenantStatus
from dnastack.common.tracing import Span
from dnastack.http.session import ClientError

WALLET_SERVICE_TYPE_V1_0 = ServiceType(group='com.dnastack',
                                       artifact='wallet',
                                       version='1.0.0')

TENANT_ADMIN_SCOPE = 'admin:tenants'

_TOKEN_ENDPOINT_PATH = 'oauth/token'


class UnknownTenantError(RuntimeError):
    """ Raised when the requested tenant does not exist """


class WalletEndpointNotDerivableError(RuntimeError):
    """ Raised when the wallet URL cannot be worked out from another service's authentication settings """


class TenantClient(BaseServiceClient):
    """
    Client for wallet's tenant management API.

    Tenants are instance-scoped, so the caller needs a management-tenant token with the "admin:tenants" scope.
    """

    @staticmethod
    def get_adapter_type() -> str:
        return 'tenants'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [WALLET_SERVICE_TYPE_V1_0]

    @classmethod
    def make_from_publisher_endpoint(cls, endpoint: ServiceEndpoint) -> 'TenantClient':
        """
        Create a client for the wallet that issues tokens for the given Publisher service endpoint.

        Wallet does not register itself in the service registry, so its URL is taken from the token endpoint of the
        given endpoint's OAuth2 authentication settings. The same client and grant types are reused, but the token is
        requested for wallet itself with the tenant admin scope.
        """
        oauth2_auths = [auth for auth in endpoint.get_authentications()
                        if auth.get('type') == 'oauth2' and auth.get('token_endpoint')]
        if not oauth2_auths:
            raise WalletEndpointNotDerivableError(
                f'Endpoint {endpoint.id} has no OAuth2 authentication to find the wallet URL from'
            )

        wallet_url = _wallet_url_from_token_endpoint(oauth2_auths[0]['token_endpoint'])
        wallet_auths = [dict(auth, resource_url=wallet_url, scope=TENANT_ADMIN_SCOPE) for auth in oauth2_auths]

        return cls.make(ServiceEndpoint(id=f'{endpoint.id}-wallet',
                                        url=wallet_url,
                                        type=WALLET_SERVICE_TYPE_V1_0,
                                        authentication=wallet_auths[0],
                                        fallback_authentications=wallet_auths[1:] or None))

    def list_tenants(self, trace: Optional[Span] = None) -> List[Tenant]:
        """ List all tenants, including disabled and expired ones """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.url, 'tenants'), trace_context=trace)
            return [Tenant(**raw_tenant) for raw_tenant in response.json()]

    def get_tenant(self, tenant_id: str, trace: Optional[Span] = None) -> Tenant:
        """ Get a tenant by ID """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            try:
                response = session.get(self._tenant_url(tenant_id), trace_context=trace)
            except ClientError as e:
                if e.response.status_code == 404:
                    raise UnknownTenantError(tenant_id) from e
                raise
            return Tenant(**response.json())

    def create_tenant(self,
                      name: str,
                      expires_at: Optional[datetime] = None,
                      status: Optional[TenantStatus] = None,
                      trace: Optional[Span] = None) -> Tenant:
        """
        Create a tenant.

        :param name: the tenant name, which must be a DNS label (lowercase letters, digits and "-")
        :param expires_at: when the tenant expires and is deleted; None means it never expires
        :param status: the initial status; wallet enables new tenants by default
        """
        trace = trace or Span(origin=self)
        request = {'name': name}
        if expires_at is not None:
            request['expires_at'] = _to_instant(expires_at)
        if status is not None:
            request['status'] = status.value
        with self.create_http_session() as session:
            response = session.post(urljoin(self.url, 'tenants'), json=request, trace_context=trace)
            return Tenant(**response.json())

    def delete_tenant(self, tenant_id: str, trace: Optional[Span] = None) -> None:
        """
        Delete a tenant.

        Wallet disables the tenant and expires it immediately, so it becomes inaccessible right away and is
        permanently deleted, along with its resources, shortly after.
        """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            self._send_to_tenant(lambda: session.delete(self._tenant_url(tenant_id), trace_context=trace), tenant_id)

    def set_tenant_status(self, tenant_id: str, status: TenantStatus, trace: Optional[Span] = None) -> None:
        """ Enable or disable a tenant. Disabling blocks all access to the tenant without deleting anything. """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            self._send_to_tenant(lambda: session.put(self._tenant_url(tenant_id, 'status'),
                                                     json={'status': status.value},
                                                     trace_context=trace),
                                 tenant_id)

    def enable_tenant(self, tenant_id: str, trace: Optional[Span] = None) -> None:
        self.set_tenant_status(tenant_id, TenantStatus.ENABLED, trace=trace)

    def disable_tenant(self, tenant_id: str, trace: Optional[Span] = None) -> None:
        self.set_tenant_status(tenant_id, TenantStatus.DISABLED, trace=trace)

    def set_tenant_expiration(self,
                              tenant_id: str,
                              expires_at: Optional[datetime],
                              trace: Optional[Span] = None) -> None:
        """ Set when a tenant expires and is deleted, or clear its expiry when expires_at is None """
        trace = trace or Span(origin=self)
        request = {'expires_at': _to_instant(expires_at) if expires_at is not None else None}
        with self.create_http_session() as session:
            self._send_to_tenant(lambda: session.put(self._tenant_url(tenant_id, 'expiration'),
                                                     json=request,
                                                     trace_context=trace),
                                 tenant_id)

    def _tenant_url(self, tenant_id: str, sub_resource: Optional[str] = None) -> str:
        path = f'tenants/{tenant_id}'
        if sub_resource:
            path = f'{path}/{sub_resource}'
        return urljoin(self.url, path)

    @staticmethod
    def _send_to_tenant(send, tenant_id: str):
        try:
            return send()
        except ClientError as e:
            if e.response.status_code == 404:
                raise UnknownTenantError(tenant_id) from e
            raise


def _wallet_url_from_token_endpoint(token_endpoint: str) -> str:
    base_url = token_endpoint.rstrip('/')
    if not base_url.endswith('/' + _TOKEN_ENDPOINT_PATH):
        raise WalletEndpointNotDerivableError(
            f'Cannot find the wallet URL from token endpoint {token_endpoint}: it does not end with /oauth/token'
        )
    return base_url[:-len(_TOKEN_ENDPOINT_PATH)]


def _to_instant(moment: datetime) -> str:
    """ Format as a UTC instant ("...Z"), the form wallet's java.time.Instant fields parse """
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
