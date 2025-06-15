from typing import List
from urllib.parse import urljoin

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.models import ServiceEndpoint
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser


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
