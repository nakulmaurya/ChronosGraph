# Product Requirements — ChronosGraph

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

Version: v1.3 | T-05 accepted via user bridge; prior CR-001/CR-002 remain the v1.2 baseline

## Outcome and truthful scope
Local engineering console backed by real FalkorDB graph snapshots of
FalkorDB/falkordb-py and FalkorDB/GraphRAG-SDK. Demonstrate connected static impact,
current/historical policy lineage, and deterministic procedural memory replay.
This does not establish runtime outages, formal rule violations, autonomous bug
fixes, semantic embeddings, generic LLM failures, or guaranteed prize eligibility.

## v1.3 additive acceptance — T-05
Dynamic registered Python Git repositories extend the two defaults. The CLI parses
tracked committed Python without running it, stores conservative AST edges and
normalized native PageRank, and links bounded real Git commits to current files.
Commit author identity is unverified; coverage can legitimately be empty. Demo
policies remain opt-in and fictional. Registered READY metadata/legacy source File
graphs are discovered; absent/invalid/incomplete tenants return HTTP 404.

The canonical audit query aggregates each traversal before joining the next branch;
three-hop semantics, locked response models, zero-model sentinels and stale/scope
HTTP 409 guards remain unchanged. T-05 acceptance covers four live tenant journeys,
53 backend / 7 frontend / 17 production Chromium checks. The **154.99–257.62 ms**
MCP SDK clone sample range is an observation, not a guaranteed latency bound.
The <250 ms ceiling in FR-02 below is historical acceptance on the original two
tenants, not a v1.3 promise for larger arbitrary repositories. See `tasks/reviews/T-05.md`.

## Requirements
| ID | Requirement | Acceptance |
|---|---|---|
| FR-01 | Real AST/GitHub-provenance multigraphs | Both tenant graphs, conservative static IMPORTS/CALLS, PageRank, real PR/contributor records, labeled demo policy chains; preserve source data |
| FR-02 | Disposable GRAPH.COPY scenario | Clone, apply explicitly SIMULATED_PR_DEPENDENCY File/Function edges, execute canonical blast radius/ownership, verify cleanup and no leaks; <250 ms local clone ceiling on both tenants |
| FR-03 | Current vs superseded policies | Read-only lexical vector search + exact file lineage, source labels and validity/recorded times; atomic supersession; retain HTTP 409 scope mismatch/mixed-scope guard |
| FR-04 | Deterministic policy-triage memory | Six cold states / five tool actions (Scout/Historian/Verifier), two DEAD_END leaves; native shortestPath retains three actions; persist vector-indexed playbook, actually replay retained tools; fingerprints invalidate stale playbooks |
| FR-05 | Honest controlled baseline and telemetry | Cold 5 actions/2 dead ends -> warm 3 actions/0 dead ends: 100% dead-end elimination and 40% fewer tool executions; actual replay speedup >1.0 in local acceptance run; no sleeps/multipliers; zero model tokens, token_savings_pct=0.0 sentinel |
| FR-06 | Five real FastMCP tools | simulate_pr_blast_radius, query_bitemporal_decisions, record_decision_override, find_true_code_owners, run_or_compile_playbook execute against live FalkorDB |
| FR-07 | Interactive Next.js console | Tenant/track selectors, action controls, controlled baseline, interactive React Flow graph, Cypher drawer, provenance/telemetry inspector, MCP config modal; responsive dark mode; clean production build and live API smoke check |

## Data and trust
- Locked models stay unchanged. All inputs parameterized and known tenants checked.
- Keep DEMO_POLICY_SCENARIO, SIMULATED_PR_DEPENDENCY, DETERMINISTIC_POLICY_TRIAGE,
  CONTROLLED_ONE_HOP_BASELINE labels in backend responses and frontend.
- No LLM is called. tokens_used=0 and token_savings_pct=0.0 explicitly mean no model
  benchmark. Do not present 40% step reduction as token or cost savings.
- Controlled one-hop/oldest-document baselines are not real model evaluations.
- Static impact and demo policies are not actual upstream breaking changes/rules.
- Limited public PR snapshot can yield empty owner results; disclose rather than
  fabricate. Lexical hashed vectors are not model semantic embeddings.
- Bound visual payloads (220 nodes/500 edges; overview 50 files). Display truncation
  caveat; never imply all affected nodes are rendered.
- No authentication or multiworker policy serialization. Localhost, trusted user,
  single process only. CORS is not authorization. No production deployment.
- Unknown/missing files and invalid scopes show actionable non-500 error states.

## Verification and gates
- T-01 remains 21 passing tests; T-02 full suite 40/40 under approved CR-002 gates.
- Both tenant clone timings <250 ms and zero orphaned sandbox graphs.
- npm install and npm run build succeed without TypeScript errors.
- Live UI integration verifies each track, tenant switching, errors/empty states,
  MCP modal, policy override and stale playbook behavior; no mocked backend data.
- Measured times are local observations, not universal performance guarantees.
- T-03 stops at its branch/report; no T-04 or deployment without authorization.
