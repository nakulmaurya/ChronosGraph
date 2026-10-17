# Quality batch 05 — correctness counterexamples and recoverable UI evidence

Branch: `fix/quality-batch-05-correctness`, stacked on `73fc843` (quality batches 01–04).
Baseline: [repository-wide 20-finding review](../reviews/Q-05-baseline-review.md).

## Delivered

- **Import setup:** exact operator-configurable loopback UI origins shared by CORS configuration and import authorization. Defaults cover local launcher 3001 and preview 3004. The launcher configures UI/API ports and matching API URL/origins consistently. Browser imports remain explicitly opt-in; no wildcard or public-origin exception was added.
- **Fresh branch imports:** mutable branch/tag/default refs fetch from origin before selecting the immutable checkout. Exact 40-character cached commit pins remain usable offline. Fetch failure does not silently reuse an old branch. Tests cover branch advance, rewritten head, unavailable origin and unchanged user checkout.
- **Useful call edges:** normal module imports, module aliases, package-child imports, aliases and relative imports resolve conservative exact definition candidates under plain, src and package/src layouts. Existing ambiguity/shadowing tests remain. Five new native ingestion + GRAPH.COPY tests verify that removing the helper reports the real downstream caller, removed CALLS edge and candidate test, without changing saved source or leaving a clone.
- **Coverage honesty:** impact payloads distinguish all observed AST calls from analyzed function-scope calls and excluded syntax. The UI separates unresolved function-scope expressions from excluded calls and explains lexical receiver/inheritance limitations. This does not implement runtime dispatch or module-initializer graph nodes. Parse failures remain separately disclosed; old saved graphs are not rewritten.
- **Strict new agent configurations:** generated stdio config sets `CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD=1`. In that mode all ten operation schemas require explicit tenant and commit; runtime checks reject omissions before tenant lookup/activity writes/operation. Native subprocess tests verify required schemas, omitted tenant/guard rejection, mismatches, source/preview and reconnect/recall. Existing servers without the flag and legacy HTTP routes retain compatibility; this is not authentication or full F05 closure.
- **Draft recovery:** proposed text/deletion flag saved per tenant + revision + path in browser-tab session storage. Latest proposal is offered on return; loading another file exposes its own saved draft. Resume re-fetches captured source and checks revision/hash before restoring. Preview results never persist. Storage/quota failures warn rather than silently promising recovery. No server-side or cross-device draft persistence, merge or simultaneous multi-file editor is claimed.
- **Stale evidence:** changing/clearing a search aborts its request; late responses are ignored. A new file inspection clears old detail/source before fetching. Commit changes clear previous history; failures offer retry and navigation back to indexed commits rather than a false empty result. Snapshot/map results also check cancellation after response parsing.

## Verification

- Initial red run against the previous implementation: **17 failed / 3 passed** across the original twenty counterexample tests. Later strict-mode/annotation/native-preview cases expanded the suite; those were not part of the initial red count.
- Final backend native suite: **262 passed in 47.31 seconds**, no skipped tests. This includes five ordinary-import broken-caller GRAPH.COPY regressions and the strict real-stdio workflow. Two earlier full passes also passed 256 tests before the last six cases were added.
- Frontend: **32 unit tests passed**, no skips; TypeScript passed. Shell syntax and `git diff --check` passed.
- Isolated production build and **40 desktop/mobile browser checks passed**: 18 change-planning, 18 recovery and 4 agent-setup checks, zero page errors. Change planning issued ten preview POSTs only to the isolated API. Recovery uses explicit read-fault injection; setup checks configuration, not an installed IDE.
- Native postconditions: saved fixture source unchanged; no sandbox graphs left. Test DB/API/UI processes were owned and cleaned by the harness. Source database was copied read-only, not reseeded.
- Evidence on the VM: `~/t09-evidence/quality-batch5/{red-before-fixes.log,final-native/backend-full.log,frontend-unit.log,typecheck.log,final-browser/}`. The final browser directory retains build/API/UI logs, screenshots and JSON results. Earlier passing runs are retained separately.
- Release hygiene: 379 tracked files and 592 reachable historical text blobs scanned; no credential-pattern findings, forbidden tracked artifacts, sandbox/test orphans or fixture nodes in the source database. This is a scoped heuristic scan, not a security certification.
- No new external public GitHub import, clean-laptop install, hosted-model/IDE task, restart/crash recovery, multiprocess stress, scale benchmark or comprehensive accessibility/security audit was performed. Passing this batch does not close those gates.

