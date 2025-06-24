# UV Migration Plan for dnastack-client

## Overview
This document tracks the migration from pip to uv for the dnastack-client project, implementing modern Python packaging with `pyproject.toml` and dependency groups.

## Key Decisions
- ✅ Python version: 3.8 (via `.python-version`)
- ✅ Lock file: Commit `uv.lock` for reproducible builds
- ✅ Environment management: Let uv manage automatically
- ✅ Full migration to `pyproject.toml` with dependency groups
- ✅ Build backend: Keep setuptools (no hatchling migration)

## Migration Phases

### Phase 1: Foundation ✅ COMPLETED
- [x] Create `.python-version` file with `3.8`
- [x] Add `check-uv` target to Makefile
- [x] Update `.gitignore` for uv artifacts (exclude `uv.lock`)

**Status**: Completed - 2025-06-21

### Phase 2: pyproject.toml Migration ✅ COMPLETED
- [x] Create comprehensive `pyproject.toml`:
  - [x] Migrate metadata from `setup.cfg`
  - [x] Migrate dependencies from `setup.cfg`
  - [x] Add test dependencies as dependency group
  - [x] Add dev dependencies group
  - [x] Configure `[tool.uv]` section
- [x] Test local installation with uv
- [x] Generate and commit `uv.lock`

**Status**: Completed - 2025-06-21

### Phase 3: Makefile Updates ✅ COMPLETED
- [x] Update `test-setup` target to use uv
- [x] Update `package-test` target for uv
- [x] Add `setup` target for development setup
- [x] Add `publish` target for package publishing
- [x] Update all targets to depend on `check-uv`
- [x] Add `test-unit-watch` target for auto-rerunning tests
- [x] Add `test-e2e` target and fix `test-all`
- [x] Update lint commands to use `uv run`

**Status**: Completed - 2025-06-21

### Phase 4: CI/CD Updates ✅ COMPLETED
- [x] Update `.github/workflows/unit-tests.yml`:
  - [x] Add `astral-sh/setup-uv@v4` action
  - [x] Replace pip commands with uv
  - [x] Update caching for uv
- [x] Update `.github/workflows/lint.yml` to use uv
- [x] Test workflows with act (dry run successful)

**Status**: Completed - 2025-06-21

### Phase 5: Documentation & Cleanup ✅ COMPLETED
- [x] Update README.md with uv installation instructions
- [x] Update CLAUDE.md with uv commands
- [x] Document all new Makefile targets
- [x] Backup setup.cfg and create minimal version
- [x] Test package building and installation
- [x] Note: Existing linting issues found but pre-date migration

**Status**: Completed - 2025-06-21

## Implementation Notes

### pyproject.toml Structure
```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dnastack-client-library"
version = "3.1.0a0"
# ... rest of metadata

dependencies = [
    # Core dependencies
]

[project.optional-dependencies]
test = ["selenium>=3.141.0", "pyjwt>=2.1.0", "jsonpath-ng>=1.5.3"]

[dependency-groups]
test = [
    # Test dependencies from tests/requirements-test.txt
]
dev = [
    { include-group = "test" },
    "ruff==0.11.13",
]
```

### Key Commands Migration
- `pip install -r tests/requirements-test.txt` → `uv pip install --group test`
- `pip install -e .` → `uv pip install -e .`
- `python -m build` → `uv build`

## Risks & Mitigation
1. **Dependency conflicts**: Use `uv pip compile` to verify resolution
2. **CI failures**: Test locally first, keep old config until verified
3. **Missing dependencies**: Carefully audit all requirements files
4. **Python version issues**: Test with all supported versions (3.8, 3.11, 3.12)

## Progress Log
- **2025-06-21 - Started**: Created migration plan, beginning Phase 1
- **2025-06-21 - Phase 1 Complete**: Added `.python-version`, `check-uv` target, and updated `.gitignore`
- **2025-06-21 - Phase 2 Complete**: Created comprehensive `pyproject.toml`, tested installation, generated `uv.lock`
- **2025-06-21 - Phase 3 Complete**: Updated all Makefile targets to use uv, added new development targets
- **2025-06-21 - Phase 4 Complete**: Updated GitHub Actions workflows for uv, tested with act
- **2025-06-21 - Phase 5 Complete**: Updated documentation, minimal setup.cfg retained
- **2025-06-21 - Migration Complete**: All phases successfully completed

## Summary of Changes
1. Added `.python-version` file set to 3.8
2. Created comprehensive `pyproject.toml` with all dependencies and metadata
3. Generated and committed `uv.lock` for reproducible builds
4. Updated Makefile with uv commands and new development targets
5. Updated GitHub Actions workflows to use uv
6. Updated documentation (README.md, CLAUDE.md)
7. Retained minimal setup.cfg for backward compatibility
8. Note: Pre-existing linting issues (216 errors) were discovered but are outside scope of this migration