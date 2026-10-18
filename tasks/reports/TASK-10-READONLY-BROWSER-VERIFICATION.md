# Task 10 — observed read-only browser verification

**PASS for the scoped current-checkpoint read-only workflow; not a complete release, integration, security or deployment certification.** Actual local Chromium 153.0.8010.12 inspected the existing Task 3/7 VM state through an owned loopback tunnel. No new agent/model trial, task creation, policy override, proposal submission, approval or execution occurred.

## Source and service boundaries

- Application: `8e83804448cf251a26735d70c5a66f5b0d26db67`, separately checked-out local Task 5 worktree; tracked application source stayed unchanged. Existing dependency symlinks are untracked local prerequisites, not archive content.
- Fresh local production frontend build: `NEXT_PUBLIC_CHRONOSGRAPH_BUILD_COMMIT=8e83804448cf251a26735d70c5a66f5b0d26db67`, API base `http://127.0.0.1:18015/api/v1`; owned frontend loopback 3004. Tunnel forwards only to existing VM API8015. No VM service was rebuilt/restarted, and the reserved VM frontend3015 was not assumed to exist.
- UI/API declarations matched the full application commit. Selected owned-synthetic fixture revision was `fabe543f8f010433a58f93d8cb7698f77e39e6b0`. Matching declarations are not cryptographic build attestation.
- Candidate remains separate/unintegrated: digest `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982` and proposal `prop_64084206f032410a923823abd797e75b`. Its complete content/reviewer verification remains in Task 7, not recreated by a UI check.

## Observed checks

| Check | Result |
| --- | --- |
| Fresh owned frontend production build | PASS at the application source above; no dependency installation. |
| Live task/plan/pack/assignment/run bindings | PASS in initial, per-viewport before/after and final API readbacks. WORKER and REVIEWER both RETURNED; reviewer RETURN report says bounded verdict ACCEPTED. |
| Desktop 1560×1000 / mobile 390×844 | PASS scoped assertions and inspected screenshots: resumed immutable plan, handoffs, raw non-success status and exact pending proposal identities. |
| Honest run/telemetry status | `IDLE_NOT_SUCCESS` and partial end-to-end completeness remain visible; no missing sequence receipts observed in the checked run metadata. Not task-success proof. |
| Proposal before/after/final | PROPOSED, exact hash/digest unchanged, explicit zero execution records. No approval or execution click. |
| Browser safety/network | Zero blocked mutation/foreign-origin/WebSocket requests in successful runs; zero page/console errors and HTTP failures in observed runs. Normal cancelled requests retained separately. |
| Read-only organizational chain | GET `context/owners` rendered owned-synthetic ACTIVE ADR-002, SUPERSEDED ADR-001, INC-007, pinned source revision/hashes and Compatibility Platform declaration, separately expanded at both widths. No policy-query POST or override. |
| Keyboard modal | Focused Connect agent → Enter opens modal; Escape closes and restores opener focus at both widths. Not a complete accessibility audit or actual MCP installation. |
| Reviewer report scrollability | Actual accepted-verdict line scrolled into view and inspected at both widths; JSON panes are independently scrollable. |
| Local frontend unit regressions after runner correction | 44 passed, zero failed. This is the local test tree including new runner contracts, not a new native VM suite. |
| Evidence integrity | Original attempt manifests preserved; separate manual-review receipt and outer SHA256 manifest added without rewriting automated results. |

## Failures and corrections retained

1. **First desktop smoke failed:** the runner checked the full snapshot declaration before asynchronous snapshot metadata loaded. UI/API build declarations had loaded; no console/network error was observed. Added an explicit wait for the full snapshot title attribute, then ran a new output directory. No product source was changed to satisfy the assertion.
2. **Second main smoke passed** at both widths.
3. **First supplemental run passed assertions**, but mobile JSON scrolled to its bottom did not visibly include the verdict line in that screenshot. Added text-range-based inner scrolling and retained a second supplemental run with the verdict visibly captured. This was evidence positioning, not a candidate or application correction.

[All selected receipts, original failed attempt, build/unit logs and screenshots](evidence/task-10-readonly-browser-verification/sha256-manifest.json) are preserved. [Manual screenshot review](evidence/task-10-readonly-browser-verification/manual-review.json) records exactly inspected images, limitations and attempt history.

## Known limitations / remaining release work

- The reviewer summary uses generic “Candidate returned; review pending” wording despite an accepted RETURN report. Inspect the actual report; do not infer another rejection or human approval. Verbose scrollable JSON is not a dedicated verdict summary.
- Task resumption does not automatically restore the context-pack panel or file target. API/saved bindings were checked separately. The Ownership pane's local target input is not automatically the separate policy-override target; no override was attempted.
- Proposal citation anchors were not verified as cross-tab navigation; the source chain was inspected explicitly in Ownership. No forced service-failure, restart/restore, new migration, physical-device, alternate-browser or full accessibility exercise was performed.
- Mutating diff-preview/lifecycle suites and tests requiring approval/execution were intentionally not run against this pending candidate. Earlier backend/plugin/candidate receipts retain their own scopes; they are not newly rerun or summed here.
- The bounded candidate is not integrated. Task 9 evidence was independently checksum/scope-verified and fetched to a review ref only; its 59-file evidence commit was **not merged** by this checkpoint. Task 11 evidence/report integration and Task 12 final source packaging remain separate work. No graph advantage conclusion is manufactured by these UI checks.
- No new recording/voiceover, final ZIP, merge, push, external publication, proposal decision or deployment occurred.

See the [verification packet](../assignments/TASK-10-FINAL-VERIFICATION.md) and [runner instructions](../../docs/task-checkpoint-readonly-smoke.md). A later application change requires affected regression/build/browser checks again; these observations cannot certify different source or a shared deployed preview.
