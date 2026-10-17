# Bulk command-center critique-only acceptance review

## Decision: NOT READY for the complete product

The bulk fixes materially improve reliability and navigation. They do not yet deliver the requested end-to-end developer/agent coordination product. Do not label the redesigned UI final or production-ready.

Method: four user personas plus a separate critique-only readiness pass, applied by the same reviewer to the code changes, previous repository-wide findings and current test evidence. No independent agents or OpenCode were used; independence is not claimed. This is risk-based source/test review, not exhaustive verification or a security certification.

## Four persona lenses

| Lens | Improved and demonstrated | Still below full acceptance |
|---|---|---|
| Vibe-coding builder | Import recovery preserves a saved request across lost responses and reload. Inventory and exact saved-version navigation reduce ambiguity. Proposed source remains a preview. | There is still no real coding-client task/proposal/approval/execution/verification loop. Imported repository code is not automatically modified or tested. A successful transport fixture is not a real GitHub/IDE demonstration. **Full acceptance: FAIL.** |
| Junior developer | Non-Python/excluded files are visible with explicit unsupported-analysis labels. Large folders/search/history tails are reachable by paging. Deleted files are represented independently from the current tree. | Python-only semantic coverage, bounded high-degree definitions/dependencies, latest-40 default local history and no historical source checkout still limit exploration. Public archives have no history. **Full acceptance: FAIL; navigation subtask substantially improved.** |
| Senior developer | Redis idempotency, process replacement, ownership-safe active-key release and publication reconciliation have native regressions. Static evidence is separated from unsupported inventory. Synthetic latency is measured, not guessed. | No maximum-size real-repository import/concurrency result; process-wide legacy mutation safety and interrupted graph remediation remain incomplete. Every-second AOF is not zero-loss durability. **Full acceptance: FAIL.** |
| Open-source maintainer | Runtime/test dependencies have a hashed Linux/Python 3.13 lock; fresh installation is tested. CI definitions and a pinned loopback persistent DB deployment are checked in with explicit scope. | Root license remains an owner decision; remote CI results must be inspected, build toolchain is not fully locked, broad platform/a11y coverage and stale historical documentation remain work. **Full acceptance: FAIL.** |

## Critique-only release gate

### Closed or materially reduced in this batch

- Process-local receipts and post-response-only client identities were replaced with Redis receipts and pre-submit persisted IDs.
- The old first-window overview/search/history omissions have paged developer routes with tests reaching tail entries.
- Current Python `File` nodes are no longer the entire repository inventory.
- Commit-file evidence no longer requires a file to survive into the saved tree.
- Identical repository names are disambiguated by commit and saved-version suffix; copied workspace links guard exact identity.
- Unpinned DB image/runtime dependencies now have explicit tested alternatives and crash-recovery coverage.

### Blocking the complete product

1. **P1 — Human–agent lifecycle absent.** Implement linked durable task/run/proposal/human-decision/execution-report/verification records, with actual supported coding-client demonstration. Approval must not be advertised as an OS security boundary for an external client.
2. **P1 — Legacy mutation/concurrency contracts remain broader than strict selected-version operation.** Apply version checks and cross-process coordination consistently; stress failure and policy-write races. Strict MCP handoff does not fix all legacy HTTP operations.
3. **P1 — Interrupted worker cleanup is manual.** A SIGKILL can leave an incomplete graph. The receipt honestly reports interruption and never auto-deletes it, but operator review is not automated orphan remediation. Seven-day idempotency expires; database loss is outside its guarantee.
4. **P2 — Scale evidence is synthetic and single-client.** The 5,000-file benchmark and 245-entry paging fixture are useful regressions, not representative large-repository import/load testing.
5. **P2 — Language/history coverage is intentionally limited.** Inventory is not all-language semantic understanding. Dynamic dispatch and arbitrary historical source remain unsupported. Public archive input still requires bounded Python source and complete safe trees.
6. **P2 — UI acceptance incomplete.** Desktop/mobile browser checks do not replace a screen-reader/keyboard audit or shared-state refactor. Paging a graph can omit cross-page edges; bounded lists remain disclosed rather than exhaustive.
7. **Release governance — license/CI.** Owner must choose the root license. Do not claim a passing remote CI run merely because the workflow file exists or local commands passed.

## Review corrections made before handoff

- Fixed an idempotency race: concurrent retries could see their own active lease before rereading their receipt and incorrectly receive 409.
- Fixed Redis decoded-response assumptions in new tests; retained native Redis rather than replacing it with a mock.
- Corrected Compose persistence to use the pinned image's actual `REDIS_ARGS` entrypoint contract, rather than an ignored/misleading command override.
- Prevented unsupported inventory entries from offering Python change planning or displaying “no dependencies” as though analysis had run.
- Added a visible unselected state for unavailable saved-version links; no silent snapshot substitution.
- Corrected a new test's false assumption that README was unselected: README is intentionally extracted as bounded rule evidence. The test now asserts inventory and semantic contracts without weakening archive safety.

No percentage-complete estimate or all-persona pass is warranted. The milestone remains open with named subtasks.
