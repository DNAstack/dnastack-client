from pprint import pformat
from typing import List, Union, Optional, Iterator
from urllib.parse import urljoin

from pydantic import ValidationError

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.base_exceptions import UnauthenticatedApiAccessError, UnauthorizedApiAccessError
from dnastack.client.collections.model import Collection, CreateCollectionItemsRequest, DeleteCollectionItemRequest, \
    CollectionItem, CollectionItemListOptions, PageableApiError, CollectionItemListResponse, \
    CollectionStatus
from dnastack.client.data_connect import DATA_CONNECT_TYPE_V1_0
from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultLoader, InactiveLoaderError, ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.common.tracing import Span
# Feature: Support the service registry integration
# Feature: Using both root and "singular" soon-to-be-deprecated per-collection data connect endpoints
from dnastack.http.session import ClientError, HttpSession, HttpError

STANDARD_COLLECTION_SERVICE_TYPE_V1_0 = ServiceType(group='com.dnastack',
                                                    artifact='collection-service',
                                                    version='1.0.0')
STANDARD_DATASOURCE_SERVICE_TYPE_V1_0 = ServiceType(group='com.dnastack',
                                                    artifact='collection-service',
                                                    version='1.0.0')


# Feature: No support for service registry integration
# Feature: Only using "plural" per-collection data connect endpoint
EXPLORER_COLLECTION_SERVICE_TYPE_V1_0 = ServiceType(group='com.dnastack.explorer',
                                                    artifact='collection-service',
                                                    version='1.0.0')




class InvalidApiResponse(RuntimeError):
    pass


class UnknownCollectionError(RuntimeError):
    def __init__(self, id_or_slug_name, trace: Span):
        super().__init__(id_or_slug_name)
        self.trace = trace


class CollectionItemListResultLoader(ResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[CollectionItemListOptions] = None,
                 max_results: int = None):
        self.__http_session = http_session
        self.__service_url = service_url
        self.__list_options = list_options
        self.__max_results = int(max_results) if max_results else None
        self.__loaded_results = 0
        self.__active = True
        self.__visited_urls: List[str] = list()
        self.__trace = trace
        self.__next_page_url = None

        if not self.__list_options:
            self.__list_options = self.get_new_list_options()

    def has_more(self) -> bool:
        return self.__active

    def __generate_api_error_feedback(self, response_body) -> str:
        if self.__service_url:
            return f'Failed to load the next page of data from {self.__service_url}: ({response_body})'
        else:
            return f'Failed to load the next page of data: ({response_body})'

    def get_new_list_options(self) -> CollectionItemListOptions:
        return CollectionItemListOptions()

    def extract_api_response(self, response_body: dict) -> CollectionItemListResponse:
        return CollectionItemListResponse(**response_body)

    def load(self) -> List[any]:
        if not self.__active:
            raise InactiveLoaderError(self.__service_url)

        with self.__http_session as session:
            current_url = self.__service_url

            try:

                if not self.__next_page_url:
                    response = session.get(current_url,
                                           params=self.__list_options,
                                           trace_context=self.__trace)
                else:
                    current_url = self.__next_page_url
                    response = session.get(self.__next_page_url,
                                           trace_context=self.__trace)
            except HttpError as e:
                status_code = e.response.status_code
                response_text = e.response.text

                self.__visited_urls.append(current_url)

                if status_code == 401:
                    raise UnauthenticatedApiAccessError(self.__generate_api_error_feedback(response_text))
                elif status_code == 403:
                    raise UnauthorizedApiAccessError(self.__generate_api_error_feedback(response_text))
                elif status_code >= 400:  # Catch all errors
                    raise PageableApiError(
                        f'Unexpected error: {response_text}',
                        status_code,
                        response_text,
                        urls=self.__visited_urls
                    )

            status_code = response.status_code
            response_text = response.text

            try:
                response_body = response.json() if response_text else dict()
            except Exception:
                self.logger.error(f'{self.__service_url}: Unexpectedly non-JSON response body from {current_url}')
                raise PageableApiError(
                    f'Unable to deserialize JSON from {response_text}.',
                    status_code,
                    response_text,
                    urls=self.__visited_urls
                )


            try:
                api_response = self.extract_api_response(response_body)
            except ValidationError:
                raise PageableApiError(
                    f'Invalid Response Body: {response_body}',
                    status_code,
                    response_text,
                    urls=self.__visited_urls
                )

            self.logger.debug(f'Response:\n{pformat(response_body, indent=2)}')

            self.__next_page_url = api_response.pagination.nextPageUrl if api_response.pagination and api_response.pagination.nextPageUrl else None
            if not self.__next_page_url:
                self.__active = False

            items = api_response.items

            if self.__max_results and (self.__loaded_results + len(items)) >= self.__max_results:
                self.__active = False
                num_of_loadable_results = self.__max_results - self.__loaded_results
                return items[0:num_of_loadable_results]
            else:
                self.__loaded_results += len(items)
                return items


