# CHRONOSGRAPH — MASTER ENGINEERING CONTRACT (AGENTS.md)

## 0. IMMUTABLE RULES FOR THE CODING AGENT
1. **FALKORDB ONLY (NO NEO4J / NO APOC):** Never import `neo4j` or call `apoc.*`. `backend/app/db/client.py` and `backend/app/db/queries.py` are already pre-written and verified. Use them directly.
2. **NO MOCKS OR STUBS:** Every service in `backend/app/services/` and every endpoint in `backend/app/main.py` must execute real Cypher queries against the live FalkorDB container on `localhost:6379`.
3. **LOCKED CONTRACTS:** Do not break or rename fields in `backend/app/models.py`. Both the E2E pytest suite and the Next.js frontend depend on those exact Pydantic models.
4. **PHASE-GATED EXECUTION:** Complete one phase at a time. Run the verification command for that phase and report the exact output back to the Principal Architect (the user) before moving to the next phase.

## 1. WHAT IS PRE-INSTALLED IN THIS REPOSITORY
- `docker-compose.yml` (FalkorDB on 6379 + Browser UI on 3000)
- `backend/pyproject.toml`
- `backend/app/config.py`
- `backend/app/models.py` (Locked Pydantic contracts for Track 1, Track 2, Track 3, and React Flow subgraphs)
- `backend/app/db/client.py` (Singleton `db_manager` with `query`, `ro_query`, `ephemeral_sandbox` via `graph.copy()`, `ensure_indexes`, and `embed_text`)
- `backend/app/db/queries.py` (All 5 canonical FalkorDB OpenCypher queries)

## 2. REMAINING MODULES YOU MUST IMPLEMENT BY PHASE

