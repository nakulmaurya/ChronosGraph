# Architecture — ChronosGraph

> Scope: MVP + Hackathon 3-Track Sweep | Related PRD: `docs/prd.md` | Status: accepted

## 1. Constraints and architectural goals
- **Pre-installed baseline:** `docker-compose.yml`, `backend/app/config.py`, `backend/app/models.py`, `backend/app/db/client.py`, and `backend/app/db/queries.py` are locked and pre-verified.
- **Database Law:** FalkorDB (`falkordb/falkordb:latest`) on port `6379`. Zero Neo4j or APOC syntax permitted. All embeddings wrapped in `vecf32($emb)`.

## 2. Context and high-level design
```text
[Next.js Live Arena UI] / [Cursor IDE via MCP]
        │
        ▼ (REST /api/v1/* & FastMCP)
[FastAPI Application (backend/app/main.py)]
   ├── Track 1: SandboxAuditor (services/sandbox_auditor.py)
   │      └── GRAPH.COPY -> Mutate Clone -> 3-Hop Blast Radius -> GRAPH.DELETE
   ├── Track 2: MemoryCompiler (services/memory_compiler.py)
   │      └── Scout/Historian (GRAPH.RO_QUERY) -> State-Transition Graph -> shortestPath Playbook
   └── Track 3: CompanyBrain (services/company_brain.py)
          └── Hybrid Vector + Cypher Lineage & Live [:SUPERSEDED] Override
        │
        ▼
[FalkorDB Multigraph Engine (localhost:6379)]
   ├── Graph: repo_falkordb_py      (FalkorDB/falkordb-py AST + PRs + Decisions + Memory)
   ├── Graph: repo_graphrag_sdk     (FalkorDB/GraphRAG-SDK AST + PRs + Decisions + Memory)
   └── Graph: sandbox_pr_<uuid>     (Ephemeral counterfactual clones)
```

## 3. Data model and ownership
| Node Label | Key Fields | Purpose / Track |
|---|---|---|
| `File` | `path`, `name`, `loc`, `pagerank` | AST module representation (`FalkorDB/code-graph` compatible) |
| `Class` / `Function` | `qualified_name`, `name`, `file_path`, `signature` | Callable symbols connected via `[:DEFINES]` and `[:CALLS]` |
| `Contributor` | `login`, `name`, `avatar_url` | Real GitHub maintainers connected via `[:AUTHORED]` and `[:REVIEWED]` |
| `PullRequest` / `Issue` | `number`, `title`, `url`, `state`, `merged_at`, `embedding` | Historical code changes and bug reports |
| `Decision` | `id`, `scope_symbol`, `rule`, `rationale`, `status` (`ACTIVE`\|`SUPERSEDED`), `valid_from`, `valid_to`, `embedding` | Track 3 Bi-Temporal Contradiction Shield |
| `Investigation` / `StateNode` | `id`, `state_type` (`START`\|`INTERMEDIATE`\|`DEAD_END`\|`VERIFIED_GOAL`), `hypothesis`, `is_dead_end` | Track 2 Multi-Agent State-Transition Graph |
| `AnomalySignature` / `ProceduralPlaybook` | `id`, `pattern_text`, `compiled_steps_json`, `avg_tokens_saved`, `confidence`, `embedding` | Track 2 `shortestPath` JIT-Compiled Memory |

## 4. API and component contracts
| Route | Request Schema | Response Schema | Backing Service |
|---|---|---|---|
| `GET /api/v1/tenants` | None | `List[Dict]` (graph names, node counts, preset PRs/files) | `main.py` |
| `GET /api/v1/subgraph` | `tenant_graph: str` | `GraphSubgraphPayload` | `company_brain.py` |
| `POST /api/v1/track1/sandbox-audit` | `SandboxAuditRequest` | `SandboxAuditResponse` | `sandbox_auditor.py` |
| `POST /api/v1/track3/ask-brain` | `BrainQueryRequest` | `PolicyLineageResponse` | `company_brain.py` |
| `POST /api/v1/track3/override-policy` | `PolicyOverrideRequest` | `PolicyLineageResponse` | `company_brain.py` |
| `POST /api/v1/track2/investigate` | `InvestigationRunRequest` | `InvestigationRunResponse` | `memory_compiler.py` |

## 5. Security and trust boundaries
- **Hardware-Enforced Read-Only Queries (`GRAPH.RO_QUERY`):** Discovery agents (`Scout`, `Historian`) and read-only brain lookups use `db_manager.ro_query()` so untrusted agent prompts cannot mutate graph state.
- **Ephemeral Sandbox Containment:** Destructive PR simulations execute strictly inside `db_manager.ephemeral_sandbox()`, which guarantees `sandbox_graph.delete()` in a `finally` block.
