# Refactor options: blank namespace / --global for platform admins

## Problem

The workbench CLI serves two admin tiers:

- **admins** — have an account and a populated `default_namespace`; they run normal per-namespace operations.
- **platform admins** — have **no account and no namespace**; they are meant to run everything with the hidden `--global` flag.

`--global` maps to the Click param `global_action`, which each command forwards into client methods as `admin_only_action`. Today `get_workflow_client()` and its siblings **fail for platform admins**: the getter unconditionally resolves `default_namespace`, which is blank/absent for an accountless user, so the client is built with an empty namespace and the request is malformed. The flag that was designed to make platform admins work never reaches the place that decides the namespace.

## Root cause

In `dnastack/cli/commands/workbench/workflows/utils.py:47-59` (`get_workflow_client`) and the identical pattern for `get_ewes_client` (`cli/commands/workbench/utils.py:57`), `get_samples_client` (`:72`), `get_storage_client` (`:86`):

- The getter runs `if not namespace: namespace = get_user_client(...).get_user_config().default_namespace`. **It is unaware of `global_action`.** Even when the user passes `--global`, the getter still resolves `default_namespace`.
- `default_namespace` is declared a **required, non-optional `str`** on `WorkbenchUser` (`workbench_user_service/models.py:11`). For an accountless platform admin, `GET users/me` either 401/403/404s, returns a body that raises a pydantic `ValidationError` at `WorkbenchUser(**response.json())` (`workbench_user_service/client.py:84-89`), or yields an empty string. No validator, comment, or test covers the empty case.
- `WorkflowClient` builds every URL as `urljoin(self.endpoint.url, f'{self.namespace}/workflows/...')`. With `""` or `None`, the path segment is broken (`None/workflows`, or a leading-slash host reset that drops the base path).
- `admin_only_action` **only adds headers** — `_GLOBAL_NAMESPACE_HEADERS = {'X-Global-Namespace': 'true', 'X-Admin-Only-Action': 'true'}` (`dnastack/client/workbench/workflow/client.py:20`). It never changes `self.namespace` or the URL. So even in global mode the request still targets `{self.namespace}` in the path.

The consequence: what a global operation should carry in the path segment is **undocumented and never exercised** by working code.

## Blast radius (shared by all options)