## Four-persona critique of this batch

These are review lenses applied by the same developer, not independent agents or external approval.

- **Vibe-coding user:** candidate inspection no longer silently destroys a change proposal; failures do not masquerade as success. Still cannot complete a real linked agent task with approval/execution/verification in this product.
- **Junior developer:** ordinary imported function calls and failure recovery are more understandable. Whole-repository inventory, exhaustive search/paging and historical source remain incomplete.
- **Senior developer:** branch identity, explicit strict tool arguments and conservative coverage are stronger. Cross-process coordination, durable import receipts, crash cleanup and broad performance evidence remain unresolved.
- **Open-source maintainer:** concrete review counterexamples are now regression oracles, with native safety postconditions and operator instructions. Clean-install CI, backend lock, deployment hardening and an owner-selected root license remain open.
- **Critique-only readiness judgment:** accept this bounded correctness batch after green checks; **NO-GO for declaring the complete developer/agent command center ready**. Main/live preview are not merged or replaced by this branch push.

## Review disposition — not a claim that all 20 findings are closed

| Finding | Current disposition |
| --- | --- |
| F01 launcher/import origins | Configuration mismatch fixed and regressions added; no fresh external public import or clean-laptop launcher test in this batch. |
| F02 stale branch cache | Reproduced defect fixed; advance/rewrite/offline/pin/user-checkout regressions. |
| F03 durable imports | Open: durable receipts, client idempotency and restart/lost-ack reconciliation. |
| F04 actual agent lifecycle | Open: task/proposal/approval/execution/verification workflow and real coding-client demonstration. |
| F05 strict snapshot safety | Partial: generated MCP strict mode enforced; legacy HTTP/server paths remain compatibility interfaces. |
| F06 module call edges | Reproduced ordinary forms fixed, with native broken-caller tests; dynamic/re-export ambiguity still conservative. |
| F07 call coverage | Partial: observed/analyzed/excluded disclosure and receiver warning; runtime dispatch and initializer modeling not implemented. |
| F08 full inventory | Open: safe all-language inventory separate from semantic parser support. |
| F09 complete history | Open: deleted/non-Python changes, pagination and historical source/diff. |
| F10 exhaustive navigation | Open: paginated navigation/search separated from compact agent context. |
| F11 draft loss | Proposal recovery implemented per tenant/revision/file with baseline checks; server/cross-device persistence is outside this batch. |
| F12 deployment boundary | Open: compose/image pinning and remote access-control design. |
| F13 stale UI evidence | Targeted races/failures fixed with desktop/mobile injection tests; not an exhaustive race proof. |
| F14 version/deep links | Open: identifiable saved versions, stable routes/back/refresh, general storage fallback. |
| F15 branch/commit semantics | Open: default-branch detection and historical commit import semantics. |
| F16 operational guarantees | Open: durable coordination, orphan recovery, bounded deadlines and multi-write failure tests. |
| F17 resource budgets | Open: representative large/dense/cyclic measurements and backpressure. |
| F18 release acceptance | Partial: new counterexample/native/browser/strict-protocol oracles; no clean-install CI or real-client release gate yet. |
| F19 reproducibility/license | Partial documentation update only; backend lock, clean install and owner license decision remain open. |
| F20 UI architecture/a11y | Partial recovery behavior only; shared session model, extraction and broad keyboard/screen-reader review remain open. |

## Next bounded batches

1. Durable, idempotent import lifecycle with lost-response/restart/timeout/publication fault tests; retain one-click public import and explicit trusted-local boundary.
2. Whole-repository file inventory and pageable developer navigation/search; source-language coverage explicit.
3. Commit-change records independent of current files, version identity and deep links.
4. Linked agent task/proposal/approval/execution/verification contracts, then a polished real builder/agent demonstration. Keep reports distinct from observed execution.
5. Cross-process correctness, deployment/clean-install CI, accessibility and scale acceptance before release approval.
