"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

# Import fixtures from organized modules
pytest_plugins = [
    'tests.unit.fixtures.auth_fixtures',
    'tests.unit.fixtures.service_fixtures', 
    'tests.unit.fixtures.data_fixtures'
]

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