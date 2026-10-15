# Product Requirements Document (PRD) — ChronosGraph

> Version: v1.0 | Status: approved | Related brief: `docs/product-brief.md`

## 1. Problem and objective
- **Target user:** Hackathon judges (WeMakeDevs x FalkorDB), AI engineers, and open-source maintainers.
- **Problem:** Autonomous agents lack a connected context layer that combines structural blast radius, bi-temporal decision validity, and self-optimizing procedural memory.
- **Intended outcome:** Win across Track 1, Track 2, Track 3, and Best Blog Post while delivering a drop-in MCP server and viral Side-by-Side Agent Arena.
- **Success measurement:**
  - `GRAPH.COPY` sandbox fork + cleanup completes in `<50ms` with `0` leaked graphs.
  - Repeat bug localization via compiled `(:ProceduralPlaybook)` achieves `>=75%` token reduction and `>=4x` latency speedup vs. cold multi-agent run.
  - 100% of E2E tests in `backend/tests/test_e2e_graph.py` pass against live FalkorDB.

## 2. MVP boundary
**In scope:**
- Multi-tenant FalkorDB graphs (`repo_falkordb_py` and `repo_graphrag_sdk`) with AST nodes (`File`, `Class`, `Function`), GitHub provenance (`Contributor`, `PullRequest`, `Issue`), bi-temporal rules (`Decision`), and memory graphs (`Investigation`, `StateNode`, `AnomalySignature`, `ProceduralPlaybook`).
- REST API (`/api/v1/*`) + FastMCP tools (`server.py`).
- Next.js single-screen **Live Agent Arena & Graph Flight Recorder**.

**Out of scope:**
- External OAuth apps, billing, multi-user authentication, or Neo4j support.

## 3. Users and primary journeys
| Actor | Trigger | Steps | Successful outcome |
|---|---|---|---|
| Judge / Engineer (Track 1) | Selects a PR on `FalkorDB/falkordb-py` and clicks **Run Sandbox Audit** | 1. Backend forks graph via `GRAPH.COPY` 2. Applies AST diff 3. Runs 3-hop blast radius & active decision check 4. Deletes fork | UI shows Blind Agent approving an outage vs. ChronosGraph catching impacted files, violated rules, and top maintainers |
| Judge / Engineer (Track 3) | Queries architectural rule or submits a **Live Policy Override** | 1. Backend runs hybrid vector + Cypher lineage query (`ro_query`) or `CYPHER_SUPERSEDE_DECISION` | Old rule flips to `SUPERSEDED` (red strikethrough); new rule becomes `ACTIVE` (emerald); expert maintainers ranked |
| Judge / Engineer (Track 2) | Runs **Cold Multi-Agent Triage** then **Compiled Playbook Race** | 1. Cold run logs 6 state transitions (including 2 dead ends) across `Scout`, `Historian`, `Verifier` 2. `shortestPath` compiles 2-step playbook 3. Second run executes compiled playbook | Stopwatch & token meter prove >80% token reduction and ~8x speedup with dead-end branches visually pruned |

