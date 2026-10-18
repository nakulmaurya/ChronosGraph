# ChronosGraph — judge's guide

## What it is

**A shared, revision-aware context, persistent memory and change-evidence layer
for coding agents.** It connects a coding client such as OpenCode to captured
source relationships, governing decisions, task plans, findings and exact-content
human review. The Command Center makes those connections and observations
inspectable; FalkorDB stores the connected records.

It complements the coding agent, Git and real tests. It is not an OS security
sandbox, universal agent scheduler, verified identity/authentication service, or
guarantee that a proposed change is correct.

## Which source to review

- **`main`:** latest judge-facing source, setup documentation and observed evidence.
- **`experiments/full-evidence-2026-10-18`:** full source/evidence checkpoint,
  including failures, comparison records, candidate patches and scoped screenshots.
  Keeping it separate provides a stable audit/reference branch; the main source
  also retains the linked evidence so its claims can be inspected.
- **`build/task-context-opencode-integration`:** implementation/review lineage.
- Earlier branches, reports and videos retain their original scope. A source
  update is not an update to a running preview. No private agent exports,
  credentials, database dumps, installed dependencies or model binaries belong
  on these branches.

The latest verified application baseline is `8e83804`; later reporting changes
do not imply all gates were rerun. The earlier external-review ZIP is pinned to
`0c6be418`, not necessarily the latest documentation commit.

## Follow one connected workflow

1. Select/import an exact repository revision and inspect captured source.
2. Investigate callers, current decisions and declared owners; retain unresolved
   relationships and bounded analysis scope.
3. Create a task, immutable plan and bounded context pack; connect the pinned
   OpenCode client and observe actual tool/usage metadata.
4. Capture the complete candidate and exact-content pending proposal. Worker,
   reviewer, test observations and human approval remain separate records.
5. Reuse findings only while their source/policy assumptions validate; stale or
   incomplete evidence must not silently become current proof.

For setup: [local platform guidance](t09-platform-setup.md),
[OpenCode bridge](../integrations/opencode/README.md),
[recovery/runbook](task-runtime-hardening-recovery.md). Use an owned isolated
database/worktree; do not seed or test against unrelated data.

## Strongest observed evidence

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| [Tasks 3–5](../tasks/reports/TASKS-03-04-05-2026-10-18.md) | Scoped native backend, plugin/frontend and build checks at the exact checkpoint | Production readiness or arbitrary-client compatibility |
| [Task 7 fresh reviewer](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md) | Separate fresh same-model review of the bounded synthetic candidate, with 39 checks passing | Human approval, integrated candidate, or an independent-person audit |
| [Task 10 actual desktop/mobile](../tasks/reports/TASK-10-READONLY-BROWSER-VERIFICATION.md) | Matching source declarations and read-only task/reviewer/proposal/ownership inspection | New approval/execution, full accessibility or broader mutating/recovery gates |
| [Task 9 observed pilot](../tasks/reports/TASK-09-OBSERVED-COMPARISON.md) and [Task 11 analysis](../tasks/reports/TASK-11-COMPARISON-ANALYSIS.md) | Four retained one-shot free-model cells, their runtime checks, usage, failures and limitations | A graph speed/token/cost advantage or cross-session memory benchmark |

The synthetic timeout-contract example is explicitly owned/fictional, not an
upstream defect. SDK comparison tasks are requested maintenance changes, not
claimed upstream bugs. Four runtime-check sets passed, but only two native turns
finished. Both lookup turns were permission-stopped with unresolved
convention/typechecker findings. Graph input was higher in each pair and timing
was mixed; **no graph advantage or savings is established**.

## Inspect the limitations, not just the screenshots

- Persistent records require a deliberately durable deployment; a source ZIP
  does not contain or recreate historical graph state.
- Host-observed context/usage and plugin identity are not provider-consumption
  proof, trusted execution attestation or a fabricated billing total.
- Static candidate tests are not proof that other tests can safely be skipped.
- Generic reviewer-summary wording, resume panel/target behavior and incomplete
  telemetry remain documented limitations.
- Historical benchmark acceptance remains unmet. The old missing-import audit
  and latency observations retain their exact dated scope.
- Sanitized evidence retains usernames, absolute paths and session/tool IDs;
  it is not anonymous. Original diagnostic whitespace warnings are retained.

For a deeper correctness review, use the [external review brief](../tasks/reviews/EXTERNAL-REVIEW-BRIEF.md).
Source publication and successful CI do not authorize deployment, candidate
approval, organizer submission, or claims of prize eligibility.