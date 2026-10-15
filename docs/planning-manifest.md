# Planning Manifest — ChronosGraph

> Contract version: v1.0 | Updated: 2026-10-15 | Status: READY_FOR_BUILD | Mode: planner (Brain) → builder (Notion Agent) → reviewer (Brain via GitHub)

## Authority and baseline
- Project/repository: `chronosgraph` (GitHub Canvas bridged by Nakul Arvind Maurya)
- Baseline ref (Archive SHA-256 prefix): `zip-sha256:68957811d3a5ba99`
- Approved MVP outcome: Side-by-side Live Agent Arena & MCP Server powered by FalkorDB on real open-source repos (`FalkorDB/falkordb-py` & `FalkorDB/GraphRAG-SDK`), proving `GRAPH.COPY` PR sandboxing (Track 1), `shortestPath` JIT Playbook Compilation (Track 2), and Bi-Temporal Contradiction Shielding (Track 3).
- Decision owner: Nakul Arvind Maurya & Principal Architect (Brain)
- Target build agent: Notion Coding Agent / Cursor / Claude Code
- Allowed spend & permissions: Local Docker (`falkordb/falkordb:latest`), local Python/Node execution, and Git commits to repo. No paid cloud provisioning or destructive host actions without user approval.

## Canonical artifacts
| Type | Path | State | Owner |
|---|---|---|---|
| Product brief | `docs/product-brief.md` | READY | Planner |
| PRD | `docs/prd.md` | READY | Planner |
| Architecture | `docs/architecture.md` | READY | Planner |
| UX Design | `docs/design.md` | READY | Planner |
| Task plan | `tasks/tasks.md` | READY | Integrator |
| Repo rules | `AGENTS.md` / `CLAUDE.md` | READY | Repo owner |
| Resume status | `docs/handoff.md` | READY | Integrator |

## Contract invariants (must not be changed silently)
1. **Schema & Models (`backend/app/models.py`):** Field names on `SandboxAuditResponse`, `PolicyLineageResponse`, `InvestigationRunResponse`, `BlindAgentComparison`, and `GraphSubgraphPayload` are locked.
2. **FalkorDB Client (`backend/app/db/client.py`) & Queries (`backend/app/db/queries.py`):** Pre-installed and verified. Do not replace with Neo4j or APOC calls.
3. **Zero Orphaned Sandboxes:** Every `GRAPH.COPY` fork must be deleted before the request finishes.

## Dispatch readiness
- **Ready now:** `T-01` (`tasks/assignments/T-01.md`), followed sequentially by `T-02` (`tasks/assignments/T-02.md`) and `T-03` (`tasks/assignments/T-03.md`).
- **Work packets:** `tasks/assignments/T-01.md`, `tasks/assignments/T-02.md`, `tasks/assignments/T-03.md`.

## Decisions and open risks
| Item | Decision/evidence | Confidence | Owner / next check |
|---|---|---|---|
| Target Open-Source Repos | Pre-warm `FalkorDB/falkordb-py` and `FalkorDB/GraphRAG-SDK` for instant `<2s` judge verification | CONFIRMED | Verify in `T-01` |
| Offline Embedding Reliability | Use deterministic 768-dim trigram projection in `FalkorDBManager.embed_text` so vector indexes work with zero API key friction | CONFIRMED | Verify in `T-01` & `T-02` |
| Scroll-Stopper Visual Hook | Include `BlindAgentComparison` in every API response and render Side-by-Side Live Arena in UI | CONFIRMED | Verify in `T-02` & `T-03` |
