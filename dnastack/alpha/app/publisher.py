from typing import Optional

from dnastack.alpha.app.publisher_helper.collection_service import (
    BlobApiMixin,
    PerCollectionApiMixin,
    RootCollectionApiMixin,
)
from dnastack.alpha.app.publisher_helper.data_connect import SearchOperation
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.collections.model import Collection as CollectionModel
from dnastack.client.data_connect import DataConnectClient
from dnastack.client.drs import Blob, DrsClient
from dnastack.client.factory import EndpointRepository
from dnastack.common.logger import get_logger_for
from dnastack.context.helper import use


class Collection(PerCollectionApiMixin, BlobApiMixin):
    """High-level Collection API Client"""

    def __init__(
        self,
        factory: EndpointRepository,
        cs: CollectionServiceClient,
        collection: CollectionModel,
        dc: DataConnectClient,
        no_auth: bool,
    ):
        self._logger = get_logger_for(self)
        self._factory = factory
        self._cs = cs
        self._collection = collection
        self._no_auth = no_auth
        self._drs: DrsClient = self._factory.get_one_of(client_class=DrsClient)
        self._dc = dc

    def get_record(self) -> CollectionModel:
        return self._collection

    def query(self, query: str):
        return SearchOperation(self._dc, self._no_auth, query)

    def find_blob_by_name(self, objectname: str) -> Blob:
        return self._find_blob_by_name(objectname=objectname, column_name="metadata_url")


class Publisher(RootCollectionApiMixin):
    """High-level Publisher API Client

    Docs: /docs/alpha/app/publisher.md

    .. code-block:: python

        from dnastack.alpha.app.explorer import Publisher

        # Data Connect
        query = Publisher(<url>).query('SELECT * FROM collections.public_datasets.metadata LIMIT 5')
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
        self._no_auth = no_auth
        self._cs: CollectionServiceClient = self._factory.get_one_of(client_class=CollectionServiceClient)
        self._dc = self.data_connect()

    def collection(self, id_or_slug_name: Optional[str] = None, *, name: Optional[str] = None) -> Collection:
        return Collection(
            self._factory,
            self._cs,
            self.get_collection_info(id_or_slug_name=id_or_slug_name, name=name),
            self._dc,
            no_auth=self._no_auth,
        )

    def query(self, query: str):
        return SearchOperation(self._dc, self._no_auth, query)

    def data_connect(self) -> DataConnectClient:
        default_no_auth_properties = {"authentication": None, "fallback_authentications": None}

        # Look up for any similar registered service endpoint.
        matched_endpoints = self._factory.all(client_class=DataConnectClient)
        if matched_endpoints:
            target_endpoint = matched_endpoints[0]
        else:
            raise RuntimeError("Unable to find a usable Data Connect endpoint")

        return DataConnectClient.make(
            target_endpoint.copy(update=default_no_auth_properties) if self._no_auth else target_endpoint
        )
