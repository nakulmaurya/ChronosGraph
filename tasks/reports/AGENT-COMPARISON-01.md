# Agent comparison 01 — prepared, no completed comparison result

**Status: BLOCKED / no completed scored trial.** Not a graph win, cost saving, provider failure or completed four-run experiment.

## Predeclaration

See `tasks/experiments/agent-comparison-01/protocol.json`, independent test files and `runner.py`. Public repository `modelcontextprotocol/python-sdk`, pinned revision `754254c08fe1c3eda18b69da3d336106fe8d72d6`; OpenCode 1.19.3, free `opencode/deepseek-v4.1-flash-free`. No paid fallback.

Two requested maintenance features, not fabricated upstream defects:

1. Synchronous exact `has_tool` lookup across MCPServer and ToolManager; delegate without mutating/executing tools. Multi-file dependency change.
2. Structured unique first-seen invalid characters on ToolNameValidationResult, independent list defaults, constructor/early-return/warnings compatibility.

Acceptance was frozen before agent execution and failed on unmodified source for the expected missing features (five failures), not missing dependencies. Source was inspected to define tests. The repository was previously used for different task instances; these instances were not development tuning targets.

Seed 20261018 gave order: ordinary invalid-characters; ordinary has-tool; graph invalid-characters; graph has-tool. Same prompts, revision, free model, native permissions and 900-second wall budgets. Fresh isolated HOME/config/data/cache and Git worktree per cell. Provider-side cache not controllable. No automatic losing-run retries; graph adds managed context/MCP only.

## Observations retained

| Stage | Result |
|---|---|
| First preparation | HTTP422 CONSTRAINT_OVERFLOW: 100-path mandatory graph pack exceeded 12 KB. No agent trial started during this setup. Failure retained, not hidden. |
| Explicit pre-run amendment | Added user-selected `analysis_path_limit` to the product; graph cells explicitly use 12 paths. Truncation/unknown relationships remain visible; mandatory evidence in selected scope is not silently dropped. Default remains 100. |
| Second preparation | Fresh ingestion 17.9824 s; four isolated worktrees/configurations prepared. Not indexing+refresh total for all setup attempts; first attempt ingestion cost not recovered. |
| Ordinary cell 1 | Actual TUI launched and displayed the pinned free model. Command to send frozen prompt was issued, but SSH stopped responding before acknowledgment. Whether prompt started is UNCONFIRMED; inspect retained state/export before further action. |
| Cells 2–4 | Not launched at last acknowledged state. |
| Completed independent task checks | None on pilot agent candidates. |
| Outcome/time/tool/usage comparison | Unavailable. Do not infer zero usage/cost or success from missing receipts. |

Latest root pointer on VM: `/tmp/chronos-public-pilot-v2-root`; first failed setup pointer `/tmp/chronos-public-pilot-root`. Private exports are excluded from release. Actual completed runs from older different experiments are not substituted into this pilot.

## Runnable continuation

Runner preparation uses native FalkorDB and a trusted loopback task API. Follow its `--help` and `docs/task-runtime-hardening-recovery.md`. `launch`/`prompt` drive the actual TUI, not an agent prompt API. Inspect startup and permissions; allow writes/bash/MCP once only after review. `stop` interrupts after the declared wall deadline. Supported `session list`/`export` is used only to collect actual observations. `verify` runs frozen external acceptance, existing relevant regression directory, diff whitespace and exact before/after candidate digest checks. Manual requirement/unintended-diff review remains mandatory; passing tests alone do not mark global success.

The runner was syntax-checked; preparation/launch were exercised before the connectivity loss. Latest collect/verify/stop recovery additions have not had end-to-end VM validation. This is an executable incomplete runner, not a certified benchmark harness. On recovery retain permission waits and any provider error, timed-out/ambiguous attempt and all failing checks. Separate reported completed-step categories from cache, unknown retry usage, actual free charge and any explicitly priced equivalent. No statistical or universal-efficiency claim is supported.
