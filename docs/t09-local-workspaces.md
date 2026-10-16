# T-09 — Guarded local Git connections and snapshot refresh

This is the **trusted-local CLI** portion of milestone C. It is not a public
GitHub importer or a workspace-writing agent. Browser mutations/import controls,
mixed-language inventory and in-place incremental sync remain pending.

## What is implemented

- Local repository roots must be explicitly allowlisted in the CLI process.
  Without configuration, new connections are disabled.
- Select an existing local branch and confirm its full SHA-1 commit. HEAD must be
  attached to that branch, at that revision, and the working tree must be clean.
- Preflight tracked Python regular-file paths, sizes and count before graph
  creation. Submodules, linked worktrees and Python symlinks are refused in this
  slice. No repository source, test, hook or fsmonitor program is executed.
- Ingest the pinned commit into a **new** tenant. No implicit overwrite, checkout,
  reset, stash or source-file write occurs in the developer's repository.
- Source HEAD/branch/dirty state is rechecked before publishing the graph READY.
  A newly created failed snapshot is deleted, never the prior tenant.
- Explicit `check` records a timestamped observation. The HTTP API/browser read
  only that graph metadata; they cannot supply host paths or trigger ingestion.
- `refresh` validates the old connection/base and a separately confirmed new
  HEAD, then performs a **full new snapshot**, reconciling additions, removals
  and renames by re-ingestion. This is not yet an incremental-update algorithm.
- Old findings/rules/playbooks remain in the old graph and are **not copied** into
  the new snapshot. Refresh is not a promise that every old finding is current.
- No absolute source path is stored in graph connection metadata or returned by
  the snapshot endpoint. A path-and-branch identity hash binds future CLI actions.

Native FalkorDB remains central: source and owner relationships, PageRank,
source-bound findings and snapshot metadata live in the selected graph.

## CLI examples (verified Linux VM setup)

From the isolated checkout, with FalkorDB reachable on loopback:

```bash
cd ~/ChronosGraph-t09
export PYTHONPATH="$PWD/backend"
# Choose only the narrow directories you intend to connect, not all of / or HOME.
export CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS="$HOME/projects"
export SOURCE="$HOME/projects/my-project"
export BRANCH="main"
export FIRST_REV="$(git -C "$SOURCE" rev-parse HEAD)"

.venv/bin/python -m app.ingestion.workspace connect \
  --source "$SOURCE" --branch "$BRANCH" \
  --tenant repo_my_project_v1 --expected-head "$FIRST_REV"

.venv/bin/python -m app.ingestion.workspace check \
  --source "$SOURCE" --branch "$BRANCH" --tenant repo_my_project_v1
```

Commit your source edits yourself, then inspect/confirm the intended new commit:

```bash
export NEXT_REV="$(git -C "$SOURCE" rev-parse HEAD)"
.venv/bin/python -m app.ingestion.workspace refresh \
  --source "$SOURCE" --branch "$BRANCH" --tenant repo_my_project_v2 \
  --from-tenant repo_my_project_v1 --expected-base "$FIRST_REV" \
  --expected-head "$NEXT_REV"
```

Choose a fresh tenant name every time. Refreshing an unchanged revision is allowed
for an explicit separate snapshot, but never replaces an existing tenant.
Allowlist entries are separated with the host's `os.pathsep` (colon on Linux).
Native Windows/macOS execution has not been verified; the existing platform
instructions remain authoritative about unsupported/unverified startup paths.

`check` exits successfully when it records an observation, **including CHANGED**;
inspect the JSON status/reasons, not just the exit code. Connect/refresh enforce
their own clean-tree and revision guards. Dirty paths/content are not printed.

## Browser/API

`GET /api/v1/workspace/snapshot?tenant_graph=repo_my_project_v1` is read-only.
The workbench repository selector loads the chosen tenant's branch, pinned commit,
last explicit check time/status and expandable metadata. Legacy snapshots show
`NOT_CHECKED` and no local connection. Selecting a snapshot does not watch disk.
Refresh the browser to reload newly created tenants or a later CLI check receipt.

Status observations include `MATCHED_AT_CHECK` and `CHANGED` with reasons such as
`BRANCH_ADVANCED_OR_REWRITTEN`, `DIFFERENT_CHECKOUT` or
`UNCOMMITTED_OR_UNTRACKED_CHANGES`. A matched check becomes historical immediately;
responses explicitly set `freshness_is_live: false`. Existing MCP/context responses
still label working-tree freshness unchecked: no global live-freshness claim.

## Trust/resource/concurrency boundaries

Only use this CLI with local Git repositories you intentionally trust. Git and
its object store are not a sandbox against a malicious same-UID process, unusual
repository configuration or filesystem races. Roots and `.git` must be ordinary
in-root directories; linked worktrees need a future explicit policy.

Git subprocesses disable hooks, fsmonitor, inherited `GIT_*` overrides, global and
system configuration, optional source-index refresh locks, credential helpers and
interactive prompts. Clone caches
are separate from user workspaces; no source checkout/reset is performed. Remote
URLs with credential/query/fragment data are not retained as source evidence.
This is defense in depth, not permission to expose arbitrary import over HTTP.

Preflight limits are 10,000 indexed Python files, 1,000,000 bytes per Python blob
and 16,000,000 total Python bytes. They do not bound all Git history/clone storage
or make arbitrary public cloning safe. The existing ingest cache may persist
outside the source tree; storage quotas/eviction remain pending.

Redis writer locks serialize our CLI jobs for a source and tenant. They do not
lock a human editor or other Git processes, and lease expiration/failures are not
a general distributed transaction guarantee. Pre/post guards plus immutable commit
reading prevent silently claiming dirty edits were incorporated. API registration
requires READY; the interim workspace-validation graph is not exposed as ready.

## Verification scope

Native tests exercise real CLI subprocesses and Git/FalkorDB, source/base/branch
mismatch, dirty/untracked changes, no overwrite, ignored hooks/fsmonitor,
symlink/size refusal, writer conflict, query-bearing remote URL privacy, new
snapshot rename/delete/add/ownership reconciliation and old-graph/finding retention.
Read-only REST metadata and browser desktop/mobile coverage supplement these.
No external coding agent, model, paid API, public import or video is required.

Run native backend and legacy/browser suites **serially** against this shared
local database. Some existing regression cases temporarily override demo policies
and compare the global sandbox set; concurrent suites can interfere. On Linux,
wrap a whole verification session with
`flock /tmp/chronosgraph-t09-native-verification.lock bash` and run the backend,
frontend and browser commands in order. All participating sessions must use that
same lock; it cannot prevent a separate user or uncoordinated process from writing.

Exception cleanup applies while the CLI is running. Abrupt process termination
can leave an INGESTING/VALIDATING_WORKSPACE graph requiring explicit owner review;
such a graph is not registered as READY. No automatic deletion of an unknown
owner's graph is attempted. “Immutable snapshot” describes pinned source; later
explicit policy/finding writes remain supported within that tenant.