class CollectionServiceClient(BaseServiceClient):
    """Client for Collection API"""

    @staticmethod
    def get_adapter_type() -> str:
        return 'collections'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [
            EXPLORER_COLLECTION_SERVICE_TYPE_V1_0,
            STANDARD_COLLECTION_SERVICE_TYPE_V1_0,
        ]

    def _get_single_collection_url(self, id_or_slug_name: str, extended_path: str = ''):
        return urljoin(self.url, f'collection/{id_or_slug_name}{extended_path}')

    def _get_resource_url(self, id_or_slug_name: str, short_service_type: str):
        return self._get_single_collection_url(id_or_slug_name, f'/{short_service_type}')

    def get(self, id_or_slug_name: str, no_auth: bool = False, trace: Optional[Span] = None) -> Collection:
        """ Get a collection by ID or slug name """
        trace = trace or Span(origin=self)
        local_logger = trace.create_span_logger(self._logger)
        with self.create_http_session(no_auth=no_auth) as session:
            try:
                get_url = self._get_single_collection_url(id_or_slug_name)
                get_response = session.get(get_url, trace_context=trace)
                try:
                    return Collection(**get_response.json())
                except Exception as e:
                    local_logger.error(f'The response from {get_url} is not a JSON string.')
                    local_logger.error(f'\nHTTP {get_response.status_code} (Content-Type: {get_response.headers.get("Content-Type")})\n\n{get_response.text}\n')
                    raise InvalidApiResponse() from e
            except ClientError as e:
                if e.response.status_code == 404:
                    raise UnknownCollectionError(id_or_slug_name, trace) from e
                raise e

    def list_collections(self, no_auth: bool = False, trace: Optional[Span] = None) -> List[Collection]:
        """ List all available collections """
        trace = trace or Span(origin=self)
        with self.create_http_session(no_auth=no_auth) as session:
            res = session.get(urljoin(self.url, 'collections'), trace_context=trace)
            return [Collection(**raw_collection) for raw_collection in res.json()]

    def create_collection(self, collection: Collection, trace: Optional[Span] = None) -> Collection:
        """ Create a collection """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            res = session.post(urljoin(self.url, 'collections') + '?includeInternalItemsQuery=true',
                               json=collection.dict(),
                               trace_context=trace)
            return Collection(**res.json())

    def list_collection_items(self,
                              collection_id_or_slug_name_or_db_schema_name: str,
                              list_options: Optional[CollectionItemListOptions],
                              max_results: Optional[int] = None,
                              trace: Optional[Span] = None) -> Iterator[CollectionItem]:
        """ List all items in a collection """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            return ResultIterator(CollectionItemListResultLoader(
                service_url=urljoin(self.endpoint.url, f'collection/{collection_id_or_slug_name_or_db_schema_name}/items'),
                http_session=self.create_http_session(),
                list_options=list_options,
                trace=trace,
                max_results=max_results))

    def get_collection_status(self,
                              collection_id_or_slug_name_or_db_schema_name: str,
                              trace: Optional[Span] = None) -> CollectionStatus:
        """ Get the status of a collection """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            res = session.get(urljoin(self.url, f'collection/{collection_id_or_slug_name_or_db_schema_name}/status'),
                              trace_context=trace)
            return CollectionStatus(**res.json())

    def create_collection_items(self,
                                collection_id_or_slug_name_or_db_schema_name: str,
                                create_items_request: CreateCollectionItemsRequest,
                                trace: Optional[Span] = None) -> None:
        """ Add items to a collection """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            session.post(urljoin(self.url, f'collections/{collection_id_or_slug_name_or_db_schema_name}/items'),
                         json=create_items_request.dict(), trace_context=trace)
            return None

    def delete_collection_items(self,
                                collection_id_or_slug_name_or_db_schema_name: str,
                                delete_items_request: DeleteCollectionItemRequest,
                                trace: Optional[Span] = None) -> None:
        """ Delete items from a collection """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            params = {
                'dataSourceId': delete_items_request.dataSourceId,
                'dataSourceType': delete_items_request.dataSourceType,
                'sourceKey': delete_items_request.sourceKey
            }
            # Remove dataSourceType if it is None
            if params['dataSourceType'] is None:
                del params['dataSourceType']

            session.delete(urljoin(self.url, f'collections/{collection_id_or_slug_name_or_db_schema_name}/items'),
                           params=params, trace_context=trace)
            return None

    def delete_collection(self,
                          collection_id: str,
                          trace: Optional[Span] = None) -> None:
        trace = trace or Span(origin=self)
        local_logger = trace.create_span_logger(self._logger)
        with self.create_http_session() as session:
            delete_url = self._get_single_collection_url(collection_id)
            session.delete(delete_url, trace_context=trace)
            return None

    def data_connect_endpoint(self,
                              collection: Union[str, Collection, None] = None,
                              no_auth: bool = False) -> ServiceEndpoint:
        """
        Get the URL to the corresponding Data Connect endpoint

        :param collection: The collection or collection ID. It is optional and only used by the explorer.
        :param no_auth: Trigger this method without invoking authentication even if it is required.
        """
        sub_endpoint = self._endpoint.copy(deep=True)
        sub_endpoint.type = DATA_CONNECT_TYPE_V1_0

        if self._endpoint.dnastack_schema_version == 2.0 and self._get_service_type() == STANDARD_COLLECTION_SERVICE_TYPE_V1_0:
            sub_endpoint.url = urljoin(self._endpoint.url, '/data-connect/')
        else:
            # noinspection PyUnusedLocal
            collection_id = None

            if isinstance(collection, Collection):
                collection_id = collection.slugName
            elif isinstance(collection, str):
                collection_id = collection
            else:
                raise AssertionError(f'For collection/{self._endpoint.dnastack_schema_version} ({self._endpoint.type}), the '
                                     f'given collection must be either an instance of Collection or the ID/slug name '
                                     f'of the collection (string). The given type of collection is '
                                     f'{type(collection).__name__}.')

            # While this part is not really necessary, it is designed as sanity check to ensure that the requested
            # collection exists before providing the data-connect endpoint for the given collection.
            existing_collection = self.get(collection_id, no_auth=no_auth)
            sub_endpoint.url = self._get_single_collection_url(existing_collection.slugName, '/data-connect/')

        if not no_auth and sub_endpoint.authentication:
            auth_type = sub_endpoint.authentication.get('type')

            # Override the resource URL
            if not auth_type or auth_type == 'oauth2':
                # NOTE: Generally, we want to restrict the access only to tables within the scope of the requested
                #       collection. However, due to the recent requirements where the client needs to have access to
                #       "/data-connect/table/system/metadata/catalogs" and the upcoming deprecation of per-collection
                #       data connect controller, the client code will now ask for authorization for the whole service.
                sub_endpoint.authentication['resource_url'] = (
                        self._endpoint.authentication.get('resource_url')
                        or sub_endpoint.url
                )

                # Reset the scope.
                if 'scope' in sub_endpoint.authentication:
                    del sub_endpoint.authentication['scope']

        return sub_endpoint

    def _get_service_type(self) -> ServiceType:
        return self._endpoint.type or self.get_supported_service_types()[0]
