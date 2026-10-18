# Task 8 — recovery documentation and demo preparation

**COMPLETE for documentation preparation; not release certification or a new recording.** The original numbered plan assigns Task 8 to recovery documentation/demo preparation, not candidate integration. An earlier review handoff used the wrong task label for integration; the review report now corrects that label while retaining original receipts unchanged.

## Deliverables

- [Current recovery runbook](../../docs/task-runtime-hardening-recovery.md): read-only safe resumption, persistent root pointers, current source/candidate/proposal identity, doctor interpretation, clean create-only setup, migration/failure decisions, and the boundary between durable metadata and proven execution.
- [Current demo and narration script](../../docs/task-runtime-checkpoint-demo.md): approximately five-minute evidence walkthrough with exact task/plan/pack/assignment IDs, owned-synthetic policy/incident explanation, candidate/reviewer steps, replay-versus-live labels, and explicit no-approval/benchmark-limit statements.
- Updated setup/index entry points. Historical pre-reboot scripts/results remain labeled historical rather than silently changed into the new reconstruction.

## Observed checks

- **PASS:** 39 relative Markdown link targets exist across the five inspected documents.
- **PASS:** six Bash fenced snippets pass `bash -n`; this is syntax validation, not execution of installation/recovery instructions.
- **PASS:** existing Task 3/7 loopback API health returned `ok`.
- **PASS:** existing API identity returned declared application commit `8e83804448cf251a26735d70c5a66f5b0d26db67`. This is deployment-environment declaration, not attestation or a frontend match.
- **PASS:** existing reviewer doctor returned pinned OpenCode 1.19.3, zero pending local events, and `RECEIPTS_PRESENT_REVIEW_FULL_WORKFLOW_SEPARATELY`. Doctor does not prove success or provider consumption.
- **PASS:** Git diff whitespace check.
- **NOT RUN by Task 8:** install/upgrade/migration execution, new restart/restore drill, new agent/model run, new video/voiceover recording, heavy native/test/build gates, final desktop/mobile browser workflow, human approval or proposal execution.

[Selected check receipts and SHA256 manifest](evidence/task-08-documentation-2026-10-18/sha256-manifest.json) are preserved with this documentation-only checkpoint. The existing application source and Agent 2's comparison environment were not modified.

## Current coordination / next gate

| Work | State at this report |
| --- | --- |
| Tasks 1–2 recovery prerequisites | Completed and recorded in persistent recovery metadata. |
| Tasks 3–5 candidate reconstruction and verification | Completed to pending-review/PASS boundary at application `8e83804`; historical receipts retained. |
| Task 6 comparison setup | Agent 2 reported prepared/validated; not independently re-certified by this documentation pass. |
| Task 7 fresh reviewer | ACCEPTED bounded candidate; worker and reviewer RETURNED; proposal still unapproved/unintegrated. |
| Task 8 documentation/demo preparation | Complete; script prepared, no new recording. |
| Task 9 measured comparison trials | Dispatched to Agent 2 for sequential execution; no result imported into this report. |
| Task 10 final release verification | Pending; do not launch heavy checks/builds during measured trials. Matching UI/API and desktop/mobile evidence still required. |
| Task 11 comparison analysis | Pending actual retained results and limitations; no savings or graph-win claim. |
| Task 12 final report/ZIP | Pending Tasks 7–11; this is not the final repository delivery. |

Next safe action is Task 10 after Agent 2 declares the measured window finished or explicitly paused. Freeze the exact application candidate and documentation identity, verify owned ports/services and matching UI/API, and run affected browser/release gates without replacing a shared deployment. If code changes, repeat affected checks. Task 11 must use the actual trial receipts, not earlier walkthrough numbers. Final packaging must exclude private dumps, agent homes, raw reasoning exports and credentials. No push, merge, approval or deployment is implied.
