# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the DNAstack client library and CLI, a Python package that provides both a command-line interface and client library for DNAstack services and GA4GH-compatible services. The package is distributed as `dnastack-client-library` and provides two entry points: `dnastack` and `omics`.

## Commit Guidelines
- Each commit must begin with the Clickup task ID surrounded by square brackets. Example: [CU-86b53h2wv].
- Branch names must includes the Clickup task ID.  E.g. upgrade_Datadog_Java_agent_version_to_v1490-CU-86b53h2wv

## Development Commands

### Development Setup
- `make setup` - Set up development environment with uv
- `source .venv/bin/activate` - Activate the virtual environment

### Running the CLI
- Use `python -m dnastack` from the project root to run the CLI (or `uv run python -m dnastack` without activation)
- To connect to a local publisher instance using a service registry you can use `python -m dnastack use  http://localhost:8093/service-registry`
- To list all collections use `python -m dnastack cs list`
- Alternatively, you can use `python -m dnastack cs list` to list all collections

### Testing
- `make test-unit` - Run unit tests
- `make test-unit-cov` - Run unit tests with coverage report
- `make test-unit-watch` - Run unit tests in watch mode (auto-rerun on file changes)
- `make test-e2e` - Run E2E tests using `.env` file for configuration
- `make test-all` - Run both unit and E2E tests
- `make docker-test-all` - Run tests across multiple Python versions in Docker
- `make docker-test-all-baseline` - Test with Python 3.8 (minimum supported version)
- `make docker-test-all-stable` - Test with Python 3.11 (current stable)
- `make docker-test-all-latest` - Test with Python 3.12 (latest)
- `./scripts/run-e2e-tests.sh` - Direct E2E test execution script

### Linting
- `make lint` - Run ruff linter to check code style and errors (zero-tolerance policy - all violations must be fixed)
- `make lint-fix` - Auto-fix linting issues and format code with ruff
  - Runs `uv run ruff check --fix .` to auto-fix violations where possible
  - Runs `uv run ruff format .` to format code consistently
- **Configuration**: Minimal setup in `pyproject.toml` with Python 3.8 target and 120 character line length
- **CI Integration**: GitHub Actions workflow (`.github/workflows/lint.yml`) uses uv for consistent environment
- **Version**: Fixed at ruff==0.11.13 in pyproject.toml for consistency across environments
- **Development Notes**:
  - Avoid star imports (`from module import *`) - use explicit imports for better code clarity
  - When fixing linting violations in critical modules, add unit tests first to prevent regressions
  - Use `make test-unit-cov` to verify test coverage before making risky changes
  - Test locally with `act` before pushing GitHub Actions changes

### Pre-commit Checks
**IMPORTANT**: Always run these checks before committing:
```bash
make lint        # Check for linting issues
make test-unit   # Run unit tests
```
Or use the combined command:
```bash
make lint && make test-unit
```

### Package Management
- `make package-test` - Build and test package installation in clean container
- `make publish` - Build package for distribution (shows publishing instructions)
- `uv build` - Build source distribution and wheel
- `uv publish` - Publish to PyPI (requires credentials)

### Development Environment
- `make reset` - Clean configuration and session files
- `make run-notebooks` - Start Jupyter notebook server for samples
- `make run-notebooks-dev` - Start Jupyter with development volume mounts

### Python Requirements
- Minimum Python version: 3.8
- Development tested on: 3.8, 3.11, 3.12
- Main dependencies: click, pydantic v1, requests, pyyaml

## Architecture

### CLI Architecture
The CLI uses a modular command structure built on Click with custom formatting:
- `dnastack/__main__.py` - Main CLI entry point with command group registration
- `dnastack/cli/core/` - Core CLI framework with custom formatting and command specs
- `dnastack/cli/commands/` - Individual command modules (auth, collections, dataconnect, etc.)
- Commands use `@formatted_command` decorator with `ArgumentSpec` for consistent parameter handling

### Client Architecture
The project follows a service-oriented client pattern:
- `dnastack/client/` - Core client implementations
- `dnastack/client/factory.py` - Dynamic client creation based on service endpoints
- `dnastack/client/base_client.py` - Base class for all service clients
- Service-specific clients: collections, data_connect, drs, workbench modules
- `dnastack/client/service_registry/` - Service discovery and registration

### Configuration System
- `dnastack/configuration/` - Configuration management with context support
- `dnastack/context/` - Context switching for different environments
- Configuration supports multiple authentication methods including OAuth2
- Session management in `dnastack/http/session.py`

### Authentication System
The CLI implements a sophisticated OAuth2 authentication system:
- `dnastack/http/authenticators/` - Core authenticator implementations
- `dnastack/http/authenticators/oauth2.py` - Main OAuth2 authenticator with state management
- `dnastack/http/authenticators/oauth2_adapter/` - OAuth2 flow adapters:
  - `device_code_flow.py` - Interactive browser-based authentication (e.g., Publisher, Workbench)
  - `client_credential.py` - Service account authentication (programmatic access)
  - `abstract.py` - Base adapter class with authentication events
  - `factory.py` - Adapter selection based on OAuth2 configuration

#### OAuth2 Authentication Flow
1. Commands trigger authentication when making API requests via `HttpSession`
2. `OAuth2Authenticator` checks for valid session, triggers auth if needed
3. Device code flow: Shows URL for browser authentication, polls for completion
4. Tokens stored locally with refresh capability
5. Authentication states: `ready`, `uninitialized`, `refresh_required`, `reauth_required`

#### Service-Specific Auth Configuration
- **Publisher**: Uses device code flow with custom login handler
- **Workbench**: Supports both device code and client credentials
- Sessions persist across CLI invocations
- Automatic token refresh using refresh tokens

#### Authentication Behavior for Protected Resources
When accessing protected resources (collections, data, etc.):
- **Automatic Authentication**: CLI automatically prompts for authentication when accessing protected resources
- **No User Rejection**: Instead of rejecting requests from unauthenticated users, the CLI initiates the OAuth2 flow
- **Seamless Continuation**: After successful authentication, the original command continues without user re-execution
- **Access Policies**: Resources can have different access levels:
  - **Public**: Open access, available to non-authenticated users
  - **Registered**: Requires authentication, triggers login flow automatically
  - **Custom**: Organization-specific access controls
- **No-Auth Mode**: Use `--no-auth` flag to skip authentication (useful for public resources)
- **Error Handling**: 401/403 responses trigger authentication unless in no-auth mode

### Key Patterns
- **Service Discovery**: Uses service registry pattern for dynamic endpoint discovery
- **Authentication**: Pluggable authenticator system with multiple OAuth2 flows
- **Client Factory**: Dynamic client instantiation based on service types
- **Context Management**: Environment-specific configuration switching
- **Alpha Features**: Experimental features isolated in `dnastack/alpha/`
- **Adapter Pattern**: OAuth2 flows implemented as pluggable adapters
- **Event-Driven Auth**: Authentication events for UI feedback

### Module Organization
- `dnastack/cli/` - Command-line interface
- `dnastack/client/` - Service client implementations  
- `dnastack/alpha/` - Experimental alpha features
- `dnastack/common/` - Shared utilities (logging, events, auth)
- `dnastack/configuration/` - Configuration management
- `dnastack/context/` - Context/environment management
- `dnastack/http/` - HTTP session and authentication

## Test Structure
- `tests/cli/` - CLI command tests
- `tests/client/` - Client library tests
- `tests/alpha/` - Alpha feature tests
- E2E tests require environment configuration via `.env` file
- Test helpers in `tests/exam_helper*.py` for different service types