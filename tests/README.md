# DNAstack Client Library Tests

## Test Structure

The test suite is organized into two main categories:

### Unit Tests (Top Level)
- **Purpose**: Fast, isolated tests that don't require external dependencies
- **Location**: Top level directories (`tests/cli/`, `tests/client/`, `tests/common/`, `tests/http/`, etc.)
- **Run with**: `make test-unit` or `uv run pytest tests/`
- **Coverage**: `make test-unit-cov`

### E2E Tests (`tests/e2e_tests/`)
- **Purpose**: End-to-end tests requiring external services and authentication
- **Location**: `tests/e2e_tests/`
- **Structure**:
  - `tests/e2e_tests/cli/` - CLI command tests
  - `tests/e2e_tests/client/` - Client library integration tests  
  - `tests/e2e_tests/alpha/` - Alpha feature tests
- **Run with**: `make test-e2e` or `./scripts/run-e2e-tests.sh`

## Setting Up Test Environment

### Quick Setup
```bash
# Set up development environment with all dependencies
make setup

# Or install test dependencies only
uv sync --group test
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
uv run pytest tests/common/test_parser.py -v
```

### E2E Tests
```bash
# Run E2E tests
make test-e2e

# Run with custom environment
E2E_ENV_FILE=.env.local make test-e2e
```

### All Tests
```bash
# Run both unit and E2E tests
make test-all
```

## Test Requirements

Test dependencies are managed in `pyproject.toml`:
- Core test dependencies are in the `[dependency-groups.test]` section
- Optional test dependencies are in `[project.optional-dependencies.test]`

Install test dependencies:
```bash
uv sync --group test
```

## Writing Tests

### Unit Tests
- Place in top-level directories (`tests/cli/`, `tests/client/`, `tests/common/`, etc.) following the source code structure
- Use mocks from `tests/fixtures/mocks.py`
- Should run without external dependencies
- Should complete in <1 second per test

### E2E Tests
- Place in `tests/e2e_tests/` with subdirectories:
  - `tests/e2e_tests/cli/` - CLI command tests
  - `tests/e2e_tests/client/` - Client library integration tests
  - `tests/e2e_tests/alpha/` - Alpha feature tests
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
uv run pytest -m unit        # Only unit tests
uv run pytest -m "not e2e"   # Exclude E2E tests
```