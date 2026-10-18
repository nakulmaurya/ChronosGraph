# Current release

## Deadline release: visual oversight and shared context

**ChronosGraph — See what your coding agents change—and the evidence behind it.**

This release makes the current application understandable through one connected
prepared example. It adds first-screen positioning, a working prepared-example
entry point (only when configured and present), clearer agent handoff status,
collapsed technical metadata and read-only context-pack recovery on task resume.
It does not change backend behavior or approve/execute/integrate a candidate.

## Exact application and verification

**Application source and deployed frontend/API:**
`44bb68b459f83dbdc091ceecf4cd60ded72b379b`.
Subsequent documentation/media publication commits do not change this application build.
The inspected prepared source is separately pinned to
`fabe543f8f010433a58f93d8cb7698f77e39e6b0`.

Fresh scoped checks for this application release:
- 47 frontend unit checks passed; frontend typecheck passed.
- Clean isolated VM production build passed.
- Deployed read-only browser walkthrough passed: prepared entry, captured file graph,
  organizational evidence, task resume/current plan, reviewer report, context retrieval,
  exact candidate comparison and pending human approval.
- Narrow viewport: 390px document width at 390px viewport; no JavaScript or failed
  HTTP responses observed in the successful walkthrough.
- Controlled browser-only regressions passed for a changed current plan with no run
  and a failed replacement context-pack fetch. Old context is not relabeled as current.
