# ChronosGraph

**A FalkorDB Change-Control Cockpit, Multi-Hop Context Layer, and Source-Bound Memory Engine for Coding Agents.**

Your coding agent sees a function. You need to see the connected consequences.
ChronosGraph brings both into one monochrome command center: explore a repository,
inspect a proposed change, approve its exact contents, observe candidate tests in
an explicitly trusted local worktree, and retain evidence that expires when code
or policy changes.

**FINAL-01 release branch:** `build/final-hackathon-release`, built from `6048a29`.
**Overall FINAL-01 status: NOT READY for unconditional submission; the free coding-model provider blocked the real-agent evaluation.**
This README describes that branch, not an automatically updated main branch or VM
preview. [Current verification and remaining gates](tasks/reports/FINAL-01.md) ·
[Critique-only readiness review](tasks/reviews/FINAL-02-persona-critique.md).
[Follow-up fixes and deployment evidence](tasks/reports/FINAL-02.md).

## Start locally

Tested verification environment: **Linux, Python 3.13, Node 24, Docker, native
FalkorDB**. Python 3.11+ / Node 20.9+ are launcher requirements, not a claim that
all combinations were tested. On Windows use **WSL2 + Docker**; on macOS use
Docker Desktop and the Bash launcher. macOS and WSL2 paths have setup guidance,
not witnessed FINAL-01 platform certification.

```sh
git clone https://github.com/nakulmaurya/ChronosGraph.git
cd ChronosGraph
git checkout build/final-hackathon-release
bash scripts/start-local.sh
# Optional, trusted local one-click public GitHub imports:
CHRONOSGRAPH_ENABLE_BROWSER_IMPORT=1 bash scripts/start-local.sh
```

Open **http://127.0.0.1:3001**. Defaults: API 8000, FalkorDB 6379. Install Git,
Bash, Python, Node/npm and Docker first. Initial dependency downloads take minutes.
The launcher owns its local processes/container; its demo DB is ephemeral. For an
existing **dedicated** local DB use `--db existing`; do not point it at unrelated
production data. Exact loopback UI origins are configured by the launcher.
See [platform setup](docs/t09-platform-setup.md) and
[durable deployment/import recovery](docs/bulk-command-center.md).

### Import a repository without a terminal

In a browser-import-enabled session, click **Import repository**, paste a public
GitHub Python repository, and import. Branch defaults to `main`; an empty commit
hash resolves the latest branch commit first and then imports that exact version.
Each import creates a separate saved snapshot; old snapshots are never overwritten.
Receipts are Redis-backed with seven-day retention, subject to the durability of
your configured Redis storage. Imports do **not** execute repository code. Public
archive imports do not fetch commit history; local Git ingestion can retain bounded
commit-file history. Private repositories, symlinks/submodules and unsupported or
oversized archives are refused rather than silently guessed.

## One workspace, three connected capabilities

```text
Coding client ── FastMCP stdio ──┐
                                ├─ Snapshot guards ─ Graph services ─ FalkorDB
Human ── Next.js Command Center ─┘                    │
          Changes: review / approve                  ├─ GRAPH.COPY previews
          Activity: memory / replay                  ├─ policy + ownership lineage
          Ownership: decisions / export              └─ proposal / execution records
                                                       │ explicit operator opt-in
                                            trusted disposable Git worktree
                                            actual bounded candidate pytest
```

FalkorDB is the primary graph store, not a decorative visualization: import/call
traversals determine candidate impact, native PageRank breaks context ranking ties,
`shortestPath` retains useful investigation actions, and current policy edges gate
approval and memory reuse. Our scope-aware Python AST parser is our own conservative
implementation; unresolved dynamic calls remain visible coverage limits.

## Hackathon judge verification matrix

All primary actions below are at **`/` or `/workbench`**, without hunting through
legacy routes. Select a Python file in **Repository** first. `/demo` remains a
historical primitive explorer, not the default product flow.

