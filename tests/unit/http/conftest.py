"""
HTTP-specific test configuration and fixtures.
"""
import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_requests_response():
    """Mock requests.Response object."""
    response = MagicMock()
    response.status_code = 200
    response.ok = True
    response.headers = {}
    response.json.return_value = {}
    response.text = ""
    response.content = b""
    return response


@pytest.fixture
def mock_failed_response():
    """Mock failed requests.Response object."""
    response = MagicMock()
    response.status_code = 401
    response.ok = False
    response.headers = {}
    response.json.side_effect = ValueError("No JSON content")
    response.text = "Unauthorized"
    response.content = b"Unauthorized"
    return response