# Namespace Create & Update CLI Commands Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `namespaces create` and `namespaces update` commands to the dnastack-client CLI.

**Architecture:** Two new client methods on `WorkbenchUserClient` backed by `POST /namespaces` and `PATCH /namespaces/{id}`. Two new CLI commands registered in `init_namespace_commands`. Uses existing `JsonPatch` model and `session.json_patch()` for the update flow. Product docs for both commands.

**Tech Stack:** Python, Click, Pydantic v2, requests

**Spec:** `docs/superpowers/specs/2026-03-13-namespace-create-update-design.md`

**ClickUp:** [CU-86b8vxxhv](https://app.clickup.com/t/86b8vxxhv)

**Pyenv:** Run `eval "$(pyenv init -)" && pyenv activate dnastack-client` before any Python/make/commit command.

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `dnastack/client/workbench/workbench_user_service/models.py` | Add `NamespaceCreateRequest` model |
| Modify | `dnastack/client/workbench/workbench_user_service/client.py` | Add `create_namespace`, `update_namespace` methods |
| Modify | `dnastack/cli/commands/workbench/namespaces/commands.py` | Add `create` and `update` CLI commands |
| Modify | `tests/unit/client/workbench/workbench_user_service/test_namespace_models.py` | Add model serialization tests |
| Modify | `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py` | Add CLI command tests |
| Create | `@dnastack-product-docs/docs/cli/reference/workbench/namespaces-create.md` | Create command reference doc |
| Create | `@dnastack-product-docs/docs/cli/reference/workbench/namespaces-update.md` | Update command reference doc |
| Modify | `@dnastack-product-docs/docs/SUMMARY.md` | Add sidebar entries for new docs |

`@dnastack-product-docs` = `/Users/patrickmagee/development/dnastack/dnastack-product-docs`

---

## Chunk 1: Model and Client Layer

### Task 1: Add NamespaceCreateRequest model

**Files:**
- Modify: `dnastack/client/workbench/workbench_user_service/models.py`
- Modify: `tests/unit/client/workbench/workbench_user_service/test_namespace_models.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/client/workbench/workbench_user_service/test_namespace_models.py`:

```python
from dnastack.client.workbench.workbench_user_service.models import (
    # ... existing imports ...
    NamespaceCreateRequest,
)


class TestNamespaceCreateRequestSerialization:
    """Test suite for NamespaceCreateRequest model."""

    def test_serializes_with_name_and_description(self):
        req = NamespaceCreateRequest(name="My Namespace", description="A test namespace")
        data = req.dict(exclude_none=True)
        assert data == {"name": "My Namespace", "description": "A test namespace"}

    def test_serializes_with_name_only(self):
        req = NamespaceCreateRequest(name="My Namespace")
        data = req.dict(exclude_none=True)
        assert data == {"name": "My Namespace"}
        assert "description" not in data

    def test_serializes_with_explicit_none_description(self):
        req = NamespaceCreateRequest(name="My Namespace", description=None)
        data = req.dict(exclude_none=True)
        assert data == {"name": "My Namespace"}
        assert "description" not in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/client/workbench/workbench_user_service/test_namespace_models.py::TestNamespaceCreateRequestSerialization -v`

Expected: FAIL with `ImportError: cannot import name 'NamespaceCreateRequest'`

- [ ] **Step 3: Add the NamespaceCreateRequest model**

Add to `dnastack/client/workbench/workbench_user_service/models.py`, after the `AddMemberRequest` class:

```python
class NamespaceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/client/workbench/workbench_user_service/test_namespace_models.py::TestNamespaceCreateRequestSerialization -v`

Expected: 3 PASSED

- [ ] **Step 5: Run full model test suite to verify no regressions**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/client/workbench/workbench_user_service/test_namespace_models.py -v`

Expected: All existing tests still PASS

- [ ] **Step 6: Commit**

```bash
eval "$(pyenv init -)" && pyenv activate dnastack-client
git add dnastack/client/workbench/workbench_user_service/models.py tests/unit/client/workbench/workbench_user_service/test_namespace_models.py
git commit -m "[CU-86b8vxxhv] Add NamespaceCreateRequest model with tests"
```

---

### Task 2: Add create_namespace client method

**Files:**
- Modify: `dnastack/client/workbench/workbench_user_service/client.py`
- Modify: `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py`. First update the imports at the top of the file:

```python
import json
from unittest.mock import Mock, patch
from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.workbench.namespaces.commands import init_namespace_commands
from dnastack.client.workbench.workbench_user_service.models import Namespace
```

Then add the test class:

```python
class TestCreateCommand:
    """Tests for the create namespace CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_namespace_commands(self.group)

        self.mock_namespace = Namespace(
            id="ns-new-123",
            name="New Namespace",
            description="A brand new namespace",
            created_at="2026-03-13T00:00:00Z",
            created_by="user@example.com",
            updated_at="2026-03-13T00:00:00Z",
            updated_by="user@example.com",
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_with_name_only(self, mock_get_client):
        mock_client = Mock()
        mock_client.create_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['create', '--name', 'New Namespace'])

        assert result.exit_code == 0
        mock_client.create_namespace.assert_called_once_with(name="New Namespace", description=None)
        output = json.loads(result.output)
        assert output["id"] == "ns-new-123"
        assert output["name"] == "New Namespace"

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_with_name_and_description(self, mock_get_client):
        mock_client = Mock()
        mock_client.create_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['create', '--name', 'New Namespace', '--description', 'A brand new namespace'])

        assert result.exit_code == 0
        mock_client.create_namespace.assert_called_once_with(name="New Namespace", description="A brand new namespace")

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_requires_name(self, mock_get_client):
        result = self.runner.invoke(self.group, ['create'])

        assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py::TestCreateCommand -v`

Expected: FAIL (no 'create' command registered)

- [ ] **Step 3: Add create_namespace client method**

Add to `dnastack/client/workbench/workbench_user_service/client.py`.

First update the imports at the top:

```python
from dnastack.client.workbench.workbench_user_service.models import (
    WorkbenchUser,
    Namespace,
    NamespaceListResponse,
    NamespaceMember,
    NamespaceMemberListResponse,
    AddMemberRequest,
    NamespaceCreateRequest,
)
```

Then add the method to `WorkbenchUserClient`, after the `set_active_namespace` method:

```python
    def create_namespace(self, name: str, description: Optional[str] = None) -> Namespace:
        """Create a new namespace."""
        body = NamespaceCreateRequest(name=name, description=description)
        with self.create_http_session() as session:
            response = session.post(
                urljoin(self.endpoint.url, 'namespaces'),
                json=body.dict(exclude_none=True),
            )
        return Namespace(**response.json())
```

- [ ] **Step 4: Add the create CLI command**

Add to `dnastack/cli/commands/workbench/namespaces/commands.py`, inside `init_namespace_commands`, after the `set_active_namespace` command:

```python
    @formatted_command(
        group=group,
        name='create',
        specs=[
            ArgumentSpec(
                name='name',
                arg_names=['--name'],
                help='The name of the namespace to create.',
                required=True,
            ),
            ArgumentSpec(
                name='description',
                arg_names=['--description'],
                help='A description for the namespace. Defaults to the namespace name if omitted.',
                required=False,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def create_namespace(context: Optional[str],
                         endpoint_id: Optional[str],
                         name: str,
                         description: Optional[str]):
        """
        Create a new namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-create
        """

        client = get_user_client(context, endpoint_id)
        namespace = client.create_namespace(name=name, description=description)
        click.echo(to_json(normalize(namespace)))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py::TestCreateCommand -v`

Expected: 3 PASSED

- [ ] **Step 6: Run full CLI test suite to verify no regressions**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/ -v`

Expected: All existing tests still PASS

- [ ] **Step 7: Commit**

```bash
eval "$(pyenv init -)" && pyenv activate dnastack-client
git add dnastack/client/workbench/workbench_user_service/client.py dnastack/cli/commands/workbench/namespaces/commands.py tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py
git commit -m "[CU-86b8vxxhv] Add namespaces create command and client method"
```

---

### Task 3: Add update_namespace client method and CLI command

**Files:**
- Modify: `dnastack/client/workbench/workbench_user_service/client.py`
- Modify: `dnastack/cli/commands/workbench/namespaces/commands.py`
- Modify: `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py`:

```python
from dnastack.http.session import ClientError


class TestUpdateCommand:
    """Tests for the update namespace CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_namespace_commands(self.group)

        self.mock_namespace = Namespace(
            id="ns-existing-456",
            name="Updated Namespace",
            description="Updated description",
            created_at="2026-03-13T00:00:00Z",
            created_by="user@example.com",
            updated_at="2026-03-13T12:00:00Z",
            updated_by="user@example.com",
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_name_only(self, mock_get_client):
        mock_client = Mock()
        mock_client.update_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['update', 'ns-existing-456', '--name', 'Updated Namespace'])

        assert result.exit_code == 0
        mock_client.update_namespace.assert_called_once_with(
            namespace_id="ns-existing-456", name="Updated Namespace", description=None
        )
        output = json.loads(result.output)
        assert output["id"] == "ns-existing-456"
        assert output["name"] == "Updated Namespace"

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_description_only(self, mock_get_client):
        mock_client = Mock()
        mock_client.update_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['update', 'ns-existing-456', '--description', 'Updated description'])

        assert result.exit_code == 0
        mock_client.update_namespace.assert_called_once_with(
            namespace_id="ns-existing-456", name=None, description="Updated description"
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_both_name_and_description(self, mock_get_client):
        mock_client = Mock()
        mock_client.update_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['update', 'ns-existing-456', '--name', 'Updated Namespace', '--description', 'Updated description'])

        assert result.exit_code == 0
        mock_client.update_namespace.assert_called_once_with(
            namespace_id="ns-existing-456", name="Updated Namespace", description="Updated description"
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_requires_at_least_one_flag(self, mock_get_client):
        result = self.runner.invoke(self.group, ['update', 'ns-existing-456'])

        assert result.exit_code != 0
        assert "at least one" in result.output.lower()

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_requires_namespace_id(self, mock_get_client):
        result = self.runner.invoke(self.group, ['update', '--name', 'Test'])

        assert result.exit_code != 0

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_update_handles_409_conflict(self, mock_get_client):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.text = "Conflict"
        mock_client.update_namespace.side_effect = ClientError(mock_response)
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['update', 'ns-existing-456', '--name', 'Conflict Test'])

        assert result.exit_code != 0
        assert "modified by another user" in result.output.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py::TestUpdateCommand -v`

Expected: FAIL (no 'update' command registered)

- [ ] **Step 3: Add update_namespace client method**

Add to `dnastack/client/workbench/workbench_user_service/client.py`. First update the import at the top:

```python
from dnastack.http.session import HttpSession, JsonPatch
```

Then add the method to `WorkbenchUserClient`, after the `create_namespace` method:

```python
    def update_namespace(self,
                         namespace_id: str,
                         name: Optional[str] = None,
                         description: Optional[str] = None) -> Namespace:
        """Update a namespace using JSON Patch. Auto-fetches ETag for optimistic locking."""
        patches = []
        if name is not None:
            patches.append(JsonPatch(op='replace', path='/name', value=name).dict())
        if description is not None:
            patches.append(JsonPatch(op='replace', path='/description', value=description).dict())

        with self.create_http_session() as session:
            get_response = session.get(
                urljoin(self.endpoint.url, f'namespaces/{namespace_id}')
            )
            etag = (get_response.headers.get('etag') or '').strip('"')

            patch_response = session.json_patch(
                urljoin(self.endpoint.url, f'namespaces/{namespace_id}'),
                headers={'If-Match': etag},
                json=patches,
            )
        return Namespace(**patch_response.json())