| Track | Command Center action | Service / real graph operation | Evidence to inspect |
| --- | --- | --- | --- |
| 01 — Agents That Act on Connected Data | **Changes** → pending proposal → approve exact hash → opt-in worktree tests | `diff_impact.py`: `GRAPH.COPY`, replacement AST, before/after `IMPORTS` and `CALLS`; `change_lifecycle.py`: durable task/run/proposal/decision/execution links | Broken callers, candidate pytest files, active rules and CODEOWNERS; actual exit/output and provenance |
| 02 — Agent Memory & Coordination | **Agent activity** → source-bound findings → policy investigation/replay → recovery note | `context_locator.py`: bounded three-hop import paths + `algo.pageRank`; `task_memory.py`: source/policy fingerprints; `memory_compiler.py`: `CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH` | Real MCP stream, CURRENT vs STALE findings, observed 5→3 deterministic actions; actual ResumeSnapshot bytes |
| 03 — Company Brain | **Ownership** → declared owners / separate contributors → policy override → wiki / ZIP | `ownership.py`: vendored CODEOWNERS matching; `company_brain.py`: ACTIVE/SUPERSEDED lineage, recorded/valid time, `vecf32` hybrid retrieval; `second_brain_wiki.py`: portable linked notes | Matching rule and line; provenance; superseded history; live invalidation; Obsidian vault |
| Best Blog Post | [Technical article](docs/blog-post-falkordb.md) | Primitives, T-09/BULK-01/FINAL-01 implementation and explicit measurement boundaries | Reproducible code/query links and observed results, not token-savings speculation |

Canonical primitive queries: [queries.py](backend/app/db/queries.py). Replacement
queries and lifecycle writes live beside their services rather than pretending
all operations share one canned audit query. Ownership means **declared matching
CODEOWNERS**, not independently verified GitHub permissions. Git contributors are
separate evidence, not a substitute for declared owners.

## Connect your coding client: 15 FastMCP tools

Use **Connect agent** to copy configuration and the selected tenant/revision
handoff. The modal prepares a template; it does not install an IDE connection.

```json
{"mcpServers":{"chronosgraph":{"command":"/absolute/path/ChronosGraph/.venv/bin/python","args":["-m","app.mcp_server.server"],"cwd":"/absolute/path/ChronosGraph/backend","env":{"CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD":"1"}}}}
```

1. `discover_repositories` — discover saved versions (not snapshot-bound by design).
2. `inspect_repository_snapshot` — verify exact tenant/revision and return guard arguments.
3. `locate_context` — bounded source context, real import paths and candidate tests.
4. `get_symbol_source` — captured complete symbol range within limits.
5. `simulate_diff_impact` — final replacement/deletion preview in GRAPH.COPY.
6. `simulate_pr_blast_radius` — legacy bounded audit / optional snippet overlay.
7. `query_bitemporal_decisions` — current and superseded policy evidence.
8. `find_true_code_owners` — legacy-named contribution/ownership evidence interface.
9. `record_decision_override` — explicit local policy replacement.
10. `run_or_compile_playbook` — deterministic native shortestPath replay.
11. `record_verified_finding` — records **agent-reported**, not independently observed evidence.
12. `recall_task_memory` — source/policy freshness on recall.
13. `propose_change_for_approval` — immutable bounded proposal and replacement preview.
14. `check_proposal_decision` — exact current approval/stale state.
15. `report_proposal_execution` — **unverified client report**, never host-observed proof.

All 13 operation tools accept revision guards; strict mode requires guards on the
legacy operations. The three new lifecycle tools always require an exact revision.
Discovery is necessarily before selection, so **not all 15 tools require a snapshot**.
Carry `tenant_graph` and `expected_revision` on every operation, never a default tenant.

## Approval and actual execution

[Lifecycle details, API and trusted runner setup](docs/final-lifecycle.md).

