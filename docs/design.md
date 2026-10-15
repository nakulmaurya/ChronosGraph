# UX & Interface Design — The ChronosGraph Live Arena & Flight Recorder

> Related PRD: `docs/prd.md` | Target: `frontend/src/app/page.tsx`

## 1. Visual Concept: "The LinkedIn Scroll-Stopper Arena"
Instead of a passive dashboard, the UI is a **high-contrast dark-mode (`bg-slate-950 text-slate-100`) Engineering Arena & Flight Recorder** designed to make any viewer understand the value in 5 seconds:
- **Top Header Bar:**
  - **Brand & Status:** `ChronosGraph // FalkorDB Context & JIT Memory Engine` + live query latency badge (`1.8 ms`).
  - **Multigraph Tenant Switcher:** Instant pill toggle between `FalkorDB/falkordb-py` and `FalkorDB/GraphRAG-SDK`.
  - **Track Mode Selector:**
    1. `🛡️ Track 1: GRAPH.COPY PR Crash-Test`
    2. `⚡ Track 2: JIT Memory Race (shortestPath)`
    3. `🧠 Track 3: Bi-Temporal Contradiction Shield`
  - **MCP Connect Button:** Opens modal with copy-ready Cursor / Claude Code MCP JSON config.

## 2. Three-Column Split Battlefield (`100vh`)
1. **Left Column (340px) — Interactive Trigger Controls & Blind Agent Failure Card:**
   - Context-sensitive scenario selector (e.g., real PR dropdown for Track 1, Bug Race trigger for Track 2, Live Policy Override form for Track 3).
   - **🚨 Standard Blind Agent Card (Red/Rose border):** Displays `blind_agent_comparison` from the API response—showing how standard Vector RAG / static AST approves a breaking change, follows a `SUPERSEDED` rule, or burns `14,200 tokens (11.4s)` wandering through dead ends.
2. **Center Column (Flex-1) — Interactive FalkorDB React Flow Canvas + Cypher Drawer:**
   - Renders `subgraph.nodes` and `subgraph.edges` with automatic hierarchical layout:
     - `SUPERSEDED` Decision Node: Red dashed border, `SUPERSEDED` badge, strikethrough rule text.
     - `ACTIVE` Decision Node: Emerald glowing border, `ACTIVE INVARIANT` badge, clickable GitHub PR link.
     - `IMPACTED` File/Function Node: Amber/Orange border showing PageRank criticality score.
     - `DEAD_END` StateNode: Muted rose node marked `PRUNED BY SHORTESTPATH`.
     - `GOLDEN_PATH` StateNode / Playbook: Animated cyan edges (`animated: true`) showing the compiled 2-step shortcut.
   - **Bottom Collapsible Drawer:** Displays exact `subgraph.cypher_executed` and `execution_time_ms`.
3. **Right Column (360px) — ChronosGraph Agent Verdict, Maintainer Centrality & ROI Meter:**
   - **✅ ChronosGraph Verdict Card (Emerald/Cyan border):**
     - Track 1: Shows `sandbox_clone_time_ms` (`~1.2ms`), `sandbox_cleaned_up: true`, blocked policy violations, and downstream impacted symbols.
     - Track 2: **Live Token & Latency ROI Meter** comparing Cold Multi-Agent Run (`6 steps | 14,200 tokens | 11.4s`) vs. JIT Compiled Playbook (`2 steps | 1,650 tokens | 1.1s | 88.4% Saved`).
     - Track 3: Bi-temporal decision timeline (`ACTIVE` <- `[:SUPERSEDED]` <- `Historical`) + Top 3 Maintainers ranked by PR/Review graph centrality (`@gkorland`, `@roi-lipman`, `@swilly22`).
