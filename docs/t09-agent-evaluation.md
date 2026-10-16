# T-09 — fair external-agent evaluation protocol

Status: **PROTOCOL ONLY — EXTERNAL RUNS NOT RUN**. No paid calls authorized.
Native FastMCP protocol integration tests exercise real tools, not an autonomous
Claude Code, Cursor or OpenCode coding task. They do not establish agent savings.

## Register the experiment before running it

Choose three independently checkable tasks on a pinned MCP Python SDK revision:
one navigation/debugging task, one cross-module refactor, and one test-impact task.
Record exact issue/task text, base commit, acceptance tests and expected behavior.
Do not invent an upstream bug merely to favor the graph. A maintainer should
approve task relevance before results are presented as a product benchmark.

For every pair use the **same** agent version, model/version/provider, prompt,
token/turn/time budget, source commit, tools allowed and verification environment.
Use two fresh working directories and sessions, with no shared conversation,
agent cache or cross-run findings. Randomize A/B order; repeat each pair at least
three times. Record tool and provider errors, failed attempts and censored runs.

| Arm | Allowed retrieval |
| --- | --- |
| A — normal agent | Its ordinary `rg`, glob, `Read`, shell and editing tools. No forced full-repo dump or disabled search. |
| B — graph-assisted | All the same native tools **plus** ChronosGraph MCP and the published skill. Raw reads remain available when useful. |

Freeze graph ingestion configuration and report its time/storage separately.
Distinguish cold-index, warm-index and cross-session memory conditions. Do not
preload a hand-written solution or B-only findings for the basic retrieval test.
For a separate compaction experiment, apply the same context limit/compaction
trigger to both arms and record exactly what handoff material each retains.

## Measure the whole workflow

- Task success against unchanged acceptance tests, reviewer correctness and
  unintended changes; not just graph-query speed.
- All tool calls and failures, not only ChronosGraph calls.
- Actual UTF-8 bytes returned to the agent for **all** retrieval tools, including
  raw reads, source expansion and graph responses. Distinguish tool data from
  protocol envelopes and repeated returns.
- Provider-reported input/output/cached tokens, cost and wall time when available.
  `chars // 4` is a deterministic proxy, never actual provider billing.
- Source bytes indexed vs returned graph bytes as a **separate focused-slice
  measurement**, not evidence that an ordinary agent would read the whole repo.
- Ingestion time, graph size and cold/warm query latency.

ChronosGraph activity tracks only its MCP invocations. Obtain other tool counts,
raw reads and provider usage from the agent's consented local trace. Do not
collect credentials, private prompts or source beyond the approved experiment.

## Reproducible evidence record

Use one JSON record per task/arm/repetition with:

```json
{
  "status": "NOT_RUN",
  "task_id": "",
  "task_text_sha256": "",
  "repository_commit": "",
  "chronosgraph_commit": "",
  "agent_version": "",
  "model_version": "",
  "arm": "A_or_B",
  "repetition": 0,
  "order_seed": 0,
  "index_condition": "cold_or_warm_or_memory",
  "success": null,
  "tool_calls_all": null,
  "tool_errors": null,
  "retrieval_utf8_bytes_all": null,
  "provider_input_tokens": null,
  "provider_output_tokens": null,
  "provider_cached_tokens": null,
  "wall_seconds": null,
  "ingestion_seconds": null,
  "review_notes": ""
}
```

Publish individual runs, medians/ranges, failures and exact commands, not only
the best pair. No numerical improvement claim until these runs exist.