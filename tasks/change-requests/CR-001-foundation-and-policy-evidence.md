# CR-001 — Foundation compatibility and policy evidence

Status: APPROVED — applied under planning manifest v1.1

Approval: Principal Architect via Nakul, explicit chat instruction. Canonical decision: CR-001.md. The original findings below are retained as historical context.
Owner: Builder; no locked contracts changed.

## 1. shortestPath compilation
Real FalkorDB 4.18.3 rejects the locked query with:

```
FalkorDB currently only supports shortestPaths in WITH or RETURN clauses
```

Proposed one-line change in backend/app/db/queries.py:

```diff
-MATCH golden_path = shortestPath((start)-[:ACTION_TAKEN*1..12]->(goal))
+WITH inv, shortestPath((start)-[:ACTION_TAKEN*1..12]->(goal)) AS golden_path
```

Tested in a disposable real graph: six state nodes, five transitions, three retained steps, two dead-end branches excluded. See ../reports/T-01-proposed-shortestpath-fix.json. The locked file was not edited. The Docker image itself is untested here; verify its version independently.

## 2. Curated decision history
T-01 source graphs and actual GitHub metadata are populated. Neither the ZIP nor pinned source snapshots supply a curated mapping of four genuine old/new architecture-policy pairs per repository. Do not invent these or attribute example rules to real maintainers.

Approval options:
- Provide curated real policy evidence with file, scope, exact rule/excerpt, source URL, valid-from/to, and explicit supersedes ID.
- Authorize separately labeled SYNTHETIC_DEMO policy fixtures for the demo, with no claim they represent upstream decisions.

The seeder supports --policies <file.json> with per-tenant lists of provenance-labeled policies. Source types: VERIFIED_SOURCE (requires matching source excerpt), USER_POLICY, SYNTHETIC_DEMO. Without a file, it truthfully returns AWAITING_CURATED_POLICY_EVIDENCE, and the two required-policy acceptance tests fail.

## 3. Editable installation
The baseline's `pip install -e .` fails under current Hatchling:

```
ValueError: Readme path must be within the project directory: ../AGENTS.md
```

Request approval to add backend/README.md, change the package readme to README.md, and add:

```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

No packaging edits were applied. Test commands currently use PYTHONPATH=. and an isolated environment with actual dependencies installed directly.

## 4. Unmeasured comparative claims
The arena must run a defined baseline against the same input or explicitly say NOT_MEASURED. Do not force false approvals, outages, 75% token savings, or 4x latency gains. Deterministic tooling without model calls must not report invented LLM token usage. Read-only enforcement is a database command restriction, not hardware isolation.

## 5. Baseline identity and runtime deviation
The supplied archive's actual SHA256 is 24624e61ca49734efa026705c022a0b5fb22b6d57a9eb14fd7e2e6dc4097b785. The planner's zip-sha256:68957811d3a5ba99 label does not equal the archive hash prefix. Keep both labels distinct.

Docker is unavailable, but real Redis 8.6.2 + FalkorDB module 4.18.3 were started from FalkorDBLite 0.10.0 on loopback port 6379 using workspace-only compatibility libraries. No paid infrastructure or system configuration changes were used. This is real database integration testing, not verification of docker compose or the production image.
