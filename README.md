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

## Optional AST snippet simulation (T-06)

Track 1 accepts `proposed_code_patch` through REST and `simulate_pr_blast_radius`.
The editable Python snippet is parsed, never executed, and overlays definitions,
resolved imports and conservative calls on the **first selected file** inside
GRAPH.COPY. Enable it in “Proposed Python patch (AST-parsed in clone)”. Selecting
a real PR/git record scopes the audit to its ingested changed Python files.

This is an **additive snippet overlay**, not a unified diff, full-file replacement,
or a fetched commit patch. Existing snapshot edges remain. Ambiguous/dynamic or
external calls are reported unresolved, not guessed. Input is limited to 32,000
characters and 500 AST observations. Blank/omitted input retains the existing
`SIMULATED_PR_DEPENDENCY` scenario. `AST_PATCH_SIMULATION` metadata and dependency
counts remain inspectable on the target file; upstream graph data is not mutated.

The inspector compares observed baselines with each result. Replay visualizes
actual **historical cold** dead ends dimmed and explicitly not replayed; backend
step counts and replay subgraphs still describe only the three executed actions.
Demo recording/narration upgrades are deferred to a later task.

### T-07: real-world utility (no model calls)

- Track 1 accepts a Python snippet or **single-file unified diff**. Diffs are
  reconstructed only when hunk offsets/context match the captured source at the
  ingested revision; multi-file patches, additions/deletions and renames return
  422. The resulting AST is an **additive clone overlay**: old edges are retained,
  so this is conservative static impact evidence, not complete source replacement
  or execution. Requests are bounded to 32,000 characters / 500 AST observations;
  reconstructed source is bounded to 1,000,000 characters.
- The copy-ready pytest command selects reachable test-file **candidates** using
  the bounded three-hop import/call graph, including modified tests. The percentage
  is a static candidate-file reduction, **not proof that other tests are safe to
  skip**. Dynamic imports, fixtures, plugins and non-Python dependencies can be
  absent. Run full-suite CI as the safety gate. Empty selection recommends `pytest`.
- Track 2 returns an actual compact JSON AST-signature / active-policy /
  source-linked-constraint / commit-author slice. Comparison uses exact Unicode
  character and UTF-8 byte lengths from captured candidate sources, with `chars // 4`
  **token equivalents**, not tokenizer counts or billed tokens. This compares a
  counterfactual full-file payload with a focused slice, not the bytes read by
  the graph tools and not equivalent semantic content. Tiny inputs can expand.
  Warm runs preserve the original cold baseline; `tokens_used`, `token_savings_pct`
  and `model_calls` remain zero. Missing source sizes are explicit, never inferred
  from LOC. Signature/policy/constraint caps and truncation are in the preview.
- Ingestion extracts concrete pyproject constraints and explicit normative
  engineering lines from README/AGENTS/CLAUDE/module docstrings. `REPO_EXTRACTED_RULE`
  records include path, line, revision and scope. They are **source-revision facts**,
  not promoted to local ACTIVE/SUPERSEDED override governance; demo policies remain
  intact. Track 3 displays both separately. No source text is exposed in generic
  visual graph payloads.

Existing snapshots need explicit revision/hash-checked enrichment (no reset):

```bash
cd backend
python -m app.ingestion.ingest_repo --source /path/to/pinned/repo \
  --tenant repo_your_repository --ref FULL_MATCHING_REVISION --enrich-utility
```

Fresh CLI ingestion and the original two-repository seeder capture source sizes
and extracted rules automatically. Enrichment adds metadata/constraints once;
subsequent enrichment is idempotent. Run enrichment before testing reseed
idempotency against a pre-T-07 database. Repository-constraint changes invalidate
existing playbook fingerprints; rerun cold triage. Use a single local writer
process; cross-process online migration/transaction isolation is not guaranteed.

T-07 deliberately does not update or record the demo video.

### T-08: Obsidian second brain and compaction recovery (contract v1.4)

ChronosGraph's deterministic compiler turns the live tenant graph into `index.md`,
`log.md` and linked `wiki/files`, `wiki/decisions`, `wiki/playbooks` and
`wiki/contributors` notes. YAML frontmatter preserves tenant, label, status,
PageRank and provenance. All wikilinks resolve to generated notes; backlinks are
explicit. Lint distinguishes superseded policy history, dead-end state evidence,
isolated files and stale playbooks. This is an inspired three-layer graph wiki,
not LLM-authored synthesis, an Obsidian plugin, or an endorsement by Karpathy.

- `GET /api/v1/ctx/stats?tenant_graph=...&file_path=...` compares actual captured
  UTF-8 source metadata with the exact serialized focused slice. Repository-wide
  comparison and affected-file/cold-candidate comparisons are labeled separately.
  `bytes // 4` and `chars // 4` are different estimates, never tokenizer counts.
