"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Common test configuration
@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test-specific environment variables
    os.environ['DNASTACK_TEST_MODE'] = 'true'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

# Authentication fixtures
@pytest.fixture
def mock_oauth2_authenticator():
    """Mock OAuth2 authenticator for unit tests."""
    with patch('dnastack.http.authenticators.oauth2.OAuth2Authenticator') as mock:
        authenticator = Mock()
        authenticator.authenticate.return_value = {
            'access_token': 'test_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock.return_value = authenticator
        yield authenticator

@pytest.fixture
def mock_http_session():
    """Mock HTTP session for unit tests."""
    with patch('dnastack.http.session.HttpSession') as mock:
        session = Mock()
        session.get.return_value.json.return_value = {}
        session.post.return_value.json.return_value = {}
        mock.return_value = session
        yield session

# Service mocks
@pytest.fixture
def mock_service_registry():
    """Mock service registry for unit tests."""
    from dnastack.client.service_registry.models import Service, ServiceType
    
    services = [
        Service(
            id='test-collections',
            name='Test Collections Service',
            type=ServiceType(group='com.dnastack', artifact='collection-service', version='1.0.0'),
            url='https://test.collections.example.com'
        ),
        Service(
            id='test-drs',
            name='Test DRS Service',
            type=ServiceType(group='org.ga4gh', artifact='drs', version='1.0.0'),
            url='https://test.drs.example.com'
        )
    ]
    
    with patch('dnastack.client.service_registry.client.ServiceRegistry') as mock:
        registry = Mock()
        registry.list_services.return_value = services
        registry.get_service.side_effect = lambda id: next((s for s in services if s.id == id), None)
        mock.return_value = registry
        yield registry

# Test data fixtures
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

# Utility functions
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Auto-mark tests based on their location
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "tests/cli" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.cli)
        elif "tests/client" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.client)