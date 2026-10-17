# From Connected Code to Approved Changes: Building a Source-Bound Memory Cockpit on FalkorDB

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

## Publication status and current source

The integrated implementation is on `main`; [current release status](current-release.md)
and [benchmark report](../tasks/reports/BENCHMARK-REPORT.md) define its evidence and
limitations. This is a repository article draft, not a claim of external publication
or an awarded prize. A [full developer walkthrough](full-walkthrough.md) accompanies it.

An AI coding assistant can understand a function and still misunderstand a change.
The missing context might be three import hops away, inside a replaced architecture
rule, or buried in the failed branches of yesterday's investigation. ChronosGraph
asks a narrower question than “can an agent fix everything?”: can a graph preserve
those connections, inspect a counterfactual without changing the saved source, and avoid repeating irrelevant work?

We built a local workbench on FalkorDB with three linked capabilities: disposable
impact audits, status-aware policy history, and compiled investigation memory.
The interesting result is not an extravagant token-savings claim. It is a small,
inspectable system whose source facts, demo scenarios, and measurements remain
separate from ingestion through the React Flow interface.

## From a graph workbench to an agent–human change cockpit

The first version demonstrated useful primitives. T-09 exposed a product gap:
a developer still had to interpret technical panels instead of following a change.
BULK-01 made imports durable and navigation honest. FINAL-01 connects those pieces
into a narrow, inspectable lifecycle at the default Command Center—not a separate
hackathon-only screen.

Consider a small payments repository. `core/pricing.py` defines
`calculate_discount`; `services/checkout.py` calls it; `api/orders.py` calls checkout;
and `tests/test_orders.py` exercises the order. A fictional current architecture
rule governs pricing, and `.github/CODEOWNERS` declares `@platform-team`.

A real FastMCP client retrieves the captured symbol and a bounded multi-hop context
package. Its first proposal renames the pricing function without updating checkout.
The service copies the tenant graph, removes the replaced file's old analysis,
parses the **complete final source**, rebuilds resolved imports/calls, and compares
before/after dependencies. Checkout is flagged as a potentially broken caller.
This is substantially different from adding snippet edges to an unchanged graph.

The coordinated proposal changes both files. The obsolete call is gone, the new
call resolves, and the same candidate order test remains reachable. Our correction
does not wave away all signature changes: retained calls to changed signatures
remain conservative flags because the parser is not a type checker. Unresolved
calls and incomplete AST coverage are not interpreted as “no impact.”

### Approval has to name something immutable

`change_lifecycle.py` records task/run/proposal nodes directly in FalkorDB. A
canonical SHA-256 binds tenant, base commit, touched base SHA-256 hashes, and final
file bodies. Repeating the same request key and payload returns the existing
proposal; reusing it for different content returns a conflict. Changing the proposal
means creating a new immutable proposal, not silently transferring an old approval.

The browser operator approves **that hash**. Before approval and execution, the
service checks the saved revision, touched base hashes, and current governing
policy fingerprint again. A shared per-tenant Redis lease serializes these writes
with policy overrides across processes. Superseding a rule atomically preserves
its history and clears approvals on touched proposals.

### A passing report is not an observed test

This distinction became the most important integration rule. An external client
can report `exit_code: 0`, but it cannot label that report locally observed. The
report remains `AGENT_REPORTED_UNVERIFIED` and does not promote a proposal into
verified success.

The separate opt-in runner accepts only an operator-configured, trusted local Git
checkout whose identity and clean HEAD match the saved snapshot. It creates a
throwaway worktree, checks base bytes, applies the approved replacements and runs
only the candidate pytest paths, with a 30-second timeout, process-group cleanup
and bounded output. It observes the actual subprocess exit code. **The worktree
isolates file edits, not arbitrary host-side code effects**; tests still execute
trusted repository code. A durable started-attempt marker prevents a lost response
from automatically executing the same ambiguous proposal again.

A passing observed run creates a finding linked to its proposal and execution.
The finding fingerprints the unchanged captured base plus the governing policy,
and stores proposed result hashes separately. It does not claim the source was
merged, deployed, or rewritten in the saved graph. On a new MCP server session,
recall returns the evidence as current at that snapshot. Override the pricing
policy and recall marks it stale. Useful memory is not just persistence; it is
persistence with an explicit invalidation condition.

### Ownership, memory and history belong beside the graph

The default interface now puts pending proposals under **Changes**, real MCP
activity and source-bound findings under **Agent activity**, and ownership/policy
operations under **Ownership**. The same activity tab runs the controlled five-action
investigation and three-action native `shortestPath` replay, then prepares a measured
`ResumeSnapshot.md` for manual context-reset recovery. The ownership tab previews
linked notes and downloads an actual three-layer Obsidian vault ZIP.

