from typing import List, Optional

from pydantic import BaseModel, Field
from dnastack.client.base_client import BaseServiceClient
from dnastack.client.collections.client import STANDARD_COLLECTION_SERVICE_TYPE_V1_0
from dnastack.client.datasources.model import DataSource
from dnastack.common.tracing import Span
from dnastack.client.service_registry.models import ServiceType


class DataSourcesResponse(BaseModel):
    """
    Response model for the data sources list endpoint
    """
    connections: List[DataSource] = Field(..., description="List of available data sources")

class DataSourceServiceClient(BaseServiceClient):
    """
    Client for interacting with the data sources API
    """

    @classmethod
    def get_adapter_type(cls) -> str:
        """Get the adapter type for this client"""
        return "collections"

    @classmethod
    def get_supported_service_types(cls) -> List[ServiceType]:
        """Get the supported service types for this client"""
        return [STANDARD_COLLECTION_SERVICE_TYPE_V1_0]

    def list_datasources(self, trace: Optional[Span] = None, type: Optional[str] = None) -> DataSourcesResponse:
        """
        List all available data sources.

        Args:
            trace: Optional trace span
            type: Optional type to filter datasources

        Returns:
            DataSourcesResponse containing the list of datasources
        """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            params = {}
            if type:
                params['type'] = type
            response = session.get(f"{self.url}/connections/data-sources", params=params)
            return DataSourcesResponse.parse_obj(response.json())