A proposal is immutable. A coordinated revision is a **new proposal/key**; approval
does not transfer to changed contents. The canonical SHA-256 binds tenant, base
commit, base file hashes and proposed bodies. Same key/same content returns the
existing record; different content returns 409. Shared per-tenant Redis mutation
leases serialize policy, decision and execution writes across processes.

Observed candidate tests are optional and **disabled by default**. Enable only for
trusted local Git roots that you explicitly configure. A disposable worktree is
**not a security sandbox**: pytest can execute repository code on the host. The
runner does not merge, commit, push or change the saved base source. External MCP
reports cannot mint `LOCAL_WORKTREE_OBSERVED` evidence. A verified finding binds the
captured base and retains proposed result hashes separately; it does not claim the
proposal was merged. Unknown execution outcomes stop retries for that proposal.

## Verified release checks

- **295 backend tests**, zero failures/skips; **34 frontend unit tests**.
- Typecheck and production build passed; **70 browser checks** across desktop/mobile.
- **15 MCP tools** with the discovery/guard exceptions described above.
- Synthetic 5,000-file native root-map p95: **107.97 ms** in the final run; not a production SLA.
- Seven-day durable Redis import receipts, subject to configured database persistence.
- Real scripted stdio and observed fixture pytest passed; hosted coding-model run blocked by provider HTTP 403.

## Reproduce verification

After installing dependencies and preparing the dedicated four demo source graphs:

```sh
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-quality-batch1.sh
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-change-planning-ui.sh
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-final-lifecycle-ui.sh
(cd frontend && npm test && npm run typecheck && npm run build)
PYTHONPATH=backend .venv/bin/python scripts/check-release-hygiene.py
```

The native scripts create **owned disposable database copies**; source graphs are
read with Redis DUMP and never reseeded. Browser scripts use owned ports 3003/8005
and clean their own services. Do not run frontend builds concurrently against the
same `.next` directory. For the synthetic real-stdio walkthrough, use an **owned
empty disposable** FalkorDB:

```sh
PYTHONPATH=backend:backend/tests FALKORDB_PORT=<owned-port> \
 .venv/bin/python scripts/run-hero-lifecycle-demo.py \
 --approve-fixture --output /tmp/chronos-hero-evidence.json
```

`--approve-fixture` preauthorizes our owned synthetic checkout only; it is not proof
of a person reviewing a UI action or a hosted model choosing the fix. The browser
lifecycle harness separately exercises actual UI approval, execution and invalidation.

Verified counts and exact evidence references are in [FINAL-01](tasks/reports/FINAL-01.md).
The 5,000-file synthetic single-client navigation benchmark is not import throughput
or a production capacity guarantee. Zero model calls means token savings are
**unmeasured**, not that tokens were measured as saved.

## Boundaries and open work

- Trusted local/operator application, not authenticated multi-user change control.
- Static Python reachability, not runtime/type compatibility proof or safe-skip permission.
- Unsupported languages retain tracked-file visibility, not fabricated function graphs.
- No hosted-model/IDE evaluation is implied by a scripted real FastMCP client.
- Legacy routes keep compatibility; they have not all been redesigned or given identical guards.
- Browser approval is a coordination record, not an OS restriction on external agents.
- Policies in bundled demos/hero fixtures are explicitly fictional, not upstream rules.
- Prize eligibility, organizer acceptance, publication and submission are owner actions;
  preexisting foundation/event-period requirements need organizer confirmation.

## License and acknowledgements

MIT, Copyright (c) 2026 Nakul Arvind Maurya. See [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), including the vendored
`sbdchd/codeowners` matcher. FalkorDB, falkordb-py, GraphRAG-SDK, FastMCP,
Next.js and React Flow provide the foundation. We did not import GitDiagram's
LLM-generated architecture as verified call edges; our analysis remains pinned,
source-derived and conservatively bounded. Earlier implementation reports remain
historical evidence, not current readiness claims.
