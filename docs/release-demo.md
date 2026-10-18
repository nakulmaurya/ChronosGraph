# Connected workflow demonstration

ChronosGraph — **See what your coding agents change—and the evidence behind it.**

This is a read-only walkthrough of a working application with a **prepared owned
synthetic organization/incident** and persisted actual agent activity. It is not
a new live model run, new test execution, human approval or merged candidate.

## Released recordings

[Watch the 4:34 Kokoro-narrated connected workflow](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-hackathon-demo.mp4).
[Script, two-line captions, evidence manifest and portable recorder](https://github.com/nakulmaurya/ChronosGraph/releases/tag/hackathon-2026-submission)
are published alongside it. The stock `af_heart` voice was generated locally
with Kokoro; this is disclosed on screen. Prepared records and edited reading
holds are identified in the manifest.

The [real stale-context regression](context-integrity-regression.md) is separate
from the synthetic candidate: the actual old UI retains stale context under a
new plan, while the fixed UI rejects it in two controlled browser cases.

The [earlier 3:25 walkthrough](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-narrated-walkthrough.mp4)
remains supplementary. The shot list below is the original three-minute rehearsal
plan, not the final exported chapter timing. Authenticated organizer video limits
remain unverified.

## Open the example

Follow [current managed-preview access](preview-access.md). On a configured
preview, click **Open prepared example**. The button is shown only if the
configured snapshot exists in that backend; it does not create a successful state.
The link opens the saved source and carries the existing task ID, which the
Agent activity panel resumes read-only. A missing snapshot or stale context must
remain an error, not be silently substituted.

## Exact path and narration

| Time | Action | Explain |
| --- | --- | --- |
| 0:00–0:20 | Open prepared example; show first screen | A developer has an agent patch but needs its dependencies, constraints, checks and next human action. |
| 0:20–0:50 | Scroll to `client.py` graph; inspect `worker.py → client.py` import | The worker relies on the timeout result. This is a captured static relationship, not complete runtime proof. |
| 0:50–1:15 | Ownership → Inspect rules & contributors; expand current decision/incident | ACTIVE ADR-002 keeps the timeout envelope; older ADR-001 is superseded. INC-007 explains the synthetic retry failure. Compatibility Platform is a declared review team. |
| 1:15–1:45 | Agent activity → immutable plan; existing bounded context pack | The task adds optional `retry_after`, preserves the default contract and forwards through the worker. The retained pack is revision/policy bound. |
| 1:45–2:10 | Expand worker/reviewer handoffs and declared reviewer report | Separate actual OpenCode sessions/worktrees. Reviewer’s recorded 39-check observation is not newly run during this video or human approval. Telemetry remains explicitly incomplete. |
| 2:10–2:40 | Changes → select existing proposal → expand `client.py`, `worker.py`, tests | Inspect exact candidate comparison and pending human decision. Do not click Approve or Run. Zero execution records belong to this proposal. |
| 2:40–3:00 | Show pending decision and graph/table | FalkorDB connects source, requirements and persistent handoffs. Map that same workflow to all three tracks. No savings or exhaustive-safety claim. |

Three minutes is our target, **not a verified organizer form limit**. The organizer
form requires sign-in; adjust only to a witnessed authenticated requirement.

## Rehearsal checklist

- Match frontend/API declared application revision to the release receipt.
- Saved fixture revision `fabe543f8f010433a58f93d8cb7698f77e39e6b0` is data,
  not the application commit.
- Task `task_ef1809a9462f0b7be50e176e6b4d1db6`; proposal
  `prop_64084206f032410a923823abd797e75b` remains PROPOSED.
- Candidate identity and full plan/pack/run/report metadata remain in disclosures.
- Do not capture secrets, provider settings, private raw exports or hidden reasoning.
- Use actual persisted receipts, not a fake terminal or simulated successful API.

If the environment becomes unavailable, use the released recording, label its
recording revision, and provide [complete local setup](../README.md#start-locally).
A fresh local database will not recreate these historical agent sessions; the
public [candidate/reviewer evidence](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md)
remains inspectable. Do not relabel old footage as current execution.
