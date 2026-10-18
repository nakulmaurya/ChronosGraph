# Task/context/OpenCode vertical slice — unpublished checkpoint

## Outcome and scope

Implemented and witnessed an additive local task bridge on isolated branch `build/task-context-opencode-integration`, based on `438c31d8fd7c7fb6c36029c4ef19fcd1d9b061cc`. No push, merge, public deployment, paid-model fallback, or original-preview replacement was performed. This report is a release-critical vertical-slice handoff, **not completion of the full implementation brief**.

ChronosGraph is a shared, revision-aware context/evidence layer with persistent findings and exact-content human review. OpenCode remains the coding harness. This checkpoint connects the two; it is neither a security sandbox nor a general autonomous-worker scheduler.

## Implemented

- Existing `ChangeTask`/`ChangeAgentRun` reused; immutable `PlanVersion`, bounded immutable `ContextPack` and allowlisted `HarnessEvent` added in the selected FalkorDB graph.
- Task creation idempotence, current-plan compare-and-set, exact snapshot guards, complete mandatory constraints or explicit overflow refusal, exact file/symbol target requirement, source/policy freshness revalidation.
- OpenCode/plugin/SDK **1.19.3** project-only adapter, first-chat context delivery, compaction context hook, actual session IDs, initial Git worktree/overlay identity, tool lifecycle metadata and cumulative assistant-message usage categories.
- Persist-before-send bounded local event queue, stable retries/deduplication, conflicting sequence/event rejection, gap/truncation/partial reporting. No hidden reasoning, prompts or arbitrary tool bodies saved to the graph.
- Existing MCP proposal operation extended additively with task/plan/pack/run/initial-overlay binding and mandatory explicitly declared rationale. No parallel approval path. Stale task context clears approval eligibility.
- Actual task creation/resumption/observed-run UI and managed proposal evidence view; original approval/execution controls retained.
- Create-only installer and live doctor, preserving the venv executable path and existing configuration. Unsupported client/version/authentication/overlay claims remain explicit.

## Verification — witnessed, not inferred

All receipts referenced here are in `evidence/task-runtime-2026-10-18/`.

| Gate | Observed result | Receipt |
|---|---|---|
| Final full native backend suite | **391 passed**, no skips/failures; 128.89s | `native-final-391-pass.txt` |
| New task-runtime tests within full suite | 11 tests, including concurrent dedup, stale plans/policies, bounded Unicode/event/pack handling, transport guards, exact-target refusal and managed-rationale refusal | `backend/tests/test_task_runtime.py` |
| Frontend unit suite | **36 passed**, no skips/failures | `frontend-tests-36-pass.txt` |
| Frontend production build + TypeScript | Passed | `frontend-production-build.txt`, `frontend-typecheck.txt` |
| Plugin tests + pinned TypeScript | **3 passed**; typecheck passed | `plugin-tests.txt`, `plugin-typecheck.txt` |
| Live installer/doctor | Correct venv path, single-export entry, create-only retry unchanged, symlink refusal; doctor accurately says CONFIG_AND_API_ONLY without harness events | `installer-checks.txt` |
| Actual browser task creation | Created a graph task + immutable pack through real API; UI correctly reported no bound harness run | `live-task-create-ui.txt` |
| Live task and proposal views | Desktop + 390px mobile; no horizontal overflow or page exceptions | `live-task-ui.txt`, `live-proposal-ui.txt` |
| Independent exact patch checks | Full proposed file equals actual edited file; only `client.py` changed; AST identical excluding docstrings; contract pytest **1 passed**; diff check passed | `independent-proposal-checks.txt` |

Native regression execution used a newly created disposable FalkorDB container, with four corpora copied by read-only Redis DUMP from the existing review database, then restored only into that disposable instance. The test container was stopped afterward. Tests were not pointed at the original default application DB. Local FalkorDB Lite was unavailable because of the sandbox's GLIBC version; no host libraries were replaced.

### Actual read-only agent investigation and recovery

