from pprint import pformat
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from dnastack.client.base_client import BaseServiceClient
from dnastack.client.base_exceptions import (
    UnauthenticatedApiAccessError, UnauthorizedApiAccessError
)
from dnastack.client.collections.client import STANDARD_COLLECTION_SERVICE_TYPE_V1_0, \
    STANDARD_DATASOURCE_SERVICE_TYPE_V1_0
from dnastack.client.collections.model import PageableApiError
from dnastack.client.datasources.model import DataSource, DataSourceListOptions
from dnastack.client.result_iterator import ResultLoader, InactiveLoaderError, ResultIterator
from dnastack.http.session import HttpSession, HttpError
from dnastack.common.tracing import Span


class DataSourcesResponse(BaseModel):
    connections: List[DataSource]

    def items(self) -> List[DataSource]:
        return self.connections

class DataSourceListResultLoader(ResultLoader):
    """
    Result loader for handling data source fetching without pagination.
    """

    def __init__(self, service_url: str, http_session: HttpSession, trace: Span,
                 list_options: Optional[dict] = None, max_results: Optional[int] = None):
        self.__service_url = service_url
        self.__http_session = http_session
        self.__list_options = list_options or {}
        self.__max_results = max_results
        self.__loaded_results = 0
        self.__active = True  # Determines when we are done fetching results
        self.__trace = trace

    def has_more(self) -> bool:
        """Checks if there are more results to fetch."""
        return self.__active

    def extract_api_response(self, response_body: dict) -> DataSourcesResponse:
        """
        Converts the API response body into a DataSourcesResponse object.
        """
        return DataSourcesResponse(**response_body)

    def load(self) -> List[DataSource]:
        """Fetches the data from the API."""
        if not self.__active:
            raise InactiveLoaderError(self.__service_url)

        with self.__http_session as session:
            try:
                # Perform the GET request
                response = session.get(
                    self.__service_url,
                    params=self.__list_options,
                    trace_context=self.__trace
                )
            except HttpError as e:
                error_feedback = f"Failed to load data from {self.__service_url}: {e.response.text}"
                if e.response.status_code == 401:
                    raise UnauthenticatedApiAccessError(error_feedback)
                elif e.response.status_code == 403:
                    raise UnauthorizedApiAccessError(error_feedback)
                else:
                    raise PageableApiError(error_feedback, e.response.status_code, e.response.text)

            # Parse the API response
            response_body = response.json() if response.text else {}
            try:
                api_response = self.extract_api_response(response_body)
            except ValidationError:
                raise PageableApiError(
                    f"Invalid response body: {response_body}",
                    response.status_code,
                    response.text,
                )

            # Retrieve the data source items
            items = api_response.items()

            # Deactivate the loader after the first fetch since there's no pagination
            self.__active = False

            # Handle max_results constraint
            if self.__max_results and len(items) > self.__max_results:
                return items[:self.__max_results]

            return items

class DataSourceServiceClient(BaseServiceClient):
    """
    Client to interact with the Data Sources API.
    """

    @staticmethod
    def get_adapter_type() -> str:
        return 'datasources'

    @classmethod
    def get_supported_service_types(cls) -> List[str]:
        """
        Returns supported service types.
        """
        return [ STANDARD_DATASOURCE_SERVICE_TYPE_V1_0,]

    def list_datasources(self, type: Optional[str] = None, trace: Optional[Span] = None,
                         max_results: Optional[int] = None) -> DataSourcesResponse:
        # Set up query parameters
        list_options = {}
        if type:
            list_options["type"] = type

        trace = trace or Span(origin=self)
        loader = DataSourceListResultLoader(
            service_url=f"{self.url}data-sources",
            http_session=self.create_http_session(),
            trace=trace,
            list_options=list_options,
            max_results=max_results
        )
        connections = list(ResultIterator(loader))
        return DataSourcesResponse(connections=connections)
