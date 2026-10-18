# Task 11 — four-trial comparison analysis (UNFILLED TEMPLATE)

**PENDING actual Task 9 receipts and manual review. No comparison result, speedup, cost reduction or graph advantage is asserted here.** Never replace missing observations with zero. Keep earlier interrupted experiments and setup failures distinct from these four trials.

## Evidence lock (fill before calculating)

- Actual Task 9 root / exact predeclared protocol path and SHA256: PENDING.
- Expected protocol: two maintenance task instances × ordinary/graph modes, one attempt per cell, sequential TUI execution; SDK revision `754254c08fe1c3eda18b69da3d336106fe8d72d6`; OpenCode 1.19.3; `opencode/deepseek-v4.1-flash-free`; 900-second wall budget. Verify these against actual receipts, not this template.
- Freeze acceptance test hashes against [the protocol](../../experiments/agent-comparison-01/protocol.json). Record amendments and whether they preceded agent execution. Scope-limited graph context is not comprehensive dependency coverage.
- Preserve each launch, attempt counter, startup/prompt acknowledgment, stop/timeout, permission decision, provider error and correction. Explicitly mark any missing start/end timestamp.
- Collect sanitized source/diff/command receipts and completed-step usage. Raw private exports remain outside the public repository and report.

## Per-trial evidence table — no inferred outcomes

| Trial | Task / mode (verify actual order) | Acceptance / exit | Existing regression / exit | Manual intended-change review | End state | Wall seconds incl. waits | Native exploration / source reads | MCP calls / failed calls | Completed-step usage / coverage | Receipt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | structured-invalid-characters / ordinary | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 2 | has-tool-lookup / ordinary | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 3 | structured-invalid-characters / graph | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |
| 4 | has-tool-lookup / graph | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

Do not turn passed targeted tests into full SDK-suite success. Report skipped tests, timeout/partial results, unexpected changes and missing reports. Confirm no post-check source changes by comparing exact before/after candidate digests. Full manual acceptance requires intended behavior and no unintended edits, not just an agent's declaration.

## Computation plan

1. Keep collected inputs immutable under a dedicated local `raw/` directory; index their SHA256s. Validate JSON/log schemas and profile completeness before analysis. Retain a clean per-trial evidence dataset, with nulls and explicit missingness reasons.
2. Extract tool calls from actual tool receipts, not narrative claims or UI screenshots alone. State counting rules: tool invocations versus completed calls, failures, search/list/read versus editing/testing, and command-level compound searches. A shell invocation containing several reads is not comparable to one file-read tool without stating the rule. Do not count browser GET polling as agent MCP usage.
3. Report both modes' task correctness first. Pair only identical task/revision/check definitions. With one run per task/mode, show individual paired observations; no significance, stable p95 or universal savings claim.
4. Use total wall time including permission waits. Where wait intervals are observable, report separately without silently subtracting them. Shared-VM review/testing overlapped part of the window; identify overlap from timestamps. If overlap cannot be measured, label timing confounded and do not claim a clean speed advantage.
5. Separate input/output/reasoning/cache-read/cache-write categories exactly as provider/OpenCode reports them; check whether categories overlap before summing. Unknown retry/interrupted-call usage stays unknown. Zero free-model charge is not paid-equivalent savings. Do not invent model prices.
6. Account separately for indexing, refresh and context-pack/setup work. Preserve the failed 100-path overflow setup and the explicit 12-path amendment. Do not treat the retained 17.9824-second ingestion observation as the total cost of all setup attempts.
7. Trace whether graph evidence actually changed a decision, found a dependency or preserved compatibility. Also retain graph failures/no-benefit cases. Presence of MCP calls alone does not prove causal benefit.
8. Compute each published number once into a machine-readable analysis object with provenance; independently check with a second aggregation method. Derive report values from that object. Any chart later must use the same verified data and its required visualization workflow.

## Required limitations / final conclusion fields

- Repetition: four-cell feasibility pilot, one sample per cell, two tasks, one repository and one free model.
- Provider cache/control, permission/operator waits, interruptions and prior repository exposure.
- Selected regression scope and external-test independence; synthetic/local evidence versus public SDK tasks.
- Actual graph/context failures, bounded scope and any missing observations.
- Separate baseline handoff adequacy if claiming a memory comparison; these additive maintenance tasks are not automatically a cross-session memory experiment.
- Strongest supported finding: PENDING.
- Losing/inconclusive observations: PENDING.
- Release implication, distinct from benchmark implication: PENDING.

Do not fill this template with earlier twelve-trial walkthrough results. Do not overwrite the historical incomplete report as though its attempts never occurred. Finalize only after Agent 2 hands off retained receipts.