- GitHub [Command center correctness](https://github.com/nakulmaurya/ChronosGraph/actions/runs/39147469784)
  passed both frontend and native-command-center jobs for `44bb68b`.
- Scoped source audit: 100 existing evidence hashes checked; no audit findings.

Backend behavior is unchanged from the prior application baseline; tonight's local
release verification did not rerun unrelated backend suites or the 39 historical
candidate checks. Counts are not combined with earlier runs. Review assistance
found one stale-context issue; it was fixed and the two browser regressions above
confirmed the fix at runtime.

The existing managed preview was updated on loopback 3004/8004 with the prepared
DB6381, startup seeding disabled, and import/execution flags off. A prior working
service override and rollback receipt were retained. The public submission uses
**complete local setup plus the public video**, not a publicly authenticated SaaS.

**Candidate state rechecked after deployment:** PROPOSED, unchanged exact candidate
digest, zero execution records. Worker/reviewer returns and retained 39-check
review evidence do not grant human approval or prove complete harness telemetry.

## Demonstration and real-bug evidence

**[Primary video: the real stale-context bug, before and after · 3:26](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-real-bug-demo.mp4).**
Local Kokoro narration, captions, reusable recorder and source manifest accompany
actual old/fixed UI footage. Controlled regression inputs are explicitly labeled.


The [real stale-context regression](context-integrity-regression.md) compares
actual old and fixed source builds under controlled browser-only inputs. Both
failure modes reproduced before the fix and rejected old context after it.
A fresh frontend rerun passed all 47 existing tests; no historical counts are
combined. No database writes, model runs or candidate approvals were performed.

A separate [4:34 Kokoro-narrated connected workflow](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-hackathon-demo.mp4)
shows the prepared synthetic project and recorded actual agent activity.
[Captions, script, source manifest and reusable recorder](https://github.com/nakulmaurya/ChronosGraph/releases/tag/hackathon-2026-submission)
accompany it. It is not an upstream bug fix. The older 3:25 walkthrough remains
supplementary, not the final Kokoro export.

[**Narrated working video and captions**](https://github.com/nakulmaurya/ChronosGraph/releases/tag/hackathon-2026-submission) ·
[Demo guide](release-demo.md) · [Setup](../README.md#start-locally) ·
[Preview operation](preview-access.md) · [Scoped release receipt](release-verification-20261018.md) ·
[Limitations and evaluation](limitations-and-evaluation.md).

<details>
<summary>Previous release identity and historical verification</summary>

# Current release status

## Latest judge-facing source — task-runtime integration checkpoint

`main` is the judge-facing source target; `experiments/full-evidence-2026-10-18`
preserves the complete source/evidence checkpoint. See the [judge's guide](judges-guide.md).
The implementation adds an opt-in OpenCode 1.19.3 task/context/event bridge and managed proposal evidence. See the [setup and compatibility boundary](../integrations/opencode/README.md) and [initial verification report](../tasks/reports/TASK-RUNTIME-OPENCODE-2026-10-18.md). Source publication is not a claim that any shared preview runs this checkpoint. Existing deployments are unchanged by Git operations.

**Verified local application checkpoint: `8e83804`.** [Tasks 3–5 recovery verification](../tasks/reports/TASKS-03-04-05-2026-10-18.md) records 403 native backend tests, 19 plugin tests, 37 frontend tests, both typechecks and production build passing. The reconstructed behavioral candidate has a persisted unapproved proposal and 39 independent checks passing. [Task 7 fresh independent review](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md) accepted only that bounded candidate after its own 39-pass run. [Task 10 actual desktop/mobile browser verification](../tasks/reports/TASK-10-READONLY-BROWSER-VERIFICATION.md) passed the scoped read-only workflow, fresh frontend build and 44 local frontend unit checks. It did not approve/execute the candidate or certify broader mutating/recovery/integration gates.

The [four-cell Task 9 observed pilot](../tasks/reports/TASK-09-OBSERVED-COMPARISON.md) and [Task 11 analysis](../tasks/reports/TASK-11-COMPARISON-ANALYSIS.md) are now integrated as documentation/evidence only. Two native turns finished; two lookup turns were permission-stopped with unresolved convention/typechecker findings despite passing selected runtime checks. Graph input was higher in both pairs; elapsed direction differed. **No graph advantage or savings established.** Earlier interrupted attempts remain historical/indeterminate, not rescored by these later observations.

No separately captured candidate was integrated by the reporting/publication work.
The owner authorized publication of the latest checkpoint to GitHub `main` and a
separate full-evidence branch. Publication changes source refs, not preview
services or proposal approval/execution. The review ZIP remains pinned to
`0c6be418`; later publication-documentation changes do not retroactively update it.
Review packaging/publication is not submission or release approval.
[Current external review scope](../tasks/reviews/EXTERNAL-REVIEW-BRIEF.md) and [third-party notices](../third_party/README.md) accompany the evidence; sanitized provenance is not anonymous.

The sections below retain the earlier published release status and historical measurements. They do not describe the new checkpoint's test counts, adapter acceptance or deployment identity; the new report does. In particular, the old 506-import result remains historical evidence, not a claim that a freshly indexed snapshot still has that exact defect.

## Historical source and publication

`main` is the primary branch for the latest hackathon implementation. It integrates
`build/final-hackathon-release`, including application baseline `479e987` and the
current documentation synchronization. The feature branch is retained for history.
No force push or rewriting of historical verification receipts is required.

## What is implemented

- Monochrome repository Command Center: folder/file and function graphs, table
  navigation, exact captured source, bounded history, ownership and agent activity.
- Public GitHub archive import with pinned source and seven-day Redis receipts.
- Fifteen MCP tools with selected-snapshot guards; real OpenCode/DeepSeek lifecycle
  verification is documented separately from the scripted video demonstration.
- GRAPH.COPY replacement-diff proposals, exact human decisions, trusted local
  observed candidate tests, and source/policy-bound findings with stale guards.
- Controlled shortestPath replay, recovery notes and Obsidian vault export.

## Verified evidence, not new test claims

The latest full verification batch is [FINAL-BENCHMARK-01](../tasks/reports/BENCHMARK-REPORT.md):
333 backend tests with no skips/failures, 34 frontend unit tests, typecheck/build,
118 browser check executions (96 excluding repeated recovery/setup executions).
These are historical witnessed results for `479e987`, not a claim that every gate
was rerun during a documentation-only publication. GitHub Actions supplies the
post-push regression checks.

**Benchmark acceptance remains NOT MET:** larger context lookups exceed 50 ms,
the legacy GraphRAG snapshot misses 506 audited absolute imports, and runtime
test-impact precision is unmeasured. Focused byte reduction of 92.22–98.19% is
not equivalent-content compression, exact token savings or validated test skipping.

## Deployment and security boundaries

Publishing `main` is not VM deployment. The existing preview remains at `46d1508`
on loopback 3004/8004. See [access and operation](preview-access.md).
Trusted local worktrees are not security sandboxes; origin/snapshot checks are
not multi-user authentication. Broader production readiness and hackathon submission
are not asserted by a Git merge or by the walkthrough.

## Repository boundaries

Application code, project-specific integration scripts, tests, docs and evidence
belong in this repository. Downloaded OpenCode/external harness binaries, model
credentials, virtual environments and generated build caches do not. Large walkthrough
media is distributed as GitHub release assets rather than committed to source.

</details>
