# ChronosGraph Engineering Handoff

## Current boundary
Contract **v1.2**, approved CR-001 and CR-002. T-01 and T-02 are merged. T-03 was
accepted by the Principal Architect and merged via **PR #3** at
`a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7` (includes product commit `25ed5c0` and
acceptance record `c332ea2`). T-04 work lives on **build/t04-release-pack** for final
review; it must not be merged, deployed, externally published or submitted yet.

## Deliverables and ownership
- `README.md`: architecture, one-command local startup, exact track/query/REST/MCP/UI
  judge matrix and historical provenance/telemetry.
- `docs/blog-post-falkordb.md`: complete technical article; 1,200–1,800 words.
- `docs/demo-video-script.md`: exact 2:45 recording plan; no video was recorded.
- `docs/release-checklist.md`: Phase 6 verification, trust boundaries and NOT RUN gates.
- `tasks/reports/T-04.md` and `T-04-evidence/`: builder/integrator evidence.
- `scripts/start-local.sh`, `run-falkordblite.py`, `check-release-hygiene.py`: minimal
  local startup/verification and read-only hygiene helpers. No backend contract changes.

## Run and verify
```bash
# New ephemeral local Docker database plus API/UI (Docker path NOT RUN here):
bash scripts/start-local.sh
# Compatible native wheel alternative (platform-dependent):
bash scripts/start-local.sh --db native
# Verification against an explicitly trusted existing FalkorDB:
bash scripts/start-local.sh --db existing --verify-only
# Individual frontend commands; package scripts already select port 3001:
(cd frontend && npm test && npm run typecheck && npm run build)
(cd frontend && npm run dev)
# Separate MCP stdio process after installing backend and seeding FalkorDB:
(cd backend && ../.venv/bin/python -m app.mcp_server.server)
```
Python 3.11+, Node 24+, Bash/npm/network required. Use `VENV_DIR` for an installed
alternative environment. UI is `http://127.0.0.1:3001`; API `/health` is on port 8000.
The MCP modal is a configuration template, not an installed IDE integration.

This workspace verified native FalkorDB **4.18.3** using falkordblite **0.10.0**,
Redis **8.6.2**, and a process-local compatibility loader. No Docker binary exists
here. The native helper passed on isolated port 6381; existing-DB verification
passed 40 backend tests, 7 frontend tests, typecheck and production build. The
complete fresh evidence, including live-smoke retry history, is in the T-04 report.

## Scientific scope and known limits
Historical source/public-GitHub layers are **458/669** and **4,252/6,251** nodes/edges.
Each tenant initially adds **8/20** fictional demo policy nodes/edges. Live counts
also include persisted investigations/playbooks. Code revisions are pinned, but
cached public GitHub metadata is an ingestion-time snapshot, not revision-pinned.

Cold triage: **6 states / 5 tool actions / 2 dead ends**; replay: **3 actions / 0 dead
ends**, hence **40% fewer tool executions**. Scout/Historian/Verifier are deterministic
roles. No external model is called. Zero tokens/percentages are unmeasured sentinels,
not a token-savings benchmark. Wall-clock speedup can be below 1×. Vectors are lexical
hashes. Synthetic clone dependencies do not execute a diff or prove an outage.

Keep `DEMO_POLICY_SCENARIO`, `SIMULATED_PR_DEPENDENCY`, `DETERMINISTIC_POLICY_TRIAGE`
and `CONTROLLED_ONE_HOP_BASELINE` visible. Confirmed overrides retain superseded
history and invalidate old playbooks; fresh cold triage is required. Incompatible
file/scope policies return HTTP 409. This is a localhost trusted-user single-process
demo with no production authentication or safety guarantee. See release checklist.

## Final architect review
Inspect README, full article, recording script, fresh checks and hygiene scope.
Approve or request changes to T-04 explicitly. Do not treat builder readiness as
architect acceptance. User authorization currently stops at publishing the review
branch, not merging it or publishing external content.

Historical v1.1 red-test report remains evidence, superseded by approved v1.2.
The old archive label `68957811d3a5ba99` was not the actual input ZIP digest; actual
SHA-256: `24624e61ca49734efa026705c022a0b5fb22b6d57a9eb14fd7e2e6dc4097b785`.
