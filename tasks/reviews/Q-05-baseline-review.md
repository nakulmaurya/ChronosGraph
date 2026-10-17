# ChronosGraph — repository-wide quality and readiness review

## Decision

**NO-GO for the complete developer/agent command-center product.** The latest code is a useful trusted-local prototype, not a finished workspace coordination layer. The graph-backed source lookup and isolated impact preview are real improvements. They do not close the import lifecycle, history, navigation, agent execution, or release gaps.

Reviewed revision: **73fc843**, `fix/quality-batch-04-change-planning`, including the four stacked quality batches. Main and the running preview are separate revisions and were not merged, restarted, or changed. The worktree was clean before and after verification.

This is a repository-wide, risk-based code review: backend API/database/ingestion/MCP/services, frontend command center/legacy tools/import/editor/graphs, tests, scripts, dependencies, and operator documentation. It is not an exhaustive proof of every code path, a penetration test, or production certification. The four personas and critique-only readiness pass are separate lenses applied by the same reviewer; **no independent subagents were available or used**.

## Evidence standard

- **R — reproduced now:** isolated fixture or pure source-analysis probe.
- **S — source-confirmed:** implementation directly establishes the issue; no new browser/crash reproduction claimed.
- **G — capability gap:** required behavior is absent or only partly implemented.
- **U — unvalidated:** evidence required for acceptance is still missing; not an assertion that it necessarily fails.

Fresh checks at this revision:
- Native disposable database copy: **235 backend tests passed in 36.59 seconds**.
- Frontend: **30 unit tests passed**, no skipped tests; TypeScript check passed.
- Targeted probes reproduced launcher/import-origin mismatch, stale local Git branch cache, ordinary import call-resolution omissions, and module-level call coverage omissions.
- Prior batch evidence contains 30 targeted browser checks and a successful build. Those browser/build checks were **not rerun for this review**.
- No real coding-client/model task, external service import, concurrency stress, restart/crash recovery, full accessibility audit, or large-repository benchmark was run in this review.

Passing tests establish the tested contracts, not the completeness of the product. New counterexamples below are outside the green suite's current acceptance oracles.

## Four persona passes

| Persona | Acceptance question | Judgment and reason |
|---|---|---|
| Vibe-coding user | Can I bring my repository in, see what the agent is doing, inspect a proposed change, approve it, and trust the result without terminal repair? | **FAIL.** Launcher/import mismatch, uncertain import completion, lost drafts, and no linked agent task/approval/verification loop. |
| Junior developer | Can I discover an unfamiliar project, navigate every relevant file and function, understand a commit, and return to the same context? | **FAIL.** Partial file inventory, non-pageable limits, three-result search, incomplete calls/history, indistinguishable saved-version labels, and no deep navigation state. |
| Senior developer | Can I distinguish observed evidence from inference, reproduce the exact version, inspect dependency uncertainty, and rely on failure/concurrency behavior? | **FAIL for full acceptance.** Good source hash checks and clone isolation, but stale branch cache, unresolved scope blind spots, process-local coordination, silent error paths, and missing scale evidence remain. |
| Open-source maintainer | Can a contributor clone, run, test, reproduce, and safely release this without previous-session knowledge? | **FAIL.** Setup paths disagree, backend dependency resolution is not locked, no checked-in CI workflow, historical documentation conflicts, and no root project license decision. |

These are acceptance decisions, not numerical scores or percentage-complete estimates.

## Findings, ordered by release impact

### F01 — P1 / R: default launcher and browser importer disagree
**Evidence:** `scripts/start-local.sh:83–90` starts UI 3001 and API 8000. `backend/app/services/import_jobs.py:35–41` accepts only origins on 3004. With browser import explicitly enabled, a constructed request from `http://127.0.0.1:3001` receives 403; the otherwise identical 3004 request is authorized.

**Impact:** the normal local setup cannot deliver the advertised one-click import merely by enabling it.

**Acceptance:** one source of truth for host/ports/operator import opt-in; test the documented launcher configuration through capability discovery and a real import start. Do not weaken the origin policy to `*`.

### F02 — P1 / R: branch-based local ingestion can silently index an old commit
**Evidence:** `backend/app/ingestion/ingest_repo.py:29–75`. A cache is cloned once. A resolvable branch ref is used without fetching; absent ref uses cached HEAD. Temporary two-commit Git fixture: after advancing source `main`, `repository_source(source, 'main')` still returns the first commit. An explicit new SHA fetches and returns the new commit.

