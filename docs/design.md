# Interface Design — ChronosGraph Flight Recorder

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

Version v1.3 / accepted T-05; prior approved CR-002 replaces illustrative fake metrics.
The tenant menu discovers registered repositories; the snapshot selector distinguishes
Git commits from PRs. Reviewer names are bounded, unverified author evidence.
Live totals may grow after ingestion; do not present initial counts as live counts.
No visual redesign or new production/security claim is part of acceptance.

## Direction
A precise, dark industrial graph workbench. Slate-950 canvas, slate-900 panels,
subtle grid, monospace identifiers and timing, system sans headings. Cyan for
connected paths, amber for impact, emerald for active rules, rose for superseded
and pruned branches. Text labels always accompany color. No stock illustration,
fake status lights, simulated counters or promotional outage verdicts.

## Layout
Header with brand, live connection/latency, tenant selector and MCP connect.
Three track tabs beneath. Desktop: 300px controls/baseline / flexible graph / 320px
results inspector. Each region scrolls internally. At tablet/mobile, stack controls,
fixed-height graph and results in reading order, no horizontal page overflow.

## Canvas and states
Fit visible graph automatically after responses; interactive nodes and real edges,
legend and counts, selectable node metadata. Status badges: ACTIVE, SUPERSEDED
(dashed + struck text), IMPACTED, DEAD_END (PRUNED BY SHORTESTPATH), GOLDEN_PATH.
Show a scoped/limited-view note rather than imply the full graph is rendered.
Cypher drawer contains exact backend query and measured query milliseconds.

## Truthful side-by-side telemetry
Controlled baseline: actual one-hop or oldest-document results and explicit notes.
ChronosGraph: actual clone cleanup, impact, policies and available PR-linked owners.
Memory: 5 actions / 2 dead ends cold vs 3 actions / 0 dead ends replay, 40% fewer
executions, actual durations/speedup. Deterministic policy-triage roles, zero models,
zero model tokens; zero savings sentinel is not a measured token/cost benchmark.
Keep DEMO_POLICY_SCENARIO, SIMULATED_PR_DEPENDENCY, DETERMINISTIC_POLICY_TRIAGE,
CONTROLLED_ONE_HOP_BASELINE visible. Empty owners are explained, never fabricated.

## Interaction and accessibility
Labeled form fields and explicit mutation submit. Busy states prevent races; no
stale tenant results. Errors are actionable and announced. Modal supports keyboard,
Escape and focus restoration; copy control reports success/failure. Focus-visible
outlines, reduced motion, accessible touch targets, readable contrast and text.
Policy records expose validity/recorded timestamps and provenance with safe links.
MCP config is a local template with editable absolute backend path, not a claim of
an already installed external IDE connection. No authentication: localhost only.
