from unittest import TestCase

from dnastack.alpha.app.publisher import Publisher
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
        cls.publisher_client = Publisher('collection-service.publisher.dnastack.com', no_auth=True)

    def test_drs(self):
        """
        Happy path for DRS API

        This is based on Jim's demo code.
        """
        logger = get_logger('Publisher.TestEndToEnd.test_drs')

        publisher = self.publisher_client
        registered_collections = publisher.list_collections()

        for collection_info in registered_collections:
            collection = publisher.collection(collection_info.slugName)
            blobs = collection.list_items(limit=10, kind=ItemType.BLOB)

            if blobs:
                logger.debug(f'C/{collection_info.slugName}: Found some blobs for this test')
            else:
                logger.info(f'C/{collection_info.slugName}: Not usable for this test. No blobs available.')
                continue

            for blob in blobs:
                signed_url = get_signed_url(collection, blob.name)
                self.assertGreater(len(signed_url), 0, f'The given signed URL is "{signed_url}".')

            return

        self.fail(f'No usable collections out of {len(registered_collections)} for this test. A suitable collection '
                  'must have at least one blob.')

    def test_data_connect(self):
        """
        Happy path for Data Connect API

        This is based on Jim's demo code.
        """
        logger = get_logger('Publisher.TestEndToEnd.test_data_connect')

        publisher = self.publisher_client
        registered_collections = publisher.list_collections()

        for collection_info in registered_collections:
            # The original code selects all columns. This test code only select one column
            # to reduce the unnecessary load on the server.

            result = publisher.query(
                # language=sql
                f'SELECT name '
                f'FROM collections.{collection_info.dbSchemaName}._tables '
                f'LIMIT 10'
            )

            df = result.to_data_frame()

            if len(df) > 0:
                logger.debug(f'C/{collection_info.slugName}: Found some tables')
                self.assertTrue(True)  # Just to mark it as ok
                return
            else:
                logger.info(f'C/{collection_info.slugName}: Not usable for this test. No tables available.')
                continue

        self.fail(f'No usable collections out of {len(registered_collections)} for this test. A suitable collection '
                  'must have at least one table.')