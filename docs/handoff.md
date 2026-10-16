# ChronosGraph Engineering Handoff

## T-09 current development checkpoint — IN_PROGRESS

Branch `build/t09-repo-workbench-and-trusted-memory`, base published main
`8927b7383f9a256f846d23a394ab0ae32c9383aa`, isolated checkout
`~/ChronosGraph-t09`. True replacement diff sandbox, bounded context/symbol source,
source/policy-bound reported findings and actual MCP activity are implemented.
The five accepted MCP interfaces remain, with five additive tools.
Four-view preview: loopback **3004/8004**, tmux `chronosgraph-t09-ui/api`.
Accepted T-08 checkout, build and **3000/8001** services remain unchanged.

Latest ownership checkpoint: 112 backend tests, 14 frontend tests, typecheck/build,
24 legacy and 9 workbench browser checks pass. Earlier receipts remain historical. Node 20.20.2/22.23.3 unit tests also pass; their
Next startup smoke uses an artifact built on Node 24. Windows/macOS and autonomous
external-agent A/B trials are NOT RUN. Final hygiene/publication receipts are in
`tasks/reports/T-09-evidence/`; checkpoint self-review is not Architect acceptance.
No video or paid models were used.

**New C slice:** pinned CODEOWNERS parser + graph relationships, read-only owners
API/MCP context and workbench trace are implemented. See
`docs/hackathon-alignment.md` and `THIRD_PARTY_NOTICES.md`. Old accepted snapshots
are not automatically backfilled. Latest ownership receipts are in the T-09 report.

**Resume at remaining milestone C:** safe importer/branch connection, mixed-file/Directory/
docstring/JS-TS indexing and explicit workspace sync. Current context
is a pinned snapshot, not verified against uncommitted working-tree edits.
Keep memory described as agent-reported evidence, not independently executed
verification. Keep graph labeled as source overview, not patch simulation.
Do not mark T-09 DONE, merge main or deploy based on the partial checkpoint.
See `tasks/assignments/T-09.md`, `tasks/reports/T-09.md`,
`docs/t09-workbench-preview.md`, `docs/t09-platform-setup.md` and
`docs/t09-agent-evaluation.md`. Remaining sections below are historical handoffs.

## T-06 code/UI accepted (recording deferred)
Branch `build/t06-wow-polish-and-demo`, base `013b66b`. Scope and compatibility
semantics are in `tasks/assignments/T-06.md`. Python snippets are additive AST
simulation inside disposable clones, not source replacement or fetched diffs.
Frontend-only historical cold branches do not change backend replay telemetry.
Docker VM verification: 61 backend tests, 10 frontend tests, typecheck/build,
20 live UI checks, zero production audit/hygiene findings. See `tasks/reports/T-06.md`.
User explicitly deferred all video/demo script/narration work. Do not overwrite
or regenerate those artifacts as part of this code task.

## Current boundary
Contract **v1.3**, additive T-05 acceptance supplied through the user bridge;
prior v1.2 / approved CR-001 and CR-002 remain the historical baseline. T-01 and T-02 are merged. T-03 was
accepted by the Principal Architect and merged via **PR #3** at
`a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7` (includes product commit `25ed5c0` and
acceptance record `c332ea2`). The Principal Architect accepted T-04 at `d47c035`
through the user bridge. M1–M4 and T-01–T-04 are DONE under the accepted v1.2 scope.
T-04 is merged into main through PR #4 at `71f9f7b979b2f4779a812149fe0ac83d184fb4ac`.
Final acceptance polish is included at `dfddf4d`; main is the canonical clone target.
Deployment, external publication and submission are not performed or authorized here.

## T-05 acceptance and running VM

Status: DONE — ACCEPTED AND MERGED.
The Principal Architect accepted `build/t05-real-world-repos` at `ed1d57a`, based on
`36baf30`; see `tasks/reviews/T-05.md`. Dynamic tenant discovery, conservative Git/AST CLI, real bounded
commit-file provenance/backfill, normalized native PageRank and opt-in demo policies
are implemented. The audit query now aggregates traversal branches independently to
avoid the actual join fan-out timeout found on `FalkorDB/code-graph`.

The accepted base passed Docker-backed 40/7 tests and 15 production UI checks.
T-05 passed 53 backend tests, 7 frontend tests, typecheck/build, 17 production UI
checks, all five MCP tools on both external repos, and zero production audit findings.
Full output, ownership limits, 257.62 ms clone outlier and hygiene are in
`tasks/reports/T-05.md`. External graph totals include history and demo policies;
normal investigations add state afterward. Historical T-01/T-02 measurements remain historical.

