---
title: Add required --admin-email to namespaces create
date: 2026-03-24
repo: dnastack-client
services:
  - dnastack-client
  - workbench-user-service
tags:
  - cli
  - namespaces
  - workbench
  - iac
status: approved
decisions:
  - Add required --admin-email flag to namespaces create (reverses prior decision to omit initial_users)
  - Single email per create call, no multi-user support
  - No client-side email validation — WUS is source of truth
  - CLI-only change — no WUS modifications in this phase
  - Role is implicit ADMIN, baked into the flag name
  - Output unchanged — returns Namespace JSON, same as before
---

# Add required `--admin-email` to `namespaces create`

**ClickUp:** [CU-86b91f2gq](https://app.clickup.com/t/86b91f2gq)

## Problem

The Workbench User Service auto-adds the authenticated caller as ADMIN when creating a namespace. This causes two issues:

1. **Token revocation in tests:** E2E tests create a test user who creates/drops namespaces. Since the user is added as a member on creation, deleting the namespace revokes their token — breaking subsequent test operations.
2. **IaC incompatibility:** Service-level credentials used for infrastructure automation are not registered workbench users. The current flow requires the caller to be a valid workbench user, blocking automation scenarios.

## Solution

Add a required `--admin-email` flag to the CLI `namespaces create` command. This sends the email as an `initial_users` entry to the existing WUS `POST /namespaces` endpoint, which already supports the field.

This is phase 1 of a two-phase approach:
- **Phase 1 (this ticket):** CLI sends `initial_users` — WUS still auto-adds the caller as ADMIN (additive, not breaking)
- **Phase 2 (separate ticket):** WUS stops auto-adding the caller — only specified `initial_users` become members

[CONFIRMED DECISION] CLI-only change — no WUS modifications in this phase. WUS behavior (auto-adding caller) changes in Phase 2. [/CONFIRMED DECISION]

## Prior Decisions

This design **reverses** a CONFIRMED DECISION from the [2026-03-13 namespace create/update spec](2026-03-13-namespace-create-update-design.md):

> "Omit initial_users from create — use members add separately"

**Reason for reversal:** The original decision assumed the caller would always be a workbench user. The IaC/service-account use case changes that assumption — the CLI must explicitly specify who should be in the namespace.

## CLI Command

```
omics workbench namespaces create --name NAME --admin-email EMAIL [--description TEXT]
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes | Namespace name |
| `--admin-email` | Yes | Email of the user to add as ADMIN |
| `--description` | No | Namespace description (API defaults to name) |
| `--context` | No | Select configuration context |
| `--endpoint-id` | No | Select service endpoint |

[HUMAN DECISION] `--admin-email` is required, not optional with deprecation warning. Breaking change is acceptable. [/HUMAN DECISION]

[HUMAN DECISION] Single email per create call. No repeatable flag for multiple users. [/HUMAN DECISION]

[HUMAN DECISION] Flag name is `--admin-email`, baking the role into the flag name. Consistent with the existing `members add` pattern of separating email and role, but simplified since only ADMIN is supported. [/HUMAN DECISION]

[CONFIRMED DECISION] No client-side email validation. WUS validates the user exists and returns 400 if not found. [/CONFIRMED DECISION]

[CONFIRMED DECISION] Output unchanged — returns the Namespace JSON object, same as before. [/CONFIRMED DECISION]

## Client Layer

### Models

**New model:** `InitialUser`

```python
class InitialUser(BaseModel):
    email: str
    role: str
```

**Updated model:** `NamespaceCreateRequest` (add `initial_users` field)

```python
class NamespaceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    initial_users: Optional[List[InitialUser]] = None
```

### Updated method

`WorkbenchUserClient.create_namespace(name, admin_email, description=None) -> Namespace`

- Constructs `NamespaceCreateRequest` with `initial_users=[InitialUser(email=admin_email, role="ADMIN")]`
- Serializes with `exclude_none=True` (existing pattern)
- `POST /namespaces` — unchanged endpoint
- Returns `Namespace(**response.json())` — unchanged

Note: This changes the `create_namespace` signature (adds required `admin_email` parameter), which is a breaking change for any direct callers of `WorkbenchUserClient`.

## Error Handling

No new error handling. Existing patterns cover all cases:

| Scenario | Handling |
|----------|----------|
| `--admin-email` omitted | Click raises `MissingParameter` (required flag) |
| Email not a registered workbench user | WUS returns 400, surfaces as `HttpError` |
| Name blank | WUS returns 400 (existing) |
| Auth failure | Existing authenticator handles 401/403 |

## Tests

### Unit tests — CLI commands (`test_namespace_commands.py`)
- Existing create tests updated to include `--admin-email`
- New: missing `--admin-email` → non-zero exit code
- New: verify `initial_users` included in request body

### Unit tests — Models (`test_namespace_models.py`)
- `InitialUser` serialization
- `NamespaceCreateRequest` with `initial_users` serializes correctly

### E2E tests
- Existing create test updated to pass `--admin-email`
- Create namespace with admin email, verify specified admin email appears in members list (note: caller is also auto-added in Phase 1)

## Files Modified

| File | Change |
|------|--------|
| `dnastack/client/workbench/workbench_user_service/models.py` | Add `InitialUser`, update `NamespaceCreateRequest` |
| `dnastack/client/workbench/workbench_user_service/client.py` | Update `create_namespace` signature |
| `dnastack/cli/commands/workbench/namespaces/commands.py` | Add `--admin-email` ArgumentSpec |
| `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py` | Update + add create tests |
| `tests/unit/client/workbench/workbench_user_service/test_namespace_models.py` | Add model tests |