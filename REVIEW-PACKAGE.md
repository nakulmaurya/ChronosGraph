# Source review package — start here

This package is for **external source/evidence review**, not an approved release,
deployment, or guarantee of safe changes.

## Identity

The accompanying `*.manifest.json` and `*.sha256` files identify the exact Git
commit, branch, ZIP SHA-256, per-file source hashes and scoped packaging audit.
The source ZIP deliberately excludes `.git`; do not infer its identity from
`main`, a deployed preview, an older ZIP filename, or historical documentation.
Compare the ZIP hash before extracting, then compare source files against the
manifest. No Git history or worktree-local uncommitted files are included.

The application code is the locally verified `8e83804448cf251a26735d70c5a66f5b0d26db67`
checkpoint; subsequent changes are tests/review helpers, reports and evidence.
The separately captured synthetic behavioral candidate and SDK trial patches
remain **evidence, not integrated application code**.

## Read in this order

1. [External review brief](tasks/reviews/EXTERNAL-REVIEW-BRIEF.md).
2. [Current source status](docs/current-release.md).
3. [Tasks 3–5 checks](tasks/reports/TASKS-03-04-05-2026-10-18.md),
   [fresh Task 7 review](tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md),
   [actual Task 10 read-only browser checks](tasks/reports/TASK-10-READONLY-BROWSER-VERIFICATION.md).
4. [Task 9 original observed evidence](tasks/reports/TASK-09-OBSERVED-COMPARISON.md)
   and [Task 11 reconciled analysis](tasks/reports/TASK-11-COMPARISON-ANALYSIS.md).
5. [Third-party notices](third_party/README.md) for copied upstream SDK context.

Four runtime-check sets passed, but only two native agent turns finished.
Both lookup turns remain permission-stopped with convention/typechecker findings.
**No graph advantage, token/cost savings, general safe-test-skipping, or
cross-session memory benchmark is established.** Task 10 is a scoped read-only
PASS, not full mutating/integration/recovery or production certification.

## Setup and execution boundary

Start with source review; no database, model credential or VM access is required
to read the code and evidence. For the portable **offline record check**, use
Python with pandas installed and follow Task 11. Do not execute the sealed
Task 9 runner/analysis scripts or candidate patches as a startup workflow: their
historical defaults and private inputs are not a portable environment.

For an intentionally isolated local application installation, follow
[platform setup](docs/t09-platform-setup.md), the root README and
[task-bridge setup](integrations/opencode/README.md). The documented verification
environment was Linux/Python 3.13/Node 24 with native FalkorDB. Dependencies, Docker,
external repositories and pinned OpenCode are not bundled. Their installation may
require network access and user review. Source ZIP startup/installation on a
clean external machine was **not rerun for packaging**. Use the supplied exact
source, not `git checkout main` from historical clone instructions.

Do not point setup/seed/import commands at an unrelated database. A new empty DB
does not contain the historical Task 3/7 records referenced by browser receipts.
Read the recovery guide before attempting restore/migration. No private DB dump
or automatic restoration is included.

## Contents, exclusions and disclosure

- Included: committed application source, scripts, manifests/lockfiles, tests,
  documentation, sanitized receipts, candidate patches and selected screenshots.
- Excluded: Git history, SSH/provider credentials, private agent homes/exports/
  reasoning, private graph backups, downloaded agent binaries, dependency trees,
  virtual environments and build caches.
- Sanitized is **not anonymous**: retained evidence contains VM usernames,
  absolute paths, session/message/tool IDs, timestamps and hashes. Review that
  disclosure before posting the archive publicly. Do not silently redact sealed
  originals; create a separately labelled derived package if needed.
- Full evidence-import whitespace checks retain exit 2 warnings in ten
  immutable log/patch/diagnostic files. Scoped new-report checks are separate.
- The source-package scan is heuristic and checks the exact committed tree,
  not Git history, provider systems or all security/license obligations.

No proposal approval/execution, shared-main integration, push, deployment, public
publication or organizer submission is authorized by this ZIP.