Declared ownership uses the licensed, vendored `sbdchd/codeowners` matcher: matching
pattern, source line and declared handle are pinned evidence, not proof of GitHub
permissions. Bounded Git commit-file authors/touch history remain separate. T-09's
scope-aware Python resolution and BULK-01's independent tracked-file inventory keep
unsupported-language visibility distinct from actual function analysis.

Durable public-import receipts live in Redis for seven days; graph records and
receipts survive process restarts only to the extent the configured database
persistence survives. Public archive import never executes repository code or
pretends to have fetched full history. Graph/Table views expose the same bounded
selection, including a keyboard-navigable table rather than requiring everyone to
operate a canvas.

### What was actually exercised

FINAL-01's full native regression run passed **295 backend tests with no skips**;
27 are new lifecycle/activity cases, including real passing/failing worktree pytest,
concurrent idempotency, stale source/policy rejection, HTTP intent checks and a
fresh-process read of a durable proposal. Frontend unit, type and production-build
gates and separate browser evidence are recorded in the release report. The
scripted real-stdio hero client reconnects to a new server process; it is **not**
a hosted-model or IDE-agent reasoning evaluation. Model-token savings remain
unmeasured.

The synthetic 5,000-file navigation fixture measures native single-client read
operations, not import throughput. Timings, exact browser counts and final
readiness are linked in [the FINAL-01 report](../tasks/reports/FINAL-01.md), rather
than turning one fast sample into a production promise. This article is a draft
for the side-prize submission; publication and organizer eligibility confirmation
are separate owner actions.

The remaining sections explain the original FalkorDB primitives and historical
measurements. Their synthetic overlay experiments are not the new replacement-diff
or observed-execution results.

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
WITH target, collect(DISTINCT downstream.path) AS impacted_files
OPTIONAL MATCH (target)-[:DEFINES]->(fn_target:Function)<-[:CALLS*1..3]-(fn_down:Function)
WITH target, impacted_files, collect(DISTINCT fn_down.qualified_name) AS impacted_functions
OPTIONAL MATCH (d:Decision {status: 'ACTIVE'})-[:GOVERNS]->(target)
OPTIONAL MATCH (d)-[:SUPERSEDED]->(old_d:Decision)
```

The full query aggregates impacted paths, functions, current decisions, and related
issue evidence. T-05 real-repository tests exposed a join fan-out timeout; aggregating
each traversal before the next join avoids that Cartesian multiplication without
reducing the three-hop horizon. A separate ownership/lineage query ranks authors and reviewers
only where ingested PR/review or bounded Git-commit file links exist. Empty results are a coverage limitation,
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
[final release checks](https://github.com/nakulmaurya/ChronosGraph/blob/main/docs/release-checklist.md).

## Measuring real-source workflows instead of promising universal savings

We added FINAL-BENCHMARK-01: 20 measured round trips after one excluded warm-up
on four pinned Python snapshots, a standard-library AST import oracle, real
replacement-diff workloads and a known-answer three-hop test fixture.

| Repository | Files | Root p95 ms | Locate p95 ms | Neighbors p95 ms | Raw → slice bytes | Byte reduction | Candidate tests / total | Test-file reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FalkorDB/falkordb-py | 42 | 12.35 | 35.48 | 1.51 | 88,300 → 6,871 | 92.22% | 9 / 19 | 52.63% |
| FalkorDB/GraphRAG-SDK | 154 | 11.98 | 184.04 | 0.81 | 251,320 → 14,085 | 94.40% | 28 / 63 | 55.56% |
| FalkorDB/code-graph | 86 | 11.14 | 43.92 | 8.75 | 361,266 → 22,213 | 93.85% | 27 / 29 | 6.90% |
| modelcontextprotocol/python-sdk | 870 | 64.04 | 449.00 | 36.94 | 2,851,684 → 51,587 | 98.19% | 160 / 238 | 32.77% |

These bytes are exact captured UTF-8 source versus a focused Markdown note—not
semantically equivalent input or billed token savings. Unicode chars/4 remains
an estimate. Test-file reduction is not runtime test-impact precision; that
requires a reproducible, safely executed failure oracle and remains unmeasured.

The misses matter as much as the gains. The full context service exceeds 50 ms
on larger snapshots, and the saved GraphRAG-SDK import index misses 506 edges in
our absolute-import oracle even though the current source reparse resolves them.
We preserve the original graphs, report the discrepancy, and require deliberate
new-snapshot reindexing rather than changing the dataset until a headline passes.
The corpus lacks indexed ownership declarations, so CODEOWNERS behavior is proved
on an explicitly labeled owned fixture, not invented for upstream repositories.

[Full methodology and raw receipts](../tasks/reports/BENCHMARK-REPORT.md) distinguish
functional regression passes from the **NOT MET** performance/structural acceptance
targets. No external model or third-party repository test code is executed by
this deterministic benchmark.
