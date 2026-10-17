# FINAL-01: exact proposals, observed tests, expiring evidence

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

## Data and state

`ChangeTask → ChangeAgentRun → ChangeProposal → HumanDecision`, with
`ChangeProposal → ExecutionRecord → ChangeVerification → TaskFinding` evidence.
Records live in the selected FalkorDB tenant, not process-local dictionaries.

`PROPOSED → APPROVED | REJECTED`; an observed local test run yields
`EXECUTED_VERIFIED | EXECUTED_FAILED`. Source/policy changes yield
`STALE_SNAPSHOT | STALE_POLICY` and clear approval. Reported external exit codes
stay `AGENT_REPORTED_UNVERIFIED`; a report does not mark an approval verified.

There is no edit endpoint: make a new immutable proposal for changed bodies.
Additions/deletions are supported; represent a rename as delete + add and update
callers explicitly. Bodies are bounded to 20 Python files / 128,000 combined UTF-8
bytes. No arbitrary client command string is executed. Source imports remain
read-only; pytest is a separate explicit opt-in action.

## REST surface

- `GET /api/v1/proposals?tenant_graph=...&revision=...` — latest 50, explicit truncation.
- `POST /api/v1/proposals` — browser-authored proposal.
- `POST /api/v1/proposals/{id}/decision` — exact proposal hash, approve/reject, reason.
- `POST /api/v1/proposals/{id}/execution` — unverified execution report.
- `GET /api/v1/proposals/runner-capabilities?tenant_graph=...` — operator configuration.
- `POST /api/v1/proposals/{id}/execute-disposable-worktree` — trusted local runner.
- `POST /api/v1/command-center/policy-override` — guarded current policy replacement.

Browser mutation calls require an allowed loopback Origin and
`X-ChronosGraph-Action: proposal-operator`. These are intent/CSRF checks in a
trusted local application, **not authentication**. Configure exact origins with
`CHRONOSGRAPH_UI_ORIGINS`. Keep the API loopback-only.

## Enable the trusted local runner

In the backend process environment, for an already imported allowlisted local
Git snapshot (not an unconfigured public archive):

```sh
export CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION=1
export CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS=/absolute/trusted/workspaces
export CHRONOSGRAPH_EXECUTION_REPOSITORIES='{"repo_my_saved_version":"/absolute/trusted/workspaces/my-repo"}'
```

Do not enable this for hostile checkouts. The root must match snapshot connection
metadata, the base commit must equal local HEAD, and the checkout must be clean.
The runner rejects symlinks/submodules and configured checkout filters, disables
Git hooks, verifies touched base bytes, and runs only the impact-selected pytest
paths with a 30-second timeout and bounded output. Repository tests still run
host code. Worktrees are removed in `finally`; a killed process may require manual
worktree cleanup. A durable started-attempt marker blocks automatic re-execution
of an ambiguous proposal, even with a new browser request key. Inspect observed
receipts and local process/worktree state before any manual recovery/new proposal.

Proposals, decisions, overrides and execution writes share the per-tenant
`chronosgraph:mutate:{tenant}` Redis lease (60s lifetime, 10s blocking wait).
Long operations check lease ownership before promotion. This is bounded local
coordination, not a claim of distributed exactly-once OS execution or rollback
of arbitrary test side effects.

## Memory semantics

An observed passing candidate run creates a source-bound finding linked to the
proposal and execution. It fingerprints the unchanged captured **base** and its
current policies; proposed result hashes are separate evidence. Additions bind their
absence at the captured base plus the exact base revision. Recall invalidates the
finding if an absent-at-base file appears or that revision changes. It does not
rewrite the source graph or claim deployed code. Recall recomputes freshness.
A policy override atomically supersedes the old rule and marks touched proposals
stale; findings are invalidated by digest checks at recall/poll time.

The seven-step hero script is a real stdio integration client with actual subprocess
pytest and a new server process for recall. It is not an LLM/IDE-agent evaluation.
The browser harness supplies separate witnessed browser approval/execution actions.

## Review limits

The per-tenant lease does not stop a trusted external editor from changing its own
checkout, nor does an approval revoke external OS permissions. Import receipts
have seven-day Redis retention, while proposal/execution records follow the lifetime
of the saved graph and its configured persistence. Static changed-signature flags
are conservative; no full Python argument/type analysis is claimed.