**Impact:** a user can create a new saved version and reasonably expect the current branch, but receive old code. The separate guarded workspace CLI avoids this when an exact new SHA is supplied; that does not fix the generic ingestion path.

**Acceptance:** explicitly distinguish pinned-cache reuse from current-branch import; resolve/fetch current branch before pinning, record the decision, and regression-test advance/rewrite/offline behavior without modifying the user's checkout.

### F03 — P1 / S: imports have no durable, idempotent lifecycle
**Evidence:** `backend/app/services/import_jobs.py:20–23,44–96`: process-local job map/active flag, daemon thread, temporary receipts, subprocess timeout. `frontend/src/components/RepositoryImport.tsx:101–123`: client stores receipt only after receiving the response. If the server accepts the mutation but its response is lost, the client has no receipt ID to reconcile and can offer retry. A subsequent retry after completion can create another random tenant. Restart loses job/active state.

**Impact:** uncertainty is communicated more honestly than before, but backend recovery and duplicate prevention remain incomplete. A restart can also leave a worker/incomplete graph needing operator attention. These restart consequences are source-review risks, not crash-tested outcomes here.

**Acceptance:** persist a client-generated idempotency key before submit; durable job state linked to tenant/revision; reconciliation after lost acknowledgement/restart; explicit terminal/incomplete status; repeat same request without duplicate snapshot. Cover restart, timeout and interrupted publication on a disposable DB.

### F04 — P1 / G: the central human–agent workflow is still absent
**Evidence:** `backend/app/services/agent_activity.py`, `task_memory.py`, MCP server and the command-center Agent activity/Changes screens. Activity records tool invocations; findings save agent-reported text. There is no linked task → agent run → proposed change → human decision → execution result → verification lifecycle.

**Impact:** this is an observability/retrieval prototype, not yet the interactive coordination layer requested. A config-copy modal is not a connected-agent session.

**Acceptance:** a real coding client completes one bounded task on a selected repository/version; UI exposes source evidence, proposed diff, explicit human decision, externally reported execution/test results, and reconnectable IDs. Keep reports distinct from independently observed execution. Approval can gate a coordinated workflow but must not be advertised as an OS sandbox for an external IDE.

### F05 — P1 / S+G: snapshot safety is optional, not enforced as the default product contract
**Evidence:** all ten legacy operations in `backend/app/mcp_server/server.py:14–98` retain default tenant and optional `expected_revision`; `agent_activity.py` checks it only when present. Discovery/preflight is explicitly not persistent binding. Many legacy HTTP mutation routes likewise have no expected-version field.

**Impact:** a client can omit the handoff arguments and continue against the default tenant. Existing compatibility is intentional, but instructions alone are not a strict selected-workspace contract.

**Acceptance:** a strict command-center/agent mode requires tenant and version on every operation, refuses omission before work, and preserves legacy behavior only via a clearly separated compatibility interface. Test omitted/wrong/unknown identity, not just wrong supplied hashes.

### F06 — P1 / R: ordinary Python import forms lose useful call edges
**Evidence:** `backend/app/ingestion/dependencies.py:39–49`. The probes index `pkg/mod.py:helper` and call it from another file using (a) `import pkg.mod; pkg.mod.helper()` and (b) `from pkg import mod; mod.helper()`. Both are reported unresolved even though the static target is unambiguous in the fixture. File IMPORTS edges are present.

**Impact:** ordinary cross-file function navigation and broken-caller explanation remain weaker than the UI suggests. This is not evidence that all imports fail; direct function imports are covered elsewhere.

**Acceptance:** normalize binding target/module suffix correctly; add both cases plus aliases, src roots, re-exports and shadowing. Resolve only when justified; keep genuinely ambiguous cases unresolved. A breaking helper rename must flag the known downstream caller in both fixtures.

### F07 — P1 / R+S: call coverage can look better than it is
**Evidence:** `backend/app/ingestion/ast_parser.py:104–119` records calls only when there is an enclosing function. Probe: `VALUE = helper()` at module scope produces zero observed calls and zero unresolved calls. Class-body calls have related scope limitations. Receiver resolution in `dependencies.py:29–34` maps a method to the lexical class; the inheritance probe resolves `A.run`'s `self.helper()` to `A.helper` without representing the subclass override alternative.

**Impact:** “0 unresolved calls” is not complete coverage, and a resolved static candidate is not a unique runtime dispatch target. Import reachability can still capture file-level impact; the finding is about function evidence and coverage honesty.

