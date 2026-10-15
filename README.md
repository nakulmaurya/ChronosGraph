# ChronosGraph

**A living context layer for coding agents: inspect connected impact, retrieve the current rule, and replay a verified investigation.**

ChronosGraph extends an AST-style code graph with three connected mechanisms on
FalkorDB: disposable `GRAPH.COPY` sandboxes, bi-temporal `ACTIVE`/`SUPERSEDED` policy
lineage, and `shortestPath` procedural playbooks. The parser follows familiar
file/function/dependency graph conventions associated with `FalkorDB/code-graph`;
it is our own conservative Python AST implementation, not an integration with that package.

```text
Next.js / React Flow console          Agent IDE via five-tool FastMCP stdio
                 \                    /
                  FastAPI + graph services
                 /            |            \
    GRAPH.COPY audit   shortestPath memory   policy lineage
                  FalkorDB tenant graphs
        falkordb-py                 GraphRAG-SDK
```

## Start locally with one command

Prerequisites: Git, Bash, Python 3.11+, Node.js 24+, npm, Docker, network access for
public source/dependency downloads, and free ports 6379/8000/3001. First-time setup
can take minutes; “60-second verification” means inspecting an already-running demo.

```sh
git clone https://github.com/nakulmaurya/ChronosGraph.git
cd ChronosGraph
bash scripts/start-local.sh
```

Open **http://127.0.0.1:3001**. The launcher creates a local Python environment,
installs locked frontend dependencies, starts an owned loopback-only Docker
container, seeds both graphs and starts the API/UI. Ctrl-C stops its own processes;
its database is **ephemeral**, not a persistent production store. No external model
or paid credentials are needed. The legacy Compose file is unchanged; this launcher
uses explicit loopback binding instead of its broader published ports.

Without Docker, use `bash scripts/start-local.sh --db native` to install/run
`falkordblite==0.10.0` on a compatible platform, or `--db existing` for a trusted
FalkorDB already on localhost:6379. Do not reuse an unrelated database.
Native module/glibc compatibility is platform-dependent; the launcher never replaces
host libraries. The native helper and existing-DB verification were tested originally. **The default
Docker launcher and production-mode UI were subsequently verified on the Google Cloud
test VM** (FalkorDB 4.22.1; [T-05 evidence](tasks/reports/T-05.md)). The legacy Compose
path remains untested. See [release limits](docs/release-checklist.md).

## Judge verification matrix

All query constants live in [backend/app/db/queries.py](backend/app/db/queries.py).
UI tab names match the console; REST routes share `/api/v1`.

| Track | Backend service | Exact query constant(s) | REST | FastMCP tool(s) | Exact UI action |
| --- | --- | --- | --- | --- | --- |
| 01 — Agents That Act on Connected Data | `backend/app/services/sandbox_auditor.py` | `CYPHER_BLAST_RADIUS_AUDIT`; `CYPHER_FILE_OWNERSHIP_AND_LINEAGE` | `POST /track1/sandbox-audit` | `simulate_pr_blast_radius` | Crash-test clone → **Run GRAPH.COPY audit** |
| 02 — Agent Memory & Coordination | `backend/app/services/memory_compiler.py` | `CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH`; read-only tool queries in `TOOLS` | `POST /track2/investigate` | `run_or_compile_playbook` | Memory compiler → **Run #1 · Cold triage**, then **Run #2 · Compiled replay** |
| 03 — Company Brain | `backend/app/services/company_brain.py` | `CYPHER_HYBRID_VECTOR_DECISION_SEARCH`; `CYPHER_FILE_OWNERSHIP_AND_LINEAGE`; `CYPHER_SUPERSEDE_DECISION` | `POST /track3/ask-brain`; `POST /track3/override-policy` | `query_bitemporal_decisions`; `find_true_code_owners`; `record_decision_override` | Time-travel rulebook → **Read current policy**; optional confirmed **Record policy override** |

**60-second inspection:** On `FalkorDB/falkordb-py`, audit `falkordb/graph.py` and
check cleanup. Run cold/replay for `Review current policy for falkordb/graph.py`:
observe 5→3 actions. Switch to `FalkorDB/GraphRAG-SDK`, read a preset file's current
policy and its crossed-out history. Open **MCP config** to inspect all five tools.
The [2:45 recording runbook](docs/demo-video-script.md) includes exact choreography.

## Provenance and measured telemetry

| Layer / measurement | Verified meaning |
| --- | --- |
| `repo_falkordb_py` | Historical T-01 real-source/public-GitHub layer: **458 nodes / 669 edges**, 42 Python files, 371 functions; code revision `31f63f44a5745b9bec65969a1db706906718cb82`. |
| `repo_graphrag_sdk` | Historical layer: **4,252 nodes / 6,251 edges**, 154 Python files, 3,364 functions; code revision `35e67a0b27fdcc7f2c28508b09e86169851a8187`. |
| `DEMO_POLICY_SCENARIO` | Four fictional supersession pairs per tenant: **+8 nodes / +20 edges**, yielding initial totals 466/689 and 4,260/6,271. Contextual PR links are not upstream policy attribution. |
| Public GitHub provenance | PR/review/issue/contributor records fetched and cached at ingestion; unlike code commits, this metadata snapshot is not pinned to those revisions. |
| `SIMULATED_PR_DEPENDENCY` | Synthetic dependency/call nodes/edges exist only in the disposable clone. This is not source-diff execution or outage proof. |
| `DETERMINISTIC_POLICY_TRIAGE` | 6 cold states / 5 actions, including 2 dead ends; compiled replay executes 3 verified actions, 0 dead ends: **40% fewer actions**. Roles are deterministic tools, not autonomous LLMs. |
| `CONTROLLED_ONE_HOP_BASELINE` | Measured shallow graph-query comparison; not a general LLM/RAG evaluation. |
| T-02 captured sandbox | **22.99 ms** clone, cleanup verified; separate clones ranged **96.62–119.79 ms**. Approved local ceiling: <250 ms, not a universal guarantee. |
| T-02 captured replay | **13.300 ms cold / 8.425 ms warm = 1.579×**; five-pair median **1.253×**, including one slower warm run (**0.821×**). |
| Model accounting | `tokens_used: 0`, `token_savings_pct: 0.0`: **unmeasured zero-model sentinels**, not token/cost savings. |

