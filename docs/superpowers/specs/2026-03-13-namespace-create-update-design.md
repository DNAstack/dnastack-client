---
title: Namespace Create & Update CLI Commands
date: 2026-03-13
repo: dnastack-client
services:
  - dnastack-client
  - workbench-user-service
tags:
  - cli
  - namespaces
  - workbench
status: approved
decisions:
  - Use PATCH API (not PUT) for update to avoid silent overwrites
  - Auto-fetch ETag transparently — no --version flag exposed
  - Omit initial_users from create — use members add separately
  - Positional ID for update, consistent with defaults update pattern
  - Flag-based PATCH — build JSON Patch ops from --name/--description flags
  - Command names: create and update (matching existing CLI conventions)
---

# Namespace Create & Update CLI Commands

**ClickUp:** [CU-86b8vxxhv](https://app.clickup.com/t/86b8vxxhv)

## Goal

Add `namespaces create` and `namespaces update` commands to the dnastack-client CLI, backed by the workbench-user-service `POST /namespaces` and `PATCH /namespaces/{id}` endpoints.

## Prior Decisions

This design aligns with:
- [2026-02-20 Namespace CLI Commands Design](../../plans/2026-02-20-namespace-cli-commands-design.md) — extend `WorkbenchUserClient`, namespace endpoints are user-scoped
- [2026-02-26 Namespace Members Add/Remove Design](../../plans/2026-02-26-namespace-members-add-remove-design.md) — CLI validation patterns, error handling

## CLI Commands

### `namespaces create`

```
omics workbench namespaces create --name NAME [--description TEXT]
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes | Namespace name |
| `--description` | No | Namespace description. API defaults to the name if omitted. |
| `--context` | No | Select context |
| `--endpoint-id` | No | Select service endpoint |

- Calls `POST /namespaces` with `{"name": "...", "description": "..."}`
- Outputs created Namespace as JSON via `to_json(normalize(...))`
- Docstring includes `docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-create`

### `namespaces update`

```
omics workbench namespaces update ID [--name NAME] [--description TEXT]
```

| Arg/Flag | Type | Required | Description |
|----------|------|----------|-------------|
| `ID` | positional | Yes | Namespace ID to update |
| `--name` | option | No | New name |
| `--description` | option | No | New description |
| `--context` | option | No | Select context |
| `--endpoint-id` | option | No | Select service endpoint |

- At least one of `--name`/`--description` must be provided
- Flow: GET namespace (extract ETag) -> build JSON Patch ops -> `PATCH /namespaces/{id}` with `If-Match` and `Content-Type: application/json-patch+json`
- Outputs updated Namespace as JSON
- Docstring includes `docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-update`

## Design Decisions

### [CONFIRMED DECISION] Use PATCH API, not PUT [/CONFIRMED DECISION]

PUT requires sending all fields, which means auto-filling unchanged fields from a GET. If another user modifies a field between the GET and PUT, the stale value silently overwrites their change. PATCH only touches what the user specified, avoiding this class of bug.

### [CONFIRMED DECISION] Auto-fetch ETag transparently [/CONFIRMED DECISION]

The `update` command fetches the namespace before patching to get the current ETag for the `If-Match` header. No `--version` flag is exposed. This is consistent with how other CLI commands work — they don't expose API internals like version tokens.

### [CONFIRMED DECISION] Omit initial_users from create [/CONFIRMED DECISION]

The `POST /namespaces` endpoint supports an `initial_users` field to seed members on creation. We omit this from the CLI — users can call `members add` after creating. This keeps the command simple and avoids a compound flag format like `--initial-user email:ROLE`.

### [CONFIRMED DECISION] Positional ID for update [/CONFIRMED DECISION]

The existing `defaults update` command uses a positional ID (`default_id`). We follow that pattern for `namespaces update`.

### [CONFIRMED DECISION] Command names: create and update [/CONFIRMED DECISION]

The CLI already uses `create` (workflows, versions, defaults, dependencies, publisher collections) and `update` (defaults, dependencies) as command names. `edit` was considered but typically implies opening an editor (like `kubectl edit`). `update` maps naturally to the PATCH verb and matches existing conventions.

### [AI DECISION] Flag-based JSON Patch construction [/AI DECISION]

The client builds JSON Patch operations from non-None flags rather than accepting raw JSON Patch input. Users shouldn't need to know RFC 6902 syntax. Only two fields are mutable (`name`, `description`), so this is a complete mapping. Reuses the existing `JsonPatch` model from `dnastack/http/session.py` for consistency with `CollectionServiceClient.patch()`.

## Client Layer

### New methods on `WorkbenchUserClient`

Both new commands are registered inside `init_namespace_commands(group)` in `commands.py`, following the pattern of `list`, `describe`, `get-active`, and `set-active`.

**`create_namespace(name: str, description: Optional[str] = None) -> Namespace`**
- `POST /namespaces` with `Content-Type: application/json`
- Body: `NamespaceCreateRequest` serialized via `.dict(exclude_none=True)` (pydantic v1)
- Returns `Namespace(**response.json())`

**`update_namespace(namespace_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Namespace`**
- Uses a single `self.create_http_session()` context manager for both requests (avoids re-authentication)
- Step 1: `GET /namespaces/{id}` — extract ETag from `response.headers['ETag']`
- Step 2: Build JSON Patch ops using the existing `JsonPatch` model from `dnastack/http/session.py`:
  ```python
  patches = []
  if name is not None:
      patches.append(JsonPatch(op='replace', path='/name', value=name).dict())
  if description is not None:
      patches.append(JsonPatch(op='replace', path='/description', value=description).dict())
  ```
- Step 3: `PATCH /namespaces/{id}` with headers `If-Match: "<etag>"` and `Content-Type: application/json-patch+json`, body is the patches list
- Returns `Namespace(**response.json())`
- The client lets `ClientError` propagate on 409 — the CLI layer catches and translates it

### New model

```python
class NamespaceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
```

No new model needed for the PATCH payload — reuses `JsonPatch` from `dnastack/http/session.py`.

### Files modified

- `dnastack/client/workbench/workbench_user_service/models.py` — add `NamespaceCreateRequest`
- `dnastack/client/workbench/workbench_user_service/client.py` — add `create_namespace`, `update_namespace` methods
- `dnastack/cli/commands/workbench/namespaces/commands.py` — add `create` and `update` commands in `init_namespace_commands`
- `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py` — add test classes
- `tests/unit/client/workbench/workbench_user_service/test_namespace_models.py` — add model tests

## Error Handling

### Create
- 400 (name blank) — surfaces as `HttpError` with API message
- 401/403 — existing authenticator system handles these

### Update
- 404 (namespace not found) — raised during auto-fetch GET as `ClientError`
- 400 (name blank, name > 256 chars, invalid patch) — surfaces as `HttpError`
- 409 (version conflict) — `ClientError` propagates from the client layer; the CLI command catches it, checks `response.status_code == 409`, and raises `click.ClickException("Namespace was modified by another user. Please retry.")`
- 401/403 — existing authenticator system

### CLI validation
- `update` with neither `--name` nor `--description` -> `click.UsageError("Specify at least one of --name or --description.")`

## Tests

### Unit tests — Client models
- `NamespaceCreateRequest` serialization with and without description

### Unit tests — CLI commands
**`TestCreateCommand`:**
- Success with name only
- Success with name and description
- Output is valid JSON
- Missing `--name` -> non-zero exit code

**`TestUpdateCommand`:**
- Success with `--name` only — patch contains only name op
- Success with `--description` only — patch contains only description op
- Success with both flags
- Neither flag -> `UsageError`
- 409 Conflict -> user-friendly error message

### E2E tests
- Create namespace, verify in list
- Update name, verify via describe
- Update description only, verify name unchanged
- Update with invalid ID -> 404 `ClientError` from the GET step

## Product Documentation

Two new pages in `docs/cli/reference/workbench/`:

### `namespaces-create.md`
- Synopsis: `omics workbench namespaces create --name NAME [--description TEXT]`
- Note that caller is auto-added as ADMIN
- Examples: name only, name + description

### `namespaces-update.md`
- Synopsis: `omics workbench namespaces update ID [--name NAME] [--description TEXT]`
- Note that at least one flag is required
- Examples: update name, update description, update both

### SUMMARY.md
- Add entries for both new pages in the namespace section
