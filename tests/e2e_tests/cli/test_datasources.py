from typing import List

import click

from tests.e2e_tests.cli.base import PublisherCliTestCase


class TestDatasourcesCommand(PublisherCliTestCase):
    @staticmethod
    def reuse_session() -> bool:
        return False

    def setUp(self) -> None:
        super().setUp()
        self.invoke('use', self.service_registry_base_url)
        
        # Add collection service registry if not exists
        collection_service_registry_id = 'collection-service-registry' # we are using collection service for this
        existing_registries = self.simple_invoke('config', 'registries', 'list')
        if not any(registry['id'] == collection_service_registry_id for registry in existing_registries):
            self.invoke(
                'config', 'registries', 'add',
                f'{collection_service_registry_id}', f'{self.collection_service_base_url}/service-registry'
            )
        else:
            click.echo(f'Registry {collection_service_registry_id} already exists. Skipping adding it.')
        
        # Sync services to ensure datasources endpoint is discovered and authenticated
        self.invoke('config', 'registries', 'sync', collection_service_registry_id)
        
        # Set default endpoint for datasources adapter type
        # Since datasources use the same collection service endpoint, set it as default
        endpoints_result = self.simple_invoke('config', 'endpoints', 'list')
        collection_endpoint_id = None
        for endpoint in endpoints_result:
            if 'collection-service' in endpoint.get('type', ''):
                collection_endpoint_id = endpoint['id']
                break
        
        if collection_endpoint_id:
            self.invoke('config', 'defaults', 'set', 'datasources', collection_endpoint_id)

    def _get_default_parameters(self) -> List[str]:
        return ['-o', 'json']

    def test_list_datasources(self):
        """Test listing datasources"""
        datasources_result = self.simple_invoke('publisher', 'datasources', 'list')
        self.assert_not_empty(datasources_result, f'Expected at least one datasource. Found: {datasources_result}')

        for datasource in datasources_result:
            self.assert_not_empty(datasource['id'], 'Datasource ID should not be empty')
            self.assert_not_empty(datasource['name'], 'Datasource name should not be empty')
            self.assert_not_empty(datasource['type'], 'Datasource type should not be empty')

    def test_list_datasources_json_format(self):
        """Test listing datasources with JSON output"""
        result = self.simple_invoke('publisher', 'datasources', 'list', '-o', 'json')
        self.assertIsInstance(result, list)
        if len(result) > 0:
            datasource = result[0]
            self.assertIn('id', datasource)
            self.assertIn('name', datasource)
            self.assertIn('type', datasource)

    def test_list_datasources_yaml_format(self):
        """Test listing datasources with YAML output"""
        result = self.invoke('publisher', 'datasources', 'list', '-o', 'yaml')
        self.assertEqual(0, result.exit_code)
        datasources = self.parse_json_or_yaml(result.output)
        self.assertIsInstance(datasources, list)
        if len(datasources) > 0:
            datasource = datasources[0]
            self.assertIn('id', datasource)
            self.assertIn('name', datasource)
            self.assertIn('type', datasource)

    def test_list_datasources_with_invalid_format(self):
        """Test listing datasources with invalid output format"""
        self.expect_error_from(
            ['publisher', 'datasources', 'list', '-o', 'invalid_format'],
            "Invalid value for '--output' / '-o': 'invalid_format' is not one of 'json', 'yaml'"
        )

    def test_list_datasources_with_type_filter(self):
        """Test listing datasources with type filter"""
        # First get all datasources to find an existing type
        all_datasources = self.simple_invoke('publisher', 'datasources', 'list', '-o', 'json')
        self.assert_not_empty(all_datasources, "Expected at least one datasource for testing type filter")

        # Get the type of the first datasource
        test_type = all_datasources[0]['type']

        # Test with the existing type
        filtered_datasources = self.simple_invoke('publisher', 'datasources', 'list', '--type', test_type, '-o', 'json')
        self.assert_not_empty(filtered_datasources, f"Expected at least one datasource of type {test_type}")

        for datasource in filtered_datasources:
            self.assertEqual(datasource['type'].upper(), test_type.upper(),
                           f"Expected all datasources to be of type {test_type}")

    def test_list_datasources_with_nonexistent_type(self):
        """Test listing datasources with a type that doesn't exist"""
        result = self.simple_invoke('publisher', 'datasources', 'list', '--type', 'NONEXISTENT_TYPE', '-o', 'json')
        self.assertEqual(len(result), 0, "Expected no datasources for nonexistent type")

    def test_filter_datasource_fields(self):
        """Test datasource field filtering utility"""
        from dnastack.cli.commands.publisher.datasources.utils import _filter_datasource_fields

        test_cases = [
            {
                'name': 'full datasource',
                'input': {
                    'id': 'test-id',
                    'name': 'test-name',
                    'type': 'test-type',
                    'extra_field': 'should-not-appear'
                },
                'expected': {
                    'id': 'test-id',
                    'name': 'test-name',
                    'type': 'test-type'
                }
            },
            {
                'name': 'partial datasource',
                'input': {
                    'id': 'test-id',
                    'extra_field': 'should-not-appear'
                },
                'expected': {
                    'id': 'test-id',
                    'name': None,
                    'type': None
                }
            },
            {
                'name': 'empty datasource',
                'input': {},
                'expected': {
                    'id': None,
                    'name': None,
                    'type': None
                }
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['name']):
                filtered = _filter_datasource_fields(test_case['input'])
                self.assertEqual(filtered, test_case['expected'],
                               f"Failed on {test_case['name']}: expected {test_case['expected']}, got {filtered}")
