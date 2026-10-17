# Quality batch 02 — UI recovery checkpoint

Branch: `fix/quality-batch-02-ui-recovery`, stacked on batch 01 (`4d6ef9f`).

## Implemented
- Reset stale file/function mode, source, search, history selection and tab on repository switches.
- Separate repository-map read failures from empty results; provide in-place Retry map and loading state.
- Use the configured API endpoint in network error guidance.
- Poll import receipts sequentially. A failed read stops automatic polling without treating the job as failed or submitting a duplicate import.
- Preserve unavailable receipts and offer status retry, repository-catalog reconciliation and explicit tracking dismissal. Dismissal does not cancel a server job or delete a repository.
- Prioritize recovery controls on mobile. Name the dialog and support Escape, focus restoration and request cancellation on unmount.
- Add `npm run test:ui-recovery` regression coverage.

## Verification
- Frontend unit tests: **19 passed**.
- Typecheck: **passed**.
- Production build: **passed**, using the preview API at localhost:8004.
- Targeted browser checks: **12 passed**, six each at 1560px and 390px. Covered repository state reset, map retry, expired receipts, manual status retry, close/focus behavior, dismissal/Escape and catalog reconciliation.
- Browser page errors: **0**. Mutation POST requests during these checks: **0**.
- Map 503 and receipt 404 responses were injected read failures, not actual failed imports. These checks do not prove import completion or real coding-agent integration.
- The isolated UI test server was stopped after testing. Original preview ports 3004/8004 were not restarted or replaced.
- Batch 01 full backend gate: **202 passed** against disposable native FalkorDB copies; no backend changes in this UI checkpoint.

## Four-persona critique and readiness boundary
- Vibe coder: recovery actions are visible and plain-language; real end-to-end agent task flow remains missing.
- Junior developer: outages no longer masquerade as empty repositories; onboarding and readable change entry still need work.
- Senior developer: stale repository state and overlapping polling are addressed; durable receipts, cross-process semantics and broader failure testing remain open.
- Open-source maintainer: saved graphs remain unchanged and regression commands are checked in; history coverage, large-repository navigation and release automation remain incomplete.
- Readiness critique: **NO-GO for full product acceptance**. This was sequential self-review, not five independent agents. Only targeted browser regression checks were run, not the entire legacy browser suite or a full accessibility audit.

No main merge or preview deployment. These fixes are isolated branch checkpoints. See `tasks/assignments/QUALITY-BACKLOG.md` for the remaining work.
