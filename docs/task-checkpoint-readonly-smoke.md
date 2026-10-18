# Current-checkpoint read-only browser smoke

**Prepared and locally contract-tested; real ChronosGraph desktop/mobile gate NOT RUN.** This is a scoped Task 10 helper, not an application feature, provider trial, recording or release certificate. Follow the [verification packet](../tasks/assignments/TASK-10-FINAL-VERIFICATION.md) for manual checks outside its coverage.

## Before running against the product

Wait for Agent 2 to finish or explicitly pause the measured Task 9 window. Obtain an owned, matching production frontend/API without restarting shared services. Confirm exact build/source/proposal bindings and no active writer on this task. No dependency installation or new agent run is performed by this script.

The [example JSON](../frontend/tests/fixtures/task-checkpoint-readonly.example.json) pins the reconstructed Task 3/7 metadata. Port 3015 is a **reserved example, not an assertion that a frontend is running**. Copy it to a private operator configuration, change only intentionally verified service addresses/identities, and retain any failures. Both frontend and API URLs must use trusted loopback HTTP; API ends in `/api/v1`. The frontend URL must include the actual workspace route (`/workbench`). If using tunnels, verify both endpoints resolve to the intended service; do not expose either publicly.

From the repository root, after preflight:

```bash
CHROMIUM_PATH="$(command -v chromium)" node frontend/tests/task-checkpoint-readonly-smoke.mjs \
  --run /absolute/path/checkpoint-readonly.json /absolute/path/new-evidence-directory
```

The parent directory must already exist; the output directory must be new. Missing Chromium, missing dependencies, an incorrect build declaration or a changed snapshot is a failed/blocked check, not permission to install/restart during measured trials. The explicit `--run` and configuration are required; importing the helper or creating this file does not run a product gate.

## Automated coverage

- Desktop 1560×1000 and mobile 390×844; independent browser contexts, service workers blocked.
- Browser routing permits only GET/HEAD/OPTIONS to the configured frontend/API origins; POST/PUT/PATCH/DELETE and other verbs, foreign origins and WebSockets are aborted and recorded as failures. Explicit API readbacks use GET only with redirects/retries disabled. This is a test-runner guard, **not a security sandbox or proof that arbitrary GET handlers never write**.
- Backend identity, selected tenant/revision, immutable plan, exact worker/reviewer assignments, predecessor/run/pack bindings, actual reviewer RETURN text, explicit idle/non-success status and missing-sequence arrays.
- UI full declared UI/API/snapshot identities; resumed task, expanded worker/reviewer reports and raw harness status; existing pending proposal with exact candidate digest and proposal hash.
- Proposal stays PROPOSED with an explicit empty execution list before and after; selected metadata must remain unchanged. No approval, execution, policy override, task creation or resubmission button is clicked.
- Screenshots, browser/page errors, HTTP failures, cancelled requests and page-wide overflow. Normal `net::ERR_ABORTED` cancellations are retained separately, not automatically called product failures.

The generic RETURNED handoff label may still say “review pending”; the test inspects actual reviewer report text instead. It intentionally does not claim a reloaded context-pack panel, new acceptance-test execution, fresh persistence/restart proof, complete policy/source-chain navigation, keyboard/accessibility certification or a fresh model connection. Full source-body/digest provenance remains in the retained candidate receipts, not re-proven by this metadata smoke.

## Evidence and interpretation

`results.json`, per-viewport screenshots (or failure screenshot when possible) and `sha256-manifest.json` are written even after a runtime failure once the new output directory exists. Failed configuration preflight exits before any browser or product request and before an output directory is created. No raw task events/reasoning exports or full source responses are saved.

A successful automated run says `AUTOMATED_PASS_MANUAL_REVIEW_PENDING`. Inspect every screenshot before signing off; update a separate manual-review receipt rather than rewriting the original automated evidence. Preserve failed first attempts. A clean automated result is not approval, human review, end-to-end task success, a full browser suite, build attestation or a benchmark.

## Local runner validation (no VM)

```bash
node --test frontend/tests/task-readonly-contracts.test.mjs
CHROMIUM_PATH="$(command -v chromium)" node frontend/tests/support/check-readonly-guard.mjs
```

The second command launches a temporary loopback HTTP fixture and actual local Chromium. It checks only the network guard (allowed GET, blocked POST/foreign origin/WebSocket), not ChronosGraph endpoints or UI. Its server/browser are closed on exit. The fixture does not change or mock any application endpoint. Keep its PASS separate from Task 10 product verification.
