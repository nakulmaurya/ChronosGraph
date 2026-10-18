# Task runtime: hardening, explicit handoffs and recovery

This is an unpublished trusted-local checkpoint. Do not replace a shared deployment or approve a proposal as a recovery shortcut.

## Local transport / schema

- Pinned Linux/OpenCode 1.19.3 bridge requires `flock` and Node with supported TypeScript stripping; retain the installed Python virtualenv executable path.
- Installer is create-only. Existing projects must retain their old queue/binding and immutable evidence; use a fresh clean owned worktree for a changed binding or upgraded installation. Do not remove lock/state to bypass a competing writer.
- Local state v1 is backed up before v2. Old `delivered` is not proof of message persistence. Prepared/injected/observed-host-part states are distinct; provider consumption is not acknowledged.
- Telemetry is durably queued before background upload. Temporary failures retry with bounded jitter; malformed/permanent events stay quarantined; stale binding requires reconciliation. Inspect `doctor` local transport pending age/errors/blocked/saturation/unobserved fields. Missing receipts do not mean zero usage or task success.
- Never delete immutable receipts to free retention. Preserve exhausted run and start a new reviewed task/run. No automatic global memory migration or database rewrite.
- Legacy graph event retry digests remain valid. v2 completed-step events are additive; cumulative message cost is reconciliation only. Never add cumulative message costs to step costs.
- New proposal candidate/evidence/assignment bindings do not rewrite historical hashes. Organization SHA pins require a newly ingested snapshot.

## Explicit scope

`POST /api/v1/tasks/{task}/context-packs` accepts `analysis_path_limit` 1–100 (default 100), plus explicit `expansion_paths`. The UI exposes the same limit. Smaller limits narrow the analysis, not just display output, and declare truncation; no comprehensive dependency claim. Every selected seed must fit or the request refuses. Relevant mandatory policies inside scope remain complete; budget overflow refuses. An outside-scope candidate requires a newly expanded pack and fresh run, not a bypass.

## Serialized assignments

`POST /api/v1/tasks/{task}/assignments` takes current scoped plan/pack/run, role ARCHITECT/WORKER/REVIEWER, owner, deliverable, allowed_paths, acceptance and optional returned/closed predecessor ID. It records the actual bound run worktree. `POST /{task}/assignments/{assignment}/transitions` takes owner, expected_version, action and report, optionally candidate_digest/evidence_ids/unresolved.

Transitions: PENDING → CLAIMED → RETURNED; RETURNED → CORRECTION_REQUESTED → CLAIMED (new claim_version) or CLOSED. One active claim per task; competing claims refuse. Different writing workers require distinct owned worktrees. Only a currently claimed WORKER may submit an assigned proposal under the matching assignment/claim version and allowed paths. Plan/source/policy/candidate changes need revalidation and, where applicable, fresh human approval.

These are serialized trusted-client declarations, **not authenticated ownership, durable worker leases, distributed scheduling or OS filesystem restrictions**. Ordinary shell edits outside mediated proposal capture are advisory. Do not run two writers in the same worktree. Actual parent sessions are linked only when the harness reports an explicit parent; separate top-level sessions use explicit assignment predecessor records, not invented parent IDs.

## Current recovery override — tasks 3–5 completed

The VM reboot removed the old `/tmp` roots. Do not follow historical pointer/digest steps below as if those files still exist. The new [tasks 3–5 report](../tasks/reports/TASKS-03-04-05-2026-10-18.md) is authoritative for recovered verification. Persistent VM root is selected by `~/chronos-work/LAST_PREREQUISITES`; its `TASK3_ROOT` points to the new reconstruction, with complete candidate files and receipts also copied off-VM. It is not the old run.

New proposal `prop_64084206f032410a923823abd797e75b` is PROPOSED, candidate digest `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`; worker RETURNED, no approval/execution. Native 403, plugin 19, frontend 37, typechecks and build passed at `8e83804`. Do not launch fresh reviewer, comparison or deployment without the next authorization. The Task 3 API is loopback 8015; its PID/log and owned graph binding are under the persistent Task 3 root. Idle OpenCode is not task success.

## Historical recovery instructions — pre-reboot, not current state

1. Check SSH access; do not reboot shared services as a first step. Pending command outcome is unknown while disconnected.
2. Read `/tmp/chronos-behavioral-handoff-root` and `/tmp/chronos-public-pilot-v2-root`; inspect tmux panes, local state, API receipts and supported OpenCode exports before sending any prompt.
3. If a pilot prompt was started, retain that attempt even if timed out during operator/network interruption. Never replay it as a clean first attempt. The declared 900 s wall budget includes waits; use runner `stop` after deadline, then `collect` and classify interruption explicitly.
4. Copy complete candidate manifests, metadata-only test receipts and proposal status before declaring evidence complete. Raw exports may contain prompts/reasoning; keep them private and outside source archives.
5. Worker final candidate must match `e6693fb0e9e0089f36601496442e04e0fdfcc8cb7fbb7024796e1f50aca53e31`. Read proposal status first; do not resubmit under new keys merely because the old response was lost.
6. Complete fresh reviewer assignment only after worker RETURN; hand off exact captured bytes into reviewer-owned tree. Review against frozen checks/current evidence. Store honest declared review, not approval. Integrator materializes the same digest in a separately owned integration worktree and records independent pre/post-test tree observation.
7. Whole native tests use `run-isolated-regression.sh` in the VM working environment, a new disposable container and read-only corpus copies. Never aim the full suite at shared deployment graphs. The latest started run's exit/result is unconfirmed; inspect before rerunning.
8. Build and verify exact UI/API commit identities, complete desktop/mobile browser flow, then archive a clean exact commit with sanitized receipts. No push/merge or pending proposal approval is implicit.

## Short actual demo script after recovery

1. Show exact API/UI build commit and selected source revision; distinguish application version from indexed code.
2. Open Agent activity; resume task and show immutable plan, explicit scope/truncation and mandatory current decision.
3. Show architect/worker assignment predecessor, role, allowed paths and claim version. Use actual TUI, not replayed text presented as live.
4. Inspect final behavioral diff and corrected forwarding/negation regression; show complete three-file digest and external 35-pass receipt as historical independent observation, not approved execution.
5. Show pending proposal evidence only if server acknowledgment/status is obtained. Explain ADR-002 → INC-007 → worker retry branch, why default remains unchanged and what remains unknown. Do not click approval.
6. Complete fresh reviewer handoff and show its actual returned review. Show pending/blocked telemetry separately from code correctness and task success.
7. If running the pilot, show both ordinary and graph conditions with equal frozen task/checks, and report failures/interventions without claiming token savings.