Sources: [T-01](tasks/reports/T-01.md), [T-02 samples](tasks/reports/T-02-response-excerpts.json),
[benchmark](tasks/reports/T-02-samples/benchmark.json), [T-03](tasks/reports/T-03.md).
Live counts include later investigation/playbook records. Latency varies with load;
the UI displays the actual factor even below 1. Owners reflect bounded PR/review or Git-commit file
coverage; Git author identities are unverified, not definitive maintainers. Vectors are lexical hashes, not semantic model embeddings.

## Ingest another Python Git repository (v1.3)

With dependencies installed and a trusted FalkorDB running:

```sh
cd backend
../.venv/bin/python -m app.ingestion.ingest_repo \
  --source https://github.com/FalkorDB/code-graph \
  --tenant repo_falkordb_code_graph --ref 2a7a52c0abb529c93e9f571e7358e097f1b76ab3 --seed-demo-policies
../.venv/bin/python -m app.ingestion.ingest_repo \
  --source https://github.com/modelcontextprotocol/python-sdk \
  --tenant repo_mcp_python_sdk --ref 754254c08fe1c3eda18b69da3d336106fe8d72d6 --seed-demo-policies
```

`--source` also accepts a local Git directory. It parses a separate checkout of the
committed snapshot, not uncommitted files, and **never imports/executes downloaded
Python**. Tracked `.py` files (1–10,000) exclude caches/build directories and symlinks.
Conservative unresolved calls stay unresolved; invalid Python produces explicit
file diagnostics. Unsupported encoding/I/O errors fail safely. This is a bounded
trusted-local tool, not a hardened untrusted-repository ingestion service.

Existing tenants are refused, not overwritten. Use a fresh `repo_[a-z0-9_]+` name.
Native `algo.pageRank` scores are normalized. `RepoMetadata.status=READY` registers
new graphs; the catalog supplies files, counts and indexed PR/commit records.
The UI discovers them on page load; refresh an already-open console after ingestion.

`GIT_COMMIT_HISTORY` identifies at most the latest 40 commits at the pinned snapshot,
real author-to-commit and exact commit-to-current-file links. Commit records use the
legacy `PullRequest` shape but are marked `record_kind=COMMIT` with negative numeric
compatibility IDs, not invented GitHub PRs. `pr_count` is therefore a legacy count
of evidence records, not exclusively PRs. Git author names are not authenticated
GitHub handles; uncovered files legitimately have no recommendation.

`--seed-demo-policies` adds fictional `DEMO_POLICY_SCENARIO` pairs, not upstream rules.
It leaves two non-policy files for the fixed triage demonstration; tiny repositories
may not support that topology. Without opt-in policies, source/ownership audits work
but policy/replay features need applicable rules. Cross-process CLI locks protect
source-cache checkouts and writers; API locks remain single-process demonstration locks.

Append-only, revision-checked ownership backfill (does not reset source or policies):

```sh
cd backend  # from repository root
../.venv/bin/python -m app.ingestion.ingest_repo \
  --source https://github.com/FalkorDB/falkordb-py --tenant repo_falkordb_py \
  --ref 31f63f44a5745b9bec65969a1db706906718cb82 \
  --backfill-history --history-path falkordb/graph.py
```

See [T-05 measurements and verification](tasks/reports/T-05.md) and
[Principal Architect acceptance](tasks/reviews/T-05.md). Contract v1.3 accepts dynamic
repository support. Historical T-01/T-02 counts/timings above remain unchanged; the
larger MCP SDK clone samples reached 257.62 ms, not a universal sub-250 ms guarantee.

## Verify and connect an agent

```sh
# Against a trusted running local FalkorDB:
bash scripts/start-local.sh --db existing --verify-only
# Individual commands after installing dependencies:
(cd backend && ../.venv/bin/python -m pytest -v)  # 53 with both external tenants; otherwise 47 pass + 6 explicit skips
(cd frontend && npm test && npm run typecheck && npm run build)  # 7 tests + build
(cd frontend && npm audit --omit=dev)
.venv/bin/python scripts/check-release-hygiene.py
```

Use the header's **MCP config** modal or adapt this local stdio template:

```json
{"mcpServers":{"chronosgraph":{"command":"/absolute/path/ChronosGraph/.venv/bin/python","args":["-m","app.mcp_server.server"],"cwd":"/absolute/path/ChronosGraph/backend"}}}
```

This is a template, not an installed IDE connection. Start/seed FalkorDB first.
See [frontend setup/live smoke](frontend/README.md), [release evidence](tasks/reports/T-04.md),
[technical article](docs/blog-post-falkordb.md) and [handoff](docs/handoff.md).
**Local trusted-client demonstration only: no authentication, no production safety
guarantee, no deployment or external publication. Release status: v1.3 accepted (53 backend tests, 7 frontend regression tests, and 17 live production Chromium checks verified).**
