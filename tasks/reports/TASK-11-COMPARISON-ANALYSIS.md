# Task 11 — reconciled four-cell observed comparison

**COMPLETE for offline reconciliation and bounded reporting, not a product-readiness, efficiency or release approval.** No models, candidate code or sealed scripts were executed for this analysis. All original cells and failures are retained.

## Conclusion

Runtime checks passed in all four cells, but only two native turns finished; no graph advantage established.

Graph-enabled trials recorded higher input in each task pair; elapsed direction differed by task. These records do not identify a causal graph effect, paid-equivalent savings, general efficiency advantage, safe test skipping, or cross-session memory benefit. Runtime assertions and a native final answer are separate outcomes.

## Evidence lock and method

- Imported original evidence commit `4b81658c0c7ca010b69c6467c1c1b621f9deea61` onto the local review branch as `73cc415`; exact original parent/application `8e83804448cf251a26735d70c5a66f5b0d26db67`. No application or trial candidate source integrated.
- SDK source `754254c08fe1c3eda18b69da3d336106fe8d72d6`; OpenCode 1.19.3; only `opencode/deepseek-v4.1-flash-free`. Four ordered cells, one attempt each, two task instances. The prompt-issued budget was 900 seconds; startup was separate.
- Frozen protocol SHA-256 `31827cb48c2a684660fb08197aca3775cbb05294d8ebf4c8310aad143b22d459`. The pretrial 100-path overflow and explicit 12-path graph-scope amendment remain in the protocol. Static truncation/unresolved relationships are not comprehensive impact coverage.
- [53-entry original manifest](evidence/task-09-observed-comparison/payload/SHA256-MANIFEST.json) and protocol/acceptance hashes verified. Each receipt was reconciled with completed-step sums, native timestamps, tool traces, test logs, CSV and original results; a separate standard-library CSV path checked headline counts and paired input differences.
- [Portable offline helper](../../scripts/analyze-task9-sanitized.py) reads only sanitized records. It does **not** reconstruct private raw provider exports, complete candidate manifests, graph restoration or exact provider consumption. The original sealed `payload/analyze.py` is not a portable rerun recipe.
- [Profile review](evidence/task-11-comparison-analysis/profile-review.txt): four rows, no duplicates or missing cells. Constant attempts=1 is by design; cache-write=0 and charge=0 are exported observations; retry usage=UNKNOWN is deliberately categorical. No exclusions or outlier removal.
- [Agent 2 audit](evidence/task-11-comparison-analysis/TASK9-TASK11-12-READONLY-AUDIT.md) is a re-audit by the Task 9 builder/operator, not independent-human certification. Integration reconciliation was performed separately by Agent 1.

## Correctness and native completion first

| Trial | Task / mode | Native terminal | Frozen external checks | Selected regressions | Repository review |
| --- | --- | --- | ---: | ---: | --- |
| 1 | structured-invalid-characters / ordinary | FINAL_RESPONSE | 3 passed | 991 passed | PASS_IN_REVIEWED_DIFF |
| 2 | has-tool-lookup / ordinary | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 passed | 647 passed | CHANGES_REQUESTED |
| 3 | structured-invalid-characters / graph | FINAL_RESPONSE | 3 passed | 995 passed | PASS_IN_REVIEWED_DIFF |
| 4 | has-tool-lookup / graph | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 passed | 647 passed | CHANGES_REQUESTED |

Selected regressions are `tests/shared` for diagnostics and `tests/server/mcpserver` for lookup; not the full SDK suite. Different added test cases mean passing-count differences are not a quality score. All verifier exit codes, candidate-unchanged checks and trial candidate diff checks passed in the retained records; they were not rerun here.

Both lookup turns stopped after the operator rejected writes to unowned shared temporary pyright configuration. Each has five new test functions without return annotations; ordinary/graph adds four/two no-cover pragmas. Typechecker diagnostics remain unresolved. Differently scoped pyright error totals must not rank quality; shell exit zero did not mean clean typechecking. These are **not clean completions**, notwithstanding runtime checks.

## Descriptive wall and usage observations

