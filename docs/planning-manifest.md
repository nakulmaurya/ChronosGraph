# Planning Manifest — ChronosGraph

> Contract version: v1.2 | Updated: 2026-10-15 | Status: READY_FOR_BUILD | Mode: planner (Brain) → builder (Notion Agent) → reviewer (Brain via GitHub)

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

## v1.1 — Approved CR-001

Principal Architect approval supplied by Nakul in chat. Approved: WITH-clause shortestPath fix, backend packaging correction, and explicit DEMO_POLICY_SCENARIO history anchored to real source files and contextual PRs. Demo PR anchors are not historical policy attribution.

T-01 verification: 21/21 tests pass on real native FalkorDB 4.18.3. Editable package installation succeeds. Preserve the actual archive digest separately from the older planner label. T-02 is authorized; T-03 remains gated on Principal Architect review.

## v1.2 — Approved CR-002: Deterministic Zero-Key Scientific Scope

Principal Architect approval supplied by Nakul in the attached review. Current
acceptance supersedes earlier illustrative token/outage claims in older documents:
5 cold actions / 6 states / 2 dead ends -> 3 retained actions / 0 dead ends / 40%
step reduction. No model calls; tokens_used=0 and token_savings_pct=0.0 are explicit
sentinels, not LLM benchmarks. Measured replay speedup >1.0 and local clone <250 ms
are tested without artificial timing. Keep current HTTP 409 scope guard. Baselines
are controlled queries, policies and synthetic dependencies retain provenance.
After 40/40 tests and integrator acceptance, T-02 may merge; T-03 is authorized on
build/t03-frontend-arena. Stop at T-03 report; no T-04 or production deployment.
