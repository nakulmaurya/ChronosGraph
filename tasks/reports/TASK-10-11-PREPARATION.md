# Tasks 10–11 preparation — no final gate or comparison result

**Prepared locally while Agent 2 owns the Task 9 measured window.** No VM command, service restart, database call, dependency installation or provider run was made by this preparation pass. Application code remains unchanged.

## Prepared

- [Task 10 verification packet](../assignments/TASK-10-FINAL-VERIFICATION.md): exact source/candidate boundaries, matching UI/API, desktop/mobile, explicit worker/reviewer reports, read-only pending proposal checks, and isolated-versus-mutating browser-suite distinctions. All new browser gates remain **NOT RUN**.
- [Task 11 analysis template](templates/TASK-11-COMPARISON-ANALYSIS.md): four pending trial rows, actual correctness/manual review before efficiency, explicit tool counting, missingness, provider/cache/retry usage, indexing overhead and shared-resource timing caveats. **No benchmark values or outcome were filled.**
- `scripts/check-source-package.py`: offline audit of an exact committed Git tree. Reports file hashes/sizes, forbidden private/cache paths, heuristic credential matches as paths/kinds only, unsupported symlinks/submodules and evidence-manifest mismatches. It scans all blob bytes, not only text. It does not contact a DB, scan Git history, create a ZIP, or approve a release.
- Current-checkpoint entry in the existing release checklist; historical published results preserved.

## Observed local checks

- **PASS:** seven isolated fixture tests cover clean evidence, forbidden paths/redaction, dirty/untracked exclusion, missing/mismatched hashes, manifest path traversal, symlinks and binary-content credential-pattern scanning.
- **PASS:** seven relative documentation targets exist; Git diff whitespace check passed.
- **PASS, scoped:** committed source `5e0ad30a5b45b06890a6793eaee21ed5e2443598`: 629 tracked entries, 40 referenced evidence hashes checked, no findings from the implemented path/credential heuristics. The working tree was intentionally dirty with these new preparation files; they were not included in that base-commit audit. This is not a final-archive scan or proof of absent secrets.

[Selected receipts and checksums](evidence/task-10-11-preparation/sha256-manifest.json) retain this scope. A final source archive must be generated from a separately selected exact commit (no `.git`, private DB dumps, agent homes/raw exports or keys), then independently inspected against its inventory. Ignored/untracked files are never included merely because they exist beside the repository. Heuristic scans do not replace manual review.

## Remaining gates

1. Agent 2 completes or explicitly pauses Task 9 and hands off retained trial evidence.
2. Run Task 10 in an owned quiet environment; resolve any failures without merging or approving the pending candidate implicitly.
3. Perform Task 11 from actual receipts, preserving failed and inconclusive observations.
4. Task 12 exact-source ZIP and final report after required gates. No final ZIP, publication, deployment, merge, approval, execution or new recording occurred here.

## Follow-up: read-only runner and external-review packet

Prepared `frontend/tests/task-checkpoint-readonly-smoke.mjs` with explicit opt-in,
loopback-only configuration, mutation/foreign-origin/WebSocket blocking, guarded
metadata/UI assertions, before/after pending-proposal checks and evidence capture.
[Instructions and exact limitations](../../docs/task-checkpoint-readonly-smoke.md)
include a configuration bound to selected retained Task 3/7 receipts. The example
frontend port remains unverified, and the real product gate remains **NOT RUN**.

Fresh **local** frontend unit run: **44 passed**, including seven new smoke-runner
contract tests. Actual local Chromium 153.0.8010.12 passed the network-guard fixture:
GET allowed, POST/foreign-origin/WebSocket blocked before reaching the fixture.
This is not a ChronosGraph browser test. The first fixture attempt failed because
`/usr/bin/chromium` was absent; the explicit installed `/usr/local/bin/chromium`
override resolved it without installation. Failure and correction are retained.

Fourteen relative documentation targets and twelve example identity bindings
against selected stored receipts were checked. No live VM state was rechecked.
[Follow-up evidence](evidence/task-10-readonly-runner-preparation/sha256-manifest.json)
preserves the actual local checks. Earlier 37-test application checkpoint evidence
remains unchanged; 44 is the new local test-tree total, not a new VM/release gate.

The [external-review brief](../reviews/EXTERNAL-REVIEW-BRIEF.md) explains product
positioning, exact source/candidate boundaries, evidence order, known limitations
and prioritized reviewer questions. The existing demo script now includes an
optional comparison-workflow narration outline with results pending. No new video,
voiceover, ZIP, model run, proposal decision, deployment or source integration
occurred. All work in this follow-up stayed local; Agent 2's VM was not contacted.
