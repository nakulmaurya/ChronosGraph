# Beyond Static ASTs: Building Disposable GRAPH.COPY Sandboxes, Bi-Temporal Policy Lineage, and Shortest-Path Playbooks on FalkorDB

An AI coding assistant can understand a function and still misunderstand a change.
The missing context might be three import hops away, inside a replaced architecture
rule, or buried in the failed branches of yesterday's investigation. ChronosGraph
asks a narrower question than “can an agent fix everything?”: can a graph preserve
those connections, test a counterfactual safely, and avoid repeating irrelevant work?

We built a local workbench on FalkorDB with three linked capabilities: disposable
impact audits, status-aware policy history, and compiled investigation memory.
The interesting result is not an extravagant token-savings claim. It is a small,
inspectable system whose source facts, demo scenarios, and measurements remain
separate from ingestion through the React Flow interface.

## Start with real structure, not a convincing screenshot

Our conservative Python AST parser extracts files, classes, functions, imports,
and resolvable calls without executing repository code. It follows familiar
AST/code-graph conventions, but does not integrate or benchmark the separate
`FalkorDB/code-graph` package. Dynamic calls that cannot be resolved remain unresolved
rather than becoming invented dependency edges. Native PageRank ranks file connectivity.

We ingested two pinned code revisions and cached public GitHub PRs, reviews,
contributors, and issues. Code revisions are pinned; the fetched GitHub metadata
is a separate ingestion-time snapshot, not history frozen at those commits.

| Repository | Historical real-source/public-metadata nodes | Edges | Python files | Functions |
| --- | ---: | ---: | ---: | ---: |
| FalkorDB/falkordb-py | 458 | 669 | 42 | 371 |
| FalkorDB/GraphRAG-SDK | 4,252 | 6,251 | 154 | 3,364 |

The code commits are `31f63f44a5745b9bec65969a1db706906718cb82` and
`35e67a0b27fdcc7f2c28508b09e86169851a8187`, respectively. T-01 records graph-write
measurements of 48.66 ms and 179.87 ms; those are not total clone, network, parsing,
or installation times. Later investigation records increase live counts.

An AST graph already supports structural traversal. What it does not automatically
supply is architectural policy validity or reusable investigation state. Flat vector
retrieval, meanwhile, can retrieve an obsolete rule because its wording resembles
the question. Neither limitation means ASTs or retrieval are useless; it means
these additional semantics need explicit representation.

## Primitive 1: copy a graph, inspect a counterfactual, delete it

The first capability creates a disposable tenant-graph clone using `GRAPH.COPY`.
Inside the clone, the service adds explicitly labeled synthetic dependency/call
changes. It then runs the canonical `CYPHER_BLAST_RADIUS_AUDIT`. Here is its actual
traversal prefix, not pseudocode:

```cypher
MATCH (target:File)
WHERE target.path IN $modified_files
OPTIONAL MATCH (downstream:File)-[:IMPORTS*1..3]->(target)
OPTIONAL MATCH (target)-[:DEFINES]->(fn_target:Function)<-[:CALLS*1..3]-(fn_down:Function)
OPTIONAL MATCH (d:Decision {status: 'ACTIVE'})-[:GOVERNS]->(target)
OPTIONAL MATCH (d)-[:SUPERSEDED]->(old_d:Decision)
OPTIONAL MATCH (open_issue:Issue {state: 'OPEN'})-[:AFFECTS]->(downstream)
```

The full query aggregates impacted paths, functions, current decisions, and related
issue evidence. A separate ownership/lineage query ranks authors and reviewers
only where ingested PR-file links exist. Empty results are a coverage limitation,
not proof that a file lacks maintainers.

The database manager attempts `GRAPH.DELETE` in a context-manager `finally` block.
The audit service additionally checks that the sandbox name disappeared before
returning successful cleanup. That distinction matters: an attempted deletion is
not the same as observed deletion, especially during database failure.

This is static potential-impact analysis. We do not apply an actual source diff,
execute changed code, predict a production outage, or prove a policy violation.
`SIMULATED_PR_DEPENDENCY` identifies the clone-only additions so that a persuasive
visualization cannot quietly promote a scenario into an upstream fact.

## Primitive 2: make discovery reads read-only

Scout and Historian are deterministic graph-tool roles, not autonomous language
models. Their discovery paths call `ro_query`, which sends `GRAPH.RO_QUERY` rather
than relying on an instruction saying “please do not write.” The integration suite
attempts a write through this interface and verifies rejection.

Read-only discovery is not a complete application authorization system. The
trusted local API still exposes explicit mutation routes for overrides and
investigation persistence. It is not safe to publish these unauthenticated
endpoints on the internet. Graph separation and localhost configuration are
useful boundaries for this demonstration, not a production multitenancy claim.

## Primitive 3: retrieve a rule without erasing its history

Policies are Decision nodes governing real File nodes. A new active decision
points through `SUPERSEDED` to the rule it replaced. Validity fields describe
when a rule applies; recorded fields describe when this system recorded it.
Live override code preserves both dimensions, while demo timestamps are labeled
as scenario clocks rather than independently verified upstream events.

We could not infer genuine architecture decisions just from PR titles. Instead,
four fictional policy pairs per tenant are labeled `DEMO_POLICY_SCENARIO`.
Each pair adds two nodes and five relationships: two governing links, two contextual
PR links, and one supersession link. That is **+8 nodes/+20 edges per tenant**,
producing initial seeded totals of 466/689 and 4,260/6,271. A contextual PR is not
evidence its author adopted the fictional rule.