**Acceptance:** count observed, resolved, unresolved and excluded constructs separately; represent module/class initializers or disclose their exclusion. Label lexical receiver targets as candidates and expose inheritance uncertainty. Do not guess through arbitrary dynamic dispatch.

### F08 — P1 / G: repository inventory is not the whole repository
**Evidence:** `_ingest_repo` selects tracked `*.py`; public intake selects Python plus a small support-file allowlist. Command-center counts/graph are built from those File nodes.

**Impact:** JS/TS, configuration, build/deployment files and other assets cannot be explored as the complete architecture. The Python footer helps but does not deliver the requested whole-codebase map.

**Acceptance:** inventory all safe tracked file paths/languages independently of semantic parser support; show indexed/unsupported/failed/excluded coverage explicitly. Keep non-Python nodes useful even before adding language analyzers.

### F09 — P1 / S+G: history cannot yet explain repository changes completely
**Evidence:** `ingest_repo.py:78–125` indexes bounded history and only links changes whose paths are in current Python `known`; deleted and non-Python paths disappear. `services/command_center.py:70–86` provides an 80-commit window and current-snapshot inspection, not historical source. Public archive imports intentionally have no history.

**Impact:** the promised “what changed with which commit” story is incomplete, particularly for deletion/rename/configuration changes. UI warnings are truthful but are not feature completion.

**Acceptance:** model commit-file changes independently of current File existence; preserve status/old path/new path; paginate history; offer explicit historical source/diff or an unambiguous unsupported state. Public snapshot import must explain history scope before the user reaches an empty History screen.

### F10 — P1 / S: bounded navigation has no complete way to reach the remainder
**Evidence:** `services/command_center.py:10–40` truncates inventory before prefix filtering and displays first 120 groups; no cursor. File details cap 80 imports/importers, UI shows 12, graph 20. `context_locator.py:58–76` selects at most three files/five symbols as a compact context package; CommandCenter uses it as general search and ignores most coverage details.

**Impact:** narrowing cannot recover the 121st root-level group, and three-result compact context is not repository search. For graphs beyond the file bound, filtering after the global cut also hides later prefixes. This is a code-path conclusion, not a large-repo benchmark.

**Acceptance:** separate paginated navigation/search from budgeted agent context; filter on the server before paging; next-page controls and totals; exact-path lookup independent of ranking; regression fixtures exceeding every presentation cap.

### F11 — P1 / S: normal inspection can destroy an unsaved change plan
**Evidence:** Changes is conditionally mounted in `CommandCenter.tsx:187`; `ChangePlanner.tsx:14–15` resets state and aborts on identity changes/unmount. Clicking a candidate navigates to inspection and unmounts the editor. No draft persistence/restore or dirty-navigation warning.

**Impact:** a recommended next interaction can throw away the proposal the developer was evaluating.

**Acceptance:** persist drafts by tenant+revision+file, or explicitly confirm discard. Inspect candidates without destroying the plan; return restores source, proposal, deletion state and applicable result. Invalid/stale results must remain invalidated after edits.

### F12 — P1 / S: deployment defaults are inconsistent with the local-only boundary
**Evidence:** root `docker-compose.yml` publishes database/UI ports without a loopback host; uses `falkordb/falkordb:latest`. Launcher binds loopback but also uses `latest`. API mutation routes other than import have no application authentication. `db/client.py` has no configured DB credentials/TLS boundary.

**Impact:** trusted-local assumptions are documented, not enforced by every provided deployment path. CORS is not authentication. This is not proof of a remotely exploitable deployment on the current VM.

**Acceptance:** loopback-only default compose ports, pinned tested image, explicit opt-in remote mode with real access control, startup boundary checks and documented threat model. Never fix this by merely adding more CORS origins.

### F13 — P2 / S: stale UI evidence can survive a changed selection/request
**Evidence:** `CommandCenter.tsx:98–103` does not clear prior commit changes while fetching a newly selected commit; failure leaves old changes rendered beneath the new selection. `inspect` clears source but leaves old detail on failure. `search` can repopulate results after the input was cleared because clearing text does not abort/invalidate that request.

**Impact:** the screen can show evidence for a previous request with insufficient identity context. Batch2 fixed repository switching; that does not cover all intra-repository transitions.

**Acceptance:** request-key every data view by tenant/version/path/query/commit; hide or explicitly label prior data during transitions; delay/failure tests for A→B, search→clear and rapid selection changes. No browser reproduction of these particular races was run in this review.

### F14 — P2 / S+G: saved-version identity and navigation are too weak
**Evidence:** CommandCenter dropdown labels contain only `repository`, while imports create new random tenants. Selection/tab/prefix/file are component/localStorage state, not a deep-link route.