```

- [ ] **Step 4: Add the update CLI command**

Add to `dnastack/cli/commands/workbench/namespaces/commands.py`. First add the import at the top:

```python
from dnastack.http.session import ClientError
```

Then add inside `init_namespace_commands`, after the `create_namespace` command:

```python
    @formatted_command(
        group=group,
        name='update',
        specs=[
            ArgumentSpec(
                name='namespace_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The namespace ID to update.',
                required=True,
            ),
            ArgumentSpec(
                name='name',
                arg_names=['--name'],
                help='The new name for the namespace.',
                required=False,
            ),
            ArgumentSpec(
                name='description',
                arg_names=['--description'],
                help='The new description for the namespace.',
                required=False,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def update_namespace(context: Optional[str],
                         endpoint_id: Optional[str],
                         namespace_id: str,
                         name: Optional[str],
                         description: Optional[str]):
        """
        Update an existing namespace

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/namespaces-update
        """

        if name is None and description is None:
            raise click.UsageError("Specify at least one of --name or --description.")

        client = get_user_client(context, endpoint_id)
        try:
            namespace = client.update_namespace(namespace_id=namespace_id, name=name, description=description)
        except ClientError as e:
            if e.response.status_code == 409:
                raise click.ClickException("Namespace was modified by another user. Please retry.")
            raise
        click.echo(to_json(normalize(namespace)))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py::TestUpdateCommand -v`

Expected: 6 PASSED

- [ ] **Step 6: Run full test suite to verify no regressions**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && uv run pytest tests/unit/cli/commands/workbench/namespaces/ tests/unit/client/workbench/workbench_user_service/ -v`

Expected: All tests PASS

- [ ] **Step 7: Lint**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && make lint`

Expected: No violations

- [ ] **Step 8: Commit**

```bash
eval "$(pyenv init -)" && pyenv activate dnastack-client
git add dnastack/client/workbench/workbench_user_service/client.py dnastack/cli/commands/workbench/namespaces/commands.py tests/unit/cli/commands/workbench/namespaces/test_namespace_commands.py
git commit -m "[CU-86b8vxxhv] Add namespaces update command with JSON Patch and conflict handling"
```

---

## Chunk 2: Product Documentation

### Task 4: Add namespaces-create.md product doc

**Files:**
- Create: `/Users/patrickmagee/development/dnastack/dnastack-product-docs/docs/cli/reference/workbench/namespaces-create.md`

- [ ] **Step 1: Create the doc file**

```markdown
---
description: Create a new namespace
---

# namespaces create

## Synopsis

```shell
omics workbench namespaces create
  --name NAME
  [--description TEXT]
```

## Description

Create a new namespace. The authenticated user is automatically added as an ADMIN of the new namespace.

If no description is provided, the API defaults the description to the namespace name.

## Examples

### Create a namespace

```shell
omics workbench namespaces create --name "My Research Lab"
```

### Create a namespace with a description

```shell
omics workbench namespaces create \
  --name "My Research Lab" \
  --description "Shared workspace for genomics research"
```

## Flags:

### `--name`=`NAME`

**Required.** The name of the namespace to create.

### `--description`=`TEXT`

A description for the namespace. If omitted, defaults to the namespace name.
```

- [ ] **Step 2: Verify file exists and is well-formed**

Run: `head -5 /Users/patrickmagee/development/dnastack/dnastack-product-docs/docs/cli/reference/workbench/namespaces-create.md`

Expected: YAML frontmatter with `description: Create a new namespace`

---

### Task 5: Add namespaces-update.md product doc

**Files:**
- Create: `/Users/patrickmagee/development/dnastack/dnastack-product-docs/docs/cli/reference/workbench/namespaces-update.md`

- [ ] **Step 1: Create the doc file**

```markdown
---
description: Update an existing namespace
---

# namespaces update

## Synopsis

```shell
omics workbench namespaces update ID
  [--name NAME]
  [--description TEXT]
```

## Description

Update the name or description of an existing namespace. At least one of `--name` or `--description` must be provided.

The command uses optimistic locking to prevent conflicting updates. If the namespace was modified by another user between when it was read and when the update is applied, the command returns an error and the update must be retried.

## Examples

### Update a namespace name

```shell
omics workbench namespaces update bcd869ca-8a06-4426-a94d-43f9d91e937d \
  --name "Renamed Lab"
```

### Update a namespace description

```shell
omics workbench namespaces update bcd869ca-8a06-4426-a94d-43f9d91e937d \
  --description "Updated workspace description"
```

### Update both name and description

```shell
omics workbench namespaces update bcd869ca-8a06-4426-a94d-43f9d91e937d \
  --name "Renamed Lab" \
  --description "Updated workspace description"
```

## Positional Arguments:

### `ID`

**Required.** The ID of the namespace to update. The namespace ID can be retrieved from the [namespaces list](namespaces-list.md) command.

## Flags:

### `--name`=`NAME`

The new name for the namespace.

### `--description`=`TEXT`

The new description for the namespace.
```

- [ ] **Step 2: Verify file exists and is well-formed**

Run: `head -5 /Users/patrickmagee/development/dnastack/dnastack-product-docs/docs/cli/reference/workbench/namespaces-update.md`

Expected: YAML frontmatter with `description: Update an existing namespace`

---

### Task 6: Add SUMMARY.md entries

**Files:**
- Modify: `/Users/patrickmagee/development/dnastack/dnastack-product-docs/docs/SUMMARY.md`

- [ ] **Step 1: Add entries after the existing namespace commands block**

Insert the following two lines after the `* [namespaces describe]` entry (line 151) and before the `* [namespaces members list]` entry (line 152):

```
    * [namespaces create](cli/reference/workbench/namespaces-create.md)
    * [namespaces update](cli/reference/workbench/namespaces-update.md)
```

The namespace section should then read:

```
    * [namespaces get-active](cli/reference/workbench/namespaces-get-active.md)
    * [namespaces set-active](cli/reference/workbench/namespaces-set-active.md)
    * [namespaces get-default](cli/reference/workbench/namespaces-get-default.md)
    * [namespaces list](cli/reference/workbench/namespaces-list.md)
    * [namespaces describe](cli/reference/workbench/namespaces-describe.md)
    * [namespaces create](cli/reference/workbench/namespaces-create.md)
    * [namespaces update](cli/reference/workbench/namespaces-update.md)
    * [namespaces members list](cli/reference/workbench/namespaces-members-list.md)
    * [namespaces members add](cli/reference/workbench/namespaces-members-add.md)
    * [namespaces members remove](cli/reference/workbench/namespaces-members-remove.md)
```

- [ ] **Step 2: Commit product docs changes**

Note: This commit is in the `dnastack-product-docs` repo, not `dnastack-client`. Create a branch there too.

```bash
cd /Users/patrickmagee/development/dnastack/dnastack-product-docs
git checkout -b add_namespace_create_update_docs-CU-86b8vxxhv
git add docs/cli/reference/workbench/namespaces-create.md docs/cli/reference/workbench/namespaces-update.md docs/SUMMARY.md
git commit -m "[CU-86b8vxxhv] Add namespace create and update CLI reference docs"
cd /Users/patrickmagee/development/dnastack/dnastack-client
```

---

## Chunk 3: Final Verification

### Task 7: Full verification pass

- [ ] **Step 1: Run linter**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && make lint`

Expected: No violations

- [ ] **Step 2: Run full unit test suite**

Run: `eval "$(pyenv init -)" && pyenv activate dnastack-client && make test-unit`

Expected: All tests PASS

- [ ] **Step 3: Verify git log**

Run: `git log --oneline add_namespace_create_update_commands-CU-86b8vxxhv --not main`

Expected: Commits for design spec, CLAUDE.md update, model, create command, update command

- [ ] **Step 4: Review checklist**

Verify:
- [ ] `NamespaceCreateRequest` model exists with tests
- [ ] `create_namespace` client method exists
- [ ] `update_namespace` client method exists with JsonPatch and ETag handling
- [ ] `create` CLI command registered in `init_namespace_commands` with docs URL in docstring
- [ ] `update` CLI command registered with positional ID, --name, --description, 409 handling, docs URL in docstring
- [ ] CLI validation: update with no flags raises UsageError
- [ ] Unit tests for both create and update commands
- [ ] Product docs created for both commands with correct format
- [ ] SUMMARY.md updated
- [ ] All commits have `[CU-86b8vxxhv]` prefix
- [ ] No regressions in existing namespace commands
