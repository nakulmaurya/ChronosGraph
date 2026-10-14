You are the Execution Coding Agent for **ChronosGraph** (WeMakeDevs x FalkorDB Hackathon — targeting all 3 tracks: Track 1 Connected Data Action, Track 2 Agent Memory & Coordination, and Track 3 Company Brain).

I am working with a **Principal Architect (Brain)** who has already designed the architecture and pre-installed the core FalkorDB database client, OpenCypher query contracts, and Pydantic schemas in this repository.

### STEP 1: READ THE IMMUTABLE CONTRACTS FIRST
Before writing a single line of code, read these pre-installed files in full:
1. `AGENTS.md`
2. `backend/app/models.py`
3. `backend/app/db/client.py`
4. `backend/app/db/queries.py`
5. `backend/app/config.py`

### STEP 2: STRICT ENGINEERING RULES
- **DO NOT** modify or delete the Pydantic model fields in `backend/app/models.py`.
- **DO NOT** hallucinate Neo4j or APOC syntax. Use `db_manager` from `backend/app/db/client.py` and the canonical Cypher queries in `backend/app/db/queries.py`.
- **DO NOT** write mocks, stubs, `pass`, or `# TODO`. Every endpoint must query the live FalkorDB container on `localhost:6379`.
- **PHASE-LOCKED EXECUTION:** You must execute **ONLY Phase 1 and Phase 2** first (`backend/app/ingestion/`, `backend/app/services/`, `backend/app/mcp_server/`, and `backend/app/main.py`), plus the Phase 3 `pytest` verification suite (`backend/tests/test_e2e_graph.py`). Do NOT start Phase 4 (Frontend) until the Principal Architect reviews your Phase 1–3 test output.

### STEP 3: YOUR IMMEDIATE DELIVERABLE (PHASES 1, 2 & 3)
1. Verify `chronos_falkordb` is running on `localhost:6379` (or start it via `docker compose up -d`).
2. Implement `backend/app/ingestion/ast_parser.py` and `backend/app/ingestion/seed_repos.py` to populate `repo_falkordb_py` and `repo_graphrag_sdk` with real files, functions, `IMPORTS`, `CALLS`, PageRank scores, contributors, PRs, open issues, and bi-temporal `(:Decision)` chains (`ACTIVE` vs `SUPERSEDED`).
3. Implement `backend/app/services/sandbox_auditor.py`, `backend/app/services/company_brain.py`, `backend/app/services/memory_compiler.py`, `backend/app/mcp_server/server.py`, and `backend/app/main.py`.
4. Implement and run `backend/tests/test_e2e_graph.py` via `pytest -v`.

### STEP 4: MANDATORY HANDOVER REPORT FORMAT
When Phases 1–3 and `pytest` pass, STOP and output a block titled **`=== PHASE 1-3 ARCHITECT REVIEW REPORT ===`** containing:
1. Exact node and edge counts in `repo_falkordb_py` and `repo_graphrag_sdk`.
2. Full `pytest -v` terminal output.
3. Sample JSON response from `POST /api/v1/track1/sandbox-audit`, `POST /api/v1/track3/override-policy`, and `POST /api/v1/track2/investigate` (both `cold_multi_agent` and `compiled_playbook` modes).

Start now by reading the 5 files listed in Step 1.