## 4. Prioritized requirements
| ID | Priority | Requirement (observable behavior) | Acceptance criteria | Notes |
|---|---|---|---|---|
| FR-01 | Must | Multi-Tenant Open-Source Repo Seeding & AST Parsing | Given a clean FalkorDB instance, when `seed_repos.py` runs, then `repo_falkordb_py` and `repo_graphrag_sdk` each contain `>=10` `File` nodes, `>=15` `Function` nodes, `IMPORTS`/`CALLS` edges, `pagerank` scores, `>=5` `Contributor` & `PullRequest` nodes, and `>=4` `SUPERSEDED -> ACTIVE` `Decision` pairs with `vecf32` embeddings. | Includes stdlib `ast_parser.py` |
| FR-02 | Must | Track 1 Counterfactual PR Sandbox via `GRAPH.COPY` | Given `SandboxAuditRequest`, when `POST /api/v1/track1/sandbox-audit` is called, then the system clones the tenant graph via `graph.copy()`, simulates the diff, computes `impacted_files`, `impacted_functions`, `active_decisions_triggered`, `recommended_reviewers`, and `blind_agent_comparison`, and deletes the sandbox (`sandbox_cleaned_up == True`). | Must never leak `sandbox_pr_*` graphs |
| FR-03 | Must | Track 3 Bi-Temporal Contradiction Shield & Maintainer Ranking | Given `BrainQueryRequest` or `PolicyOverrideRequest`, when `/api/v1/track3/ask-brain` or `/api/v1/track3/override-policy` is called, then `ask-brain` executes `ro_query` hybrid vector search returning both `ACTIVE` and `SUPERSEDED` lineage, and `override-policy` atomically marks the previous `ACTIVE` decision as `SUPERSEDED` (`valid_to > 0`) and links the new `ACTIVE` decision via `[:SUPERSEDED]`. | Prevents temporal contradiction |
| FR-04 | Must | Track 2 Multi-Agent Coordination & `shortestPath` Playbook Compiler | Given `InvestigationRunRequest`, when `execution_mode="cold_multi_agent"`, then `Scout` (`ro_query`), `Historian` (`ro_query`), and `Verifier` log `>=5` `StateNode` transitions (including `>=2` `DEAD_END` branches), run `shortestPath` from `START` to `VERIFIED_GOAL`, persist a `(:ProceduralPlaybook)`, and when `execution_mode="compiled_playbook"`, execute the pruned steps with `token_savings_pct >= 75.0`. | Genuine state-transition graph |
| FR-05 | Must | Side-by-Side "Blind Agent vs. ChronosGraph" Arena Telemetry | Given any Track 1, 2, or 3 response, when returned by the API, then `blind_agent_comparison` is populated with concrete baseline failure/latency metrics so the frontend Arena can render side-by-side comparisons. | Scroll-stopper visual hook |
| FR-06 | Must | FastMCP Server Integration (`server.py`) | Given an MCP client (Cursor / Claude Code), when connecting to `backend/app/mcp_server/server.py`, then all 5 tools (`simulate_pr_blast_radius`, `query_bitemporal_decisions`, `record_decision_override`, `find_true_code_owners`, `run_or_compile_playbook`) execute against live FalkorDB. | Track 1 MCP requirement |
| FR-07 | Must | Interactive Next.js Live Arena & Subgraph Flight Recorder (`frontend/`) | Given the running frontend on port 3000/3001, when the user switches tenants (`falkordb-py` / `GraphRAG-SDK`) or triggers Track 1, 2, or 3 actions, then the React Flow canvas renders the returned `GraphSubgraphPayload` with distinct styling for `ACTIVE`, `SUPERSEDED`, `IMPACTED`, `DEAD_END`, and `GOLDEN_PATH` nodes plus the executed OpenCypher drawer. | Dark-mode engineering console |

## 5. Input, output, and failure contracts
- All API inputs/outputs strictly conform to `backend/app/models.py`.
- Empty/unknown file paths return graceful empty collections with a valid fallback overview `GraphSubgraphPayload`, never unhandled 500 tracebacks.
- `ephemeral_sandbox` guarantees `sandbox_graph.delete()` even if a query raises an exception.

## 6. Non-functional requirements
| Area | Requirement | Verification |
|---|---|---|
| Performance | `GRAPH.COPY` clone `<50ms`; Cypher queries `<100ms` | Asserted via `execution_time_ms` and `sandbox_clone_time_ms` in `pytest` |
| Security/Safety | Discovery agents (`Scout`, `Historian`, `ask_brain`) must use `db_manager.ro_query()` | Code inspection & unit test verification |
| Zero-Cost Offline Reliability | Vector indexing & search must work with `FalkorDBManager.embed_text()` even if external LLM API keys are unset | Run `pytest` with empty `.env` |

## 7. Acceptance / release bar
- [ ] All FR-01 through FR-07 implemented without mocks or `# TODO` stubs
- [ ] `pytest -v` in `backend/tests/test_e2e_graph.py` passes 100% against live FalkorDB
- [ ] Frontend builds (`npm run build`) with zero TypeScript errors
