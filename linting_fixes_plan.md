# Plan to Fix Remaining Linting Violations

## Overview
There are 30 linting violations in the codebase, all related to unused imports (F401) and unused variables (F841). These appear to be pre-existing issues that were revealed when we set up proper linting.

## Summary of Issues

### By Type:
- **F401 (Unused imports)**: 27 violations
- **F841 (Unused variables)**: 3 violations

### By Location:
- **Production code**: 5 violations (all in explorer module)
- **Test code**: 25 violations (mostly in explorer tests)

## Detailed Analysis

### Production Code Issues (5 violations)

1. **dnastack/cli/commands/explorer/questions/commands.py**
   - Line 149: Unused variable `collection_names`
   - This appears to be dead code that can be removed

2. **dnastack/cli/commands/explorer/questions/tables.py**
   - Line 2: Unused imports `QuestionParam`, `QuestionCollection`
   - These imports can be safely removed

3. **dnastack/client/explorer/client.py**
   - Line 1: Unused import `Iterator` from typing
   - Line 14: Unused import `QuestionQueryResult`
   - These imports can be safely removed

### Test Code Issues (25 violations)

Most violations are in test files where imports were added but never used:
- Multiple unused `MagicMock`, `Mock`, `patch` imports
- Unused `json`, `tempfile`, `os` imports
- Unused model imports in explorer tests
- Two unused variables in `test_explorer_client_working.py`

## Implementation Plan

### Phase 1: Automated Fixes (Safe)
Use ruff's auto-fix capability for all F401 violations:
```bash
make lint-fix
```
This will automatically remove 27 unused imports.

### Phase 2: Manual Fixes (Requires Review)
Fix the 3 F841 violations manually:

1. **dnastack/cli/commands/explorer/questions/commands.py:149**
   - Review the logic to determine if `collection_names` was intended to be used
   - Either use the variable or remove the assignment

2. **tests/unit/test_explorer_client_working.py:295**
   - The test creates `result_iter` but doesn't assert on it
   - Add assertions or remove if not needed

3. **tests/unit/test_explorer_client_working.py:318**
   - The test creates `result_iter2` but doesn't use it
   - Add assertions or remove if not needed

### Phase 3: Verification
1. Run full test suite to ensure no functionality is broken
2. Run linting to confirm all issues are resolved
3. Review the changes to ensure no important code was removed

## Risk Assessment

### Low Risk
- Removing unused imports (F401) is generally safe
- Most violations are in test files

### Medium Risk
- Removing unused variables in production code requires careful review
- The `collection_names` variable might have been intended for future use

### Mitigation
- Run comprehensive test suite after each change
- Review each manual fix carefully
- Keep changes in a separate commit for easy reversion

## Execution Steps

1. **Create a new branch for linting fixes**
   ```bash
   git checkout -b fix-linting-violations
   ```

2. **Run automated fixes**
   ```bash
   make lint-fix
   git diff  # Review changes
   ```

3. **Fix remaining violations manually**
   - Fix each F841 violation
   - Add appropriate tests if needed

4. **Verify all tests pass**
   ```bash
   make test-unit
   make test-e2e  # if environment is set up
   ```

5. **Commit changes**
   ```bash
   git add -A
   git commit -m "Fix linting violations: remove unused imports and variables"
   ```

6. **Create PR for review**

## Expected Outcome
- All 30 linting violations resolved
- No functional changes to the codebase
- Cleaner, more maintainable code
- CI/CD linting checks will pass

## Alternative Approach
If some imports/variables are intentionally kept for future use:
1. Add `# noqa: F401` or `# noqa: F841` comments to suppress specific warnings
2. Document why these are kept
3. Consider using `__all__` for imports that should be re-exported

## Next Steps
After fixing these violations:
1. Consider adding pre-commit hooks to catch these issues earlier
2. Update contributing guidelines to mention linting requirements
3. Consider gradually enabling more ruff rules for better code quality