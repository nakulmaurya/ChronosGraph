# Implementation Plan — ChronosGraph

> Source of truth: PRD `docs/prd.md`, Architecture `docs/architecture.md`. Updated: 2026-10-15.
> Multi-agent statuses: TODO, ASSIGNED, IN_PROGRESS, READY_FOR_REVIEW, CHANGES_REQUESTED, BLOCKED, DONE.

## Milestones (vertical slices)
| Milestone | User-visible proof | Dependencies | Status |
|---|---|---|---|
| M1 — Open-Source Multigraph Seeder & AST Engine | `repo_falkordb_py` & `repo_graphrag_sdk` populated with AST, PRs, Contributors & `SUPERSEDED` Decisions | Baseline DB client | DONE |
| M2 — 3-Track Core Services, FastMCP & E2E Pytest | All `/api/v1/*` routes, `GRAPH.COPY` sandbox, `shortestPath` compiler & `pytest` green | M1 | DONE |
| M3 — Next.js Live Agent Arena & Flight Recorder UI | Controlled baseline + React Flow canvas on port 3001 | M2 | DONE |
| M4 — Polish, Demo Script & Blog Benchmark Export | End-to-end smoke check + blog markdown table output | M3 | IN_PROGRESS |

## Tasks

### T-01 — Implement AST Parser & Dual Open-Source Repo Seeder (`FalkorDB/falkordb-py` & `FalkorDB/GraphRAG-SDK`)
- Status: DONE
- Assigned agent: Builder (Notion Agent)
- Assignment packet: `tasks/assignments/T-01.md`
- Goal / user impact: Hydrate FalkorDB with realistic, high-density structural and bi-temporal data for two real FalkorDB open-source repos plus a working Python `ast` parser.
- Requirements: FR-01
- Prerequisites: Pre-installed `backend/app/db/client.py` and `queries.py`
- Likely files/components: `backend/app/ingestion/__init__.py`, `backend/app/ingestion/ast_parser.py`, `backend/app/ingestion/seed_repos.py`
- Acceptance criteria:
  - [ ] `python -m app.ingestion.seed_repos` executes cleanly against `localhost:6379` in `<5s`.
  - [ ] Populates both `repo_falkordb_py` and `repo_graphrag_sdk` with `File`, `Class`, `Function`, `Contributor`, `PullRequest`, `Issue`, and `Decision` (`ACTIVE` & `SUPERSEDED`) nodes + `vecf32` embeddings.
  - [ ] Computes or assigns `pagerank` on `File` nodes.
- Verification plan:
  - Integration: `python -m app.ingestion.seed_repos` prints node and edge counts for both tenant graphs.

### T-02 — Implement Track 1, 2 & 3 Services, FastMCP Server, FastAPI Routes & E2E Pytest Suite
- Status: DONE
- Assigned agent: Builder (Notion Agent)
- Assignment packet: `tasks/assignments/T-02.md`
- Goal / user impact: Complete backend execution engine for Track 1 (`sandbox_auditor.py`), Track 2 (`memory_compiler.py`), Track 3 (`company_brain.py`), FastMCP (`mcp_server/server.py`), FastAPI (`main.py`), and pass 100% of E2E tests (`tests/test_e2e_graph.py`).
- Requirements: FR-02, FR-03, FR-04, FR-05, FR-06
- Prerequisites: T-01
- Likely files/components: `backend/app/services/*.py`, `backend/app/mcp_server/server.py`, `backend/app/main.py`, `backend/tests/test_e2e_graph.py`
- Acceptance criteria:
  - [ ] `sandbox_auditor.py` forks via `ephemeral_sandbox`, computes blast radius + `BlindAgentComparison`, and leaves 0 leaked `sandbox_pr_*` graphs.
  - [ ] `company_brain.py` serves hybrid vector + Cypher lineage (`ro_query`) and live `CYPHER_SUPERSEDE_DECISION` overrides.
  - [ ] `memory_compiler.py` executes 6-state multi-agent trajectory (with 2 `DEAD_END` branches), prunes via `shortestPath` into a `ProceduralPlaybook`, and replays 3 actions vs 5 cold (40% fewer), removes both dead ends, with honest zero-model sentinels and measured local speedup >1.0.
  - [ ] `pytest -v` passes 100%.

### T-03 — Build Next.js "Live Agent Arena & Graph Flight Recorder" Frontend
- Status: DONE
- Assigned agent: Builder (Notion Agent)
- Assignment packet: `tasks/assignments/T-03.md`
- Goal / user impact: Deliver the scroll-stopping dark-mode UI racing the Blind Baseline Agent against ChronosGraph alongside an interactive React Flow subgraph visualizer.
- Requirements: FR-07, FR-05
- Prerequisites: T-02
- Likely files/components: `frontend/package.json`, `frontend/src/app/page.tsx`, `frontend/src/components/*.tsx`, `frontend/src/lib/api.ts`
- Acceptance criteria:
  - [ ] Renders Tenant Switcher (`FalkorDB/falkordb-py` | `FalkorDB/GraphRAG-SDK`), Track 1/2/3 tabs, Blind Agent vs. ChronosGraph comparison cards, interactive React Flow canvas, and Cypher query drawer.
  - [ ] `npm run build` succeeds with zero TypeScript/build errors.


### T-04 — Release Readiness, Judge Verification README, Demo Script & Technical Blog Post
- Status: IN_PROGRESS
- Milestone: M4
- Assigned agent: Builder + integrator (Notion Agent)
- Assignment packet: `tasks/assignments/T-04.md` (created on the T-04 branch)
- Prerequisites: T-03 accepted by Principal Architect and merged into main.
- Scope: Root README; publication-ready technical blog; 2:45 recording script;
  release checklist; final handoff; minimal local startup/verification helpers;
  T-04 assignment, report and evidence.
- Acceptance: Exact track/query/route/MCP/UI matrix; source-backed provenance and
  telemetry; 1,200–1,800-word article; fresh 40 backend + 7 frontend checks and build;
  secret/artifact/fixture hygiene checked; T-04 branch published but not merged.
- Non-goals: Backend/API redesign, production deployment, external model calls,
  article/social publication, hackathon submission or a claim of prize eligibility.
