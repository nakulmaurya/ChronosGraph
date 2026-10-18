# Delivery and transport hardening — first code checkpoint

Baseline: 668fbb3dac8ebbded9a82bc15a48e08ec3703d4d. Historical receipts remain unchanged.

## Observed regression and repair

The actual plugin factory was exercised with real temporary Git/files and explicitly controlled host/HTTP fault fixtures. These tests are not model runs or native graph substitutes.

Before repair, all three initial regressions failed: a receipt HTTP 503 rejected the first chat; a slow telemetry endpoint delayed an ordinary tool hook by 1204.784815 ms against the declared 250 ms fault-test bound; a second writer was accepted.

After repair, context preparation/freshness remains synchronous; event persistence is local and upload is a bounded background drain. Stable context/part identities are reconciled with the supported pinned SDK `session.message` interface. Local preparation, hook injection, and observed host persistence are distinct; no exactly-once provider-consumption claim is made. Missing/stale mandatory context still refuses the action.

Retryable network/temporary failures back off with jitter. Permanent malformed/conflicting envelopes are retained in quarantine; stale binding requires reconciliation. Local state records pending age, errors, blocked count, saturation, and unobserved count. Linux kernel `flock` enforces one writer per project; abrupt process death releases it. Disposal leaves durable pending events and bounds network waiting.

## Verification

- PASS: 13 local adapter tests, including same-message retry, SDK persistence reconciliation, process restart, stale context, compaction output deduplication, queue recovery, permanent rejection, retention exhaustion, disposal, competing factories, and abrupt cross-process death/recovery.
- PASS: adapter typecheck.
- PASS: 392 native backend tests in a new disposable FalkorDB container, including old/new context-delivery event readability. This count is one run, not historical totals added together.
- NOT YET RUN at this commit: new actual OpenCode outage timing acceptance; multi-sample same-machine VM overhead measurement; completed-step usage verification. Those belong to subsequent checkpoints.

## Migration / recovery

Installer now copies and doctors all implementation modules. Linux `flock` is required. Local state v1 is backed up before v2 migration; old event payloads and queues are preserved. An old `delivered` flag is not treated as proof of message persistence. Doctor reports local transport state; it cannot prove provider consumption or task success.

Never remove immutable receipts to clear a queue. A reconciliation-required stale run should remain archived; select a fresh reviewed pack/run in a new clean worktree. Do not run two plugin instances against the same project state. Existing deployments and pending human approval were not changed.
