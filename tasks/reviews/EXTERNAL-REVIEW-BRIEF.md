# ChronosGraph — external reviewer brief

**Review request, not release approval.** Review the exact repository checkout accompanying this file. For Git, first record `git rev-parse HEAD`, branch and dirty state; for a source ZIP without `.git`, use the accompanying package manifest and per-file checksums. Do not assume `main` or a deployed preview matches it. Current source includes an unpublished task-runtime checkpoint, separate retained candidate evidence, observed comparison/browser receipts and local review helpers. Packaging integrity is not product-readiness certification.

## What the project is

ChronosGraph is a **shared, revision-aware context, memory and change-evidence layer for coding agents**. It sits alongside an agent such as OpenCode rather than replacing its model, editor, Git or test runner. A Next.js Command Center and MCP tools use FastAPI/FalkorDB services to inspect saved source relationships, decisions, ownership declarations, task plans, findings, proposed changes and execution receipts.

The unpublished bridge adds task → immutable plan → bounded context pack → actual OpenCode run telemetry, plus explicit worker/reviewer handoffs. Persistence and sharing mean access to the configured graph and scoped records, not universal memory synchronization across arbitrary agents or an automatic migration of every finding to every revision.

It is **not an OS sandbox, verified identity system, multi-user authentication layer, guarantee of safe code, or proof that tests can be skipped**. Visual change inspection, persistent context and exact-content review guards are parts of the workflow, not independent claims of complete security or autonomous correctness.

## Exact evidence boundaries

| Item | Verified identity / scope |
| --- | --- |
| Last verified application code | `8e83804448cf251a26735d70c5a66f5b0d26db67`; later preparation commits do not imply new application gates. |
| Synthetic fixture base | `fabe543f8f010433a58f93d8cb7698f77e39e6b0`; owned timeout-envelope compatibility example, not a reported upstream defect. |
| Separately reviewed candidate | `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`; complete `client.py`, `worker.py`, `tests/test_retry_after.py` capture. Not integrated into application/source merely because evidence is in this repository. |
| Bounded candidate check | Fresh actual same-model reviewer session, separate worktree; 39 frozen acceptance + repository checks passed. ACCEPTED for this candidate, not a global approval or different-model/human review. |
| Proposal boundary | `prop_64084206f032410a923823abd797e75b`, PROPOSED, zero execution records at last retained readback. Live state must be rechecked before presenting it as current. |
| Separate retained regression gates | 403 backend; 19 plugin tests/types; 37 frontend tests/types and production build, with exact scope in Tasks 3–5. Do not add overlapping suites into one success count. |
| Scoped browser gate | Task 10 actual Chromium desktop/mobile read-only workflow PASS at application `8e83804`; fresh frontend build and 44 local frontend unit checks. Generic reviewer wording, resume panel/target and broader gate limitations remain. Not full release certification. |
| Public agent comparison | Four one-shot Task 9 cells retained and reconciled in Task 11: selected runtime checks pass; two final answers and two permission stops with unresolved lookup convention/typechecker findings. No performance, token/cost savings or graph-win conclusion. Earlier twelve-run walkthrough and incomplete pilot records are distinct experiments. |

## Read in this order

1. [Tasks 3–5 report](../reports/TASKS-03-04-05-2026-10-18.md) and its raw scoped receipts.
2. [Fresh independent Task 7 review](TASK-07-INDEPENDENT-REVIEW-2026-10-18.md); [full candidate/checksum evidence](../reports/evidence/task-07-independent-review-2026-10-18/sha256-manifest.json).
3. [Recovery/migration runbook](../../docs/task-runtime-hardening-recovery.md) and [OpenCode bridge](../../integrations/opencode/README.md).
4. [Task 10 observed read-only verification](../reports/TASK-10-READONLY-BROWSER-VERIFICATION.md), [read-only runner boundaries](../../docs/task-checkpoint-readonly-smoke.md), [Task 9 sealed observations](../reports/TASK-09-OBSERVED-COMPARISON.md) and [Task 11 reconciled analysis](../reports/TASK-11-COMPARISON-ANALYSIS.md). The old Task 11 template is not the current execution report.
5. Product paths: `backend/app/services/task_runtime.py`, `task_assignments.py`, `harness_usage.py`, `context_locator.py`, `task_memory.py`, `workspace.py`, `change_lifecycle.py`, `proposal_evidence.py`; `backend/app/task_api.py`; `integrations/opencode/`; `frontend/src/components/TaskRuntime.tsx` and `ChangeProposals.tsx`. Verify paths and call chains in the supplied checkout.

