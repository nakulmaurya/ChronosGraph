# Task 9 — observed four-cell comparison

**Outcome: all four frozen runtime check sets passed; two native turns finished and two were permission-stopped. No graph advantage or token/cost savings established.**

No attempts were rerun. No candidate was approved, merged, pushed or deployed.

## Protocol and evidence
- Source: `modelcontextprotocol/python-sdk` at `754254c08fe1c3eda18b69da3d336106fe8d72d6`; application `8e83804448cf251a26735d70c5a66f5b0d26db67`.
- Actual OpenCode TUI 1.19.3, only free `opencode/deepseek-v4.1-flash-free`; same per-task prompts, frozen checks, permissions, source and 900-second prompt-to-wall budgets. Four sequential attempts, exactly one per cell.
- Isolated Task6/9 homes, worktrees, DB6386/API8016. Shared Task3/7 application worktrees, DB6381/API8015 were not modified.
- Every candidate digest was unchanged across independent tests and again at final preservation. Frozen runner and acceptance SHA-256 values rechecked.

## Observed outcomes

| # | Task / condition | Native terminal | External tests | Selected regressions | Manual diff review |
|---|---|---|---:|---:|---|
| 1 | structured-invalid-characters / ordinary | FINAL_RESPONSE | 3 passed | 991 passed | Bounded requirements/unintended-diff PASS |
| 2 | has-tool-lookup / ordinary | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 passed | 647 passed | Behavior PASS; conventions need changes |
| 3 | structured-invalid-characters / graph | FINAL_RESPONSE | 3 passed | 995 passed | Bounded requirements/unintended-diff PASS |
| 4 | has-tool-lookup / graph | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 passed | 647 passed | Behavior PASS; conventions need changes |

Selected regressions were `tests/shared` for invalid-character tasks and `tests/server/mcpserver` for lookup tasks. Prepared baselines: 984 and 642 respectively. Added cases differ, so passing-count differences are not a quality score. Acceptance checks were run independently, outside native trial wall intervals. Diff and candidate-unchanged checks also passed in every cell.

## Wall observations and native completed-step usage

| # | Prompt → last native message (s) | Prompt → observed terminal (s) | Input | Output | Reasoning | Cache read | Cache write |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 420.8 | 488.5 | 22,081 | 2,466 | 1,246 | 220,800 | 0 |
| 2 | 462.1 | 515.7 | 32,918 | 3,733 | 2,459 | 409,856 | 0 |
| 3 | 323.9 | 341.4 | 33,239 | 3,743 | 1,771 | 275,712 | 0 |
| 4 | 585.5 | 624.7 | 99,651 | 6,397 | 786 | 805,120 | 0 |

Timing includes permission waits, provider/network and tools, not pure model latency. For permission-stopped turns, the last native message timestamp is not a successful-answer time; terminal observation is separately shown. Startup before prompt and wall-to-collection are separate in `trials.csv`. Do not subtract operator delays without independent measurements.

Token categories are preserved as exported, not summed into a fabricated billable total. Message-level usage independently matched completed-step sums and collector receipts. Provider-side caching is uncontrolled and retry usage UNKNOWN. Harness-reported cost was 0 throughout the authorized free model; no paid-equivalent savings estimate. Graph input was higher in both task pairs; wall direction was mixed. These are observations, not causal rankings.

## Actual tool traces and intervention

| # | Tool calls | Error-status tools | Native read attempts | Repeated read paths | Allow-once / reject |
|---|---:|---:|---:|---:|---:|
| 1 | 15 | 0 | 3 | 0 | 10 / 0 |
| 2 | 22 | 1 | 5 | 1 | 17 / 1 |
| 3 | 17 | 0 | 3 | 1 | 13 / 0 |
| 4 | 22 | 2 | 7 | 0 | 14 / 1 |