### PHASE 1: Realistic Open-Source Repo Seeder (`backend/app/ingestion/`)
Create `backend/app/ingestion/__init__.py` and `backend/app/ingestion/seed_repos.py`:
- Must populate two isolated FalkorDB multigraphs: `repo_falkordb_py` (modeling `FalkorDB/falkordb-py`) and `repo_graphrag_sdk` (modeling `FalkorDB/GraphRAG-SDK`).
- Must also include an AST parser helper (`backend/app/ingestion/ast_parser.py`) using Python stdlib `ast` that can parse any local/downloaded `.py` file into `(:File)-[:DEFINES]->(:Class|:Function)`, `[:IMPORTS]`, and `[:CALLS]`.
- In `seed_repos.py`:
  1. Call `db_manager.ensure_indexes(graph_name)`.
  2. Insert realistic, high-density nodes based on actual `FalkorDB/falkordb-py` structure (`falkordb/graph.py`, `falkordb/falkordb.py`, `falkordb/node.py`, `falkordb/edge.py`, `falkordb/query_result.py`, `falkordb/asyncio/graph.py`, `falkordb/asyncio/falkordb.py`, `tests/test_graph.py`, `tests/test_async.py`, etc.) and `FalkorDB/GraphRAG-SDK` (`graphrag_sdk/kg.py`, `graphrag_sdk/ontology.py`, `graphrag_sdk/orchestrator.py`, `graphrag_sdk/agents/kg_agent.py`, etc.).
  3. Create real `(:Function)` nodes (`Graph.query`, `Graph.ro_query`, `Graph.copy`, `Graph.delete`, `FalkorDB.select_graph`, `AsyncGraph.query`, `QueryResult._parse_results`, etc.) with `[:CALLS]` edges and `[:IMPORTS]` edges between files.
  4. Run `CALL algo.pageRank('File', 'IMPORTS')` (with fallback calculation if procedure signature varies) and store `pagerank` on every `(:File)`.
  5. Insert real `(:Contributor)` handles (`gkorland`, `roi-lipman`, `swilly22`, `avi-avni`, `falkordb-bot`), real `(:PullRequest)` nodes (e.g., PR #42 "Add async connection pool lock", PR #58 "Enforce vecf32 explicit cast on vector queries", PR #64 "Implement GRAPH.COPY sandbox wrapper", PR #71 "Refactor QueryResult header parsing"), and open `(:Issue)` nodes.
  6. Insert at least 6 bi-temporal `(:Decision)` chains per repo where an older `(:Decision {status: 'SUPERSEDED'})` is linked via `<-[:SUPERSEDED]-(:Decision {status: 'ACTIVE'})` and `[:GOVERNS]->(:File)` with embeddings wrapped in `vecf32($emb)`.

### PHASE 2: Track 1, Track 2 & Track 3 Services + FastMCP + FastAPI (`backend/app/services/`, `mcp_server/`, `main.py`)
1. `backend/app/services/sandbox_auditor.py` (Track 1):
   - Uses `with db_manager.ephemeral_sandbox(req.tenant_graph) as (sandbox_graph, sandbox_name):`
   - Simulates PR modifications inside `sandbox_graph`, runs `CYPHER_BLAST_RADIUS_AUDIT` and `CYPHER_FILE_OWNERSHIP_AND_LINEAGE`, builds the `GraphSubgraphPayload` (`VisualNode` & `VisualEdge` lists), verifies `sandbox_name not in db_manager.list_tenant_graphs()` after context exit, and returns `SandboxAuditResponse`.
2. `backend/app/services/company_brain.py` (Track 3):
   - `ask_brain(req: BrainQueryRequest)`: Runs `CYPHER_HYBRID_VECTOR_DECISION_SEARCH` via `db_manager.ro_query` and returns active decisions, superseded decisions, top experts, and a rich `GraphSubgraphPayload` where superseded decisions have `status="SUPERSEDED"` and active ones have `status="ACTIVE"`.
   - `override_policy(req: PolicyOverrideRequest)`: Runs `CYPHER_SUPERSEDE_DECISION` to mark the existing active decision on `target_file_path` as `SUPERSEDED`, inserts the new `ACTIVE` decision, and returns `PolicyLineageResponse` with the updated bi-temporal lineage subgraph.
3. `backend/app/services/memory_compiler.py` (Track 2):
   - `run_investigation(req: InvestigationRunRequest)`:
   - In `cold_multi_agent` mode: Creates an `(:Investigation)` node and logs a realistic 6-node branching `(:StateNode)` trajectory across `Scout` (using `ro_query`), `Historian` (using `ro_query`), and `Verifier`—including 2 explicit `DEAD_END` state branches (e.g., inspecting unrelated sync parser files) and 1 valid 3-step chain ending at `VERIFIED_GOAL`.
   - Runs `CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH` (`shortestPath`) to prune the `DEAD_END` branches, persists the golden path as a `(:ProceduralPlaybook)` linked to an `(:AnomalySignature)`, and returns `InvestigationRunResponse` where dead-end nodes have `status="DEAD_END"` and golden path nodes have `status="GOLDEN_PATH"`.
   - In `compiled_playbook` mode: Queries the `(:AnomalySignature)` vector index, retrieves the compiled `(:ProceduralPlaybook)`, executes only the 2 pruned steps in ~15% of the tokens/time, and returns the ROI comparison metrics.
4. `backend/app/mcp_server/server.py`:
   - Implements the 5 FastMCP tools wrapping the services above.
5. `backend/app/main.py`:
   - FastAPI app with CORS enabled (`*`), health/tenants endpoints, all `/api/v1/*` endpoints, and auto-seeding on startup if `repo_falkordb_py` is empty.

### PHASE 3: Automated E2E Pytest Verification (`backend/tests/test_e2e_graph.py`)
Write comprehensive `pytest` tests verifying:
1. Both `repo_falkordb_py` and `repo_graphrag_sdk` graphs exist and have files, functions, PRs, and `SUPERSEDED` decision chains.
2. Track 1 `/api/v1/track1/sandbox-audit` clones the graph, returns impacted downstream files/functions and recommended reviewers, and leaves zero orphaned `sandbox_pr_*` graphs in FalkorDB.
3. Track 3 `/api/v1/track3/override-policy` supersedes an existing active decision and preserves the historical chain.
4. Track 2 `/api/v1/track2/investigate` runs `cold_multi_agent`, prunes dead-end states via `shortestPath` into a `ProceduralPlaybook`, and then runs `compiled_playbook` with greater than 75% token reduction.

### PHASE 4: Next.js "Graph Flight Recorder" Frontend (`frontend/`)
Build a responsive, dark-mode (`slate-950`) single-screen engineering console using Next.js, TailwindCSS, `@xyflow/react` (React Flow), and `lucide-react`:
- Top bar: Tenant switcher (`FalkorDB/falkordb-py` | `FalkorDB/GraphRAG-SDK`), Track selector tabs (Track 1 Sandbox | Track 2 Memory Compiler | Track 3 Company Brain), live query latency badge, and MCP Config modal.
- Left panel: Context-sensitive action controls for the active Track (PR dropdown & Sandbox button for Track 1; Cold vs. Compiled Playbook runner for Track 2; Semantic Brain search & Live Policy Override form for Track 3).
- Center panel: Custom React Flow canvas rendering `subgraph.nodes` and `subgraph.edges` with color-coded badges (`SUPERSEDED` with red strikethrough, `ACTIVE` in emerald, `IMPACTED` in amber, `DEAD_END` in muted rose, `GOLDEN_PATH` with animated cyan edges) + collapsible bottom drawer showing `subgraph.cypher_executed`.
- Right panel: Recommended maintainer reviewers with GitHub links, bi-temporal decision lineage cards, and the Track 2 Cold vs. Compiled Token/Latency ROI meter.