| Trial | Prompt → last message (s) | Prompt → terminal observation (s) | Input | Output | Reasoning | Cache read | Cache write |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 420.8 | 488.5 | 22,081 | 2,466 | 1,246 | 220,800 | 0 |
| 2 | 462.1 | 515.7 | 32,918 | 3,733 | 2,459 | 409,856 | 0 |
| 3 | 323.9 | 341.4 | 33,239 | 3,743 | 1,771 | 275,712 | 0 |
| 4 | 585.5 | 624.7 | 99,651 | 6,397 | 786 | 805,120 | 0 |

Keep categories separate: output/reasoning/cache are not added into a fabricated billable total. Reported free-model charge was zero; retry/interrupted-call usage stays UNKNOWN. Neither zero charge nor input differences establish paid-model savings.

Wall includes tools, network/provider and operator permission waits. A permission-stopped last message is not a successful-answer endpoint. Startup and collection clocks remain separately available in the [reconciled table](evidence/task-11-comparison-analysis/reconciled-trials.csv). Trial 1 overlapped Task 7 model review and small verification work; all cells share VM/provider conditions. No isolated operator-delay subtraction, pooled speedup, significance, p95 or causal ranking is warranted.

[Observed input chart](evidence/task-11-comparison-analysis/task11_input_comparison_notion_agent_chart.html) uses the same [computed evidence object](evidence/task-11-comparison-analysis/analysis.json). The [specification](evidence/task-11-comparison-analysis/input-chart-spec.json) preserves both tasks and ordinary/graph series without pooling. It shows reported input only, not total/provider-billed tokens. Static canonical-builder preflight passed; no new browser measurement was performed.

## Tools and graph evidence

| Trial | All tool calls | Error-status calls | Native read attempts | MCP calls | Managed context UTF-8 bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 15 | 0 | 3 | 0 | 0 |
| 2 | 22 | 1 | 5 | 0 | 0 |
| 3 | 17 | 0 | 3 | 1 | 12,660 |
| 4 | 22 | 2 | 7 | 0 | 12,168 |

Count one retained invocation/part, not browser GET polling. Native read attempts include errors and offset reads; shell searches/reads are separately classified in original tool traces. They are not total source access or redundant-work counts. Trial 3 made one snapshot-inspection MCP call; trial 4 made none. Both graph cells have a host-observed managed context part; this does not prove exact provider consumption, a dependency discovery, or that graph evidence caused a better patch.

## Failures and unknowns preserved

- All four original collector PIPE/JSON failures remain; a regular-file capture correction collected the same attempts, not reruns.
- Graph doctor pending=0 does not establish end-to-end completeness. Scope is bounded to 12 paths, shallow history and static analysis; unresolved calls remain.
- Four ordered cells, one repository/model and no repeats: not the previously proposed 12/18-run study. No baseline handoff/memory claim is inferred from additive maintenance tasks.
- Earlier interrupted pilot and twelve-trial walkthrough remain separate historical experiments, not retrospectively rescored.
- Sanitized evidence contains usernames, absolute paths, IDs and timestamps; it is not anonymous or a self-contained rerunnable benchmark. Private homes/raw reasoning/provider exports/graph dumps are excluded.
- The original import full-diff whitespace check returns exit 2 on ten immutable evidence/diagnostic paths. New reporting whitespace checks are separate. Original bytes are preserved.
- Upstream SDK [MIT attribution](../../third_party/README.md) is added outside the sealed payload. Source/context redistribution is not upstream acceptance.

## Reproduce the offline record check

Use a review environment with Python and pandas already installed; no application services or credentials are required. Choose a new output directory:

```bash
python scripts/analyze-task9-sanitized.py \
  --payload tasks/reports/evidence/task-09-observed-comparison/payload \
  --out /absolute/path/to/new-review-output
```

This validates public record consistency, not rerun candidate correctness or provider billing. It leaves the original payload untouched.

## Release implication

Evidence-only integration is accepted for review packaging. No SDK trial patch or owned-synthetic candidate is approved/integrated. [Task 10](TASK-10-READONLY-BROWSER-VERIFICATION.md) remains a scoped read-only application PASS, not broader release certification. Next product work should repair lookup convention/typechecking issues in a separate candidate branch and repeat a controlled evaluation only under a new authorized protocol—not rewrite these losing/inconclusive observations. No push, shared-main merge or deployment was performed.
