# T-09: upstream reuse decisions and improvement plan

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

Status: source review, not a guarantee of better agent outcomes or full T-09 completion.
Roles: builder + integrator sequential self-review. No independent audit.

Selected upstream files were downloaded as text at immutable commits listed in
`t09-upstream-sources.json`. The initial review executed/installed no upstream code. A subsequent authorized
slice vendors the pinned MIT CODEOWNERS parser unchanged, with license and notices;
its matching code is exercised by tests. Other upstreams remain review-only. GitHub repository license
badges were checked against actual license text; badges alone are insufficient.

## Immediate measured improvement in our own implementation

`backend/app/services/context_locator.py` previously selected the first five
symbols collected for a matched file, regardless of the query. A native fixture
with eight decoys preceding `needle_target` reproduced omission of the requested
symbol. Now symbols are ranked by query match (exact short name, substring, then
qualified name), with deterministic source-line/name tie breaking. Exact matches
are retained first when byte-budget trimming removes symbols from the tail.
The coverage flag also reports omission of symbols beyond the per-file limit.

This is an original local change, not copied Aider source. It adopts the general
principle of task-sensitive context selection, not Aider's full weighted graph
algorithm. A red-before/green-after regression tests the exact omission; it does
not establish external-agent task success or token savings. Hard payload budgets,
source hashes, policy boundaries and conservative graph analysis remain intact.

## 1. Aider: task-sensitive ranking and structural context (Apache-2.0)

Reviewed `aider/repomap.py`: definition/reference tags, mentioned-file/identifier
personalization, weighted graph ranking, scope-aware snippets and budget fitting.
Source: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py
License: same commit, `LICENSE.txt`.

**Pick:** explicit task identifiers, file targets and relationship evidence as
ranking signals; structural signatures with exact source coordinates.
**Where:** `context_locator.py` and future JS/TS indexing adapter.
**Keep:** FalkorDB as the graph authority. Do not import Aider's agent/editor/model
stack or replace native graph queries with a second permanent NetworkX graph.
**Change rather than copy:** keep content-hash/revision-based cache keys; do not
rely on mtime-only freshness. Retain our strict byte cap even if a token-budget
heuristic would permit overshoot.
**Gate:** entry-point/symbol recall at fixed 2/4/8 KiB budgets, deterministic
ordering, warm/cold latency, and no stale cache after same-mtime content edits.
If source is adapted later, preserve Apache license/attribution and any applicable
upstream notices, mark modifications and assess transitive dependency licenses.

## 2. Repomix: collection pipeline, exclusion safety and token accounting (MIT)

Reviewed `src/core/file/fileCollect.ts`, `src/core/git/gitCommand.ts`,
`src/core/security/{validateFileSafety,securityCheck,filterOutUntrustedFiles}.ts`,
`src/core/metrics/{TokenCounter,tokenCountCache,tokenEncodings}.ts`.
Source: https://github.com/yamadashy/repomix/tree/55c6de6aebde4c38877fbcaf005c4cc396bf6e2d/src/core

**Pick:** separate collection/validation/security/measurement stages; explicit
skip reasons; encoding-labeled token counting and bounded token-count caching.
**Where:** milestone C importer/workspace inventory and context/export metrics.
**Do not pick blindly:** its permissive supported remote URL forms are broader
than our intended public-GitHub allowlist. Its reviewed safety routine warns on
suspicious Git diffs/logs yet retains them. ChronosGraph should redact/omit
suspicious source, history and diff content consistently before persistence or
export, and document false positives/negatives rather than promise no secrets.
**Implementation fit:** use native Python services or a narrow adapter; do not
add the whole Node CLI to the backend just for file scanning/token counting.
**Gate:** `.env`/key fixtures, suspicious diffs/history, binary/oversize files,
UTF-8/multilingual source, ignored files, symlink escapes and actual byte counts.
Token counts must name the encoding; neither tokenizer counts nor chars/4 are
provider-billed usage or proof of savings.

## 3. sbdchd/codeowners: declared ownership (MIT)

Reviewed `CodeOwners`, `matching_line`, `matching_lines`, `of`, owner parsing and
pattern translation in `codeowners/__init__.py`.
Source: https://github.com/sbdchd/codeowners/blob/ad29fa77ce9726d97103cc49fbfcf4e295679034/codeowners/__init__.py

**Selected and implemented:** vendor the pinned MIT Python parser unchanged behind
a bounded GitHub-subset adapter. Preserve matching pattern, source line, commit
and hash in FalkorDB. See `THIRD_PARTY_NOTICES.md` and `hackathon-alignment.md`.
**Where:** new `backend/app/ingestion/codeowners.py`, declared-owner evidence in
context/rules UI, separate from Git author contribution history.
**GitHub wrapper required:** choose `.github/CODEOWNERS`, root `CODEOWNERS`, then
`docs/CODEOWNERS` (first existing); last matching pattern wins. Explicitly test
invalid/unsupported patterns, empty owner rules, case sensitivity, escaped spaces,
team/user/email forms and source branch/revision. Library supports GitLab sections;
do not silently claim those are GitHub semantics.
GitHub reference: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
**Gate:** precedence/pattern fixtures and source-line links. A declared owner is
not proof of GitHub identity, team membership, write access or enforced review.

