# Testing Strategy for DNAstack Client Library

## Overview

This document outlines the testing strategy for the DNAstack client library, including the separation of unit tests from E2E tests and the implementation of a comprehensive CI/CD pipeline for automated testing.

## Current State

### Existing Test Structure
- **Total test files**: 31 (excluding `__init__.py`)
- **Current CI coverage**: Only CLI E2E tests (`tests/cli/test_*`)
- **Excluded from CI**: ~59% of tests including client library tests, core utility tests, and alpha features
- **Test framework**: unittest (Python standard library)

### Test Categories Currently Present
1. **CLI Tests** (`tests/cli/`): 14 files - E2E tests requiring external services
2. **Client Library Tests** (`tests/client/`): 10 files - Mix of unit and integration tests
3. **Core/Utility Tests** (`tests/`): 8 files - Mostly unit tests
4. **Alpha Feature Tests** (`tests/alpha/`): 2 files - E2E tests

## Proposed Testing Strategy

### 1. Test Classification

#### Unit Tests
Tests that can run in isolation without external dependencies:
- `tests/test_common_class_decorator.py`
- `tests/test_events.py`
- `tests/test_json_argument_parser.py`
- `tests/test_parser.py`
- `tests/test_workflow_source_loader.py`
- `tests/client/test_auth_isolated.py`
- Core functionality tests that can be mocked

#### Integration Tests
Tests requiring some external components but not full services:
- HTTP session tests with mocked responses
- OAuth2 flow tests with mocked endpoints
- Client tests with mocked API responses

#### E2E Tests
Tests requiring real external services and authentication:
- All CLI command tests (`tests/cli/test_*.py`)
- Integrated authentication tests
- Full workflow tests
- Alpha feature tests

### 2. Directory Restructuring

**Important Constraint**: The existing E2E tests must remain in their current locations to maintain compatibility with Google Cloud Build, which expects tests at `tests/cli/test_*`.

```
tests/
├── unit/                       # Pure unit tests (no external dependencies)
│   ├── __init__.py
│   ├── common/                 # Common utilities unit tests
│   │   ├── test_class_decorator.py
│   │   ├── test_events.py
│   │   ├── test_json_argument_parser.py
│   │   └── test_parser.py
│   ├── client/                 # Client library unit tests
│   │   ├── test_auth_isolated.py
│   │   └── test_models.py
│   ├── http/                   # HTTP layer unit tests
│   │   ├── test_authenticators_oauth2.py
│   │   └── test_session.py
│   └── fixtures/               # Shared test fixtures and mocks
│       ├── __init__.py
│       └── mocks.py
├── cli/                        # E2E CLI tests (KEEP IN ORIGINAL LOCATION)
│   ├── test_auth.py
│   ├── test_collections.py
│   └── ...                     # All existing CLI tests remain here
├── client/                     # E2E Client tests (KEEP IN ORIGINAL LOCATION)
│   ├── test_collections.py
│   └── ...                     # All existing client tests remain here
├── alpha/                      # Alpha tests (KEEP IN ORIGINAL LOCATION)
├── conftest.py                 # Pytest configuration
├── exam_helper*.py             # Test helpers (KEEP IN ORIGINAL LOCATION)
└── ...                         # Other helper files
```

### 3. CI/CD Pipeline Implementation

#### GitHub Actions Workflows

**Unit Test Workflow** (`.github/workflows/unit-tests.yml`):
- Triggers: Every PR and push to main
- Python versions: 3.8, 3.11, 3.12
- Features:
  - Parallel test execution
  - Code coverage reporting
  - Fast feedback (<2 minutes)
  - No external dependencies required

**E2E Test Workflow** (`.github/workflows/e2e-tests.yml`):
- Triggers: Push to main and manual dispatch
- Uses existing Google Cloud Build for heavy E2E tests
- Can be optional for PRs due to time/resource constraints

### 4. Testing Infrastructure

#### Pytest Migration
- Migrate from unittest to pytest for better features:
  - Parameterized testing
  - Better fixtures management
  - Plugin ecosystem (coverage, parallel execution)
  - More readable output

