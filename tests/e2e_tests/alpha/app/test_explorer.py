from unittest import TestCase

from dnastack.alpha.app.explorer import Explorer
from dnastack.alpha.app.publisher_helper.models import ItemType
from dnastack.common.logger import get_logger


def get_signed_url(collection, file_name):
    """
    Given a collection and a file within that collection, get a signed URL for that file
    Args:
      collection (Collection): An Explorer collection containing the file of interest
      file_name (str)        : The name of a file contained in the collection
    Returns:
      signed_url (str): A signed https:// URL that can be used to retrieve the file
    """
    signed_url = collection.find_blob_by_name(file_name).get_access_url_object().url
    return signed_url


class TestEndToEnd(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.explorer_client = Explorer('viral.ai', no_auth=True)

    def _find_collection_with_items(self, item_type, item_type_name):
        """
        Helper method to find a collection with items of the specified type.
        
        Args:
            item_type: The ItemType to search for (e.g., ItemType.BLOB, ItemType.TABLE)
            item_type_name: Human-readable name for error messages (e.g., "blob", "table")
            
        Returns:
            tuple: (collection, items) if found, raises AssertionError if not found
        """
        registered_collections = self.explorer_client.list_collections()
        
        for collection_info in registered_collections:
            collection = self.explorer_client.collection(collection_info.slugName)
            items = collection.list_items(limit=10, kind=item_type)
            identical_items = collection.list_items(limit=10, kinds=[item_type])
            
            if items:
                # Verify both filter methods yield the same result
                self.assertEqual(len(items), len(identical_items),
                               'Both filter methods should yield the same result.')
                return collection, items
        
        # If no suitable collection found, fail the test
        self.fail(f'No usable collections out of {len(registered_collections)} for this test. '
                 f'A suitable collection must have at least one {item_type_name}.')

    def test_drs(self):
        """
        Happy path for DRS API

        This is based on Jim's demo code.
        """
        logger = get_logger('Explorer.TestEndToEnd.test_drs')
        
        collection, blobs = self._find_collection_with_items(ItemType.BLOB, "blob")
        logger.debug(f'C/{collection.info.slugName}: Found some blobs for this test')

        for blob in blobs:
            signed_url = get_signed_url(collection, blob.name)
            self.assertGreater(len(signed_url), 0, f'The given signed URL is "{signed_url}".')

    def test_data_connect(self):
        """
        Happy path for Data Connect API

        This is based on Jim's demo code.
        """
        collection, tables = self._find_collection_with_items(ItemType.TABLE, "table")

        for table in tables:
            self.assertRegex(table.name, r'^collections\.[^.]+\.[^.]+$')

            df = collection.query(
                # language=sql
                f'SELECT * FROM {table.name} LIMIT 10'
            ).to_data_frame()

            self.assertGreaterEqual(len(df), 0, 'Failed to iterating the result.')
            return  # We only concern the first table that is available for testing.
