# Product Brief — ChronosGraph

> Status: validated | Owner: Nakul Arvind Maurya (Bridge) & Principal Architect (Brain) | Last updated: 2026-10-15

## One-sentence problem
AI coding and SRE agents break production codebases and burn 80%+ redundant tokens because they operate on static syntax snapshots or flat vector chunks—missing multi-hop blast radius, superseded architectural rules, and reusable debugging trajectories.

## Target users and job-to-be-done
- **Primary user:** AI engineers, open-source maintainers, and autonomous coding agents (Cursor, Claude Code, OpenCode, CI/CD PR gatekeepers).
- **Their current workaround:** Combining static AST tools (`FalkorDB/code-graph`) with vector RAG (`CodeRabbit`, `Mem0`), which cannot simulate changes in a disposable graph fork, cannot distinguish active rules from superseded rules, and repeats failed tool calls across sessions.
- **Job-to-be-done:** When evaluating a Pull Request, querying architectural history, or triaging a bug on a real codebase (`FalkorDB/falkordb-py`, `FalkorDB/GraphRAG-SDK`), the user wants deterministic blast-radius simulation, bi-temporal contradiction shielding, and JIT-compiled procedural playbooks so changes are safe and repeat investigations execute in ~1 second.

## Evidence vs assumptions
| Claim | Evidence/source or label ASSUMPTION | Confidence | How to validate |
|---|---|---|---|
| Hackathon judges require FalkorDB to shape agent actions across 3 tracks | Official WeMakeDevs x FalkorDB brief (Oct 14–18, 2026) | High | Map every UI/MCP action to Track 1, 2, and 3 rubrics |
| FalkorDB already has `FalkorDB/code-graph` for basic AST parsing | Verified on GitHub (`github.com/FalkorDB/code-graph`) | High | Pitch ChronosGraph as the temporal, sandbox & JIT-memory layer ON TOP of `code-graph` |
| `GRAPH.COPY` clones an in-memory repo graph in <10ms | FalkorDB GraphBLAS sparse matrix specification | High | Measure `sandbox_clone_time_ms` in E2E tests |
| `shortestPath` over a State-Transition Graph prunes dead-end agent steps | Graph theory invariant on branching state trajectories | High | Verify `pruned_golden_steps < total_steps_executed` in `test_e2e_graph.py` |

## Existing approaches and alternatives
| Approach | Advantage | Limitation | Reuse/buy/build decision |
|---|---|---|---|
| `FalkorDB/code-graph` | Standard AST labels (`File`, `Class`, `Function`, `CALLS`) | Stateless snapshot; no PR history, no `GRAPH.COPY` sandbox, no agent memory | **Reuse schema convention**, **build** temporal + sandbox + memory layers |
| `Graphiti` / `Mem0` | Stores episodic chat facts | Does not compile multi-step tool traces into fast Cypher playbooks | **Build** `shortestPath` State-Transition JIT Playbook Compiler |
| Standard Vector RAG | Easy text chunk indexing | Retrieves outdated/superseded rules alongside active rules | **Build** AST-bound `[:SUPERSEDED]` contradiction shield |

## MVP outcome
In one browser session (or via MCP in Cursor), a judge or engineer selects a real open-source repository (`FalkorDB/falkordb-py` or `FalkorDB/GraphRAG-SDK`) and runs a side-by-side **Live Agent Arena** proving that ChronosGraph:
1. Clones the graph via `GRAPH.COPY` in milliseconds to block a breaking PR that a Blind Agent approves (Track 1).
2. Enforces `ACTIVE` architectural decisions while crossing out `SUPERSEDED` rules and ranking real maintainers (Track 3).
3. Prunes a 6-step multi-agent debugging trace (with 2 dead ends) via `shortestPath` into a 2-step compiled playbook that cuts repeat token burn by >80% (Track 2).

### Must have
- Pre-warmed, realistic open-source multigraphs for `FalkorDB/falkordb-py` and `FalkorDB/GraphRAG-SDK` + Python `ast` parser.
- Ephemeral `GRAPH.COPY` counterfactual PR sandbox with automatic `GRAPH.DELETE` cleanup.
- Bi-temporal `(:Decision)` lineage (`ACTIVE` vs `SUPERSEDED`) + live policy override mutation.
- Multi-agent (`Scout` via `ro_query`, `Historian` via `ro_query`, `Verifier`) State-Transition trajectory logger + `shortestPath` Playbook Compiler.
- FastMCP server (`/mcp` + stdio) and Next.js **Live Agent Arena & Flight Recorder** UI.

### Not in this MVP
- Live GitHub OAuth login or webhook installation flows requiring repository admin permissions.
- Unbounded synchronous cloning of 100,000-LOC external repositories during a request.

## Constraints
- **Time:** Submission deadline October 18, 2026, 11:59 PM IST (~86 hours remaining).
- **Cost ceiling:** $0 mandatory API spend (deterministic 768-dim vector projection fallback built into `client.py`; optional Gemini/OpenAI enrichment).
- **Platform:** Docker (`falkordb/falkordb:latest`), Python 3.11+ FastAPI/FastMCP backend, Next.js 15 frontend.

## Feasibility and risks
| Risk | Likelihood / impact | Cheap validation / mitigation | Trigger to revisit |
|---|---|---|---|
| Builder agent hallucinates Neo4j/APOC syntax | High / High | Pre-installed `client.py` and `queries.py` in baseline zip | Any Cypher syntax error in `pytest` |
| Orphaned sandbox graphs consume RAM | Medium / Medium | Enforced `@contextmanager ephemeral_sandbox` with `finally: sandbox_graph.delete()` | `test_e2e_graph.py` checks `list_tenant_graphs()` |
| Demo looks like a dry dashboard on LinkedIn | Medium / High | Built-in `BlindAgentComparison` payload + Side-by-Side Live Arena UI with stopwatch & token meters | UI review at T-03 |

## Decision
Proceed immediately with controlled multi-agent build (`T-01` -> `T-02` -> `T-03` -> `T-04`).