The canonical retrieval query uses FalkorDB's vector primitive:

```cypher
CALL db.idx.vector.queryNodes('Decision', 'embedding', 4, vecf32($query_embedding))
YIELD node AS d, score
WHERE d.status = 'ACTIVE'
MATCH (d)-[:GOVERNS]->(f:File)
OPTIONAL MATCH (d)-[:SUPERSEDED]->(old_d:Decision)
OPTIONAL MATCH (c:Contributor)-[:AUTHORED]->(pr:PullRequest)-[:MODIFIES]->(f)
```

Embeddings here are deterministic 768-dimensional lexical hashes, not semantic
model embeddings. Writes and searches wrap vectors in `vecf32()`. Explicit file
selection and lineage reads supplement retrieval; top-k search followed by active
filtering is not a guarantee of exhaustive policy recall.

A live override uses `CYPHER_SUPERSEDE_DECISION` to mark old active rules superseded
and create their successor. The service refuses incompatible scopes with HTTP 409
because the canonical mutation is file-wide. It does not silently retire unrelated
scope rules. The UI requires explicit mutation confirmation and exposes provenance.

## Primitive 4: compile the verified path, not a better story

A cold investigation executes five real read-only tool actions. Two candidate
checks find no governing policy; three useful actions inspect the selected target,
retrieve policy history, and verify an active governing rule. The trajectory has
six StateNodes: a start, two dead-end leaves, and three retained-action states.
Its separate Investigation node is not a seventh workflow state.

The syntax lesson on native FalkorDB 4.18.3 was to bind the path in a `WITH`
projection. These lines are copied from `CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH`:

```cypher
MATCH (inv:Investigation {id: $investigation_id})-[:HAS_STATE]->(start:StateNode {state_type: 'START'})
MATCH (inv)-[:HAS_STATE]->(goal:StateNode {state_type: 'VERIFIED_GOAL'})
WITH inv, shortestPath((start)-[:ACTION_TAKEN*1..12]->(goal)) AS golden_path
```

The remaining query collects relationship tool names, outcomes, recorded
costs, and golden node identifiers. The service persists an anomaly signature
and compiled playbook. Replay executes the three retained tools again; it does
not merely return yesterday's narrative. A fixed tool allowlist, exact scenario
matching, and a fingerprint of source/current policies guard reuse. Policy
changes invalidate the old playbook and return HTTP 409.

Shortest path alone does not establish procedural correctness. It works for this
constrained branching topology because prerequisite discovery, policy retrieval,
and verification remain on the valid chain. General investigations would need
richer dependency constraints before “fewer hops” could mean “safe replay.”

## What the measurements actually say

All numbers below are captured local observations, not universal performance promises.

| T-02 observation | Recorded result |
| --- | --- |
| Sample sandbox clone | 22.99 ms; cleanup verified |
| Six separate clone checks | 96.62–119.79 ms; no orphan sandboxes |
| Sample cold / replay duration | 13.300 / 8.425 ms; 1.579× |
| Five-pair median speedup | 1.253×; one pair was slower at 0.821× |
| Executed actions | 5 cold → 3 replay; 40% fewer |
| Dead ends executed | 2 cold → 0 replay |
| Model calls / model tokens | 0 / 0 |

We originally had acceptance targets for 75% token savings and 4× acceleration.
Those did not describe a model-free local system honestly. Rather than fabricate
tokens or insert delays, we raised CR-002. The architect approved v1.2: exact
branch pruning, measured replay behavior, zero-model sentinels, and a local clone
ceiling below 250 ms. Historical failures remain in the repository.

`token_savings_pct: 0.0` therefore means unmeasured, not a measured zero-percent
or eighty-percent saving. Whole-route latency includes persistence and graph
construction overhead, so a replay can still be slower under load. The interface
displays the returned factor even below one.

## Make the evidence inspectable

The console exposes real relationships, status labels, source metadata, and the
backend-reported Cypher. Its focused view states visible-versus-payload counts;
users can reveal the full bounded payload. It never labels that subset the entire
repository. Controlled shallow/oldest-document baselines are described as graph
queries, not measured failures of a competing AI system.

The release candidate has 40 backend tests, seven frontend regression tests,
a successful optimized build, and a 15-check live UI smoke suite. Native execution
was verified; Docker-image execution and production deployment were not. That
boundary is part of the result, not a footnote to hide.

The useful idea is simple: memory should retain evidence and invalidate itself
when its assumptions change. FalkorDB let us put structure, policy history, and
execution state in one inspectable model—without pretending a demo is already
an autonomous production engineer.

## Source and reproduction

[Repository](https://github.com/nakulmaurya/ChronosGraph) ·
[canonical queries](https://github.com/nakulmaurya/ChronosGraph/blob/a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7/backend/app/db/queries.py) ·
[T-01 evidence](https://github.com/nakulmaurya/ChronosGraph/blob/a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7/tasks/reports/T-01.md) ·
[T-02 accepted report](https://github.com/nakulmaurya/ChronosGraph/blob/a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7/tasks/reports/T-02.md) ·
[raw HTTP excerpts](https://github.com/nakulmaurya/ChronosGraph/blob/a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7/tasks/reports/T-02-response-excerpts.json) ·
[benchmark samples](https://github.com/nakulmaurya/ChronosGraph/blob/a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7/tasks/reports/T-02-samples/benchmark.json) ·
[final release checks](https://github.com/nakulmaurya/ChronosGraph/blob/build/t04-release-pack/docs/release-checklist.md).
