# Task 10 — final verification packet (PREPARED, NOT RUN)

This is the next gate, not a new browser/test receipt. Start only after Agent 2 explicitly finishes or pauses its measured Task 9 window. Do not stop, build, import, restart services or run parallel agent workloads during that window.

## Freeze and authority

- [ ] Record exact application commit, documentation commit, branch and dirty state in a new dated receipt. Application last verified at `8e83804448cf251a26735d70c5a66f5b0d26db67`; documentation preparation began at `5e0ad30`. Later documentation commits are not application changes.
- [ ] Record whether checking the base application or a separately integrated candidate. The Task 3/7 candidate is **not integrated**. No merge or source modification is authorized by this checklist; if integration is requested later, freeze the new source and rerun affected gates.
- [ ] Bind candidate `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`, fixture revision `fabe543f8f010433a58f93d8cb7698f77e39e6b0`, and proposal `prop_64084206f032410a923823abd797e75b` separately from the application revision. Do not substitute a proposal hash for a full-worktree digest.
- [ ] Confirm working root from `~/chronos-work/LAST_PREREQUISITES`; inspect existing owners/PIDs/ports before starting anything. Task 3/7 API last used loopback 8015; frontend 3015 is reserved, **not a verified running/matching frontend**. Never kill by broad process name or reuse Agent 2 ports.
- [ ] Capture backend `/health` and `/api/v1/release/identity`, plus UI build identity and the selected snapshot revision. Matching declarations are not build attestation. Missing/mismatched identities block a matching-build claim.
- [ ] Use an owned loopback frontend/API and a trusted local client only. This is not an authenticated multi-tenant production deployment.

## Read-only current workflow: desktop and mobile

Run Chromium at desktop 1560×1000 and mobile 390×844; record actual dimensions, runtime versions, URLs, timestamps, console errors and failed requests. Screenshots must be inspected, not merely generated. No physical-device/browser/accessibility certification is implied.

- [ ] Open the owned-synthetic organization fixture, not the public comparison tenant. Show labels distinguishing synthetic policy/incident data, selected revision, current ADR-002 and historical ADR-001.
- [ ] Navigate Agent activity → task runtime; enter resume task ID `task_ef1809a9462f0b7be50e176e6b4d1db6`. The ID field polls; there is no separate Resume button. Do not create/launch a new task for this read-only check.
- [ ] Inspect immutable current plan and explicit worker handoffs: worker `assignment_37c364ea14474ac1a9b139bc0c5aa0d8` and reviewer `assignment_a04c4c6ab9f64ba98d50c159e3db4996`, both RETURNED. Verify actual review report says ACCEPTED for the bounded candidate, not product-wide approval.
- [ ] Check raw `IDLE_NOT_SUCCESS` / partial completeness labels, usage categories and retained events remain visible; IDLE must never be presented as task success or zero cost.
- [ ] Check reviewer return/candidate digest against selected receipts. Generic RETURNED UI text may say “Candidate returned; review pending” even for a returned reviewer. Record this wording limitation; inspect the report, do not infer a new rejection or silently relabel it.
- [ ] Verify scope/pack identity using API and saved receipts if the resumed UI does not reload the context-pack panel. Missing resumed pack display must be reported rather than claimed as covered.
- [ ] Open Changes and inspect the exact pending proposal read-only. Confirm status PROPOSED and zero execution records before and after. **Do not click approval, execution or policy override controls.**
- [ ] Inspect current decision → incident → declared team evidence; expand historical decision separately. Do not interpret CODEOWNERS or pinned source chains as authorization.
- [ ] At mobile width, inspect horizontal overflow, wrapping of IDs, usable controls, expanded evidence and navigation. Check keyboard focus and accessible labels on desktop; no formal accessibility sign-off.
- [ ] If a request fails, preserve the old result with the actual error and distinguish stale display from new success. Do not break shared services to provoke a failure.

## Prepared read-only automation

Use the [read-only smoke helper instructions](../../docs/task-checkpoint-readonly-smoke.md)
only after the measured window is clear. Its example configuration pins this task;
copy/verify owned URLs before explicit `--run`. Authoring/contract-testing the runner
is not a Task 10 product PASS. Automated success still requires inspected screenshots
and the remaining manual evidence/keyboard/policy-chain checks above.

## Other browser suites — separate scopes

| Suite | Scope / preconditions | Gate meaning |
| --- | --- | --- |
| `frontend/tests/agent-setup-smoke.mjs` | Read-only setup modal and clipboard/config rendering; inspect configured frontend/API/output variables first. | Not installation, MCP connectivity or a successful task. |
| `frontend/tests/change-planning-smoke.mjs` | POST diff preview; only disposable `repo_test_` tenant, frozen fixture, dedicated service ports. | Mutating preview regression, not approval/execution or current Task 3 proof. |
| `scripts/verify-final-lifecycle-ui.sh` | Builds/restarts isolated services, clones graphs, permits execution within its own fixture roots. Requires quiet window and separately reviewed scope. | Do not run against the live pending candidate or a shared DB. Not implicitly authorized approval of Task 3. |
| Current task-runtime checks above | Existing Task 3/7 state, GET-only observation, owned matching frontend/API. | These are new required gates; historical browser suites do not automatically cover them. |

Use the scripts' actual environment-variable names after reading them; this packet intentionally does not guess launch commands or reuse historical default ports.

## Regression and evidence gates

- [ ] Reconcile Task 4 (403 backend), Task 5 (19 plugin / 37 frontend, types/build) and Task 7 (39 bounded candidate checks) with their exact sources/scopes. These are retained receipts, not rerun totals and must not be summed into one invented suite.
- [ ] If application/plugin/frontend source changes, rerun affected tests/types/build in isolated owned environments. Preserve first failure and correction; do not run a whole backend suite on a shared durable DB.
- [ ] Save sanitized browser screenshots, console/network results, task/reviewer/proposal readbacks, source/build identities, check commands and exit codes, plus a SHA256 manifest. No raw reasoning exports, auth data or private DB dumps.
- [ ] Record each item PASS / FAIL / NOT_RUN / BLOCKED with evidence location. Missing tests are not zero failures. Final readiness remains pending until required gates pass.

Task 11 depends on Task 9 actual receipts. Task 12 depends on Tasks 7–11 and an explicit frozen source-package audit. This packet authorizes neither publication, deployment, merge, proposal approval nor execution.