VM review checkout: `~/ChronosGraph-t05`; production Next.js on loopback **3000**,
API **8001**, Docker DB **6379**, tmux `chronosgraph-t05-ui` / `chronosgraph-t05-api`.
Original accepted-main demo remains on **3001/8000**, tmux `chronosgraph`.
A laptop must tunnel **both** 3000 and 8001 to the same local ports to use the T-05
bundle; the browser's API base is `http://localhost:8001/api/v1`.
Do not expose these unauthenticated services publicly. The original launcher owns
the ephemeral Docker database: stopping it also stops the shared T-05 database.
Persisted runtime graphs are not a backup or reboot-persistent service guarantee.

## Deliverables and ownership
- `README.md`: architecture, one-command local startup, exact track/query/REST/MCP/UI
  judge matrix and historical provenance/telemetry.
- `docs/blog-post-falkordb.md`: complete technical article; 1,200–1,800 words.
- `docs/demo-video-script.md`: exact 2:45 recording plan; no video was recorded.
- `docs/release-checklist.md`: Phase 6 verification, trust boundaries and NOT RUN gates.
- `tasks/reports/T-04.md` and `T-04-evidence/`: builder/integrator evidence.
- `scripts/start-local.sh`, `run-falkordblite.py`, `check-release-hygiene.py`: minimal
  local startup/verification and read-only hygiene helpers. No backend contract changes.

## Run and verify
```bash
# New ephemeral local Docker database plus API/UI (subsequently verified on the VM):
bash scripts/start-local.sh
# Compatible native wheel alternative (platform-dependent):
bash scripts/start-local.sh --db native
# Verification against an explicitly trusted existing FalkorDB:
bash scripts/start-local.sh --db existing --verify-only
# Individual frontend commands; package scripts already select port 3001:
(cd frontend && npm test && npm run typecheck && npm run build)
(cd frontend && npm run dev)
# Separate MCP stdio process after installing backend and seeding FalkorDB:
(cd backend && ../.venv/bin/python -m app.mcp_server.server)
```
Python 3.11+, Node 24+, Bash/npm/network required. Use `VENV_DIR` for an installed
alternative environment. UI is `http://127.0.0.1:3001`; API `/health` is on port 8000.
The MCP modal is a configuration template, not an installed IDE integration.

The original containerless workspace verified native FalkorDB **4.18.3** using falkordblite **0.10.0**,
Redis **8.6.2**, and a process-local compatibility loader. No Docker binary exists
here. The native helper passed on isolated port 6381; existing-DB verification
passed 40 backend tests, 7 frontend tests, typecheck and production build. The
complete fresh evidence, including live-smoke retry history, is in the T-04 report.

## Scientific scope and known limits
Historical source/public-GitHub layers are **458/669** and **4,252/6,251** nodes/edges.
Each tenant initially adds **8/20** fictional demo policy nodes/edges. Live counts
also include persisted investigations/playbooks. Code revisions are pinned, but
cached public GitHub metadata is an ingestion-time snapshot, not revision-pinned.

Cold triage: **6 states / 5 tool actions / 2 dead ends**; replay: **3 actions / 0 dead
ends**, hence **40% fewer tool executions**. Scout/Historian/Verifier are deterministic
roles. No external model is called. Zero tokens/percentages are unmeasured sentinels,
not a token-savings benchmark. Wall-clock speedup can be below 1×. Vectors are lexical
hashes. Synthetic clone dependencies do not execute a diff or prove an outage.

Keep `DEMO_POLICY_SCENARIO`, `SIMULATED_PR_DEPENDENCY`, `DETERMINISTIC_POLICY_TRIAGE`
and `CONTROLLED_ONE_HOP_BASELINE` visible. Confirmed overrides retain superseded
history and invalidate old playbooks; fresh cold triage is required. Incompatible
file/scope policies return HTTP 409. This is a localhost trusted-user single-process
demo with no production authentication or safety guarantee. See release checklist.

## Published integrity checkpoint
The pack was published at `a165abcdb49bff19641c93eddb7625b7afb7ee00`; all 21 changed
files matched fetched GitHub bytes and the checkout was clean. A post-publication
scan covered 129 tracked files / 142 reachable text blobs with zero matched findings,
zero test fixtures and no sandbox/test graph leaks. This follow-up records the result;
final chat identifies the latest branch head and repeats the clean status check.

## Final acceptance and remaining human actions
`tasks/reviews/T-04.md` records the user-supplied Principal Architect acceptance.
The README starts directly from main; the article's release-checklist link targets main.
The final integrator checks scoped hygiene and clean checkout after publishing and merge.

