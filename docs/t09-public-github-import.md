# T-09 public GitHub intake — bounded CLI slice

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

Status: implemented for explicit public Python repositories, not a hosted import
service or full milestone-C acceptance. Main/production remain unchanged.

## From a GitHub link to FalkorDB context

The workbench has an expandable **Connect a public GitHub repository · local CLI
setup** panel. It prepares commands and can reload the real indexed catalog.
It does **not** transmit the pasted URL, run a job or authenticate with GitHub.
Run commands in your installed ChronosGraph checkout on the same machine as
FalkorDB, with its existing backend environment:

```bash
cd ~/ChronosGraph-t09
PYTHONPATH="$PWD/backend" .venv/bin/python -m app.ingestion.github_import inspect \
  --url https://github.com/pallets/click --branch main
```

Inspect reads public GitHub metadata and prints `source_revision` and `tree_sha`.
For an explicitly pinned version, use the returned 40-character `source_revision`:

```bash
CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT=1 PYTHONPATH="$PWD/backend" \
  .venv/bin/python -m app.ingestion.github_import import \
  --url https://github.com/pallets/click --branch main \
  --tenant repo_click_snapshot_1 --expected-head YOUR_CONFIRMED_40_CHARACTER_SHA
```

The placeholder must be replaced, not executed literally. In the browser guide,
**Commit hash (optional)** may instead be left empty: the generated command runs
inspect at execution time and passes that exact result into the pinned importer.
An empty branch uses `main` (not automatic detection of a repository's default
branch); change it to `master` or another branch when needed. An empty
**Saved copy name (optional)** generates a unique `repo_github_` UUID at execution.
On GitHub, find a full hash under repository → Commits → select a commit → copy
full hash. Latest mode still creates an immutable graph and does not monitor it.
Import refuses branch
movement or an existing tenant. Click **Reload indexed repositories** and select
the newly created snapshot. Use the usual workbench search, source coordinates,
GRAPH.COPY impact preview, CODEOWNERS evidence and MCP context tools. A public
archive has no local workspace connection; use a new tenant for a later import.
It does not support local `workspace check` or `refresh` on this archive snapshot.

## Trust and limits

- Mutations require an explicit process opt-in. No new import HTTP endpoint,
  browser mutation, automatic startup import, token handling or private GitHub
  importer. CLI process access remains an operator trust boundary.
- Only exact credential-free `https://github.com/owner/repo` URLs, explicit
  supported branch names and full SHA-1 confirmations. No arbitrary hosts,
  ports, SSH/file schemes, tree URLs, query/fragment tokens or URL userinfo.
- HTTPS requests use only `api.github.com` and `codeload.github.com`; environment
  proxies are disabled, redirects are rejected, no GitHub token/cookie/credential
  helper is used. API rate-limit/rename/private errors fail closed; no retries
  that silently change the pin. TLS uses system certificate validation.
- Require public visibility, exact commit/tree pin and a complete non-truncated
  tree. Maximum 10,000 tree entries; 16 MB compressed archive; 64 MB summed file
  sizes; 16 MB selected Python bytes; 1 MB per Python file. Selected documentation
  is at most 512 KB/file, CODEOWNERS at most 64 KB. Download request timeout is
  at most 20 seconds, with an elapsed 180-second budget checked between reads.
  These are application bounds, not a hostile-process OS sandbox/resource quota.
- Refuse symlinks, submodules, file/parent collisions, case-colliding paths,
  traversal, `.git` components, control characters and ambiguous ZIP names.
  No `extractall`, Git clone/checkout, hooks, package install or source execution.
  ZIP member sizes and complete file membership must match the API tree; selected
  source/support bytes must match each pinned **Git blob SHA-1**, then receive the
  existing captured-source SHA-256 representation in the graph. Blob verification
  covers selected files, not every ignored binary in the archive.
- Python files plus README/pyproject/AGENTS/CLAUDE and CODEOWNERS support source
  enter a temporary private directory; it is removed on ordinary success/failure.
  Only existing Python AST/IMPORTS/CALLS/PageRank, extracted-constraint and ownership
  graph logic runs. Imported prose remains evidence, not trusted agent instructions.
- No commit history fetched: `history_limit=0`,
  `history_scope=NOT_FETCHED_GITHUB_ARCHIVE`; **no invented contributors, PRs or
  demo policies**. GitHub branch name and pin are recorded as `PINNED_AT_IMPORT`,
  not a live freshness check. Read-only `/workspace/snapshot` exposes archive/tree
  receipts and scope. All ingested source is publicly accessible GitHub content;
  a public repository can still accidentally contain secrets. The operator should
  choose repositories they are comfortable storing locally; no secret-scanning
  guarantee is made.
