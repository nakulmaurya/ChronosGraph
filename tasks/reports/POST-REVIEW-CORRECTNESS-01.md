# POST-REVIEW-CORRECTNESS-01 — correctness-first hardening

Status: **READY_FOR_REVIEW — first work package only**. Baseline: `dd8f44a`.
Branch: `build/post-review-correctness`. No main merge or VM deployment is implied.

## Changes

- New pinned UTF-8 byte continuation for REST `context/symbol-source` and MCP
  `get_symbol_source`. Every continuation must echo the file's original SHA-256
  and source revision; mismatch is HTTP 409. Invalid byte boundaries/ranges are
  HTTP 422. Existing first-page calls retain the 8,000-byte default cap.
- Exact file paths, case-sensitive symbol names and qualified symbols use indexed
  candidate selection, followed by bounded expansion. General prose retains the
  old bounded lexical inventory fallback. Exact mode deliberately does not add
  unrelated lexical-only entry files. Both modes label their strategy/coverage.
- Shared pytest default-filename classifier across context, full replacement
  diff, legacy sandbox, wiki/statistics and benchmark denominators. Supports
  `test_*.py` and `*_test.py`; does not count arbitrary helpers in `tests/` as
  test files. Deleted tests remain evidence but are not runnable recommendations.
  Collection remains unknown, including custom pytest collection: no safe-skip claim.
- Policy ranking now considers ACTIVE governed candidates before LIMIT 4. It
  uses exact cosine-distance ranking over those current candidates, not the
  nearest four mixed-status vector-index neighbors. This trades scalability of
  very large policy sets for reliable current-rule recall; it is not semantic RAG.
- New independent reindex-audit and paired lookup-profile scripts. CI includes
  the new native source/classification/policy regressions.

## Fresh GraphRAG source audit — PASS within stated scope

Source revision: `35e67a0b27fdcc7f2c28508b09e86169851a8187`.
All **154** Python files and the exact captured-source digest match the historical
benchmark population. The independent stdlib-AST absolute-import oracle covers
**134** files and excludes **20** (relative imports/parse exclusions per oracle).

- Expected in-scope imports: **506**.
- Fresh indexed in-scope imports: **506**; all are true positives.
- Missing: **0**. Extra: **0**. Historical missing edges recovered: **506/506**.
- The recheck created a NEW graph and verified deletion. No existing deployment
  graph was replaced. The original `benchmark-results.json` is unchanged.
- This does not establish full Python dependency/runtime correctness. Dynamic
  dispatch, excluded imports and unresolved relationships remain limitations.

See [complete audit receipt](post-review-correctness/fresh-graphrag-audit.json).
Rebuilding with the **existing current analyzer** corrected the stale index;
there was no need to rewrite the parser for this discrepancy.

## Paired lookup profile — bounded evidence, not a universal SLA

One predefined real GraphRAG task: `_ensure_ontology_initialized`, with target
`graphrag_sdk/src/graphrag_sdk/api/main.py`. Twenty paired samples with randomized
within-pair order and one warm-up per mode, on the same fresh pinned graph.

- Legacy `dd8f44a` locator p95: **108.205 ms**.
- New exact-symbol locator p95: **7.116 ms**.
- Entry inventories transferred: **154 files → 1 file**.
- Expected target entry and target import routes retained.
- `GRAPH.EXPLAIN` confirms an index scan for symbol selection.

These same-host measurements isolate the locator change, not the full agent
workflow. They are not comparable to a different historical host's p95 as a
controlled experiment. Other queries, inventories, policy/memory/ownership work
and other repositories can still exceed 50 ms. No model tokens or costs measured.

See [paired raw samples and query plan](post-review-correctness/context-profile.json).

## Verification

- PASS: complete native backend suite: **355 passed**, no failures/skips,
  **62.42 seconds**; four pinned public repository graphs present.
- PASS: **22 new native regressions**, including gapless large-Unicode module
  and symbol reconstruction, wrong revision/content pins, invalid UTF-8 offset,
  actual FastMCP and REST continuation, default/suffix/helper/deleted tests,
  obsolete-neighbor policy starvation and exact-path/symbol/fallback discovery.
- PASS: frontend **34 unit tests**, zero skips; typecheck; production build.
- PASS: locked backend dependency install and `pip check`.
- PASS: **25 live browser smoke checks**, real local API/DB, no response stubs,
  no uncaught browser errors; desktop and 390px mobile. See
  [smoke receipt](post-review-correctness/browser-smoke.json).
- PASS: scoped release hygiene: no credential-pattern findings, forbidden tracked
  artifacts, orphan test/sandbox graphs or E2E fixture nodes. This is heuristic,
  not a security audit. See [receipt](post-review-correctness/release-hygiene.json).
- Initial smoke setup attempts failed before completion: OS Python lacked the
  locked dependencies; then the five recent GitHub PRs had no paths matching the
  pinned FalkorDB-py snapshot. Corrected the interpreter and appended 40 real
  pinned Git commit records (38 file links) via existing ingestion. Final run
  passed. No invented commit or MODIFIES fixture was inserted.
- VM Docker/image parity, deployed preview and real-agent comparisons: **NOT RUN**.

Environment details: [receipt](post-review-correctness/environment.json).
Native tests used an isolated local FalkorDB Lite runtime, not the production VM.
The host's system libraries were not modified.

## Source pagination contract

1. Request `file_path`, `symbol_name` (`__module__` includes imports/constants),
   optional `max_bytes` (4..8000).
2. Append the returned `source`. While `next_start_byte` is not null, request
   that `start_byte`, unchanged file/symbol/tenant, and echo `source_sha256` as
   `expected_source_sha256`, `source_revision` as `expected_source_revision`.
3. Offsets are half-open UTF-8 byte ranges **within the selected symbol**. Each
   page ends at a complete character boundary. Preserve the original ordering.
4. On HTTP 409, discard accumulated pages and restart. `complete_source` is true
   only for a complete single-page response. A final continuation page may still
   say `truncated`; `has_more=false` is the end-of-stream indicator.
5. Missing legacy revision metadata is not silently bypassed. Reindex such a
   snapshot before attempting a pinned continuation.

## Reproduce

```bash
python -m pytest backend/tests/test_post_review_correctness.py backend/tests/test_context_memory.py -v
python scripts/audit-fresh-snapshot.py \
  --source /path/to/local/graphrag-git-repo \
  --revision 35e67a0b27fdcc7f2c28508b09e86169851a8187 \
  --historical-report tasks/reports/benchmark-results.json \
  --output /tmp/fresh-graphrag-audit.json
```

The audit refuses to overwrite reports or existing graphs. Use `--keep-graph`
only when intentionally retaining an owned graph for profiling; remove it after
use. The profile script requires Git baseline `dd8f44a` available locally.

## Remaining work / boundaries

- New audit graphs do not replace the saved VM snapshot automatically. Rebuild
  and verify an accepted snapshot in the actual configured durable deployment.
- Restore VM SSH access; verify known host fingerprint; record source and snapshot
  revisions before deployment. No working SSH credentials carried into this chat.
- Next work packages: organizational document/incident/team evidence chain,
  cross-snapshot memory revalidation, stronger real-repository agent tasks,
  18-run/12-run fair comparison, integrated acceptance and final packaging.
- No independent external reviewer, new autonomous-agent evaluation, user study,
  security sandbox, prize qualification or submission success is claimed.