- Model: `opencode/deepseek-v4.1-flash-free`; actual interactive OpenCode TUI, not an API-authored substitute or simulated trace.
- Source: `7aeaa1c667c90017ff741887ecbe784fffdb3e0c` — owned, clearly labeled synthetic timeout/compatibility fixture.
- Task `task_a20a8f00470a846021fb06f549b35311`; plan `plan_ac310c0c85e9490a9cf872031afc79f8`.
- Pack `pack_4d26f28e43644af3aa631876bd2047d8`, complete serialized response 9796 UTF-8 bytes; size/4 is a token-equivalent estimate, not provider tokenization.
- Real session `ses_eb1f1a697ffe3vd7su2LSYzqlM`, run `run_9c5215a184765322579646fbbfda4ff7`.
- Agent used actual MCP snapshot, policy and source reads. It identified ADR-002 as active, ADR-001 as superseded, INC-007 as the motivating synthetic incident, the worker/test dependency, and Compatibility Platform as a **declared**, not authenticated, reviewer.
- The agent refused to treat the exception switch as currently acceptable. This meets the narrow investigation acceptance; it is not proof of universal engineering correctness. Its final wording included an imprecise possible TypeError aside; raising here would propagate the exception. The correct source-backed policy/consumer conclusion does not justify treating every explanatory phrase as verified.
- During an intentional restart of only the owned test API on port 8011, the local queue held three pending events at sequence 13. Later hooks flushed it to zero. Actual `/compact` completed; the final receipt has **27 unique sequence numbers, no gaps, one initial context-delivery event and one compaction event**. Idle remains `IDLE_NOT_SUCCESS`.
- Usage and compaction receipts are local harness observations, not an independently measured invoice or proof every context byte reached the provider. Initial provider HTTP 500 retries were retained, not counted as performance wins.

### Actual bounded patch and pending review

A separate fresh actual OpenCode session received a new task permitting only a docstring change in `client.py`; no first-session transcript was supplied. This is not claimed as a worker-handoff or memory experiment.

- Source `324978932177eb96075c22107f78249b1cc07614`; same owned fixture content, separate repository/snapshot identity.
- Task `task_95e732a7984739fd94a1bd9d5dffc376`; plan `plan_40c3e46f74be49f08c68d234113e9609`; pack `pack_33f54cbfe5bc4b56b564de042308d63e`.
- Session `ses_eb1e6e252ffeY5X3v0DIAXGDOm`; run `run_808e526ce1d3fac194164387de55a771`.
- Actual proposal `prop_60faf09d225f4b048cf5f80808437e25`; hash `b4c95e7b8b27e84f18eed552d77188bdb3c4944aeaed38dc95ffa3fcbfa694c2`.
- Agent read current governing evidence, edited only the docstring through an individually inspected native edit permission, and submitted the full exact replacement through the existing MCP proposal tool with matching managed identities and a declared ADR-002/INC-007 rationale.
- Final file SHA-256 `183696ff8d64b0c4a7a5be4806a5e95fe61fd4d8f91596cccdf45f9d6453c1d0`.
- Status remains **PROPOSED**, no approved hash, executions `[]`. Independent operator pytest/AST checks are external acceptance receipts, **not** a graph-recorded approved execution or a test run on some later revision.

## Failures retained and corrected

1. Local native library GLIBC incompatibility: moved native verification to the real VM; no success inferred locally.
2. OpenCode loader invoked helper exports as plugins: split into one-export plugin entry and a helper module outside the autoload directory. Actual subsequent TUI connected.
3. Installer resolved a venv symlink to system Python, breaking MCP imports: preserved the venv executable path; subsequent actual MCP calls and installer checks passed.
4. First full-suite command omitted the disposable benchmark flag and used a relative PYTHONPATH: preserved setup failures, corrected the isolated runner, then passed the native suite.
5. New unknown-target regression failed (**1 failed, 389 passed**): lexical fallback could match unrelated inventory for a mistyped exact task target. Managed packs now explicitly reject fallback; corrected **390 passed**, then final **391 passed** after adding the managed-rationale refusal test. Historical results remain separate.
6. Browser scripts initially filled before snapshot readiness / failed to select a proposal explicitly. UI now disables task resumption until revision identity loads; successful browser checks use the actual user selection path. No fake API responses were introduced.