The Docker launcher gap is closed and T-05 is accepted. After integration, record the demo
and publish/submit only after checking the event's actual rules and deadlines.
The short 2:45 script does not include a mutating override; that is an optional
longer take. Prize eligibility, publication and submission are not verified here.

Historical v1.1 red-test report remains evidence, superseded by approved v1.2.
The old archive label `68957811d3a5ba99` was not the actual input ZIP digest; actual
SHA-256: `24624e61ca49734efa026705c022a0b5fb22b6d57a9eb14fd7e2e6dc4097b785`.

## Final integration verification
Fresh final-integration checks: 40 backend tests PASS (4.65 s), 7 frontend tests PASS,
TypeScript PASS. The prior accepted 15-check smoke/build/audit evidence is retained,
not rerun for documentation-only polish. Merged-main hygiene found zero matched
credential/artifact patterns, test fixtures or sandbox leaks; checkout was clean.
See `tasks/reports/T-04-evidence/final-integration/`. Final chat supplies the main
head after this receipt is committed and a repeat clean/hygiene check.

## Final integration receipt
PR #5 (`https://github.com/nakulmaurya/ChronosGraph/pull/5`) merged T-05 into main
at `37f9540dfcfa2c4b97cf0a7ae06889d045e191f5`. Accepted documentation tip `bf047dc0ea74d50a7eaa6458693b66adcf81274c`
is an ancestor of fetched main; the merged tree is identical to that accepted tip.
A fresh merged-main hygiene scan found no matched credential/artifact patterns,
no E2E fixture nodes across all four tenant graphs, no orphan sandboxes and an
empty git status. See `tasks/reports/T-05-evidence/final-integration/merge-receipt.json`
and `merged-main-hygiene.json`. These are observed merge-time receipts; the final
chat supplies the later main head after committing this receipt and repeats the
clean checkout/health scan. No product code changed during closure.

## T-07 utility extension (video deferred)

Branch `build/t07-real-world-utility-and-demo`, baseline `3c27b39` (merged T-06).
See `tasks/assignments/T-07.md` and the T-07 report/review for final gates.
Use `--enrich-utility` only with a matching pinned revision; never reset a source
graph to enable measurements. Existing playbooks need cold re-verification after
constraint fingerprint changes. Exact source Unicode/UTF-8 lengths are captured,
not guessed from LOC; generic graph payloads omit full source text.
Static pytest candidates do not authorize skipping full-suite CI. Context-token
equivalents are `chars // 4`, not model tokens or billed savings. Repository
constraints are source facts, separate from local override governance.
Demo script, voiceover, generator and recording remain untouched.

## T-08 second-brain context mode
Baseline main `80b206d`; assignment `tasks/assignments/T-08.md`. Use the original
five MCP tools and the additive `/api/v1/ctx/*` REST interface; the portable skill
is `skills/chronos-second-brain/SKILL.md`. Exported vaults are local managed
immutable generations with an append-only export ledger. The HTTP download is a
fresh graph snapshot; neither route imports or executes source text. Recovery
snapshots exclude superseded policy text and stale/dead-end playbooks. They are
bounded excerpts, not complete policy authority. Refresh current graph state.

Recording script: `scripts/record-second-brain-demo.cjs`. Requires the four seeded
public snapshots, a running loopback production UI/API and installed Playwright/
Chromium. Set CHRONOSGRAPH_REPO, BACKEND_PYTHON, FRONTEND_URL, TEST_API_URL and
CHRONOSGRAPH_RECORDING_DIR as needed. It changes local policy for the recorded
override scene and restores complete original properties in cleanup; do not run
concurrently with policy writers. The backend replay-guard diagnostic is a real UI
request, not an artificially enabled button. TTS/rendering output stays outside Git.


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

VM rollout verified from code commit `cfd17e1d0f8b8201b06f3a755cd2a8addbc7b9ed`: loopback 3000/8001, 27/27 production checks, four-tenant brain APIs PASS, zero post-rollout hygiene findings. GitHub publication completed after human approval; both main and feature refs remotely verified at 6924c5cae97fd06164618bea3ba9af3629e4ae18.


### Open the running VM from your laptop
Install Google Cloud CLI, then run `bash scripts/connect-vm.sh` **on your laptop**.
The helper requests Google sign-in if necessary and forwards only laptop loopback
ports 3000/8001 to VM loopback 3000/8001. Keep the terminal open, then browse
http://127.0.0.1:3000 (UI) or http://127.0.0.1:8001/docs (API).
Google Cloud access and GitHub sign-in are separate accounts/permissions.
No public firewall ports are opened, and the helper does not restart the VM stack.
