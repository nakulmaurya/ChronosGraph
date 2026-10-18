# Current task-runtime checkpoint — demo and narration script

**Prepared script, not a new video, browser verification or fresh benchmark execution.** Use the observed Task 3/7 receipts; the old 35-pass run/digest and published walkthrough are historical. Do not show retained output under a LIVE label. Do not start a second comparison or a new model run merely to fill this script while Agent 2 is measuring Task 9.

## Preflight and recording rules

- Verified application code: `8e83804448cf251a26735d70c5a66f5b0d26db67`; candidate fixture base: `fabe543f8f010433a58f93d8cb7698f77e39e6b0`. Later documentation commits are separate from application builds.
- [Recovery and read-only doctor commands](task-runtime-hardening-recovery.md#current-entry-points-and-safe-resumption) establish owned bindings. The API health/declared identity and doctor checks are lightweight; they are not final desktop/mobile UI checks.
- If showing UI, first use Task 10 to establish an intentionally owned frontend and matching API build; do not reuse a shared preview with a different version. Until that gate is observed, label UI portions **PLANNED / NOT NEWLY VERIFIED** and use retained evidence for this walkthrough. This script itself does not launch a frontend.
- Show only selected code, safe IDs, immutable plans, sanitized tool/test receipts and source-backed policy excerpts. Hide keys, private dumps, provider configuration and raw exports/reasoning. Explain that the organization/incident are OWNED_SYNTHETIC.
- Demo is read-only at the current boundary: **no Create task, policy override, proposal resubmission, approval or execution click**. Stop before any action that changes evidence.

## Shot-by-shot script (approximately five minutes)

| Segment | Show / operator action | Suggested narration | Evidence / stop condition |
| --- | --- | --- | --- |
| 1. What the product is | Project description; optionally identity strip after the UI gate. | “ChronosGraph is a shared, revision-aware context and evidence layer for coding agents. OpenCode still does the coding. ChronosGraph connects the selected source, governing decisions, task context and exact proposed changes. It is not an operating-system security layer or a replacement for Git and tests.” | Separate declared application commit from indexed source revision. Do not call declared identity attestation. |
| 2. The actual task | In Agent activity, select the reconstruction snapshot and enter the existing **Resume task ID**; show **Immutable plan v1 · current**. Do not create another task. | “This is a new reconstruction of an owned synthetic example after temporary experiment files were lost. The requirement is opt-in retry delay while preserving existing timeout behavior. None and the default keep exactly the old result envelope.” | Task `task_ef1809a9462f0b7be50e176e6b4d1db6`. If the expected snapshot/task cannot be loaded, stop and use the labeled saved receipt—not an invented live result. |
| 3. Why the relationship matters | Actual local `worker.py` plus ACTIVE ADR-002 and INC-007 evidence. In the UI, Ownership/current-rule evidence may be inspected read-only after the gate. | “The worker reads the result’s ok flag to choose a retry. An exception-first change would bypass that branch. The current decision retains the envelope; the older exception proposal is superseded. This is a declared synthetic organizational case, not a claimed upstream outage.” | Current ADR-002/incident hashes and source revision are attached to the proposal. Ownership is a declaration, not verified GitHub identity or access. |
| 4. Exact candidate, not a vague suggestion | Saved complete candidate manifest and all three actual file bodies; display digest once. Label these **RETAINED CANDIDATE EVIDENCE**. | “The candidate changes the client, forwards the optional value through the worker, and adds regression tests. It rejects booleans and other nonintegers, rejects negative delays, and accepts zero. The review is bound to this complete set of bytes, not just the task title or one production file.” | Digest `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`. Files: `client.py`, `worker.py`, `tests/test_retry_after.py`. |
| 5. Real worker and independent reviewer | Retained actual OpenCode response/tool receipts, then **Explicit worker handoffs**. Show WORKER RETURNED → separate REVIEWER RETURNED and reviewer verdict. | “The implementation and review used separate actual OpenCode sessions and worktrees. The reviewer did not receive the worker conversation or its passing-test claim. It independently read the bytes and ran frozen acceptance plus repository tests: 39 passed. This is a fresh session of the same model, not a human or different-model review.” | [Actual review response](../tasks/reports/evidence/task-07-independent-review-2026-10-18/reviewer-response.md). Do not impersonate a running model by replaying terminal text as live. |
| 6. What acceptance does not mean | Changes → existing proposal status and attached current source references. Do not click approval. | “The bounded code review accepted this candidate. The proposal is still PROPOSED, with zero execution records. Source-backed citations and passing checks are evidence for a human decision, not approval. Different content, source or policy must be reconsidered.” | Proposal `prop_64084206f032410a923823abd797e75b`; inspect current state before stating it as live. Reference status `VALIDATED_PINNED_SOURCE_CHAIN_NOT_APPROVAL` is not an approval. |
| 7. Persistent context and honest status | Read-only saved task/run metadata, current doctor summary, **OpenCode-reported usage categories · not a billing total**. | “Task, plan, assignment and evidence records survive in the configured durable graph. Project-local receipts preserve delivery/upload state. A drained queue and an idle agent do not prove task success or provider consumption. Historical test observations are not automatically tests on a new revision.” | Runtime uses `IDLE_NOT_SUCCESS` / partial-completeness labels. Do not perform a restart during measured trials or present persistence configuration as a fresh restart experiment. |
| 8. Verification and limits | Small table from current reports, then a final plain-language summary. | “At application commit 8e83804, 403 backend tests, 19 plugin tests, 37 frontend tests, both typechecks and the production build passed. Those are separate overlapping verification scopes, not numbers to add into a task-success score. Final browser/release verification remains pending. The public agent comparison is owned by a separate run; no efficiency result is claimed here.” | Tasks 3–5 report and Task 7 review. No current speed, token-savings or universal graph-advantage claim. |

## Exact current handoff identifiers

- Task: `task_ef1809a9462f0b7be50e176e6b4d1db6`.
- Plan: `plan_b2481e86f777458ab609224836495caf`.
- Pack: `pack_44db4093d43a4ebfbf3f9b2a4cc16fcd`.
- Worker assignment: `assignment_37c364ea14474ac1a9b139bc0c5aa0d8`; reviewer assignment: `assignment_a04c4c6ab9f64ba98d50c159e3db4996`; both RETURNED.
- Worker run: `run_4f194b9967e6afbf3a6232a90b9319f6`; reviewer run: `run_8af0e0b766505039b09fb751cfbcfa47`.
- [Full candidate and before/after reviewer captures](../tasks/reports/evidence/task-07-independent-review-2026-10-18/sha256-manifest.json).

## If the demonstration encounters a failure

Show the actual error and stop the affected segment. Preserve the current run and candidate before attempting recovery. A missing/expired/changed pack, different digest, mixed UI/API builds, ambiguous proposal status or unavailable free model is a reason to label the segment blocked, not substitute old success output without disclosure. Do not change a governing rule, fabricate an owner, clear receipts, mint a new request key or click approval to rescue a recording.

## Closing line

“An agent proposes. A person decides. ChronosGraph keeps the connected evidence inspectable—and makes the boundaries of that evidence explicit.”
