# Quality batch 04 — selected-file change planning and stronger acceptance

Branch: fix/quality-batch-04-change-planning. Stacked on agent discovery/guards 697f498.

## Delivered
- File inspector opens a selected-file change planner rather than a raw JSON-only form.
- A new read-only file-source route returns a complete captured file only after commit/hash checks. Missing, oversized, hash-inconsistent or revision-inconsistent bodies are refused; source is never read from a user-supplied host path.
- Full saved/proposed source, a bounded contiguous changed-region display, and deletion-preview control. No apply/run-command action is exposed.
- HTTP diff preview accepts an optional expected_revision and refuses mismatches before cloning. Existing clients remain compatible.
- Before/after graphs use real reparsed File IMPORTS relationships inside candidate impact scope. Up to 30 nodes/120 edges are shown with truncation disclosed; function-call removals and potentially broken callers remain separately identified. Unchanged import graphs do not imply unchanged calls.
- Candidate files/tests are clickable back into the repository inspector. Recommendations are not presented as executed tests or safe-skip proof.
- Changes is now a separate screen. The old Workbench is mounted only for ownership/activity rather than remaining invisibly active on repository/change views.
- Added owned DB/API/UI native browser harness and documented acceptance oracles in tasks/TESTING.md.

## Verification
- Backend full native suite: **235 passed in 36.77s**, in a disposable database. An earlier full pass also had 235 passing tests.
- Frontend unit tests: **30 passed**, no skips. Typecheck and isolated production build passed.
- Browser acceptance: **30 checks passed** — 14 change-planning, 12 UI-recovery and 4 agent-setup checks, across desktop/mobile. No page errors. The change planner made 10 deliberate preview POST requests only to the isolated API; other checks issued no mutation POSTs. Final acceptance is recorded in quality-batch4/browser/{ui,recovery,setup}/results.json and associated logs. Change planning uses native API responses and an actual Git-ingested fixture; recovery intentionally injects read failures; setup checks copied configuration, not IDE installation.
- Native postconditions verify unchanged fixture source and no sandbox graphs. All owned test servers and containers are stopped by the harness; current preview and source DB are not replaced.
- New API tests cover full-source integrity, wrong-version read/preview rejection, missing/uncaptured/oversized/corrupt source, deletion and deterministic graph bounds. Discovery immutability now compares all fixture node and edge properties, not just file counts.

## Test development observations
The first browser attempt counted graph nodes before the lazy renderer mounted; it now waits for visible graph evidence. The next test assumed repository switching kept the Changes tab, contrary to the existing intentional state-reset contract; it now reopens Changes and verifies an empty editor. A harness retry mistook a closed socket's TIME_WAIT state for a listening server; preflight now allows address reuse and cleanup waits for owned processes. Failure logs were retained. These are test/harness corrections, not claims that those failures were production bugs.

## Four-persona critique / readiness
- Vibe coder: a file-to-impact flow is now usable without constructing JSON. Still lacks a real coding-client task conversation and approval workflow.
- Junior developer: saved/proposed source, directions, broken callers and candidate tests are explicit. Large mobile graphs still require zooming; full-file drafts are not persisted and navigation discards them.
- Senior developer: source identity is checked and previews do not apply; static Python coverage and process-local locks remain limitations. Multi-file, add/rename and unified diffs remain API/legacy tools, not this editor.
- Open-source maintainer: isolated reproducible native verification and explicit coverage are improved; full history/language inventory, large-repository navigation and CI/deployment hardening remain open.
- Readiness critique: bounded Q09 first iteration, not complete product acceptance. Overall NO-GO remains; there was no independent review team, actual IDE demonstration, hosted model call, main merge or video.