Native read attempts include failed and offset-based reads; repeated path is not proof of redundant work. Shell grep/diff/import probes are separately classified per command in `trial-*/tool-trace.json`, so native reads are not a total source-access metric. Full private supported exports, terminal ANSI, permission screens and resource samples remain in the private evidence, not the release.
- Trial3 made one actual ChronosGraph snapshot-inspection MCP call. Trial4 made no native MCP tool call. Both graph exports contained one managed context part (12,660 and 12,168 UTF-8 bytes); that is host-side evidence, not proof of exact provider consumption.
- Trial2 rejected a write to `/tmp/opencode/pyrightconfig.json`; trial4 rejected `/tmp/pyrightconfig.json`. These were operator isolation decisions, not a new human instruction. Native export error text says “user rejected”; operator provenance is recorded. No continuation or retry followed.
- Trial4 also retained a failed read of nonexistent `src/mcp/server/mcpserver/tools.py`. Trial1 retained a nonzero shell capability probe. No provider message errors were observed; that does not mean no failed tools or checks.
- Lookup candidates have five new test functions without return annotations each, plus four/two new no-cover pragmas. Both have unresolved native typechecker diagnostics. They are not clean ready-to-ship successes. Invalid-character diffs passed bounded review; zero-error typechecker output still included a missing .venv notice.

## Harness and environmental limitations
- One attempt per cell; fixed order and no statistical or causal inference.
- Trial1 overlapped Agent1 Task7 free model review and small pytest/export/hash workload; all runs use shared VM/provider.
- Wall intervals include operator permission waits, network/provider and local tools. Not provider-only latency; operator-only waits not independently separable.
- Both has_tool turns stopped after operator rejected unowned shared /tmp typechecker config writes. No model restart or continuation.
- Pyright output reported 15 errors in ordinary has_tool and 39 in graph has_tool (latter also checks test file); scopes differ and totals are not a comparative quality metric. Missing .venv/source-resolution diagnostics retained; root cause not proven. Shell pipelines can report exit0 despite diagnostics.
- Each has_tool candidate adds five tests without return annotations; ordinary adds four no-cover pragmas, graph two. Runtime success is not repository-wide readiness.
- All four frozen collectors initially failed on truncated CLI JSON captured through PIPE. Original failures retained; regular-file capture wrapper ran the same collector logic, no trial reruns.
- Graph doctor pending0 but completeness NOT_PROVEN. Exported synthetic context does not prove exact provider consumption or billing effects.
- Graph scope12paths, static unresolved calls and shallow one-commit history; no comprehensive impact/ownership claim.
- Free-model reported cost0 does not establish paid-equivalent savings. Provider cache uncontrolled, retry usage UNKNOWN.
- Original pre-reboot interrupted pilot remains incomplete/unknown; Task6 reconstructed pilot-v2 is separately disclosed.
- No approval/merge/push/deployment; source candidates remain isolated.

## Integrity and handoff
The following SHA-256 candidate digests describe isolated candidates, not approvals:

| Trial | Candidate digest |
|---|---|
| 1 | `724aa8f203747b324bc5a7f31265623da6d7b0954bbec2543425d84228fa9b1e` |
| 2 | `31380ee4dccf0ce3b699133fa0556abb443cc444497c7d5f9a39e4d865009dff` |
| 3 | `e9f42a9afe7cdec095d5b2541d8be8eac7f63ba8cdb6af70ca7359e492771b22` |
| 4 | `e602cc367a30846b5a146289355f1a9e140e24875069deeae1438015265e822b` |

- `comparison-results.json`: single computed evidence object, complete rows, tool counts, reviews, checks and caveats.
- `trial-*/receipt.json`, `manual-review.json`, `tool-trace.json`, `candidate.patch` and verifier logs: sanitized handoff evidence.
- VM Task9 `sealed-inputs/`: frozen checks/protocol, exact final candidate files, context telemetry/configuration and operator scripts.
- VM Task9 `final-graph-backup/`: native DUMP payloads only from owned DB6386; compatibility image and hashes retained. Restoration was not exercised.
- Private archive additionally preserves full native exports/terminal traces, including model reasoning; do not publish. Sanitized release excludes these exports, homes, credentials and graph dumps.
- See adjacent final archive SHA-256 sidecars and `TASK9-COMPLETE.json` for verified VM and second-copy backup status.
