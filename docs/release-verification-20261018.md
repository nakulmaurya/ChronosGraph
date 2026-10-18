# Deadline release verification — October 18, 2026

Application: `44bb68b459f83dbdc091ceecf4cd60ded72b379b`.
Presentation release `6896183`, followed by context invalidation fix `44bb68b`.
Current documentation can be newer than the deployed application; this record pins
what was actually built and checked.

## Fresh checks

| Check | Result / scope |
| --- | --- |
| Frontend unit tests | 47 passed, 0 failed/skipped |
| Frontend typecheck | Passed |
| Production build | Passed in isolated VM release worktree |
| Deployed browser | Prepared entry, file graph, decision/incident/owner, task/plan/context, worker/reviewer report, exact proposal diff and pending approval passed |
| Mobile smoke | 390px document / 390px viewport; no horizontal document overflow |
| Browser console/network | No page errors or HTTP failures observed in successful read-only smoke |
| Context regression | Client-only current-plan/no-run interception clears old pack |
| Context regression | Client-only replacement-pack HTTP503 clears old pack, shows unavailable |
| Source package audit | 100 historical evidence payload hashes verified, no scoped audit findings |
| GitHub Actions | [Both jobs passed](https://github.com/nakulmaurya/ChronosGraph/actions/runs/39147469784) for exact app commit |

Controlled regressions changed intercepted browser responses only; no persistent
plans, policies or source were mutated. They are not presented as live agent footage.
Initial operator attempts included an unsupported local-origin connection and
recording selector/codec setup failures; successful checks were rerun after fixing
those setup issues. These are not timed agent-comparison runs.

## Exact prepared evidence

- Snapshot: `fabe543f8f010433a58f93d8cb7698f77e39e6b0`
- Task: `task_ef1809a9462f0b7be50e176e6b4d1db6`
- Proposal: `prop_64084206f032410a923823abd797e75b`
- Candidate digest: `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`
- State: **PROPOSED; human approval pending; zero execution records**.
- Worker and separate reviewer returned; bounded reviewer report accepted the
  candidate after its recorded 39-check run. No fresh candidate check is claimed
  from the video or this frontend release.

The organization/ADR/incident are owned synthetic examples, not an upstream defect.
Recorded agent activity is retained actual OpenCode activity, not a new model run.
Missing/end-to-end-incomplete telemetry stays visible. Agent acceptance, observed
checks, human approval and integration are distinct.

## Deployment / recording boundaries

Only the existing managed preview frontend/API units were updated, using the same
prepared FalkorDB6381 with lifespan startup seeding disabled. Services remain
loopback-only; import and worktree-execution flags are off. That does not make all
API operations read-only or provide multi-user authentication. Separate review
services were untouched. [Access and rollback](preview-access.md).

The public video records actual read-only navigation of this deployed application,
with synthetic explanatory voiceover and captions. The opening load is trimmed;
chapter pauses and navigation are retained. No approval/execution is shown or done.
Public local setup does not reconstruct historical private sessions automatically.

No backend behavior changed tonight; unrelated full backend suites, fresh native
agent comparison, token-savings proof and broader production/security certification
are outside this receipt. [Evaluation and limitations](limitations-and-evaluation.md).
