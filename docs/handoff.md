# ChronosGraph Engineering Handoff

Current contract: v1.2 (approved CR-001 and CR-002)
T-01 merged via PR #1 at 1caa513; T-02 passed 40/40 tests under v1.2 and is accepted
for merge. Next authorized work: T-03, branch build/t03-frontend-arena, after merge.
Stop at T-03 report; no frontend merge or production deployment authorized.

## Run locally
```bash
docker compose up -d
cd backend
pip install -e .
python -m app.ingestion.seed_repos
pytest -v
uvicorn app.main:app --host 127.0.0.1 --port 8000
# separate terminal for MCP:
python -m app.mcp_server.server
# after frontend exists:
cd frontend
npm ci
npm run build
npm run dev -- --port 3001
```

This environment verified native FalkorDB 4.18.3 via embedded package; Docker was
unavailable. No host system changes, paid services, credentials or source caches
are in the repository. For exact runtime versions and evidence see tasks/reports/.

## Scientific scope
5 cold tool actions / 6 states / 2 dead ends -> 3 replay actions / 0 dead ends,
40% fewer tool executions. No LLM calls or token savings benchmark. Labels must
remain visible: DEMO_POLICY_SCENARIO, SIMULATED_PR_DEPENDENCY,
DETERMINISTIC_POLICY_TRIAGE and CONTROLLED_ONE_HOP_BASELINE. Scope guard returns
409 on incompatible policies. Localhost, trusted-user, single-process use only.

Historical v1.1 red-test report remains as evidence, superseded by approved v1.2.
The old archive label 68957811d3a5ba99 was not the actual input ZIP digest; actual
SHA-256 is 24624e61ca49734efa026705c022a0b5fb22b6d57a9eb14fd7e2e6dc4097b785.
