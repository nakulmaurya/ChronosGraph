# AGENTS.md — ChronosGraph Project Rules & Multi-Agent Contract

## Project purpose
**ChronosGraph** is a speculative `GRAPH.COPY` PR blast-radius gatekeeper, bi-temporal architectural contradiction shield, and `shortestPath` JIT procedural memory compiler built on **FalkorDB** (`falkordb/falkordb:latest`), benchmarked on real open-source repositories (`FalkorDB/falkordb-py` and `FalkorDB/GraphRAG-SDK`).

## Repo map
- Planning & Specs: `docs/planning-manifest.md`, `docs/product-brief.md`, `docs/prd.md`, `docs/architecture.md`, `docs/design.md`, `docs/handoff.md`
- Task Queue & Packets: `tasks/tasks.md`, `tasks/assignments/T-01.md`, `tasks/assignments/T-02.md`, `tasks/assignments/T-03.md`
- Pre-Installed FalkorDB Layer (DO NOT BREAK): `backend/app/db/client.py`, `backend/app/db/queries.py`, `backend/app/models.py`, `backend/app/config.py`
- Backend App Entry: `backend/app/main.py`
- E2E Tests: `backend/tests/test_e2e_graph.py`
- Frontend App: `frontend/`

## Local commands
- Start FalkorDB: `docker compose up -d`
- Install Backend: `cd backend && pip install -e .`
- Seed Open-Source Graphs: `cd backend && python -m app.ingestion.seed_repos`
- Run Backend Server: `cd backend && uvicorn app.main:app --reload --port 8000`
- Run E2E Tests: `cd backend && pytest -v`
- Install & Build Frontend: `cd frontend && npm install && npm run build`
- Run Frontend Dev: `cd frontend && npm run dev -- -p 3001`

## Non-Negotiable FalkorDB Coding Conventions
1. **NO NEO4J OR APOC:** Never import `neo4j` or call `apoc.*`. Always use `db_manager` from `backend/app/db/client.py` and the canonical OpenCypher queries in `backend/app/db/queries.py`.
2. **MANDATORY `vecf32()` WRAPPING:** Every vector write or query in FalkorDB MUST wrap the float list in `vecf32($embedding)`.
3. **READ-ONLY SAFETY:** Discovery agents (`Scout`, `Historian`) and read-only brain queries MUST call `db_manager.ro_query(...)` (`GRAPH.RO_QUERY`).
4. **EPHEMERAL SANDBOX CLEANUP:** Counterfactual PR audits MUST use `with db_manager.ephemeral_sandbox(tenant_graph) as (sandbox_graph, sandbox_name, clone_ms):` so `GRAPH.COPY` clones are always deleted via `GRAPH.DELETE`.
5. **ZERO STUBS OR MOCKS:** Never return hardcoded dummy JSON from endpoints. Every route must query FalkorDB on `localhost:6379`.

## Cross-agent handoff and authority (`vibe-engineering` protocol)
- **Brain / Planner & Reviewer:** Gemini (via User Bridge). Owns `docs/*`, `tasks/tasks.md`, and `tasks/assignments/*`.
- **Bridge / Repo Owner:** Nakul (`GitHub Canvas`).
- **Builder / Executor:** Notion Coding Agent. Reads `docs/planning-manifest.md` and executes `tasks/assignments/T-01.md` -> `T-02.md` -> `T-03.md` sequentially.
- After completing each task `T-xx`, the Builder writes `tasks/reports/T-xx.md` with actual terminal outputs (`PASS` / `FAIL` / `NOT RUN`) and commits to GitHub for Brain review.
