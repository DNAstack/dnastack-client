from uuid import uuid4

from dnastack.client.base_exceptions import DataConnectError
from dnastack.client.collections.client import UnknownCollectionError
from tests.cli.base import DeprecatedPublisherCliTestCase


class TestCollectionsCommand(DeprecatedPublisherCliTestCase):
    @staticmethod
    def reuse_session() -> bool:
        return True

    def setUp(self) -> None:
        super().setUp()
        self.invoke('use', self.explorer_urls[0])

    def test_general_flow(self):
        """ This is to test with the current implementation of collection service. """

        # Test listing collection
        collections = self.simple_invoke('collections', 'list', '--endpoint-id=collection-service')
        self.assertGreaterEqual(len(collections), 1, 'Must have at least one collection for this test')

        last_error = None

        for collection in collections:
            collection_slug_name = collection['slugName']
            try:
                self.assertIn('id', collection)
                self.assertIn('name', collection)
                self.assertIn('slugName', collection)
                self.assertIn('description', collection)
                self.assertNotIn('itemsQuery', collection)

                # Test listing tables in the collection
                tables = self.simple_invoke('cs',
                                            'tables',
                                            'list',
                                            '-c', collection_slug_name, '--endpoint-id=collection-service')
                self.assertGreaterEqual(len(tables), 0)

                max_size = 10

                # JSON version
                items_from_direct_query = self.simple_invoke('collections',
                                                             'list-items',
                                                             '--limit', str(max_size),
                                                             '--collection', collection_slug_name, '--endpoint-id=collection-service')
                self.assertLessEqual(len(items_from_direct_query), max_size, f'Expected upto {max_size} rows')

                # CSV version
                for table in tables:
                    query = f"SELECT * FROM ({table['name']}) LIMIT {max_size}"
                    result = self.invoke('cs', 'query', '-c', collection_slug_name, '-o', 'csv', query, '--endpoint-id=collection-service')
                    lines = result.output.split('\n')
                    self.assertLessEqual(len(lines), max_size + 1, f'Expected upto {max_size} lines, excluding headers')
                    for line in lines:
                        if not line.strip():
                            continue
                        self.assertTrue(',' in line, f'The content does not seem to be a CSV-formatted string.')

                # Test the list-item command.
                items_from_command = self.simple_invoke('collections',
                                                        'list-items',
                                                        '-c', collection_slug_name,
                                                        '-l', str(max_size), '--endpoint-id=collection-service')
                self.assertLessEqual(len(items_from_command), max_size, f'Expected upto {max_size} rows')

                common_ids = set([i['id'] for i in items_from_direct_query])\
                    .intersection([i['id'] for i in items_from_command])
                self.assert_not_empty(common_ids)

                return  # The test is complete here.
            except SystemExit as e:
                self._logger.warn(f'Collection "{collection_slug_name}" is not usable for this test. (CLI unexpected '
                                  f'termination)')
                last_error = e
            except AssertionError as e:
                self._logger.warn(f'Collection "{collection_slug_name}" is not usable for this test. (failed assertion')
                last_error = e

        raise RuntimeError('No usable collection for this test.') from last_error

    def test_182678656(self):
        """
        https://www.pivotaltracker.com/story/show/182678656

        When using the "dnastack collections query" command after initializing with the "dnastack use" command,
        there should not be an additional auth prompt if the target per-collection data-connect endpoint is registered.
        """
        self.invoke('use', self._explorer_hostname)
        collections = self.simple_invoke('collections', 'list', '--endpoint-id=collection-service')
        self.assert_not_empty(collections, 'No collection available')
        last_error = None
        for c in collections:
            try:
                self.simple_invoke('collections',
                                   'query',
                                   '-c', c['slugName'],
                                   'SELECT 1', '--endpoint-id=collection-service')

                return
            except DataConnectError as e:
                self._logger.warn(f'Collection "{c["slugName"]}" caused a DataConnectError: {e}')
                last_error = e
            except Exception as e:
                self._logger.warn(f'Collection "{c["slugName"]}" caused an unexpected error: {e}')
                last_error = e
            except SystemExit as e:
                self._logger.warn(f'Collection "{c["slugName"]}" caused an unexpected exit: {e}')
                last_error = e


        raise last_error

    def test_182881149(self):
        """
        https://www.pivotaltracker.com/story/show/182881149

        When querying on a non-existing collection, it should fail as the collection does not exist,
        not the authentication error, which is misleading.
        """
        with self.assert_exception_raised_in_chain(UnknownCollectionError):
            self.invoke('collections',
                        'query',
                        '-c', f'foobar-{uuid4()}',
                        'SELECT 1',
                        '--endpoint-id=collection-service')