**Impact:** repeated imports look alike; refresh/back/share cannot reconstruct a specific investigation. LocalStorage is also used without availability/error handling.

**Acceptance:** repository grouping plus version labels with branch, short commit, time and provenance; stable URL for exact snapshot/tab/path/symbol; back/forward and refresh tests; safe storage fallback.

### F15 — P2 / S: the Commit hash field is stricter than its ordinary meaning
**Evidence:** `github_import.py:218–230` requires the supplied SHA to equal the branch's current head. Import UI says optional commit hash/latest on branch but does not clearly say an older commit is refused. Empty branch means literal `main`, not the repository's actual default branch.

**Impact:** perfectly valid older hashes/default-master repositories surprise users.

**Acceptance:** either label this as current branch-head confirmation, or implement pinned historical commit selection with provenance; detect default branch when omitted. Test master/default-branch changes and moved-head confirmation.

### F16 — P1 / S+U: coordination, cleanup, and indexing need stronger operational guarantees
**Evidence:** `common.py` uses process-local RLocks; ingestion uses separate Redis writer locks; these are not a common mutation protocol. `db/client.py:47–51,88–97` suppresses general index/clone-delete exceptions. Policy override uses two writes, so provenance can fail after supersession commits. Diff/audit detect cleanup failure after normal completion, which is useful, but cannot clean up after process death by itself.

**Impact:** claims such as “production manager”/“guarantees cleanup” exceed the failure model. Cross-process races and crash recovery were not reproduced here and remain required tests.

**Acceptance:** explicit concurrency ownership and bounded DB deadlines; report index readiness/failure; durable orphan detection/recovery; failure injection between policy writes; two-process mutation tests. Keep original operation errors and cleanup errors distinguishable.

### F17 — P2 / U+S: resource and graph UX budgets remain unproven
**Evidence:** map reads broad inventories/edge sets then filters in Python; context lookup scans all indexed file/symbol records; diff reparses captured sources and copies a graph per preview. CommandGraph uses a simple three-lane heuristic, not a measured large-graph layout. Activity repeatedly recalls findings.

**Impact:** node/response caps do not establish bounded CPU, memory, DB execution time or responsive interaction.

**Acceptance:** declared repository tiers; measured cold/warm p50/p95, memory, query plans, clone cost and UI interaction budget; server-side deadlines/backpressure; representative dense/cyclic/large repositories. No latency promises until measured.

### F18 — P1 / G+U: acceptance tests are stronger, but still not a release gate
**Evidence:** new backend stdio/source/impact tests and browser harness are worthwhile. Fresh green suite still misses F01/F02/F06/F07. No checked-in `.github` CI workflows. Disposable verifier relies on an installed environment and four pre-existing source graphs; real IDE, lost POST acknowledgement, restart, multiprocess, broad accessibility and large-repo cases are not established.

**Impact:** a contributor cannot interpret “235 passed” as the new product's complete acceptance test. The previous tests should not all be deleted: many protect useful safety/compatibility contracts.

**Acceptance:** add regression oracles for reproduced findings; a clean-environment setup gate; persistent import fault tests; linked real-client acceptance; deterministic fixtures; security/keyboard/performance suites and CI artifacts. Separate compatibility, feature acceptance and release evidence.

### F19 — P2 / S: maintainer handoff is not reproducible enough
**Evidence:** backend dependencies are lower-bound ranges in `backend/pyproject.toml`, without a backend lock; frontend has a package lock. Pytest is a runtime dependency. Root project has no LICENSE (vendored code has its own license/notice). Historical docs describe previous tool counts, service states and importer limitations, with later “supersedes” appendices rather than one current setup contract.

**Impact:** installs can drift and contributors need session history to determine authoritative behavior. Missing root license is a distribution/reuse decision, not permission to remove third-party notices.

**Acceptance:** supported Python/Node/OS matrix; locked backend environment and development extras; clean install; one authoritative setup/status document; archived historical notes; owner-selected root license and complete retained notices.

### F20 — P2 / S+G: UI architecture and accessibility are only partly modernized
**Evidence:** CommandCenter hosts multiple async workflows in one stateful component; Changes/CommandGraph are compressed, making lifecycle review difficult. Ownership and Agent activity still embed legacy Workbench and its duplicate catalog/snapshot/subgraph fetching. Graph interaction has an alternative explorer, but no complete keyboard/screen-reader acceptance evidence.

