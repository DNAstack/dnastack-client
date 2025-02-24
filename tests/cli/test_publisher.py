import time
import unittest

import click

from dnastack.client.collections.model import Collection
from dnastack.common.environments import env
from tests.cli.base import PublisherCliTestCase


class TestPublisherCommand(PublisherCliTestCase):
    @staticmethod
    def reuse_session() -> bool:
        return True

    def setUp(self) -> None:
        super().setUp()
        self.invoke('use', self.service_registry_base_url)
        collection_service_registry_id = 'collection-service-registry'
        existing_registries = self.simple_invoke('config', 'registries', 'list')
        if not any(registry['id'] == collection_service_registry_id for registry in existing_registries):
            self.invoke(
                'config', 'registries', 'add',
                f'{collection_service_registry_id}', f'{self.collection_service_base_url}/service-registry'
            )
        else:
            click.echo(f'Registry {collection_service_registry_id} already exists. Skipping adding it.')

        self.collection = self._create_empty_collection()

    def _get_first_collection_with_table(self):
        collections_result = self.simple_invoke(
            'publisher', 'collections', 'list'
        )
        for collection_data in collections_result:
            collection = Collection(**collection_data)
            if collection.itemCounts.get('table', 0) > 0:
                return collection
        raise ValueError('No collection with table item count greater than 0 found')

    def _create_empty_collection(self):
        collection_name = f'dnastack-client-col{time.time_ns()}'
        return Collection(**self.simple_invoke(
            'publisher', 'collections', 'create',
            '--name', collection_name,
            '--description', "foo",
            '--slug', collection_name,
        ))


    def test_collections_list(self):
        collections_result = [Collection(**collection) for collection in self.simple_invoke(
            'publisher', 'collections', 'list'
        )]

        self.assert_not_empty(collections_result, f'Expected at least one collection. Found: {collections_result}')
        for collection in collections_result:
            self.assert_not_empty(collection.id, 'Collection ID should not be empty')


    def test_collections_describe(self):
        describe_collections = self.simple_invoke(
            'publisher', 'collections', 'describe',
            self.collection.slugName,
        )

        self.assertEqual(len(describe_collections), 1, 'Expected exactly one collection.')
        for collection in describe_collections:
            self.assertEqual(collection['id'], self.collection.id, 'Collection ID should match')


    def test_collections_describe_with_duplicate_ids(self):
        describe_collections = self.simple_invoke(
            'publisher', 'collections', 'describe',
            self.collection.id,
            self.collection.id
        )

        self.assertEqual(len(describe_collections), 1, 'Expected exactly one collection. Duplicates should be removed.')
        for collection in describe_collections:
            self.assertEqual(collection['id'], self.collection.id, 'Collection ID should match')


    def test_collections_describe_with_duplicate_results(self):
        describe_collections = self.simple_invoke(
            'publisher', 'collections', 'describe',
            self.collection.slugName,
            self.collection.id
        )

        self.assertEqual(len(describe_collections), 1, 'Expected exactly one collection. Duplicates should be removed.')
        for collection in describe_collections:
            self.assertEqual(collection['id'], self.collection.id, 'Collection ID should match')


    def test_collections_create(self):
        collection_name = f'dnastack-client-col{time.time_ns()}'
        created_collection = Collection(**self.simple_invoke(
            'publisher', 'collections', 'create',
            '--name', collection_name,
            '--description', "Cohort of participants with quality of life assessments",
            '--slug', collection_name,
        ))

        self.assertEqual(created_collection.name, collection_name)
        self.assertEqual(created_collection.description, "Cohort of participants with quality of life assessments")
        self.assertEqual(created_collection.slugName, collection_name)


    def test_collections_create_with_conflicting_name(self):
        collection_name = f'dnastack-client-col{time.time_ns()}'
        self.simple_invoke(
            'publisher', 'collections', 'create',
            '--name', collection_name,
            '--description', "Cohort of participants with quality of life assessments",
            '--slug', collection_name,
        )

        self.expect_error_from([
            'publisher', 'collections', 'create',
            '--name', collection_name,
            '--description', "Cohort of participants with quality of life assessments",
            '--slug', collection_name,
        ],
            rf'.*Error: A collection with the name "{collection_name}" or slug .* already exists.*')


    def test_collections_create_with_missing_required_fields(self):
        # Missing name
        self.expect_error_from([
            'publisher', 'collections', 'create',
            '--description', "Cohort of participants with quality of life assessments",
            '--slug', "study1-cohort",
        ],
            r'.*Missing option \'--name\'.*')

        # Missing description
        self.expect_error_from([
            'publisher', 'collections', 'create',
            '--name', "Study1 Cohort",
            '--slug', "study1-cohort",
        ],
            r'.*Error: Missing option \'--description\'.*')

        # Missing slug
        self.expect_error_from([
            'publisher', 'collections', 'create',
            '--name', "Study1 Cohort",
            '--description', "Cohort of participants with quality of life assessments",
        ],
            r'.*Error: Missing option \'--slug\'.*')


    def test_collections_status(self):
        result = self.invoke(
            'publisher', 'collections', 'status',
            '--collection', self.collection.slugName,
        )

        self.assertIn('Validation Status:', result.output)


    @unittest.skip("Skipping this test until the issue with BQ sideloading is resolved")
    def test_collections_query(self):
        collection_slug = env(key='E2E_COLLECTION_SLUG', default=None)
        if not collection_slug:
            collection_slug = self._get_first_collection_with_table()

        tables_result = self.simple_invoke(
            'publisher', 'collections', 'tables', 'list',
            '--collection', collection_slug
        )
        first_table = tables_result[0]
        query_result = self.simple_invoke(
            'publisher', 'collections', 'query',
            '--collection', collection_slug,
            f'SELECT * FROM {first_table["name"]} LIMIT 1'
        )

        self.assertIsNotNone(query_result, 'Query result should not be None (can be empty though)')


    def test_collections_items_list(self):
        collection_with_table = self._get_first_collection_with_table()
        items_result = self.simple_invoke(
            'publisher', 'collections', 'items', 'list',
            '--collection', collection_with_table.slugName,
            '--max-results', 1
        )

        self.assertEqual(len(items_result), 1, f'Expected exactly one item. Found {items_result}')
        for item in items_result:
            self.assert_not_empty(item['id'], 'Item ID should not be empty')


    def test_collections_items_list_with_type_and_limit(self):
        collection_with_table = self._get_first_collection_with_table()
        items_result = self.simple_invoke(
            'publisher', 'collections', 'items', 'list',
            '--collection', collection_with_table.slugName,
            '--limit', 100,
            '--type', 'table',
            '--max-results', 1
        )

        self.assertEqual(len(items_result), 1, f'Expected exactly one item. Found {items_result}')
        for item in items_result:
            self.assert_not_empty(item['id'], 'Item ID should not be empty')
            self.assertEqual(item['type'], 'table', 'Item type should be table')


    def test_collections_items_add_with_missing_required_fields(self):
        # Missing collection
        self.expect_error_from([
            'publisher', 'collections', 'items', 'add',
            '--datasource', 'test-datasource',
            '--files', 'file1.txt'
        ],
            r'.*Missing option \'--collection\'.*')

        # Missing datasource
        self.expect_error_from([
            'publisher', 'collections', 'items', 'add',
            '--collection', 'test-collection',
            '--files', 'file1.txt'
        ],
            r'.*Error: Missing option \'--datasource\'.*')

        # Missing files
        self.expect_error_from([
            'publisher', 'collections', 'items', 'add',
            '--collection', 'test-collection',
            '--datasource', 'test-datasource',
        ],
            r'.*Error: Missing option \'--files\'.*')


    def test_collections_items_remove_with_missing_required_fields(self):
        # Missing collection
        self.expect_error_from([
            'publisher', 'collections', 'items', 'remove',
            '--datasource', 'test-datasource',
            '--files', 'file1.txt'
        ],
            r'.*Missing option \'--collection\'.*')

        # Missing datasource
        self.expect_error_from([
            'publisher', 'collections', 'items', 'remove',
            '--collection', 'test-collection',
            '--files', 'file1.txt'
        ],
            r'.*Error: Missing option \'--datasource\'.*')

        # Missing files
        self.expect_error_from([
            'publisher', 'collections', 'items', 'remove',
            '--collection', 'test-collection',
            '--datasource', 'test-datasource',
        ],
            r'.*Error: Missing option \'--files\'.*')


    def test_collections_tables_list(self):
        collection_with_table = self._get_first_collection_with_table()
        tables_result = self.simple_invoke(
            'publisher', 'collections', 'tables', 'list',
            '--collection', collection_with_table.slugName
        )

        self.assert_not_empty(tables_result, f'Expected at least one table. Found: {tables_result}')
        for table in tables_result:
            self.assert_not_empty(table['name'], 'Table name should not be empty')