#### Test Requirements
```
# tests/requirements-test.txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0
pytest-mock>=3.10.0
pytest-timeout>=2.1.0
responses>=0.23.0
hypothesis>=6.0.0  # For property-based testing
```

#### Makefile Updates
```makefile
# Unit tests
test-unit:
	pytest tests/unit -v

test-unit-cov:
	pytest tests/unit -v --cov=dnastack --cov-report=html --cov-report=term

test-unit-watch:
	pytest-watch tests/unit -v

# E2E tests (maintain backward compatibility with GCB)
test-e2e:
	./scripts/run-e2e-tests.sh tests/cli/test_*

test-e2e-local:
	E2E_ENV_FILE=.env.local ./scripts/run-e2e-tests.sh tests/cli/test_*

# All tests
test-all: test-unit test-e2e
```

### 5. Test Markers and Categories

```python
# pytest markers in pytest.ini
[pytest]
markers =
    unit: Unit tests that run without external dependencies
    integration: Tests requiring some external components
    e2e: End-to-end tests requiring full services
    slow: Tests that take >10 seconds
    auth: Authentication-related tests
    cli: CLI command tests
    client: Client library tests
```

### 6. Coverage Requirements

#### Initial Goals
- Unit test coverage: 70% minimum
- Critical path coverage: 90% (auth, core client functionality)
- New code coverage: 80% minimum

#### Coverage Configuration
```ini
# .coveragerc
[run]
source = dnastack
omit = 
    */tests/*
    */alpha/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### 7. Mock Strategy

#### Common Mocks
```python
# tests/unit/fixtures/mocks.py
class MockOAuth2Authenticator:
    """Mock OAuth2 authentication flows"""

class MockHTTPSession:
    """Mock HTTP requests with responses"""

class MockServiceRegistry:
    """Mock service discovery"""
```

### 8. Implementation Phases

#### Phase 1: Foundation (Week 1)
- [x] Create Testing_Strategy.md
- [ ] Set up directory structure
- [ ] Create GitHub Actions workflow for unit tests
- [ ] Add pytest configuration

#### Phase 2: Migration (Week 2)
- [ ] Move existing unit tests to new structure
- [ ] Convert simple unittest tests to pytest
- [ ] Create basic mock infrastructure
- [ ] Update Makefile

#### Phase 3: Enhancement (Week 3)
- [ ] Add coverage reporting
- [ ] Create missing unit tests for critical paths
- [ ] Implement test markers
- [ ] Add parallel test execution

#### Phase 4: Integration (Week 4)
- [ ] Make unit tests required for PRs
- [ ] Add coverage badges to README
- [ ] Document testing guidelines
- [ ] Train team on new structure

### 9. Future Enhancements

Based on previous recommendations:
1. **Security Testing Suite**: Add security-focused unit tests
2. **Performance Testing**: Add benchmark tests for critical paths
3. **Property-Based Testing**: Use hypothesis for edge case discovery
4. **Contract Testing**: Validate API compatibility
5. **Cross-Platform Testing**: Test on Windows, macOS, Linux in CI

### 10. Success Metrics

- **Speed**: Unit tests complete in <2 minutes
- **Coverage**: Achieve 70% unit test coverage
- **Reliability**: <1% flaky test rate
- **Developer Experience**: Tests can run locally without setup
- **CI/CD**: All PRs have automated test feedback

## Migration Checklist

- [ ] Create new directory structure
- [ ] Set up GitHub Actions workflows
- [ ] Move and categorize existing tests
- [ ] Add pytest and coverage configuration
- [ ] Update Makefile with new commands
- [ ] Create mock infrastructure
- [ ] Update CLAUDE.md with testing guidelines
- [ ] Add coverage badges to README
- [ ] Document in developer guide

## Conclusion

This testing strategy separates fast-running unit tests from slower E2E tests, enabling rapid feedback on PRs while maintaining comprehensive test coverage. The phased approach allows for gradual migration without disrupting current development workflows.