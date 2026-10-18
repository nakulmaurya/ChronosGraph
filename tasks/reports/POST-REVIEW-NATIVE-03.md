# Native durable-deployment hardening and release identity

Status: bounded implementation and native VM verification PASS; not a claim that all hackathon acceptance packages are complete. Parent application commit: c9e09cd0b16e707e455c44a81278a8e2cd610b38. Main was not merged or replaced.

## Deployment-specific failure discovered, not hidden

The first full VM run against a separate, AOF-enabled native FalkorDB container returned **1 failed, 369 passed, 4 errors**. Its original output is retained in `POST-REVIEW-NATIVE-03/backend-full.log.gz`. The affected service returned 503 because native `GRAPH.COPY` returned `GRAPH.COPY failed, could not fork`. This is not evidence that the prior ephemeral local test result was fabricated: the failure appeared under durable native-server persistence.

A controlled five-run reproduction explicitly requested a real AOF rewrite, verified that rewriting was active, and called native GRAPH.COPY: all five copies refused the fork. No mocked database, memory-pressure assumption, persistence disablement, or user database modification was used.

## Bounded fix

`FalkorDBManager.copy_graph` retries only that exact Redis ResponseError, with exponential backoff and a maximum five-second retry-wait window. It never retries transport errors, other server errors, or a destination found to exist. It does not delete an ambiguous destination, lock the source, or claim to freeze concurrent source mutations. Command execution/transport time is not a five-second request deadline. Persistent failure remains an error.

Both ephemeral sandbox creation and owned workflow benchmark copies use this wrapper. Ownership-index copy parity tests use the same path. Finally-based owned graph cleanup remains in force. Native regressions cover successful copy, existing-destination rejection without overwriting, and cleanup when the sandbox body raises.

The opt-in `scripts/verify-copy-persistence-contention.py` requires explicit disposable-database consent and actual AOF enablement. All five native overlaps reproduced raw refusal and passed through the wrapper, with observed copy-plus-read time 212–329 ms. This is not a universal latency SLA.

## Source and application identity

The read-only `/api/v1/release/identity` route returns an optional, strictly validated full lowercase commit supplied by `CHRONOSGRAPH_BUILD_COMMIT`. Missing/malformed values are UNRECORDED; no Git/path inference or private host paths are exposed. The UI separately embeds `NEXT_PUBLIC_CHRONOSGRAPH_BUILD_COMMIT` at build time and compares it to the API declaration, while retaining the selected snapshot's source revision. Match, mismatch and unknown are distinct. These are **deployment declarations, not cryptographic attestations**. A declaration match alone cannot prove a clean build.

## Checks actually executed

- Native VM: Python 3.13.5, exact hashed Linux backend requirements, `pip check` PASS.
- FalkorDB container image: `falkordb/falkordb@sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a`, bound only to loopback review port 6381, separate named volume, appendonly=yes. Existing database and preview were not replaced.
- Full native VM backend suite after fix: **380 passed, zero failures/errors/skips**, 124.80 seconds. Original failure and fixed run both retained.
- Native AOF contention: **5/5 controlled overlaps passed after raw refusal**, persistence stayed enabled, owned probes cleaned.
- Independent stdlib-AST GraphRAG audit on the fresh durable corpus: 154 captured files, 134 eligible, 20 excluded; expected=observed=true-positive **506**, missing=extra=0. Same source revision and digest as the earlier audit. Historical missing-506 result preserved in its original report. Oracle limitations remain: unambiguous absolute imports only, not dynamic runtime truth.
- Scripted demonstration: two fresh strict stdio MCP server processes; actual docs-only Git commit and normal snapshot refresh; predecessor finding VALID_FOR_THIS_SNAPSHOT under STATIC_NEIGHBORHOOD, explicitly **no test execution on the new revision**. This is not an autonomous model comparison.
- Actual SIGKILL of only the isolated review database, restart from its named AOF volume, and another fresh strict MCP server: identical retained finding/revalidation response, organizational decision/incident/team chain, graph inventory and source digests of all four real-repository corpora. Waited two seconds before SIGKILL under default every-second fsync; **not a zero-loss power-failure guarantee**.
- Frontend local tests: **36 passed**, zero skipped/failed; TypeScript typecheck PASS.
- Focused local native backend identity/copy/index checks: **9 passed**.

Receipts are in `POST-REVIEW-NATIVE-03/`. They contain owned synthetic organization text, clearly labeled as such. No provider keys or SSH private material are included.

## Deployment handoff and remaining work

Build a clean pinned worktree with matching full application commit declarations for API and UI, use the isolated durable database, run the review preview on separate loopback ports, and retain the old preview for rollback. A production frontend build and browser acceptance for the final pinned identity build must be observed separately; this report does not pre-claim them.

The 12/18-run real-model comparison, second untuned autonomous engineering target, final blog/video/submission packaging, and integration approval are **not established by these native tests**. Do not turn protocol demonstrations, source audits, or byte reductions into model-token/cost or universal task-success claims.