## 4. Tree-sitter Python bindings: JS/TS syntax evidence (MIT bindings)

Reviewed `Parser`, `Tree`, `Node`, `Query` API and error/source-coordinate fields
in `tree_sitter/__init__.pyi`.
Source: https://github.com/tree-sitter/py-tree-sitter/blob/2e556e540dd4ccce0e24c92d4413ef9ac85284a5/tree_sitter/__init__.pyi

**Pick:** pinned bindings + separately licensed/pinned JS/TS grammar packages for
import/export and symbol extraction. Keep the proven Python `ast` path.
**Where:** future `backend/app/ingestion/js_ts_parser.py`; shared mixed-file
inventory with `Directory-CONTAINS->File` and source-bound import evidence.
**Boundaries:** grammar licenses/ABI and packaging still need evaluation. Parsing
is not full TS module/type resolution. Path aliases, package exports, dynamic
imports, barrel re-exports and error nodes require explicit unresolved evidence;
never invent CALLS edges from mere identifier mentions.
**Gate:** TS/TSX/JS/JSX fixtures, Unicode byte-vs-character ranges, malformed syntax,
relative paths, exports and documented unsupported resolution; portable installs.

## 5. python-pathspec: useful, but license is version/file dependent

Reviewed `pathspec/gitignore.py`, ignore backends/patterns and `LICENSING.md`.
Source: https://github.com/cpburnz/python-pathspec/blob/4f65e9d67cbe2dfc635794fc3da243f1c8aa1bfd/LICENSING.md

The repository badge says MIT, but its actual licensing document states old code
before May 24, 2026 remains MPL-2.0-only and newer code is dual licensed. Do not
label the complete project MIT based on the badge.
**Pick:** preferably Git's own NUL-safe `ls-files` / `check-ignore` for local Git
repositories. Consider a pinned pathspec dependency only where non-Git matching
is actually required and after checking that release's licensing obligations.
**Do not:** use gitignore matching as CODEOWNERS semantics or a security boundary.
**Gate:** nested ignores/negation, tracked-but-ignored files, spaces/non-ASCII,
.git/info/exclude behavior and explicit secret exclusions. No symlink following.

## 6. context-mode: architecture reference, no code adoption (ELv2)

Source license: https://github.com/mksglu/context-mode/blob/5f6298a9bdc480ebc7c88a29c9fbdf38ae2f8cb6/LICENSE

The inspected license is Elastic License 2.0, including a restriction on hosted
or managed access to a substantial set of its functionality. Treat it as
source-available, not a permissive open-source drop-in. No implementation reuse
is approved by this review. Discuss desired behaviors (bounded tool results,
relevant session recovery, client-supported compaction hooks) independently;
use original code/permissively licensed components after review. Do not copy
hooks/execution engine or add arbitrary-code execution to ChronosGraph.
Compaction integration must be verified per client; current exported snapshots
are not proof of an automatically installed Claude/Cursor hook.

## Project-specific priorities upstream code cannot replace

1. Harden existing `repository_source` before exposing browser imports: local-root
   allowlist and exact GitHub HTTPS host/path rules; reject credentials/options,
   unsupported transports/submodules/LFS execution and unexpected redirects.
   Apply time/byte/file limits, sanitize Git environment/config, disable prompts,
   hooks and filters. Prefer reading pinned Git blobs over checkout side effects.
2. Isolate cached snapshots by full commit and guard concurrent operations. The
   current locator-keyed mutable checkout is not a safe multi-user branch store.
3. Implement explicit HEAD/worktree sync with add/change/delete/rename evidence,
   content hashes and staging/snapshot consistency. Do not silently overwrite a
   graph or label unchecked workspace contents fresh. Invalidate findings only
   against the correct source/policy generation.
4. Keep GRAPH.COPY replacement analysis, shortestPath replay and ACTIVE/SUPERSEDED
   lineage as ChronosGraph's core. Upstream repo packers are not substitutes for
   graph correctness, clone cleanup or stale-playbook HTTP 409 guards.

## Proposed sequence and measurable acceptance

- Immediate: original query-sensitive symbol fix + native regression.
- Next: safe import/workspace generation model; Git-backed inventory/ignore tests.
- Then: declared CODEOWNERS and Python docstrings; JS/TS imports with parse gaps.
- Finally: richer task-sensitive ranking, encoding-labeled token metrics, live
  activity highlighting and client-specific recovery adapters.
- Always: existing backend/frontend/browser gates and source hygiene; same-agent,
  same-model A/B task correctness, recall, bytes and latency before outcome claims.

Before any actual third-party code inclusion: pin source/release and digest,
review the exact license/dependencies, record copied files/modifications in
THIRD_PARTY_NOTICES, preserve required notices and scan source/artifacts. No root
project LICENSE was found in the local reviewed tree; choose/verify ChronosGraph's
own distribution license rather than assuming GitHub publication grants one.
Only the explicitly selected MIT CODEOWNERS parser has been adopted. Other
runtime dependencies or upstream code are not approved merely by appearing here.
