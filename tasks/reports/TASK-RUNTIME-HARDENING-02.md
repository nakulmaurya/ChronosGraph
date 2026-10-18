# Task-runtime hardening 02 — checkpoint handoff, not final release certification

> Historical pre-reboot checkpoint. Later [tasks 3–5 verification](TASKS-03-04-05-2026-10-18.md) supersedes the whole-native blocker and records a new reconstructed pending proposal; it does not restore the old candidate or complete reviewer/browser/comparison work.

Code checkpoint: `ebb747d` on `build/task-context-opencode-integration`, following `d86db9a` (A/B) and `9bf4e0f` (C/D/E/G). No push, merge, deployment replacement or human approval was performed.

## Outcome by requirement

| Area | Implementation | Observed verification and remaining boundary |
|---|---|---|
| A: first-message delivery | Separate preparation/injection/host-part observation; stable part identity; telemetry upload cannot abort a prepared turn. Stale mandatory context still refuses. | Actual factory fault tests and real OpenCode outage/restart/compact acceptance passed. Host message persistence is not provider-consumption acknowledgment. |
| B: transport | Atomic local state, one Linux flock writer, bounded background drain, jittered retries, quarantine, saturation/unobserved indicators, bounded disposal. | Competing writers, restart, HTTP failure, malformed/permanent rejection and retention tests pass. Local hook measurements below; not a VM/provider latency benchmark. |
| C: candidate | Clean relevant source start; exact changed/add/delete UTF-8 files, canonical complete manifest, immediate recapture, omitted/mismatched/binary/symlink/mode/large-file refusal; initial overlay distinct. Runner checks exact materialized tree before/after tests. | Native candidate regressions passed at prior checkpoint. Actual behavioral candidate captured with three files and independent tests below. Plugin observation is not attestation. Existing proposal/runner supports Python files, not arbitrary source languages. |
| D: scope | Exact file/symbol resolution before presentation; explicit bounded dependency scope, mandatory-rule deduplication, discovery/expansion refusal. | Public preparation exposed a real 100-path mandatory-budget overflow. Added explicit `analysis_path_limit` 1–100 (default unchanged). All seeds retained or refusal; truncation declared; outside-scope proposals still refuse. New native narrow-scope regression written, final native execution unconfirmed after VM access loss. |
| E: usage | Completed-step identity and separate input/output/reasoning/cache categories; message cumulative cost reconciliation only; legacy read/retry compatibility. | Real supported export matched persisted totals across multiple turns/restart/compact. Retry usage remains unknown; zero free-model charge is not savings. |
| F: handoffs | Serialized explicit architect/worker/reviewer assignment records; task/plan/pack/run/worktree identity, owner/version/claim version, allowed paths, predecessor, immutable reports. Current claimed worker required for assigned proposal. Late explicit parent links preserved. | Native initial handoff/late-parent tests passed in 401-test working run. Actual architect→worker→architect correction→worker occurred; fresh reviewer initialized but final review NOT COMPLETED. Concurrent claim native test added but latest whole native result unavailable. No worker leases, scheduler or OS write sandbox. |
| G: citations/UI | Current decision/excerpt/source hash validation, complete ADR/incident chain, citation freshness and readable candidate/runtime/handoff UI. | Prior native evidence tests passed; fresh synthetic graph source hashes captured. Final behavioral proposal submission acknowledgment not obtained before SSH outage. Final integrated browser flow NOT RUN. |
| H: public comparison | Frozen public tasks, checks, random order, isolated homes/worktrees and real TUI runner. | Second preparation succeeded after declared scope amendment. First ordinary TUI launched; prompt-start command outcome UNCONFIRMED after access loss. No completed scored trial or improvement claim. See AGENT-COMPARISON-01.md. |
| I: packaging | Local code commit, plugin/frontend checks, pinned production build and handoff material. | Final native gate and pinned integrated browser verification BLOCKED by unavailable VM. This is a review checkpoint, not submission-ready certification. |

## Test receipts — do not add historical counts

- **PASS, current adapter:** 19 tests, typecheck; `evidence/task-runtime-hardening-02/plugin-final.log`.
- **PASS, current frontend:** 37 tests, TypeScript check; `frontend-final.log`.
- **PASS, code ebb747d production frontend:** Next.js production build; `production-build-ebb747d.log`. This is not live UI/API identity verification.
- **PASS, historical native:** 399 tests / 137.26 s for `9bf4e0f`; retained prior receipt.
- **PASS, intermediate working F:** 401 tests / 139.57 s, before the concurrent-claim and narrow-scope tests were added. This does not certify all code in ebb747d.
- **INDETERMINATE, latest native:** disposable native database runner started; only corpus-copy preamble received before SSH became unavailable. Do not infer completion or success.
- **NOT RUN:** final integrated desktop/mobile browser flow at ebb747d. Local production compilation is not a substitute.

## Actual behavioral handoff

Owned synthetic organization, **not a claimed upstream defect**. Task: optional keyword-only `retry_after`; preserve the default timeout envelope, propagate through `worker.should_retry`, reject bool/noninteger/negative inputs, keep bool result. Current ADR-002 and motivating INC-007 remain governing evidence.

