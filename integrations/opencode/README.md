# Opt-in local OpenCode task bridge (unreleased checkpoint)

ChronosGraph remains a shared source-and-evidence layer, not a second coding model, operating-system security boundary, or replacement for Git/tests. This adapter connects an actual OpenCode session to a versioned task, immutable context pack, observed tool/usage metadata, and the existing exact-content proposal workflow.

## Supported boundary

- Pinned client/plugin/SDK: **OpenCode 1.19.3**. Other versions/clients are not verified by this adapter.
- Loopback HTTP API and local trusted user only. Tenant/revision/task IDs and the action header are consistency/transport guards, **not authentication**.
- Native read/edit/shell permissions remain `ask`. The plugin does not approve proposals, sandbox code, prevent native edits, or enforce worker path claims.
- Exact captured file or symbol required for a managed pack. General discovery remains available through existing MCP tools. Full mandatory constraints must fit the budget or creation fails; they are not silently trimmed.
- Packs describe a pinned base snapshot. `BASE_ONLY_OVERLAY_NOT_INDEXED` means working edits have **not** been reindexed. Initial overlay identity is not an attestation of the final checkout.

## Install into an owned project

First run the backend locally with FalkorDB and ingest/select the exact Git revision using the existing workflow. Do not replace a deployment or expose this API publicly.

1. In **Agent activity**, enter a task objective and acceptance checks with a selected file, then create its bounded context pack. Alternatively use the small REST API below.
2. Record the returned tenant, revision, task, current plan and pack IDs.
3. From this repository run:

```bash
python scripts/setup-task-opencode.py install \
  --project /absolute/path/to/owned/worktree \
  --backend /absolute/path/to/ChronosGraph/backend \
  --python /absolute/path/to/installed/venv/bin/python \
  --api http://127.0.0.1:8011 --db-port 6381 \
  --tenant repo_SELECTED --revision EXACT_40_CHARACTER_GIT_SHA \
  --task task_RETURNED --plan plan_RETURNED --pack pack_RETURNED
```

The API/DB ports above are acceptance-environment examples, not universal defaults. Use the ports of your deliberately selected local deployment. Preserve the virtualenv executable path, including its symlink; replacing it with the resolved system Python can break MCP dependencies.

The installer is create-only: it refuses existing target files and symlinked integration directories rather than merging/overwriting configuration. It writes only project `.opencode/` and `.chronosgraph-local/` files. It does not read provider credentials or change global settings. Review existing project configuration before choosing a separate owned worktree.

Launch **from the selected worktree** with the generated project configuration:

```bash
OPENCODE_CONFIG="$PWD/.chronosgraph-local/opencode.json" /absolute/path/to/opencode-1.19.3
```

The generated model is `opencode/deepseek-v4.1-flash-free`; availability is provider-dependent. No paid fallback is selected. The small wrapper in `.opencode/plugins/chronosgraph.ts` must export **only** `ChronosGraph`. Helper exports belong in `.opencode/chronosgraph/bridge.ts` because the pinned loader invokes all plugin-directory exports.

```bash
python scripts/setup-task-opencode.py doctor \
  --project /absolute/path/to/owned/worktree \
  --opencode /absolute/path/to/opencode-1.19.3
```

`CONFIG_AND_API_ONLY` is not a connected-agent claim. Receipt presence is not proof of task success, full provider consumption or a successful proposal.

## Task API

All paths below are under `/api/v1/tasks`. Mutation requests require `X-ChronosGraph-Action: task-runtime`, a loopback URL and, when supplied, an approved local UI Origin. Every operation is scoped by `tenant_graph` and `expected_revision`.

