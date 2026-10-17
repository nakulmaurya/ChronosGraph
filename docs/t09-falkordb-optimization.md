# T-09: docs-backed native FalkorDB ownership lookup optimization

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

## Applied change

The existing File/Function/Class and policy indexes remain unchanged. Pinned
CODEOWNERS ingestion previously matched three newer ownership node types by keys
without corresponding range indexes. For imports with actual matched ownership
rows, it now ensures:

- OwnershipSource.id
- OwnershipRule.id
- DeclaredOwner.name (kind is still filtered separately; names are not unique)

`backend/app/db/ownership_indexes.py` reads `CALL db.indexes()`, creates only the
missing fixed-schema indexes and waits for OPERATIONAL status before ownership
MERGEs. DDL/readiness errors propagate into the existing new-snapshot cleanup;
they are not swallowed by the older general index helper. Polling is bounded at
10 seconds but is not a hard server-side DDL deadline. Caller is the ingestion
writer, not a REST/MCP discovery request. Existing tenant/source writer locks stay.
No global graph/Redis configuration, new dependency, vector dimension, graph
relationship semantics, source hash or ownership interpretation was changed.

This applies to subsequent local/public imports containing matching CODEOWNERS
rules. Existing saved graphs are not automatically migrated or reingested. The
T-09 preview API on 8004 has been restarted with this implementation; UI remains
3004. User-requested old services 3000/8001 remain stopped. No main merge.

## Documentation and native verification

Official references reviewed:
- https://docs.falkordb.com/cypher/indexing/range-index.md
- https://docs.falkordb.com/commands/graph.explain
- https://docs.falkordb.com/cypher/unwind.md

The docs recommend selective range indexes and using EXPLAIN/PROFILE to verify
actual usage, noting memory/write overhead. This is a small targeted range-index
change, not speculative full-text/vector/CCH adoption or a server tuning exercise.

`test_ownership_indexes.py` uses native FalkorDB, not mocked query results. It
checks three key lookup result/plan equivalences, repeated setup with unchanged
node properties, same name/different owner kind behavior, and GRAPH.COPY retaining
indexes/results. The existing owner/source/API/MCP tests also pass unchanged.

## Measured experiment

Synthetic disposable graph: 2,000 nodes per ownership label (6,000 total), 41 warm
reads per lookup per phase. The same indexed and unindexed query parameters and
results are used. Native PROFILE shows a 2,000-record label scan before and a
one-record index scan after for each lookup.

| Lookup | Before median client ms | After median client ms | Ratio |
|---|---:|---:|---:|
| OwnershipSource.id | 1.0196 | 0.5704 | 1.788x |
| OwnershipRule.id | 0.9987 | 0.5851 | 1.707x |
| DeclaredOwner.name | 0.9818 | 0.5598 | 1.754x |

These are observed warm synthetic point-lookup timings, including Python/client
roundtrip overhead. They are not whole-import, app, agent, cold-start or paid-token
benchmarks; workload and VM timing will vary. Indexed reads trade extra storage
and write maintenance for less scanning. No speed-ratio assertion is imposed on
unit tests; index plans and exact-result invariants are the stable regression gate.

Reproduce on the installed VM checkout (creates/removes only its own test graph):

```bash
cd ~/ChronosGraph-t09
flock /tmp/chronosgraph-t09-native-verification.lock \
  env PYTHONPATH="$PWD/backend" .venv/bin/python \
  scripts/profile-ownership-indexes.py --output /tmp/ownership-profile.json
```

The raw `ExecutionPlan.plan` lines are retained because the client's string
rendering drops PROFILE counters. Initial plan-only experiment and raw logs remain
outside Git on the VM. Final `profile.json` includes counters, timings and results.

## Gates and boundaries

- 152 backend tests pass, 32.68s, serial native gate.
- 17 frontend unit tests pass; no frontend implementation change in this slice.
- 24 legacy + 10 workbench + 5 import-guide browser checks pass against real API.
- Four accepted tenants' complete Decision-property ledgers match exactly
  before/after; all owned test/sandbox graphs removed.
- Typecheck/build from the preceding unchanged-frontend checkpoint remain valid;
  not rerun or represented as fresh results for this backend-only slice.
- Main remains unchanged; T-09 remains IN_PROGRESS, not Architect acceptance.

Receipts: tasks/reports/T-09-evidence/native-optimization/. FalkorDB remains the
actual provenance and relationship engine for the hackathon; this is not a
cosmetic graph or an upstream AI-summary dependency.
