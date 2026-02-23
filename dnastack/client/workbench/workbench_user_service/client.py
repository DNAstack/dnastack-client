from typing import List, Optional, Iterator
from urllib.parse import urljoin

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.base_client import WorkbenchResultLoader
from dnastack.client.workbench.models import BaseListOptions
from dnastack.client.workbench.workbench_user_service.models import (
    WorkbenchUser,
    Namespace,
    NamespaceListResponse,
    NamespaceMember,
    NamespaceMemberListResponse,
)
from dnastack.common.tracing import Span
from dnastack.http.session import HttpSession


class NamespaceListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[BaseListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> BaseListOptions:
        return BaseListOptions()

    def extract_api_response(self, response_body: dict) -> NamespaceListResponse:
        return NamespaceListResponse(**response_body)


class NamespaceMemberListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[BaseListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> BaseListOptions:
        return BaseListOptions()

    def extract_api_response(self, response_body: dict) -> NamespaceMemberListResponse:
        return NamespaceMemberListResponse(**response_body)


class WorkbenchUserClient(BaseServiceClient):

    @staticmethod
    def get_adapter_type() -> str:
        return 'workbench-user-service'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [
            ServiceType(group='com.dnastack.workbench', artifact='workbench-user-service', version='1.0.0'),
        ]

    # noinspection PyMethodOverriding
    @classmethod
    def make(cls, endpoint: ServiceEndpoint):
        """Create this class with the given `endpoint` and `namespace`."""
        if not endpoint.type:
            endpoint.type = cls.get_default_service_type()
        return cls(endpoint)

    def get_user_config(self) -> WorkbenchUser:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, 'users/me')
            )
        return WorkbenchUser(**response.json())

    def list_namespaces(self,
                        list_options: Optional[BaseListOptions] = None,
                        max_results: Optional[int] = None) -> Iterator[Namespace]:
        """List namespaces the authenticated user belongs to."""
        return ResultIterator(NamespaceListResultLoader(
            service_url=urljoin(self.endpoint.url, 'namespaces'),
            http_session=self.create_http_session(),
            list_options=list_options,
            trace=None,
            max_results=max_results))

    def get_namespace(self, namespace_id: str) -> Namespace:
        """Get a single namespace by ID."""
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'namespaces/{namespace_id}')
            )
        return Namespace(**response.json())

    def list_namespace_members(self,
                               namespace_id: str,
                               list_options: Optional[BaseListOptions] = None,
                               max_results: Optional[int] = None) -> Iterator[NamespaceMember]:
        """List members and their roles in a namespace."""
        return ResultIterator(NamespaceMemberListResultLoader(
            service_url=urljoin(self.endpoint.url, f'namespaces/{namespace_id}/members'),
            http_session=self.create_http_session(),
            list_options=list_options,
            trace=None,
            max_results=max_results))