| Operation | Path | Additional required values |
|---|---|---|
| Create task + initial immutable plan | `POST /` (without trailing slash) | title, objective, acceptance array, target, request_key |
| Inspect/resume | `GET /{task}` | scope query parameters |
| Supersede plan, compare-and-set | `POST /{task}/plans` | parent_plan_id, objective, acceptance, target |
| Build immutable context pack | `POST /{task}/context-packs` | current plan_id; budget_equivalents 1500–3000 (default 2500); analysis_path_limit 1–100 (default 100); optional expansion_paths |
| Read and revalidate pack | `GET /{task}/context-packs/{pack}` | scope query parameters |
| Bind actual harness session | `POST /{task}/runs` | plan_id, pack_id, session_id, optional parent_session_id, worktree_id, overlay_digest, harness_version |
| Append bounded observed event | `POST /{task}/runs/{run}/events` | schema_version 1 (legacy) or 2 (completed-step), event/source IDs, sequence, kind, observed_at_ms, session_id, payload_digest; allowlisted metadata only |

[Hardening, serialized assignment API, migration and interrupted-run recovery](../../docs/task-runtime-hardening-recovery.md).

Use the actual returned IDs. A revised plan invalidates old packs and managed proposals. Rebinding an existing session to different context is rejected: explicitly archive project telemetry/configuration and create a fresh session/worktree for a new binding, preserving prior evidence. There is no silent migration or generic scheduler.

## Event, context and review semantics

- Mandatory context freshness remains synchronous/fail-closed. First chat uses a stable synthetic block; preparation, hook injection and supported SDK observation of a persisted host part are distinct. Unconfirmed delivery remains safely reconcilable. None proves provider consumption or exactly-once delivery.
- No prompts, reasoning text or arbitrary tool-input/output bodies are retained in the event graph. Safe metadata, stable IDs, statuses and reported usage categories are retained. Raw private harness exports are separate and never belong in source archives.
- A background drain uploads atomically persisted local receipts with bounded timeout/backoff/jitter. Permanent failures are retained in quarantine, stale binding requires reconciliation, saturation/unobserved state remains visible and disposal is bounded. Linux flock enforces one writer per state file. Do not clear evidence to make a queue look healthy.
- Bounds: 250 pending events, 2000 dedup/server event entries per run, detail last 100 events, at most 10 runs/100 plans, explicit truncation. Retention exhaustion is not a complete audit service or permission to discard receipts.
- v2 completed-step parts with stable session/message/part IDs are the authoritative observed usage basis. Input/output/reasoning/cache read/write remain separate. Message cumulative cost is reconciliation only, not another additive cost source. Legacy cumulative messages remain labelled separately; provider retry usage and a guessed token_total are unknown. Zero free-model charge is not paid-model savings.
- Clean managed start; complete supported-text changed/add/delete candidate manifest and digest; immediate recapture prevents mixed local observations. Tracked metadata changes are not excluded. Binary/symlink/mode/large-file and non-Python proposal limitations explicitly refuse. A plugin observation is not independent runner attestation.
- Assigned proposals require the current WORKER claim/version and allowed paths; complete task/plan/pack/run/candidate/evidence bindings are validated. Current decision/excerpt/hash citations differ from a declared rationale. Missing citations do not imply no policy exists. Changed content or stale context never inherits approval.
- Idle means IDLE_NOT_SUCCESS. Local assignment reports, tests, candidate verification, task success and exact human approval remain separate. Roles are explicit serialized records, not leases, authenticated users or OS write controls.

## Verification and limitations

See `tasks/reports/TASK-RUNTIME-HARDENING-02.md` for the latest checkpoint and blockers, and `tasks/reports/TASK-RUNTIME-OPENCODE-2026-10-18.md` for the earlier checkpoint and its evidence directory for actual native-test and live-harness receipts, including failures encountered and corrected. The synthetic read-only investigation and documentation patch are integration acceptance, **not** an agent speed/cost comparison or an untuned public-repository task. No worker lease/fencing scheduler, context-mode integration, arbitrary-client support, final-tree overlay index, or universal token-saving claim is included in this checkpoint.
