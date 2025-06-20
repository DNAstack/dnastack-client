# DNAstack Client Library Tests

## Test Structure

The test suite is organized into two main categories:

### Unit Tests (`tests/unit/`)
- **Purpose**: Fast, isolated tests that don't require external dependencies
- **Location**: `tests/unit/`
- **Run with**: `make test-unit` or `pytest tests/unit`
- **Coverage**: `make test-unit-cov`

### E2E Tests (Original Locations)
- **Purpose**: End-to-end tests requiring external services and authentication
- **Locations**: 
  - `tests/cli/` - CLI command tests
  - `tests/client/` - Client library integration tests
  - `tests/alpha/` - Alpha feature tests
- **Run with**: `make test-e2e` or existing cloud build scripts

**Note**: E2E tests remain in their original locations to maintain compatibility with Google Cloud Build.

## Setting Up Test Environment

### Quick Setup
```bash
# Install all test dependencies
make test-setup

# Or manually install
pip install -e .
pip install -r tests/requirements-test.txt
```

## Running Tests

### Unit Tests
```bash
# Run all unit tests
make test-unit

# Run with coverage
make test-unit-cov

# Watch mode (auto-rerun on changes)
make test-unit-watch

# Run specific test file
pytest tests/unit/common/test_parser.py -v
```

### E2E Tests
```bash
# Run CLI E2E tests (as per GCB)
make test-e2e

# Run all E2E tests
make test-e2e-all

# Run with custom environment
E2E_ENV_FILE=.env.local make test-e2e
```

### All Tests
```bash
# Run both unit and E2E tests
make test-all
```

## Test Requirements

Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

## Writing Tests

### Unit Tests
- Place in `tests/unit/` following the source code structure
- Use mocks from `tests/unit/fixtures/mocks.py`
- Should run without external dependencies
- Should complete in <1 second per test

### E2E Tests
- Keep in original locations (`tests/cli/`, `tests/client/`, etc.)
- Require `.env` file with authentication credentials
- May take longer to run
- Test real service integration

## Test Markers

Tests can be marked with pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests taking >10 seconds
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.cli` - CLI tests
- `@pytest.mark.client` - Client library tests

Run tests by marker:
```bash
pytest -m unit        # Only unit tests
pytest -m "not e2e"   # Exclude E2E tests
```