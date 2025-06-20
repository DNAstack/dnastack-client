"""
Service-related test fixtures.
"""
import pytest
from unittest.mock import Mock, patch


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
        ),
        Service(
            id='test-data-connect',
            name='Test Data Connect Service',
            type=ServiceType(group='org.ga4gh', artifact='data-connect', version='1.0.0'),
            url='https://test.dataconnect.example.com'
        )
    ]
    
    with patch('dnastack.client.service_registry.client.ServiceRegistry') as mock:
        registry = Mock()
        registry.list_services.return_value = services
        registry.get_service.side_effect = lambda id: next((s for s in services if s.id == id), None)
        mock.return_value = registry
        yield registry


@pytest.fixture
def mock_collection_service_client():
    """Mock collection service client."""
    with patch('dnastack.client.collections.client.CollectionServiceClient') as mock:
        client = Mock()
        client.list_collections.return_value = []
        client.get_collection.return_value = None
        mock.return_value = client
        yield client


@pytest.fixture
def mock_drs_client():
    """Mock DRS client."""
    with patch('dnastack.client.drs.DrsClient') as mock:
        client = Mock()
        client.get_object.return_value = None
        mock.return_value = client
        yield client