"""
Client-specific test configuration and fixtures.
"""
import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_base_client():
    """Mock base client with common functionality."""
    client = Mock()
    client.endpoint = Mock()
    client.endpoint.url = "https://test.example.com"
    client.authenticator = Mock()
    return client


@pytest.fixture
def mock_service_endpoint():
    """Mock service endpoint."""
    from dnastack.client.models import ServiceEndpoint
    return ServiceEndpoint(
        id="test-endpoint",
        url="https://test.example.com",
        type="test-service"
    )