"""
Authentication-related test fixtures.
"""
import pytest
from unittest.mock import Mock, patch


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


@pytest.fixture
def mock_device_code_authenticator():
    """Mock device code flow authenticator."""
    with patch('dnastack.http.authenticators.oauth2_adapter.device_code_flow.DeviceCodeAuthorizationFlow') as mock:
        flow = Mock()
        flow.authenticate.return_value = {
            'access_token': 'device_token',
            'refresh_token': 'device_refresh',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock.return_value = flow
        yield flow