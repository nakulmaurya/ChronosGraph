# Real bug: old context shown under a new plan

ChronosGraph's task context panel had a real frontend evidence-identity defect.
The recorded comparison uses actual application source builds, with **controlled
browser-only GET responses** to reproduce the selection change reliably. It is
not a new coding-agent run or a fix to FalkorDB itself. FalkorDB Python issue #244
is deferred and is not claimed as implemented.

[Watch the narrated before/after demonstration](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-real-bug-demo.mp4) ·
[Recording evidence and source mapping](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-2026-submission/ChronosGraph-real-bug-demo-evidence.md).

## Before and after

- Before: `689618354f6b821f072e3af873c45a5da3abd5fa`.
- Fixed application: `44bb68b459f83dbdc091ceecf4cd60ded72b379b`.
- Source fix: [`TaskRuntime.tsx`](../frontend/src/components/TaskRuntime.tsx),
  [`isCurrentContextPack`](../frontend/src/lib/task-runtime.ts), and
  [regression unit assertions](../frontend/tests/task-runtime.test.mjs).

After loading pack A, the old UI could retain it when polling selected plan B
without a run, or when fetching a replacement pack failed. Its provenance label
used the current plan B even though its manifest still belonged to A.

The fix invalidates context on selection changes, clears failed replacements,
and checks the actual pack's task, plan and recorded pack identity before
rendering. A render-time guard prevents an old pack appearing while effects
catch up. Missing evidence remains missing rather than being substituted.

## Recorded verification, October 18

| Controlled input | Old source | Fixed source |
| --- | --- | --- |
| Current plan changes; no recorded run for it | Defect reproduced: old pack displayed with new-plan label | Old pack hidden; “No recorded context pack for this current plan.” |
| Replacement pack fetch returns HTTP 503 | Defect reproduced: old pack retained | Old pack hidden; explicit “Context unavailable” notice |

All four captures completed with no JavaScript page errors. The 503 in the
second case is an intentional injected response, not a passing network request.
The frontend suite was freshly rerun after capture: **47 passed, zero failed**.
This is the existing suite, not 47 new regression tests. Its count is not added
to the historical 39-check observation for the prepared candidate.

The old frontend ran in an isolated local process; the fixed frontend was the
current managed preview. Both read the same existing backend. Interception
changed responses only in the recording browser. No persistent task, source,
policy or database records were modified, and no proposal was approved or run.

## Reproduction boundaries

The recorder needs both real builds and the existing prepared task/context pack.
A fresh empty database will not recreate historical agent sessions. Use the
complete [setup](../README.md#start-locally) for the application and inspect the
source/unit tests above independently. The public recording package includes
the browser harness, source-version mapping, clips and verification receipts.

The prepared task is `task_ef1809a9462f0b7be50e176e6b4d1db6`; its original pack is
`pack_44db4093d43a4ebfbf3f9b2a4cc16fcd`, bound to original plan
`plan_b2481e86f777458ab609224836495caf`. `plan-controlled-b` and
`pack-controlled-b` are explicitly controlled regression input identifiers.
The prepared organization and incident remain synthetic; the UI defect and
source fix are real ChronosGraph implementation work.