## Compatibility matrix

| Capability | State |
|---|---|
| OpenCode 1.19.3 first-chat, tool metadata, usage, compaction, queue replay, managed proposal | Implemented and witnessed in the bounded live scenarios above |
| Existing 15 MCP tools / legacy unmanaged proposal path | Retained; native full regression passed |
| Other OpenCode versions; Claude Code/Cursor/Antigravity task lifecycle | Not adapter-verified; MCP configuration alone is protocol-only |
| Baseline cross-snapshot memory / organizational evidence | Existing implementation retained; this checkpoint does not rebrand it as newly completed |
| Real worker assignments, path claims, CAS leases/fencing and correction/handoff | **Deferred**; no scheduler/path-enforcement claim |
| context-mode integration | **Deferred/not installed**; no upstream code or performance credit claimed |
| Dirty-tree reindexing/live overlay, authenticated multi-user service | **Not implemented**; initial identity and pinned snapshot guards only |
| Untuned public task and new matched agent comparison | **Not run in this checkpoint**; older comparison results are not fresh evidence for this adapter |

## Evidence model and important read-only queries

`ChangeTask-HAS_PLAN-PlanVersion-HAS_CONTEXT-ContextPack`; `ChangeTask-HAS_RUN-ChangeAgentRun-USES_CONTEXT-ContextPack`; `ChangeAgentRun-HAS_EVENT-HarnessEvent`; `ChangeAgentRun-PROPOSED-ChangeProposal-BASED_ON_CONTEXT-ContextPack`.

Use the selected tenant graph and `GRAPH.RO_QUERY`, not a global cross-tenant query:

```cypher
MATCH (t:ChangeTask {id:$task})-[:HAS_RUN]->(r:ChangeAgentRun)-[:PROPOSED]->(p:ChangeProposal)-[:BASED_ON_CONTEXT]->(c:ContextPack)
RETURN t.id,r.session_id,p.id,p.status,p.proposal_hash,c.id
```

```cypher
MATCH (:ChangeAgentRun {id:$run})-[:HAS_EVENT]->(e:HarnessEvent)
RETURN e.sequence,e.kind,e.provenance ORDER BY e.sequence LIMIT 100
```

Recovery/setup/schema/budget details and package licenses are documented in `integrations/opencode/README.md`, its lockfile and `dependency-manifest.json`. The append-only API is not tamper-proof against a trusted local DB administrator. No hidden agent reasoning is exposed or invented.

## Review/demo script and next checkpoint

1. Select the synthetic source revision; create/resume a real task in Agent activity. Show current plan and bounded pack, not configuration as proof of connection.
2. Launch actual pinned OpenCode with the project bridge. Show received session/tool receipts and separate usage categories.
3. Ask the migration question: inspect the active decision → source excerpt → incident → declared team chain. Do not imply synthetic sources are an upstream incident.
4. Inspect the separate actual docstring proposal in Changes. Match task/plan/pack/run and full-file hash; show declared rationale, AST/contract receipt, and still-pending human approval.
5. Show recorded restart/compaction receipts explicitly as **recorded acceptance**, not a new live execution. No new video was generated for this implementation checkpoint.

Next: add one explicit bounded worker assignment/handoff only after review of this core slice; then predeclare an untuned public Python task and a fair matched comparison. Preserve the existing demo, report losing runs, retain ordinary baseline handoff, and measure actual harness usage/elapsed time without byte-to-billing conversions. Do not claim prizes, universal speedups, or the entire supplied roadmap complete.

AI-assisted implementation and verification: Notion AI; actual coding-harness acceptance: upstream OpenCode + DeepSeek free model. Original ChronosGraph graph/task/proposal adapter work is distinct from upstream client/SDK/DB implementations.
