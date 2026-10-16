# T-09 checkpoint — source replacement, context and reported memory

This branch is **IN_PROGRESS**, not a replacement production release. T-08 main
and ports 3000/8001 remain untouched. No new video or paid model benchmark.

## Implemented at this checkpoint
- `/api/v1/diff/impact` + MCP `simulate_diff_impact`: strict multi-file Python
  unified diff, pure rename, addition/deletion, or explicit `file_bodies` JSON map
  (null deletes). Rebuild outgoing imports and all captured-source static CALLS
  in GRAPH.COPY. The base graph and user's working tree are never changed.
- Dependency differences compare **reparsed captured before-source vs final-source**
  using the same resolver, not mismatched indexing versions. Native graph queries
  and source-derived pre-state reachability retain the before/after impact union.
  Removed/renamed/signature/async-changed functions report candidate callers.
  Candidate tests are not safe-skip proof; deleted tests are not runnable arguments.
- `/api/v1/context/locate` + MCP `locate_context`: lexical path/symbol ranking with
  native File PageRank tie-break; bounded signatures, importer/caller/callee/rule
  evidence and source-bound finding references. Actual compact JSON byte budget
  2–8 KiB and character-count//4 equivalents, not billed tokens or a fair-agent
  benchmark. Source constraints remain distinct from ACTIVE local policies.
- `/api/v1/context/symbol-source` + MCP `get_symbol_source`: exact captured symbol
  coordinates/hash and up to 8,000 UTF-8 source bytes. Ambiguous names fail closed.
- POST/GET `/api/v1/memory/findings` + MCP `record_verified_finding` /
  `recall_task_memory`: caller-supplied exact indexed source hashes, evidence note,
  scoped policy/constraint digest. Findings are **AGENT_REPORTED_EVIDENCE**, not
  independently executed verification. Changed/missing supporting files or
  governing policy flag STALE. Source/evidence is never an instruction authority.
- `/api/v1/activity`: real invocations of all ten MCP tools, shared via FalkorDB
  between stdio and REST processes. Per-tenant latest 500, timestamp+ID pagination.
  Metadata excludes raw arguments, source, questions, notes and exception messages.
  Result size measures compact JSON value bytes, excluding protocol envelopes.
- `/workbench`: four-view functional preview for those APIs. Classic `/` retains
  all three tracks and Obsidian vault/recovery. New MCP modal lists ten tools;
  all five original interfaces are unchanged. Browser REST calls are not logged
  as agent invocations. No external live-agent run is claimed.

## Analysis and trust limits
Replacement analysis requires all indexed Python File nodes to have exact captured
source and matching SHA-256; maximum 10,000 captured files / 16 MB source, 20 changed
files, 1 MB and 10,000 AST observations per final file, 128 KB pasted diff. Binary,
symlink, mode-only and quoted Git path formats are rejected. Rename destinations
must not already exist; rename chains/swaps are unsupported. Static Python dispatch
is conservative: dynamic/ambiguous calls remain unresolved. Existing source files
with AST parse failures are listed in `parse_coverage`, with a visible UI warning;
missing syntax-derived edges must never be interpreted as no impact. Non-Python replacement
is not implemented. Legacy snippet/unified-overlay semantics are preserved in
`/track1/sandbox-audit`; use the new route for actual removals.

Every context/source/finding response explicitly says
`PINNED_SNAPSHOT_WORKSPACE_NOT_CHECKED`. An uncommitted local edit is **not** detected
by this checkpoint; never treat CURRENT_AT_INDEXED_SNAPSHOT as current working-tree
verification. Actual workspace sync is the next milestone. Existing locks are
process-local; no distributed, transactional snapshot-isolation claim is made.
Activity logging is best effort with an explicit stderr warning on failure, so
successful mutations do not falsely appear failed just because logging failed.

## Isolated preview on the VM
The development checkout is `~/ChronosGraph-t09`, branch
`build/t09-repo-workbench-and-trusted-memory`. Preview frontend/backend are bound
only to 127.0.0.1 ports **3004 / 8004**, not publicly exposed. On your laptop:

```sh
gcloud compute ssh nakulmaurya13579@instance-falkordb-hackathon \
  --project=amazon-ml-509907 --zone=us-central1-a -- \
  -N -L 3004:127.0.0.1:3004 -L 8004:127.0.0.1:8004
```

Open `http://127.0.0.1:3004/workbench` and API docs
`http://127.0.0.1:8004/docs`. Keep the terminal open. This tunnel is separate from
accepted production's 3000/8001 tunnel. MCP uses this checkout's backend as `cwd`;
configure the installed Python environment explicitly. Browser REST activity is
not falsely shown as a coding-agent tool invocation.

## Remaining milestones (not delivered)
- Safe allowlisted local/public-GitHub connection, selected branch metadata,
  mixed-file/Directory graph, JS/TS imports, docstrings, declared CODEOWNERS.
- Explicit incremental workspace sync, rename/deletion reconciliation, HEAD guard,
  source/policy freshness in every existing response, persistent-volume review.
- Primary workbench promotion/connection UI, activity-driven graph highlights,
  richer caller/owner drill-down, platform-specific startup validation.
- Actual Windows/macOS verification. Node 20/22 test-loader compatibility is
  implemented; see [runtime/platform boundaries](t09-platform-setup.md).
- Same-agent/model/task A/B trials with measured bytes, calls and timings; indexing
  separated from cold/warm runs. No paid calls authorized and no fabricated results.
- Final release gate, merge/publication and production rollout after approval.

The [fair external-agent A/B protocol](t09-agent-evaluation.md) is written, but its
trials remain NOT RUN. A compact focused response is not a measured improvement
over an ordinary agent's native search workflow.
