import json
from typing import Optional
from urllib.parse import urljoin

from pydantic import BaseModel

from dnastack.alpha.app.publisher_helper.collection_service import BlobApiMixin, RootCollectionApiMixin, \
    PerCollectionApiMixin
from dnastack.alpha.app.publisher_helper.data_connect import SearchOperation
from dnastack.alpha.app.publisher_helper.filter import FilterOperation
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.collections.model import Collection as CollectionModel
from dnastack.client.data_connect import DataConnectClient
from dnastack.client.drs import DrsClient, Blob
from dnastack.client.factory import EndpointRepository
from dnastack.client.models import ServiceEndpoint
from dnastack.common.logger import get_logger_for
from dnastack.context.helper import use
from dnastack.http.authenticators.factory import HttpAuthenticatorFactory
from dnastack.http.session import HttpSession


class FilterInfo(BaseModel):
    sql: str
    cli: str
    python: str
    sharedQueryUrl: str


class Collection(PerCollectionApiMixin, BlobApiMixin):
    """ High-level Collection API Client """

    def __init__(self,
                 factory: EndpointRepository,
                 cs: CollectionServiceClient,
                 collection: CollectionModel,
                 no_auth: bool):
        self._logger = get_logger_for(self)
        self._factory = factory
        self._cs = cs
        self._collection = collection
        self._no_auth = no_auth
        self._dc: DataConnectClient = self.data_connect()
        self._drs: DrsClient = self._factory.get_one_of(client_class=DrsClient)

    def get_record(self) -> CollectionModel:
        return self._collection

    def query(self, query: str):
        return SearchOperation(self._dc, self._no_auth, query)

    def get_filter_info(self, table_name: str, filters={}) -> FilterInfo:
        endpoint = self._cs.endpoint
        session = HttpSession(endpoint,
                              HttpAuthenticatorFactory.create_multiple_from(endpoint=endpoint),
                              suppress_error=False,
                              enable_auth=(not self._no_auth))
        url = urljoin(endpoint.url, f'collections/{self._collection.slugName}/tables/{table_name}/filter/query'
                                    '?includeSharedQueryUrl=true')
        headers = {'Content-Type': 'application/json'}
        return FilterInfo(**session.post(url, data=json.dumps(filters), headers=headers).model_dump_json())

    def data_connect(self):
        default_no_auth_properties = {'authentication': None, 'fallback_authentications': None}

        proposed_data_connect_endpoint = self._cs.data_connect_endpoint(self._collection.slugName,
                                                                        no_auth=self._no_auth)

        target_endpoint: Optional[ServiceEndpoint] = None

        # Look up for any similar registered service endpoint.
        for endpoint in self._factory.all(client_class=DataConnectClient):
            proposed_data_connect_endpoint_url = proposed_data_connect_endpoint.url
            if not proposed_data_connect_endpoint_url.endswith('/'):
                proposed_data_connect_endpoint_url += '/'

            reference_data_connect_endpoint_url = endpoint.url
            if not reference_data_connect_endpoint_url.endswith('/'):
                reference_data_connect_endpoint_url += '/'

            if proposed_data_connect_endpoint_url == reference_data_connect_endpoint_url:
                target_endpoint = endpoint
                break

        if not target_endpoint:
            target_endpoint = proposed_data_connect_endpoint

            self._logger.debug(
                f'Unable to find a registered {proposed_data_connect_endpoint.type} endpoint '
                f'at {proposed_data_connect_endpoint.url}.'
            )

        return DataConnectClient.make(
            target_endpoint.copy(update=default_no_auth_properties)
            if self._no_auth
            else target_endpoint
        )

    def find_blob_by_name(self, objectname: str) -> Blob:
        return self._find_blob_by_name(objectname=objectname, column_name='drs_url')


class Explorer(RootCollectionApiMixin):
    """ High-level Explorer API Client

        Docs: /docs/alpha/app/explorer.md

        .. code-block:: python

            from dnastack.alpha.app.explorer import Explorer

            # Data Connect
            query = collection.query('SELECT * FROM collections.public_datasets.metadata LIMIT 5')
            df = query.to_data_frame()
            rows = query.to_list()

            # DRS (not yet manually tested with collections with blobs)
            blob: Optional[Blob] = collection.blob(id='123-456') or collection.blob(name='foo-bar')
            blobs: Dict[str, Optional[Blob]] = collection.blobs(ids=['123-456']) or collection.blobs(names=['foo-bar'])

    """

    def __init__(self, context_name_or_url: str, *, no_auth: bool = False):
        self._logger = get_logger_for(self)
        self._context_name_or_url = context_name_or_url
        self._factory = use(self._context_name_or_url, no_auth=no_auth)
        self._cs: CollectionServiceClient = self._factory.get_one_of(client_class=CollectionServiceClient)
        self._no_auth = no_auth

    def collection(self, id_or_slug_name: Optional[str] = None, *, name: Optional[str] = None) -> Collection:
        # NOTE: "ID" and "slug name" are unique identifier whereas "name" is not.
        return Collection(self._factory,
                          self._cs,
                          self.get_collection_info(id_or_slug_name=id_or_slug_name, name=name),
                          no_auth=self._no_auth)

    def get_filtered_data(self, signed_url):
        return FilterOperation(signed_url)
