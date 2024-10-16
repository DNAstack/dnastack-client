from copy import deepcopy
from typing import Optional, Dict, List, Iterable, Callable, Any

from dnastack.alpha.app.publisher_helper.exceptions import NoCollectionError, TooManyCollectionsError
from dnastack.alpha.app.publisher_helper.models import ItemType, BaseItemInfo, BlobInfo, TableInfo
from dnastack.client.collections.client import UnknownCollectionError
from dnastack.client.collections.model import Collection as CollectionModel
from dnastack.client.drs import Blob
from dnastack.common.simple_stream import SimpleStream


class RootCollectionApiMixin:
    def list_collections(self) -> List[CollectionModel]:
        return self._cs.list_collections(no_auth=self._no_auth)

    def get_collection_info(self, id_or_slug_name: Optional[str] = None, *, name: Optional[str] = None) -> CollectionModel:
        # NOTE: "ID" and "slug name" are unique identifier whereas "name" is not.
        assert id_or_slug_name or name, 'One of the arguments MUST be defined.'

        if id_or_slug_name is not None:
            try:
                collection = self._cs.get(id_or_slug_name, no_auth=self._no_auth)
            except UnknownCollectionError as e:
                raise NoCollectionError(id_or_slug_name) from e
            return collection
        elif name is not None:
            assert name.strip(), 'The name cannot be empty.'
            target_collections = SimpleStream(self._cs.list_collections(no_auth=self._no_auth)) \
                .filter(lambda endpoint: name == endpoint.name) \
                .to_list()
            if len(target_collections) == 1:
                return target_collections[0]
            elif len(target_collections) == 0:
                raise NoCollectionError(name)
            else:
                raise TooManyCollectionsError(target_collections)
        else:
            raise NotImplementedError()


class PerCollectionApiMixin:
    def list_items(self,
                   *,
                   limit: Optional[int] = 0,
                   kind: Optional[ItemType] = None,
                   kinds: Optional[Iterable[ItemType]] = None,
                   on_has_more_result: Optional[Callable[[int], None]] = None) -> List[BaseItemInfo]:
        """
        List items in the collection.

        :param limit: The number of items to return (default to ZERO)
        :param kind: The ONLT type of items to list
        :param kinds: The list of types of items to list
        :param on_has_more_result: A callback when there are more result to iterate.
        :return:
        """
        # NOTE: We opt for an enum on item types (kind/kinds) in this case to avoid SQL-injection attempts.
        assert limit >= 0, 'The limit has to be ZERO (no limit) or at least 1 (to impose the limit).'

        if kinds is None and kind is not None:
            kinds = [kind]

        items: List[BaseItemInfo] = []

        # NOTE: We DO NOT query the internal tables (_files and _tables) directly as it does not come with
        #       the pre-computed fully qualified table name, which automatically generated by Collection Service
        #       or Explorer.
        items_query = self._collection.itemsQuery.strip()

        # We use +1 as an indicator whether there are more results.
        actual_items_query = f'SELECT * FROM ({items_query})'

        if kind:
            actual_items_query = f"{actual_items_query} WHERE type = '{kind.value}'"
        elif kinds:
            types = ', '.join([f"'{kind}'" for kind in kinds])
            actual_items_query = f"{actual_items_query} WHERE type IN ({types})"

        if limit is not None and limit > 1:
            actual_items_query = f"{actual_items_query} LIMIT {limit + 1}"

        items.extend([
            self.__simplify_item(i)
            for i in self._dc.query(actual_items_query, no_auth=self._no_auth)
        ])

        row_count = len(items)

        if 0 < limit < row_count and on_has_more_result and callable(on_has_more_result):
            on_has_more_result(row_count)

        return items

    @staticmethod
    def __simplify_item(row: Dict[str, Any]) -> BaseItemInfo:
        if row['type'] == ItemType.BLOB:
            return BlobInfo(**row)
        elif row['type'] == ItemType.TABLE:
            row_copy = deepcopy(row)
            # FIXME This is a hack to improve the usability issue.
            row_copy['name'] = (
                    row.get('qualified_table_name')
                    or row.get('display_name')
                    or row['name']
            )
            return TableInfo(**row_copy)
        else:
            return BaseItemInfo(**row)


class BlobApiMixin:
    def blob(self, *, id: Optional[str] = None, name: Optional[str] = None) -> Optional[Blob]:
        blobs = self.blobs(ids=[id] if id else [], names=[name] if name else [])
        if blobs:
            return blobs.get(id if id is not None else name)
        else:
            return None

    def blobs(self, *, ids: Optional[List[str]] = None, names: Optional[List[str]] = None) -> Dict[str, Optional[Blob]]:
        assert ids or names, 'One of the arguments MUST be defined.'

        if ids:
            conditions: str = ' OR '.join([
                f"(id = '{id}')"
                for id in ids
            ])
        elif names:
            conditions: str = ' OR '.join([
                f"(name = '{name}')"
                for name in names
            ])
        else:
            raise NotImplementedError()

        collection: CollectionModel = self._collection

        id_to_name_map: Dict[str, str] = SimpleStream(
            self.query(f"SELECT id, name FROM ({collection.itemsQuery}) WHERE {conditions}").load_data()
        ).to_map(lambda row: row['id'], lambda row: row['name'])

        return {
            id if ids is not None else id_to_name_map[id]: self._drs.get_blob(id)
            for id in id_to_name_map.keys()
        }

    def _find_blob_by_name(self,
                           objectname: str,
                           column_name: str) -> Blob:
        collection: CollectionModel = self._collection

        db_slug = collection.slugName.replace("-", "_")

        # language=sql
        q = f"SELECT {column_name} FROM collections.{db_slug}._files WHERE name='{objectname}' LIMIT 1"

        results = self.query(q)
        return self._drs.get_blob(next(results.load_data())[column_name], no_auth=self._no_auth)