"""
Sample data fixtures for testing.
"""
import pytest


@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing."""
    return {
        'id': 'test-collection-1',
        'name': 'Test Collection',
        'description': 'A test collection for unit tests',
        'items': [
            {'id': 'item-1', 'name': 'Test Item 1'},
            {'id': 'item-2', 'name': 'Test Item 2'}
        ]
    }


@pytest.fixture
def sample_table_data():
    """Sample table data for Data Connect testing."""
    return {
        'name': 'test_table',
        'description': 'Test table for unit tests',
        'data_model': {
            'properties': {
                'id': {'type': 'string'},
                'name': {'type': 'string'},
                'value': {'type': 'number'}
            }
        }
    }


@pytest.fixture
def sample_drs_object():
    """Sample DRS object data."""
    return {
        'id': 'drs://example.com/12345',
        'name': 'test_file.txt',
        'size': 1024,
        'checksums': [
            {'type': 'md5', 'checksum': 'd41d8cd98f00b204e9800998ecf8427e'}
        ],
        'access_methods': [
            {
                'type': 'https',
                'access_url': 'https://example.com/files/test_file.txt'
            }
        ]
    }


@pytest.fixture
def sample_query_response():
    """Sample Data Connect query response."""
    return {
        'table_name': 'test_table',
        'data': [
            {'id': '1', 'name': 'Item 1', 'value': 100},
            {'id': '2', 'name': 'Item 2', 'value': 200}
        ],
        'pagination': {
            'next_page_token': None,
            'prev_page_token': None
        }
    }