**Impact:** premium monochrome styling is ahead of coherent information architecture. File relationships, history, ownership, agent task state and change plans still feel like connected tools rather than one working session.

**Acceptance:** shared selected-snapshot session/data model, separate feature screens/hooks, retained workspace context, named loading/error/empty states, accessible inspector navigation and graph-equivalent lists. Test keyboard-only, focus, contrast and mobile interactions; do not equate screenshots with accessibility approval.

## What should be retained

- FalkorDB remains a real core dependency: graph inventory, provenance, CALLS/IMPORTS traversal, GRAPH.COPY previews, graph-backed findings/activity, policy lineage and playbook behavior.
- Source hash verification, exact snapshot preflight, safe archive/blob checks, no repository code execution during intake, preservation of old snapshots, and explicit static-analysis caveats are valuable.
- New behavioral fixtures are better than exact tool-count or screenshot-only tests. Keep them and add counterexamples rather than relaxing assertions.
- Test candidates are recommendations, not safe-skip proof. Agent-reported evidence is not independently executed verification. These distinctions should remain visible but move into a consistent evidence model instead of repetitive warning blocks.

## Critique-only quality/readiness pass

The coding work addressed bounded pieces of earlier findings, not complete acceptance of those findings. In particular:
1. Lost-receipt UI handling is **not** durable import recovery.
2. Stdio subprocess tests are **not** a real coding-client demonstration.
3. A per-call optional hash is **not** mandatory workspace binding or authorization.
4. A before/after import picture is **not** complete function impact or a persistent change plan.
5. Python file counts are **not** whole-repository coverage.
6. Bounded lists without a cursor are **not** complete navigation.
7. A successful fixture on an existing VM is **not** reproducible clean-room release evidence.
8. Four self-review lenses are **not** independent reviewer approval.

**Release decisions:**
- Continued isolated development: **GO**.
- Supervised trusted-local alpha: **conditional**, with exact revision and limits disclosed; do not claim smooth default setup until F01/F02 are fixed.
- Polished end-to-end builder/agent demo: **NO-GO** until a real client workflow is evidenced.
- Complete developer command center or public multi-user deployment: **NO-GO**.
- Hackathon packaging: graph-centric differentiation is present, but no new hackathon eligibility/compliance audit or measured autonomous-agent/token-savings claim is established by this review.

## Recommended corrective batches and acceptance gates

**A — Trust the selected code:** F01/F02/F05/F06/F07/F13. Fix reproduced setup/cache/analyzer gaps, strict version contracts and request identity. Gate: new counterexamples fail before fixes and pass afterward; no old safety regression.

**B — Reliable intake:** F03/F15/F12. Durable idempotent jobs, acknowledgement/restart reconciliation, real default branch semantics, standard local deployment. Gate: clean-launch real import plus dropped response, restart and interrupted-worker recovery in disposable infrastructure.

**C — Make the workspace navigable:** F08/F09/F10/F11/F14/F20. Full inventory, paginated graph/search/history, durable change drafts, explicit saved-version selection and deep links. Gate: a new developer can find a known file beyond every old cap and return to the same draft after inspecting its affected test.

**D — Deliver the actual agent loop:** F04 plus strict snapshot/task/evidence integration. Gate: real coding-client task with source-linked proposal, human decision, recorded verification and reconnectable UI session; explicitly distinguish observed results from agent reports.

**E — Maintainer/release hardening:** F16/F17/F18/F19 plus complete accessibility acceptance. Gate: clean install/CI, fault/concurrency/performance evidence, documented deployment boundary and owner-approved licensing.

Do not merge all of these merely because aggregate tests pass. Review each batch against its stated user outcome, then repeat all four persona passes and a critique-only readiness decision.

## Source navigation

All references above are relative to the reviewed commit. Stable root:
https://github.com/nakulmaurya/ChronosGraph/tree/73fc843

Key source links:
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/backend/app/services/import_jobs.py
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/backend/app/ingestion/ingest_repo.py
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/backend/app/ingestion/dependencies.py
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/backend/app/ingestion/ast_parser.py
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/backend/app/services/command_center.py
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/frontend/src/components/CommandCenter.tsx
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/frontend/src/components/ChangePlanner.tsx
- https://github.com/nakulmaurya/ChronosGraph/blob/73fc843/tasks/TESTING.md

Evidence folder contains fresh test logs, probe scripts and observed outputs. Probes do not modify production source or existing repository data. The runtime probe's Git revision resolution may print an expected failing `rev-parse` diagnostic before successfully fetching the explicit new commit; judge its JSON result rather than that intermediate stderr message.