- Source and tenant writer locks, no overwrite, READY after completion and deletion
  of only this newly created graph on ordinary ingestion error are preserved.
  Abrupt VM/process death can leave an unregistered INGESTING graph; operator review
  remains necessary. FalkorDB data persists; this slice adds no persistent source
  checkout/cache. Server crash recovery, persistent quotas, queued browser jobs,
  private imports, export-ignore archives missing tree members, mixed-language
  semantics and incremental in-place sync are not supported here.

## Why not install Gitingest/GitDiagram in the application?

Both were actually tried against `https://github.com/pallets/click`:

| Tool | Observed utility | Integration decision |
|---|---|---|
| Gitingest, MIT, `coderamp-labs/gitingest@4e259a02fe72115bee538271622f1234a81c8e1a` | Isolated CLI succeeded: 171 files, commit `2247b35ea1c47c727d7a06e51fa280e12a863ff6`, 1,617,243-byte digest, upstream estimate 442.8k tokens | Useful raw-context baseline and UX model for URL→summary/tree/content. Not the graph parser, security sandbox, or runtime dependency. Its token estimate is not directly comparable to our char÷4 equivalents. |
| GitDiagram, MIT, `ahmedkhaleel2004/gitdiagram@310e2e696b1953cec0e76560cad5e9cd7ca5d964` | Read existing `https://gitdiagram.com/pallets/click.md`: grouped CLI-definition/runtime/terminal/support architecture with source links, explicitly AI-generated from sampled source | Useful architecture onboarding and source-link UX. Reviewed bounded tree/source and Git-blob verification design. No model generation requested, key configured, remote MCP installed or Mermaid imported as verified edges. |

This slice is original ChronosGraph code; **no upstream implementation is copied
or vendored and no new application dependency is added**. The live trial also exposed a navigation issue: filename substrings beat an exact
`Command` symbol match. Exact short-symbol matches now receive a stronger entry
score, ahead of native PageRank tie-breaking, with a native graph regression.
The import-free fixture exposed FalkorDB returning no rows for a nonexistent
`IMPORTS` relationship type; ingestion now uses native File PageRank with a NULL
relationship selector only when there are no File-to-File edges, rather than
fabricating fallback scores or refusing a valid import-free Python repository.
The generic SHA-1 blob
format and API protocol are independently implemented, not a transplant of a
project's module. Existing third-party notices remain unchanged. Evaluation
clones and Gitingest's venv are outside the application worktree. No inference
call was made by this build; the fetched GitDiagram page is already AI-generated
external content, not an output generated or verified by ChronosGraph.

Gitingest digest → useful whole-source baseline. GitDiagram → useful architecture
summary. ChronosGraph → **pinned source evidence connected by native FalkorDB
IMPORTS/CALLS/PageRank, GRAPH.COPY impact and source/policy-bound memory**.
The hackathon submission remains graph-driven, not a wrapper around either site.
No claim that reuse guarantees better agent outcomes, performance or eligibility.

## Verification commands

```bash
# Run native backend/browser suites serially, never overlapping policy fixtures.
flock /tmp/chronosgraph-t09-native-verification.lock \
  env PYTHONPATH="$PWD/backend" \
  CHRONOSGRAPH_SOURCE_CACHE="$HOME/ChronosGraph-t05/.source-cache" \
  .venv/bin/python -m pytest backend/tests -v
cd frontend
npm test && npm run typecheck
NEXT_PUBLIC_API_BASE_URL=http://localhost:8004/api/v1 npm run build
FRONTEND_URL=http://127.0.0.1:3004 CHROMIUM_PATH=/usr/bin/chromium \
  node tests/github-import-smoke.mjs
```

The browser test prepares/copies/rejects commands and reloads catalog; it never
starts an import. A separate live public-Click CLI receipt verifies real API,
archive, graph/index and context integration, then removes only its test tenant.
No external-agent A/B improvement trial, Windows/macOS run or independent review
is claimed. See `tasks/reports/T-09.md` for actual checkpoint results.


## Latest command-center continuation (supersedes earlier UI-only limitations)

The new root UI and `/workbench` are now the monochrome command center. The old
workbench/CLI guide is at `/workbench/tools`; three-track demo/wiki at `/demo`.
The isolated preview is loopback 3004/8004; the old 3000/8001 services were stopped
at the user's request. One-click public imports are now opt-in on this local
preview; private/hosted import and durable job recovery remain unimplemented.
See [current walkthrough, gates and boundaries](t09-command-center.md).
T-09 remains IN_PROGRESS; main has not been merged.