- Base revision: `b9c6e297861b6a813a3174f88297c52f290c6602`.
- Task: `task_afeeb47adfa83e0aa3fab1874e67bd47`; distinct actual Git worktrees and isolated OpenCode sessions for architect/worker/reviewer.
- Initial worker candidate: `8cd8353f1a00646b72d6d0916fc2494df06eaaeeb185a217744219fe78081812`; external frozen checks plus repository tests **34 passed**.
- Architect initially said no correction was needed. Operator challenged a missing repository regression for forwarding/negation. Architect withdrew the claim and requested a bounded monkeypatch test. This was **operator-prompted coverage correction**, not discovery of a failed behavioral requirement.
- Worker claim advanced to version 2; only `tests/test_retry_after.py` changed during correction. Actual source bytes in `client.py` and `worker.py` were compared with the first capture and unchanged.
- Final captured candidate: `e6693fb0e9e0089f36601496442e04e0fdfcc8cb7fbb7024796e1f50aca53e31`; files `client.py`, `worker.py`, `tests/test_retry_after.py`. External frozen checks plus repository tests **35 passed in 0.05 s**. Worker independently ran 14 repository tests.
- Frozen external test SHA256: `6198bde4453c8415edd2c313f90766bab76b7f23876891b06fceab170558a92d`.
- Source-backed evidence references prepared for actual ACTIVE decision/document/incident; worker reached the proposal MCP permission screen. A subsequent SSH command intended to allow submission has **unconfirmed execution**. Do not invent a proposal ID or citation validation result.
- Fresh reviewer read the base contract/current policy and waited for final candidate. Final candidate handoff, reviewer assignment, final review, combined integration worktree observation and proposal approval **not completed**.

The complete captures and private exports remain on the VM under the pointer `/tmp/chronos-behavioral-handoff-root`; complete manifests were not downloaded before access loss. The local metadata-only receipt is not a substitute for those files. Do not recreate them from prose or label an operator test as an approved proposal execution.

Human interventions retained: clarify None remains valid despite ambiguous architect bullet; provide the already-installed test interpreter after system Python lacked pytest; an operator chat entry during a permission screen rejected an unnecessary environment probe; challenge missing regression coverage; inspect/allow individual assigned reads/edits/test commands. Wall time here includes long operator waits and is not comparison timing.

## Actual delivery/usage integration acceptance

OpenCode 1.19.3 / `opencode/deepseek-v4.1-flash-free`; owned API interrupted after successful pack response. First context-bearing turn answered ADR-002 correctly; eight pending events survived and drained. Follow-up did not duplicate first-message context. Actual process restart, `/compact`, then post-compaction answer succeeded.

Independent supported export and graph totals matched: input 24,267; output 1,307; reasoning 342; cache-read 27,008; cache-write 0; reported cost 0. First persisted context block 10,944 UTF-8 bytes. Pending 0, blocked 0. Older acceptance API predated the late-idle display fix; historical export status remains BOUND_NOT_COMPLETED, not silently relabelled.

## Hook overhead — bounded fixture measurement, no savings claim

Same local Linux sandbox/process, actual plugin factory and filesystem, controlled HTTP fixture; 20 ordinary pre-tool-hook samples per mode. Declared local-persistence bound 250 ms. Healthy: median 1.664 ms, nearest-rank p95 3.837 ms, max 4.532 ms. Delayed HTTP503: median 0.921 ms, p95 1.196 ms, max 1.392 ms. Fixed healthy-then-outage order, warmup/cache uncontrolled; the smaller outage figure is **not evidence outages improve performance**. Both modes met the bound. These exclude synchronous mandatory-context validation, proposal recapture/validation, model latency and VM timing. Raw samples: `hook-overhead-final.json`.

Before repair, the first three hook regressions failed, including a 1204.78 ms delayed-endpoint hook and accepted competing writer. Those controlled failures are labelled fault fixtures, not agent runs.

## Compatibility, migration and recovery

See `integrations/opencode/README.md` and `docs/task-runtime-hardening-recovery.md`. Local v1 state backs up to v2; old delivered flags are not host persistence proof. Legacy event canonical retry digests remain unchanged; v2 completed-step events are additive. Old proposals keep immutable hashes; new candidate/evidence/assignment bindings require current claims and fresh review. New organizational source pins require a fresh snapshot, never silent enrichment of historical graphs.

No approval endpoint was called in this checkpoint. The previously pending human proposal was left alone; a fresh read-back of its status after the SSH outage is still required. Existing shared preview services were not restarted or replaced. Dedicated test APIs/graphs/containers are separate from shared deployments.

## Remaining release gates

1. Restore SSH; inspect state and the first pilot attempt before sending any new prompt. Do not replay an ambiguous prompt or discard a losing attempt.
2. Retrieve native result/complete candidate, confirm both pending proposals read-only, finish fresh reviewer handoff and exact integration verification.
3. Run the four declared public cells if safe and time permits; otherwise retain an executable runner and explicit incomplete result.
4. Run final whole native suite once against disposable DB, then pinned integrated desktop/mobile flow. Preserve current test receipts as historical if code changes again.
5. Final exact-commit archive and submission packaging only after truthful gate review. Deadline 2026-10-18 18:29 UTC; reserve 16:29 UTC onward for packaging/submission.
