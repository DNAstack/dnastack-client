---
title: Hidden --global Flag for Workflow CLI Commands
date: 2026-03-30
repo: dnastack-client
services:
  - workflow-service
tags:
  - cli
  - admin
  - workflows
  - hidden-flag
status: approved
ticket: CU-86b948j8q
decisions:
  - "[CONFIRMED DECISION] Add hidden field to ArgumentSpec for reusable hidden option support"
  - "[CONFIRMED DECISION] Use inline admin_only_action param per client method (not session-level)"
  - "[CONFIRMED DECISION] Shared GLOBAL_ARG in workbench utils.py, not local definitions"
  - "[CONFIRMED DECISION] Apply to create, update, and delete operations across all workflow resource types"
  - "[CONFIRMED DECISION] Retroactively hide existing dependencies --global flag for consistency"
---

# Hidden `--global` Flag for Workflow CLI Commands

## Problem

The Workflow Service supports global workflows visible to all users via the
`X-Admin-Only-Action` request header. This header must be set on create, update,
and delete operations for workflows, versions, defaults, transformations, and
dependencies. Currently there is no low-friction way to set this header from the
CLI. The dependency commands already have a visible `--global` flag, but the
other workflow resource commands do not, and the flag should be hidden from
`--help` to avoid exposing admin functionality to all users.

## Design

### 1. Framework: Hidden Option Support

[CONFIRMED DECISION]
Add `hidden: bool = False` to `ArgumentSpec` (`dnastack/cli/core/command_spec.py`).
Pass `hidden=spec.hidden` into the `option_kwargs` dict in `formatted_command`
(`dnastack/cli/core/command.py`). Click natively supports hidden options — they
work normally but do not appear in `--help` output.
[/CONFIRMED DECISION]

Two lines of code across two files.

### 2. Shared GLOBAL_ARG

[CONFIRMED DECISION]
Define `GLOBAL_ARG` once in `dnastack/cli/commands/workbench/utils.py` alongside
existing shared args (`NAMESPACE_ARG`, `create_sort_arg`):

```python
GLOBAL_ARG = ArgumentSpec(
    name='global_action',
    arg_names=['--global'],
    help='Perform this action as a global admin operation',
    type=bool,
    hidden=True,
)
```

Remove the local definition from `dependencies/commands.py` and import from
`utils` instead.
[/CONFIRMED DECISION]

### 3. Client Layer

[CONFIRMED DECISION]
Add `admin_only_action: bool = False` parameter and `X-Admin-Only-Action` header
injection to each mutating `WorkflowClient` method, following the existing
dependency method pattern. For methods that already have headers (e.g.,
`If-Match`), merge the admin header into the same dict.
[/CONFIRMED DECISION]

Methods to update in `dnastack/client/workbench/workflow/client.py`:

| Method | Existing Headers |
|---|---|
| `create_workflow` | None |
| `delete_workflow` | `If-Match` |
| `update_workflow` | `If-Match` |
| `create_version` | None |
| `delete_workflow_version` | `If-Match` |
| `update_workflow_version` | `If-Match` |
| `create_workflow_defaults` | None |
| `delete_workflow_defaults` | `If-Match` |
| `update_workflow_defaults` | `If-Match` |
| `create_workflow_transformation` | None |
| `delete_workflow_transformation` | None |

### 4. CLI Commands

[CONFIRMED DECISION]
Add `GLOBAL_ARG` to the `specs` list and `global_action: bool = False` to the
function signature of each command below, passing `admin_only_action=global_action`
to the client call.
[/CONFIRMED DECISION]

**Workflows** (`cli/commands/workbench/workflows/commands.py`):
`create_workflow`, `update_workflow`, `delete_workflow`

**Versions** (`cli/commands/workbench/workflows/versions/commands.py`):
`add_version`, `update_workflow_version`, `delete_workflow_version`

**Defaults** (`cli/commands/workbench/workflows/versions/defaults.py`):
`create_workflow_defaults`, `update_workflow_defaults`, `delete_workflow_defaults`

**Transformations** (`cli/commands/workbench/workflows/versions/transformations.py`):
`add_workflow_transformation`, `delete_workflow_transformation`

**Dependencies** (`cli/commands/workbench/workflows/versions/dependencies/commands.py`):
`create`, `update`, `delete` — already wired, just switch to shared `GLOBAL_ARG`
import.

## Scope

- No new CLI commands, models, or test fixtures
- No changes to read operations (list, describe)
- Transformations have no `update` command — only create and delete