| Surface | Location | Status for platform admins |
|---|---|---|
| Getter family | `get_user_client` (`utils.py:47`, no namespace param), `get_ewes_client` (`:57`), `get_samples_client` (`:72`), `get_storage_client` (`:86`), `get_workflow_client` (`workflows/utils.py:47`) | All resolve `default_namespace` → broken |
| Workflow commands **WITH** `--global` (14 mutating) | `workflows/commands.py` create(:239)/delete(:311)/update(:375); `versions/commands.py` delete(:161)/create(:239)/update(:318); `defaults.py` create(:92)/update(:354)/delete(:411); `transformations.py` delete(:151)/create(:228); `dependencies/commands.py` create(:124)/update(:290)/delete(:351) | `global_action` is in scope but not forwarded to the getter |
| Workflow commands **WITHOUT** `--global` (~12 read-side) | `workflows` list(:100)/describe(:148); `versions` list(:64)/describe(:114)/files(:385); `defaults` list(:156)/search(:222)/describe(:273); `transformations` list(:53)/describe(:100); `dependencies` list(:175)/describe(:230) | **No flag, no working path** — the gap any fix must reckon with |
| ewes/samples/storage family (~30 commands) | runs/*, engines/*, samples/*, instruments/*, storage/* — **all pass `namespace=namespace`, NONE expose `--global`** | Fully broken; clients have no `admin_only_action`/header support at all |
| `@patch` test surface | `test_samples_commands` ~11, `test_runs_commands` ~10, `test_runs_samples_commands` ~11, `namespaces/test_namespace_commands` ~16, `test_workbench_workflow_dependencies` ~12, `test_workflows_commands` ~7, `test_workbench_runs_submit` ~6, `test_hooks_commands` ~5, `test_workflow_defaults_commands` ~2, `test_workflow_label_filter` ~2, `test_workbench_workflow_versions` (constant `_GET_CLIENT`), `members/test_commands` | Patched by import path; any getter **rename** breaks these strings |
| Members helper | `namespaces/members/commands.py:45-49` `resolve_namespace()` (also `namespaces/commands.py:34`) | Own `default_namespace` fallback; separate parallel copy of the bug |

Two structural facts drive everything below:

1. **Read-only workflow commands have NO `--global` today**, and their client read methods (`list_workflows` `client.py:146`, `get_workflow` `:168`) never emit the global headers. Any fix that only threads a flag into mutating commands leaves platform admins unable to *read* anything.
2. **Calling convention varies.** `workflows/commands.py` + `versions/commands.py` pass namespace **positionally**; `defaults`/`transformations`/`dependencies`/`ewes`/`samples`/`storage` use `namespace=`. A signature change must accommodate both — which every option does by appending a trailing defaulted param.

A third fact, surfaced by the adversarial reviews and **not** in the original inventory, is decisive for correctness: **7 of the 14 mutating commands do a header-less pre-fetch READ before their write.** `delete`/`update` fetch an etag via `get_workflow`/`get_workflow_version`/`get_workflow_defaults`/`get_workflow_transformation` (`client.py:168/176/359/420`), none of which accept `admin_only_action` or send the global headers. If the server validates the path namespace on those reads, delete/update fail *before* the correctly-headered write — regardless of how the mutating call is built.

## The key open question

**What path-namespace does workflow-service expect for a global operation?** Every option states an *assumption* here; none can verify it from the repo. Concretely, the backend team must answer:

1. When `X-Global-Namespace: true` / `X-Admin-Only-Action: true` are present, does the service **ignore** the `{namespace}` path segment, **validate/authorize** it, or **attribute** the created resource to it? (Ignore → any well-formed placeholder works. Validate → a wrong sentinel 404/403s. Attribute → a global `create` could silently file the resource under a bogus owner — a 2xx data-integrity hazard.)
2. Is there a **specific reserved token** (empty, `-`, `_`, `global`, a distinct `/admin` route), or is the segment free-form?
3. Are the global headers honored on **GET/list** endpoints (needed for reads *and* for the delete/update etag pre-fetch), or only on mutations?
4. For a global list, what path shape does the server return in `next_page_url` (does pagination even start)?
5. Is an **accountless platform-admin token** authorized for header-driven global ops at all, and does it carry a usable `sub`?

The only in-repo "evidence" cuts *against* the ignore-the-path assumption: `test_workflow_client_admin_header.py:16` and every historical `--global` request use a **real** namespace in the path (`test-ns` / the caller's `default_namespace`). The header renaming happened mid-flight during an active fine-grained-RBAC reland (commit `e895fd3`, epic `86b9nzq74`) — i.e. the exact authorization layer that decides whether a sentinel path is accepted is itself in motion. **This question discriminates between all six options and must be answered before any of them can be called "fixed."**

## Backend answers (confirmed 2026-07-03) — impact on the plan

The backend team answered the five questions. The contract is now known, and it reshapes the scope:

1. **Path namespace is ignored on global ops** — any non-empty value works (`null`, `global`, `-`, …). → Validates Option 1's placeholder; **eliminates the sentinel-validation risk that sank Options 2 & 6** and the attribution/data-integrity risk. Use `"global"` for readability.
2. **The create endpoint has no segment-free form** — the segment must be present and non-empty. → **Rules out Option 5's `GLOBAL_NAMESPACE_PATH_SEGMENT=''` (omit-segment) default.** Always send a placeholder, never omit.
3. **Global headers are honored only on POST / PATCH / DELETE (no PUT for workflows).** → (a) **No global GET.** The etag pre-fetch reads that `delete`/`update` perform are *not* treated as global and will 404 for a namespace-less admin — and **Option 5's session-level header injection cannot fix this**, because the server ignores the header on GET regardless. The etag pre-fetch is a hard, server-side blocker. (b) **PUT is not honored** → `update_workflow_defaults` and `update_workflow_dependency` (both use `session.submit("PUT")`, `client.py:401/495`) won't work as global ops as written.
4. **Global list/read: not applicable** — there is **no global read capability**. → **Phase 2 (platform-admin reads + ewes/samples/storage global family) is not achievable with the current server.** Drop it from scope or escalate as a backend feature request.
5. **The platform admin is not accountless — it is namespace-less.** → `users/me` returns (no 404); the crash is purely the blank/absent `default_namespace` against the required-`str` pydantic field. → **Confirms Option 3's `Optional[str]` model fix is necessary and is the true crash point.**

### Revised, contract-aware recommendation

Primary remains **Option 1 (placeholder `"global"`) + Option 3 (model fix)**. **Option 5 deflates** — its unique advantage (session headers on GETs/pagination) buys nothing once the server ignores global headers on GET. Scope by what the server actually supports:

- **✅ Ship now — pure POST creates (Option 1 + Option 3 fully fix these):** `create_workflow`, `create_version`, `create_workflow_defaults`, `create_workflow_transformation`, `create_workflow_dependency`.
- **⚠️ Blocked by the etag pre-fetch GET (needs backend change, not client):** `delete_workflow`/`_version`, `update_workflow`/`_version`, `delete_workflow_defaults`. Ask backend to either honor global on the etag GET or accept the mutation without a client-supplied `If-Match` in global mode.
- **⚠️ Blocked by PUT not being honored:** `update_workflow_defaults`, `update_workflow_dependency` — verify with backend / convert to PATCH.
- **❌ Not server-supported — remove from scope:** global read commands (`list`/`describe`) and the entire ewes/samples/storage global family. (Supersedes "Phase 2" below.)

## Options

### Option 1: Thread `global_action` into the getters with a routing placeholder namespace

**Key idea.** Append `global_action: bool = False` (last) to `get_workflow_client` and its siblings. When set and no explicit `--namespace` was supplied, skip the `default_namespace` lookup and construct the client with a truthy sentinel path segment (`GLOBAL_NAMESPACE_PLACEHOLDER`, e.g. `"-"`). URL construction and the per-method header logic are untouched; the placeholder just keeps `urljoin` well-formed and keeps `BaseWorkbenchClient` (`base_client.py:44`) from falling into its OAuth-`sub` fallback.

**Before/after (`workflows/utils.py:47`).**
```python
# before
if not namespace:
    namespace = get_user_client(...).get_user_config().default_namespace
# after
if not namespace:
    if global_action:
        namespace = GLOBAL_NAMESPACE_PLACEHOLDER   # skip users/me
    else:
        namespace = get_user_client(...).get_user_config().default_namespace
```
Call site (14×): `get_workflow_client(context, endpoint_id, namespace, global_action=global_action)`.

**Files touched.** `workflows/utils.py`, `workbench/utils.py`, `workflow/client.py` (constant), the 5 command modules, `test_workflows_commands.py`.

**Blast radius / effort.** ~1 real getter edit + 3 parity getters + 1 constant + **14 one-line call-site edits**; ~13 read-side + ~30 ewes/samples/storage sites untouched. **Effort: M.**

**Backward compatibility.** Full. New param last, defaults False; both positional and keyword callers compile; no getter rename → zero `@patch`-string churn; no test asserts getter call-args.

**Server-contract assumption.** Header drives routing; server ignores/tolerates any non-empty placeholder in the path. `"-"` is a proposal.

**Pros.** Smallest change that unbreaks the mutating global commands; zero test-mock churn; cleanly separates the platform-admin path from the normal path; contract isolated to one constant next to the headers.

**Cons.** "Global" is split across two args (`global_action` to the getter + `admin_only_action` to the method) — easy to forward one but not the other. Only fixes mutating commands; reads and ewes/samples/storage stay broken. Does **not** address the etag pre-fetch reads. Placeholder value is a guess.

**Adversarial verdict.** 2 **sound** (regression 8, blast-radius 8), 2 **concerns** (fixes-platform-admin 3, server-contract 5); **avg 6 — the highest of all options, and no lens rated it broken.** Caveats: it is a partial fix, and the server-contract lens noted it silently swaps a real namespace for `"-"` on the one `--global` flow that arguably works today (normal admin + `--global`, no `-n`).

### Option 2: Sentinel-namespace resolution via a shared resolver

**Key idea.** Add one `GLOBAL_NAMESPACE` constant and a `resolve_workbench_namespace()` helper implementing precedence *explicit → global sentinel → default_namespace → clear error*; thread `global_action` into the getters. In global mode the resolver returns the sentinel; a blank `default_namespace` becomes a `click.UsageError`.

**Before/after.** Getter body collapses to `namespace = resolve_workbench_namespace(namespace, global_action=..., ...)`; sentinel `GLOBAL_NAMESPACE = "~global"`.

**Files touched.** `workflow/client.py`, `workbench/utils.py`, `workflows/utils.py`, 5 command modules, 2 test files.

**Blast radius / effort.** 4 getters + 14 write call sites; the design *also* lists call-arg test edits at those sites. **Effort: M** (but see below).

**Backward compatibility.** Yes (trailing defaulted param).

**Server-contract assumption.** Header-driven; path cosmetic, only needs to be non-empty and URL-safe.

**Pros.** URL/methods unchanged; single constant + resolver; adds a clear forgot-flag error; skips the failing `users/me` for platform admins.

**Cons.** Sentinel is fabricated; `"~"` may fail server namespace-format validation *before* the header is read; the collision-mitigation ("pick a value invalid as a namespace") works *against* passing that validation. Read-side + ewes/samples/storage still broken.

**Adversarial verdict.** 1 **broken** (fixes-platform-admin 3), 3 **concerns** (regression 7, server-contract 5, blast-radius 3); **avg 4.5.** The blast-radius lens found the design both **under-scopes** (misses the etag pre-fetch reads → delete/update still 403/404) and **over-states** test churn (no test asserts getter call-args; several cited test files exercise only read commands it doesn't touch), so the effort estimate is untrustworthy in both directions.

### Option 3: Optional-namespace model with global-aware, blank-tolerant getters

**Key idea.** Two layers. (1) Fix the model: `default_namespace: Optional[str] = None` so `get_user_config()` no longer raises a `ValidationError` on null/absent. (2) Add `global_action` to the getters; tolerate a blank result — if still blank and not global, raise a `click.UsageError`; if blank and global, pass `namespace=None` and let `BaseWorkbenchClient`'s `sub`-claim fallback (`base_client.py:44-61`) supply a non-empty segment.

**Files touched.** `workbench_user_service/models.py`, both getter modules, 5 command modules, `namespaces/members/commands.py`, `namespaces/commands.py`, 2 test files.

**Blast radius / effort.** 14 write call sites + model widening (6 attribute readers) + members/namespaces helpers. **Effort: M.**

**Backward compatibility.** Yes, with one behavior delta: a genuinely-missing `default_namespace` for a normal admin no longer errors loudly at deserialization but surfaces later as `None`/`UsageError`.

**Server-contract assumption.** Header-driven; global segment supplied by the `sub`-claim fallback.

**Pros.** Fixes the genuine pydantic model bug at source; clear error for every blank-namespace case across all ~40 commands; no URL/header change.

**Cons.** Leans on the non-obvious `sub`-claim fallback (needs a routable `sub` an accountless admin may lack, and `sub` may contain `/` and misroute). Global write still runs a `users/me` lookup (email stays required). Does not enable reads or ewes/samples/storage.

**Adversarial verdict.** 1 **broken** (server-contract 3), 2 **concerns** (fixes-platform-admin 3, regression 7), 1 **sound** (blast-radius 8); **avg 5.3.** Server-contract lens: the etag pre-fetch reads still hit `{sub}/workflows/{id}` with no headers → delete/update fail before the write; only pure creates can succeed.

### Option 4: Central namespace resolver (single source of truth)

**Key idea.** One `resolve_namespace(...)` owning precedence *explicit → sentinel → default → error*; getters become thin wrappers over it plus a deduped `_build` helper; the members helper delegates to the same resolver. Sentinel value is TBD (server-contract open question).

**Files touched.** `workbench/utils.py`, `workflows/utils.py`, `members/commands.py`, 5 command modules, `members/test_commands.py`.

**Blast radius / effort.** 14 write call sites + resolver/getters/members. **Effort: M.**

**Backward compatibility.** Yes for happy paths; but the new pre-factory `UsageError` **preempts** the existing `BaseWorkbenchClient` `sub`-claim fallback for the blank-`default_namespace` non-global case, and a broad `except (ValidationError, HttpError, NamespaceError)` can mask genuine 5xx/auth failures on `users/me` behind a misleading "pass `--global`" message.

**Server-contract assumption.** Header-driven; sentinel non-empty; value TBD.

**Pros.** True single source of truth for precedence; getters shrink; removes 4× copy-paste; actionable error; naturally extensible.

**Cons.** Sentinel is a guess; contract argument is a stated non-sequitur; etag pre-fetch reads unaddressed; unifying members subtly changes blank-passthrough semantics.

**Adversarial verdict.** 1 **broken** (fixes-platform-admin 3), 3 **concerns** (regression 6, server-contract 4, blast-radius 7); **avg 5.0.** Blast-radius lens found a concrete self-contradiction: the write-side create getter is cited at `:100`, which is actually the read-side `list` getter (real create is `:239`) — following the map literally injects a `NameError` and leaves `create --global` unfixed.

### Option 5: Client-layer global awareness (namespace-optional `BaseWorkbenchClient`)

**Key idea.** Make "global mode" a construction-time property of every workbench client. `BaseWorkbenchClient` gains `global_action`; when set, `namespace=None` is legitimate (skip both `default_namespace` and `sub` resolution), a centralized `_resolve_url()` supplies the segment via one `GLOBAL_NAMESPACE_PATH_SEGMENT` knob, and `create_http_session` injects the global headers onto **every** request the client makes — reads, paginated loaders, and the intermediate etag GETs alike. Getters just forward `global_action` into `make()`.

**Before/after.** `urljoin(self.endpoint.url, f'{self.namespace}/workflows/{id}')` → `self._resolve_url(f'workflows/{id}')`; `create_http_session` calls `session.add_default_headers(GLOBAL_NAMESPACE_HEADERS)` when global.

**Files touched.** `base_client.py`, `workflow/client.py`, both getter modules, `http/session.py`, `client/base_client.py`, **ewes/samples/storage client.py**, 5 command modules. ~60 `f'{self.namespace}/...'` sites refactored across 4 clients.

**Blast radius / effort.** 4 getter defs + 4 `make()` signatures + 14 write call sites + ~60 URL edits + `HttpSession`. **Effort: L.**

**Backward compatibility.** Yes for `global_action=False`; but forcing `make()`/`__init__` changes across three currently-working sibling clients in lockstep, and a mechanical ~60-site URL refactor the mock-heavy suite would not catch if botched, widen the exposure to ~30 well-used runs/engines/instruments/samples/storage commands.

**Server-contract assumption.** Header-driven; **default `GLOBAL_NAMESPACE_PATH_SEGMENT=''` (omit the segment)** — which the server-contract lens flags as the routing-*riskiest* default (a `/{namespace}/...`-only route won't match `/workflows`).

**Pros.** The **only** design that solves the etag pre-fetch read problem (session-level headers cover the GETs) and enables reads the moment a read command forwards the flag. Fixes the root cause centrally; `namespace=None` becomes first-class; extends to ewes/samples/storage "for free" once a command adds the flag; single greppable contract knob.

**Cons.** Broadest surface; keeps `admin_only_action` as redundant cruft; the omit-segment default silently changes the wire format for the one working `--global` flow (normal admin, no `-n`); immediate user-visible win is still only the workflow write family until read commands adopt the flag.

**Adversarial verdict.** 0 **broken**, 4 **concerns** (fixes-platform-admin **5 — the highest any option scored on that lens**, regression 7, server-contract 4, blast-radius 7); **avg 5.8.** Uniquely credited for solving the etag reads and enabling reads; penalized for blast radius and for defaulting to the segment-omission most likely to 404.

### Option 6: Global-aware resolution with an isolated server-contract sentinel ("open-best")

**Key idea.** Same shape as Options 2/4 — `global_action` into getters, shared `_resolve_namespace()`, sentinel `GLOBAL_NAMESPACE = '_'` co-located with the headers, blank-namespace `UsageError`. Positioned as the minimal change that unbreaks every command already carrying `--global`.

**Files touched.** Both getter modules, `workflow/client.py`, 5 command modules, 4 test files.

**Blast radius / effort.** Claims "15" write sites (actually 14). **Effort: M.**

**Backward compatibility.** Yes; same `sub`-claim-fallback-preemption and sentinel-swap deltas as the other resolver designs.

**Server-contract assumption.** Header-driven; `'_'` placeholder; contract confined to one constant.

**Pros.** Smallest resolver-based change; backward compatible; contract in one place; removes duplication; actionable error.

**Cons.** Same etag pre-fetch gap (delete/update break); sentinel unverified; reads + ewes/samples/storage unfixed.

**Adversarial verdict.** 2 **broken** (fixes-platform-admin 3, server-contract 3), 2 **concerns** (regression 6, blast-radius 6); **avg 4.5.** Blast-radius lens found concrete inventory errors: an off-by-one count, a write-site line ref (`:385`) that is actually the read-side `files` command while the real `update` site (`:318`) is omitted, and **two non-existent test paths** in `filesTouched`. Following the map verbatim injects a `NameError` and leaves `update --global` broken.

## Comparison

| Option | Effort | Blast radius | Backward compat | Server-contract risk | Avg verdict score |
|---|---|---|---|---|---|
| 1 — getter placeholder param | M | Small (getters + 14 sites) | High (no rename, no churn) | High; unaddressed etag reads | **6.0** |
| 2 — sentinel resolver | M | Medium | High | High; `~` may fail path validation | 4.5 |
| 3 — optional-namespace model | M | Small–Med (+ model) | High (deferred error surface) | High (broken); etag reads still fail | 5.3 |
| 4 — central resolver | M | Medium | Medium (preempts `sub` fallback) | High; sentinel TBD | 5.0 |
| 5 — client-layer global | **L** | Large (4 clients + session) | Med (lockstep sibling changes) | High; **solves etag reads**, but omit-segment default riskiest | 5.8 |
| 6 — isolated sentinel | M | Small | Medium | High (broken); etag reads fail | 4.5 |

Two things are true of **every** row: none is rated above 5 on the dedicated *fixes-platform-admin* lens, and all six leave read-side workflow commands and the ~30 ewes/samples/storage commands broken for platform admins. **No design, as scoped, fully fixes the platform admin.**

## Recommendation

**Adopt a phased plan built on Option 1's getter shape, with Option 3's model fix folded in, and Option 5's session-level header injection reserved for whichever step the backend contract forces it into. Do not merge any of it until the backend contract is confirmed.**

Rationale against the verdicts:

- **Option 1 is the best *tactical* first move.** It carries the highest average (6.0), is the only design rated *sound* on **both** regression (8) and blast-radius (8), has zero `@patch` churn (no getter rename, no test asserts getter args), and is honestly scoped. Its low score on *fixes-platform-admin* (3) reflects scope, not defect — the mechanism is correct where it acts.
- **Fold in Option 3's model correctness fix** (`default_namespace: Optional[str] = None`) plus a clear `click.UsageError` for the blank-namespace/forgot-flag case. This eliminates the latent pydantic crash that otherwise fires *before* any nicer error, and it's cheap. Take the narrower exception handling the reviews demanded: catch only the account-missing case, and do **not** preempt the `BaseWorkbenchClient` `sub`-claim fallback the way Options 4/6 do.
- **Option 5's core insight is not optional — it is the tiebreaker on correctness.** It is the *only* design that solves the etag pre-fetch read problem (session-level headers on the intermediate GETs) and the only path to enabling reads and ewes/samples/storage. If the backend says the pre-fetch reads need the global headers, then Option 1 alone does **not** fix delete/update (only create-style ops), and we must adopt Option 5's `create_http_session` header injection. Reserve Option 5's riskier pieces — the ~60-site URL refactor across four clients and the `GLOBAL_NAMESPACE_PATH_SEGMENT=''` default — for when they're actually needed, and never default to omit-segment; use a confirmed placeholder.
- **Reject Options 2, 4, 6 as primaries.** They add a shared resolver (nice) but each carries a concrete defect the reviews caught (inventory errors that mislead the implementer, `sub`-fallback preemption, or sentinel values likely to fail server-side validation) without buying anything Option 1 + the Option 3 model fix doesn't already give more safely. The shared-resolver *refactor* is worth doing later for de-duplication, but it is not the fix.

### What must be confirmed with the backend team before implementation

This is blocking. Answers select the architecture and the sentinel value:

1. When the global headers are present, does workflow-service **ignore / validate / attribute** the `{namespace}` path segment? (Attribution on `create` is a silent data-integrity risk — get this in writing.)
2. What is the **exact** token for a global op — free-form placeholder, a reserved literal, or omitted segment? (Sets Option 1's `GLOBAL_NAMESPACE_PLACEHOLDER` / Option 5's `GLOBAL_NAMESPACE_PATH_SEGMENT`. Do not ship a guess.)
3. Are the headers honored on **GET/list** endpoints, including the etag pre-fetch reads used by delete/update? **If yes → the etag reads need headers → adopt Option 5's session-level injection now.** If the server resolves those reads by ID regardless of path, Option 1 alone suffices for writes.
4. What path does a global list return in `next_page_url`? (Does pagination start?)
5. Is an accountless platform-admin token authorized for header-driven global ops, and does it carry a usable `sub`?

## Suggested implementation order & testing

**Phase 0 — Confirm the contract (blocking).** Get written answers to the five questions above. Capture a real `--global` request trace against a running workflow-service. Nothing merges until the sentinel value and the read-header behavior are known.

**Phase 1 — Model correctness + mutating workflow writes (Option 1 + Option 3 model fix).**
1. `default_namespace: Optional[str] = None` in `workbench_user_service/models.py:11`.
2. Add `global_action: bool = False` (last) to `get_workflow_client` and the three siblings; skip the `users/me` lookup when global; add a narrow `click.UsageError` for blank-and-not-global. Set `GLOBAL_NAMESPACE_PLACEHOLDER` to the confirmed value in `workflow/client.py` next to `_GLOBAL_NAMESPACE_HEADERS`.
3. Forward `global_action=global_action` at the **14** mutating call sites (verify each line against the source — the reviews caught bogus line refs in Options 4 and 6; do not trust `:100`/`:385` as write sites).
4. **If Phase 0 says pre-fetch reads need headers:** pull in Option 5's `create_http_session`/`add_default_headers` injection so delete/update actually work; otherwise leave URL/method logic untouched.

**Phase 2 — Enable platform-admin reads and the ewes/samples/storage family.** Add `GLOBAL_ARG` to the ~12 read-side workflow commands and, using the client-layer model, extend `--global` to the ~30 ewes/samples/storage commands. This is where the shared-resolver de-duplication (Options 2/4/6) and the client-layer architecture (Option 5) earn their keep. Treat this as committed work, not "someday follow-on" — per the *fixes-platform-admin* lens, without it the platform admin still cannot do their job.

**Tests to add.**
- **Model (currently missing empty-namespace case):** `default_namespace` null *and* absent both deserialize to `None` with no `ValidationError`; an explicit value still round-trips.
- **Getter:** `global_action=True` **does not** call `get_user_client`/`get_user_config` (`assert_not_called`) and builds the client with the placeholder; `global_action=False` still resolves `default_namespace`; blank + non-global raises `click.UsageError`.
- **Client (contract-shape):** in global mode the built URL contains the confirmed segment and the request carries `X-Global-Namespace`/`X-Admin-Only-Action`; if session-level injection is adopted, assert the **etag pre-fetch GET and pagination loaders also carry the headers** — this is the case a per-method approach cannot cover.
- **Regression:** run the getter-`@patch` suites (`test_workflows_commands`, `test_workbench_workflow_dependencies`, `test_workflow_defaults_commands`, `test_workflow_label_filter`, `test_workbench_workflow_versions`) unchanged to confirm no signature/patch breakage. Do **not** mass-edit call-arg assertions — verified across the reviews that no test asserts getter call-args, so most of the "test churn" the other designs list is spurious.
- **E2E (gated, before merge):** a platform-admin `workflows create --global` **and** a `delete`/`update --global` against a real/staged workflow-service — the only way to validate the contract assumption and the etag-read behavior.

Run `make lint && make test-unit` before commit.