Older README/architecture/planning sections preserve historical contracts. Resolve current behavior from exact source and scoped receipts, not the most optimistic historical description.

## Review questions (prioritize correctness over feature breadth)

1. **Bindings and staleness:** Can the wrong tenant/revision/plan/pack/run/candidate or a changed policy be accepted as current? Are missing facts distinguished from absence of impact? Does source continuation avoid mixed revisions and incomplete replacement bodies?
2. **Context completeness:** Are mandatory rules kept within an explicitly bounded scope? Are truncation, unresolved dependencies and exact inventory/index limitations visible? Do not assume historical missing-import audits were fixed without fresh evidence at the same source revision.
3. **Handoffs and observations:** Do claims/versions/predecessors and complete candidate captures actually connect worker to reviewer? Can plugin-reported local identity be confused with trusted execution or attestation? Are paths advisory outside captured proposals?
4. **Approval and execution:** Is a proposal bound to exact content and current source/policy? Do duplicate submissions, changed content and replayed approvals fail safely? Are a declared review verdict and recorded test result kept separate from human approval/execution?
5. **Memory and recovery:** Are historical findings/observations retained with original provenance across snapshots? Is carry-forward explicitly scoped and revalidated, including dependency changes? Which restart/restore/migration cases have actually been executed versus documented only?
6. **Usage and telemetry:** Are duplicate/cumulative message snapshots prevented from double-counting completed-step usage? Are missing sequences, interrupted/retried calls, cache categories and unknown provider usage exposed rather than converted to zero cost or success?
7. **UI truthfulness:** Do mobile/resume/failed-request states preserve uncertainty? Generic reviewer RETURNED wording and resumed context-pack visibility are known items to inspect. Missing UI/API declarations must not masquerade as matched builds.
8. **Comparison validity:** Check exact prompts/source/check hashes, permissions, attempt accounting, 12-path scope amendment, model/cache and wall-time waits/shared-resource interference. Four cells with one repetition each are a small pilot, not statistical proof or a cross-session memory benchmark.

## Requested review output

Return findings first, sorted by severity, each with exact file/line, demonstrated failure or reproducible scenario, affected invariant and minimal correction. Distinguish **observed**, **inferred**, **not run** and **blocked**. Include useful counterevidence and successful checks. Finish with a bounded verdict: ACCEPTED / CHANGES_REQUESTED / BLOCKED / UNVERIFIED for the named scope; never turn a source review into production or submission certification.

Default to read-only review. Do not approve/execute proposals, modify shared graphs, restart services, install dependencies, launch paid models or merge/push/deploy. The measured window has ended; still request an isolated quiet environment for integration checks. Public review material excludes credentials, SSH keys, agent homes/raw reasoning exports and private database dumps, but deliberately retains identifying provenance (VM usernames/absolute paths, timestamps and session/tool IDs). It is sanitized, not anonymous.

Task 9's sealed `payload/analyze.py` and `frozen/runner.py` are historical evidence,
not a portable benchmark recipe: raw private inputs are absent and historical
default service ports must not be used blindly. The new
`scripts/analyze-task9-sanitized.py` is an offline record-reconciliation helper
requiring pandas; it does not recreate trials or rederive raw provider exports.
The [upstream SDK MIT notice](../../third_party/README.md) accompanies copied source
context. Immutable evidence retains whitespace warnings (full import diff exit 2
across ten paths); new report/metadata checks are separate.
