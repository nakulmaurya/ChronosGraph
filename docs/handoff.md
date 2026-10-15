# Engineering Handoff — ChronosGraph

> Last updated: 2026-10-15 | Baseline version: `v1.0 (zip-sha256:68957811d3a5ba99)` | Scope: Hackathon 3-Track MVP

## Working state
- **What is pre-installed and ready today:**
  - `docker-compose.yml` (`falkordb/falkordb:latest` on 6379 + Browser on 3000)
  - `backend/pyproject.toml`, `backend/app/config.py`, `backend/app/models.py`
  - `backend/app/db/client.py` (`FalkorDBManager` singleton with `query`, `ro_query`, `ephemeral_sandbox`, `ensure_indexes`, `embed_text`)
  - `backend/app/db/queries.py` (All 5 canonical FalkorDB OpenCypher queries)
  - Complete `vibe-engineering` planning pack (`docs/*`, `tasks/*`, `AGENTS.md`)
- **What is assigned to the Builder Agent now:**
  - `T-01` (`tasks/assignments/T-01.md`): AST Parser & Open-Source Repo Seeder (`FalkorDB/falkordb-py` & `FalkorDB/GraphRAG-SDK`)
  - `T-02` (`tasks/assignments/T-02.md`): Track 1, 2 & 3 Services, FastMCP, FastAPI & E2E Pytest
  - `T-03` (`tasks/assignments/T-03.md`): Next.js Live Agent Arena & Flight Recorder UI

## Setup and run
- Start FalkorDB: `docker compose up -d`
- Install backend dependencies: `cd backend && pip install -e .`
- Seed open-source graphs (after T-01): `cd backend && python -m app.ingestion.seed_repos`
- Run E2E tests (after T-02): `cd backend && pytest -v`
- Start backend API (after T-02): `cd backend && uvicorn app.main:app --reload --port 8000`
- Build & run frontend (after T-03): `cd frontend && npm install && npm run build && npm run dev -- -p 3001`

## Cross-agent transfer
- **Source agent:** Principal Architect (Brain / Gemini)
- **Target agent:** Builder (Notion Coding Agent) bridged via GitHub by Nakul
- **Baseline archive checksum:** `zip-sha256:68957811d3a5ba99`
- **First executable assignment packet:** `tasks/assignments/T-01.md` (proceeding sequentially to `T-02.md` after verification)

## Next exact task
`T-01` — Implement `backend/app/ingestion/ast_parser.py` and `backend/app/ingestion/seed_repos.py`, run the seeder against `localhost:6379`, and record the output in `tasks/reports/T-01.md`.