- `POST /api/v1/ctx/compile-wiki` accepts `tenant_graph`, optional `file_path`, and
  `export` (default false); returns Markdown pages, lint and ResumeSnapshot.
- `GET /api/v1/ctx/wiki-page?tenant_graph=...&page=index.md` reads only generated
  keys; it is not an arbitrary filesystem reader.
- `POST /api/v1/ctx/compact-snapshot` returns a bounded, under-2-KiB Markdown
  excerpt: current target, connected symbols ranked by owning-file PageRank,
  ACTIVE local policy excerpts, current-fingerprint retained playbook and bounded
  commit-author evidence. Superseded rule text and dead-end tools are excluded;
  refresh full policies before acting. It does not install PreCompact hooks.
- `GET /api/v1/ctx/export?tenant_graph=...` downloads a ZIP with the generated
  notes and ResumeSnapshot, without a server filesystem write.

Explicit `export: true` writes only under the server-controlled
`CHRONOSGRAPH_VAULT_ROOT` (default `/tmp/chronosgraph-obsidian-vault`). The compiler
refuses symlink/unmanaged destinations and creates immutable content-ID generation
folders, never overwriting an existing personal vault. Open a generation as an
Obsidian vault. The tenant's persistent `log.md` appends previously unseen source
event IDs; older runs without timestamps are marked UNDATED, not assigned invented
chronology. Source deletion cannot erase an already exported event. Export and
ledger are designed for the local single-process app, not distributed concurrent
writers or a crash-safe event store. Exported histories can contain obsolete policy
text as explicitly historical notes; only ResumeSnapshot is current-only.

The HUD shows live measured source/slice sizes, a navigable wiki preview and copy/
export controls. A focused lossy summary is not equivalent full source, and a
repository-wide ratio does not claim the whole repository would otherwise be read.
No fixed 95% savings, sub-4-KiB full audit response, safe test skipping or measured
billed-token savings is promised. All five existing MCP tool names remain intact.

Portable client workflow: `skills/chronos-second-brain/SKILL.md`. Reference it from
Claude Code / Cursor / Antigravity / OpenCode / Windsurf project instructions using
the client's supported MCP configuration; no IDE integration is auto-installed.


## T-08 builder-facing Second Brain + /compact Shield
The existing five-tool MCP contract and `/api/v1/ctx/*` interfaces remain compatible.
New read-only APIs:
- `GET /api/v1/brain/wiki-slice?tenant_graph=...&file_path=...`: live YAML/wiki note,
  AST signatures, three-hop static import/call candidates, current/history rules,
  exact captured connected-source UTF-8/Unicode estimates and pytest candidates.
- `POST /api/v1/brain/lint-and-compact` with tenant_graph and optional file_path:
  observed rule/dead-end/stale-playbook counts, actual sandbox count and a bounded
  `LESSON:` ResumeSnapshot. Recovery is manual, not an installed PreCompact hook.
- `GET /api/v1/brain/obsidian-vault.zip?tenant_graph=...&file_path=...`: in-memory ZIP
  with `raw/repo_snapshot_manifest.json`, `wiki/index.md`, `wiki/log.md`, file/rule/
  playbook/contributor notes, `ResumeSnapshot.md`, `_CLAUDE.md` and `SKILL.md`.

The header's **Obsidian Wiki & /compact Shield** opens live notes, `/brain-lint`,
copyable recovery Markdown and the three-layer ZIP. `skills/chronos-second-brain/SKILL.md`
routes Claude Code, Cursor, Antigravity/OpenCode and Windsurf through graph-first
investigation without assuming every client automatically discovers the skill.
Source notes remain untrusted evidence; policy writes require confirmation.
The HUD compares connected captured source with the exact lossy wiki note, not raw
repo totals or the entire HTTP envelope. Compression can be negative or unavailable;
no fixed reduction, billed-token savings, safe test skips or zero-amnesia guarantee.
The previously accepted video is retained unchanged; this amendment excludes video.

VM checkout: `/home/nakulmaurya13579/ChronosGraph-t08`; production target is loopback
frontend 3000 and API 8001 after authorized integration. Prior checkout remains rollback.
Publication/deployment receipts and gate evidence are in `tasks/reports/T-08.md`.


## Open the already-running GCP demo
With Google Cloud CLI installed and access to project `amazon-ml-509907`, run
`bash scripts/connect-vm.sh` on your laptop. Keep that terminal open and browse
http://127.0.0.1:3000; API docs are at http://127.0.0.1:8001/docs.
The helper forwards loopback ports over SSH without exposing the app publicly.
This connects to the existing VM; local setup above instead uses port 3001.
