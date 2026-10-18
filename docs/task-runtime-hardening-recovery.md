# Task runtime: hardening, explicit handoffs and recovery

This is an unpublished trusted-local checkpoint. Do not replace a shared deployment or approve a proposal as a recovery shortcut.

## Current entry points and safe resumption

Use this runbook with the [current checkpoint status](current-release.md), [Task 7 review](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md), and [current evidence/demo script](task-runtime-checkpoint-demo.md). Earlier published walkthroughs and pre-reboot instructions below are historical, not the current run's identities or results.

The original numbered plan defines **Task 8 as recovery documentation and demo preparation**, not integration. Independent review acceptance does not implicitly authorize integration, approval, execution or deployment.

### Establish what survived before starting anything

On the existing VM, these commands are read-only. Do not paste private keys, provider credentials or raw agent exports into recordings or source archives.

```bash
P=$(cat "$HOME/chronos-work/LAST_PREREQUISITES")
R3=$(cat "$P/TASK3_ROOT")
R7=$(cat "$P/TASK7_ROOT")
test -d "$P/repository" && test -d "$R3" && test -d "$R7"
git -C "$P/repository" rev-parse HEAD
git -C "$R3/worker" status --short
git -C "$R7/reviewer" status --short
tmux list-sessions
curl --fail --silent --show-error http://127.0.0.1:8015/health
curl --fail --silent --show-error http://127.0.0.1:8015/api/v1/release/identity
```

The surviving prerequisite repository stays at application `8e83804`; later documentation/evidence checkpoints are separate refs, not a claim that the API changed. Health is a database connectivity check. Release identity is an environment declaration, not cryptographic attestation or proof of matching frontend deployment. Task 10 still owns final UI/API identity and desktop/mobile checks.

Read the saved metadata without dumping complete private conversations:

```bash
python3 - "$R3" "$R7" <<'PYMETA'
import json, sys
from pathlib import Path
for root in map(Path, sys.argv[1:]):
    receipt = json.loads((root / 'completion-receipt.json').read_text())
    print(root.name, {k: receipt.get(k) for k in (
        'status', 'verdict', 'candidate_digest', 'proposal_id',
        'proposal_status', 'approved_execution_records')})
PYMETA
```

Expected saved state: reconstructed candidate digest `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`; proposal `prop_64084206f032410a923823abd797e75b` PROPOSED; zero execution records; worker and reviewer RETURNED. These receipts are point-in-time observations: re-read server state before a future mutation. Do not re-submit solely because a terminal response is missing.

### Check the existing bridge without creating a session

```bash
PY="$HOME/ChronosGraph-quality-batch1/.venv/bin/python"
"$PY" "$P/repository/scripts/setup-task-opencode.py" doctor \
  --project "$R7/reviewer" --opencode "$P/tools/opencode"
```

`doctor` verifies the pinned binary, installed module bytes, current pack/task and local transport. It makes no model request and does not approve or run a proposal. Current read-only check returned version 1.19.3, zero pending local events and `RECEIPTS_PRESENT_REVIEW_FULL_WORKFLOW_SEPARATELY`. That label is not success certification. Use the immutable review response and test/tool receipts for the bounded result.

If health/doctor fails, retain its error before changing anything. Inspect only the owned API PID/log under Task 3 and the explicit graph/port binding. A stale PID after reboot is not proof that the old process is running. Do not restart/delete shared containers, clear a queue, reinstall into an existing worktree, or replace Agent 2's services as a shortcut. The existing Task 3/7 API is loopback **8015** and its durable database is loopback **6381**; these are this environment's assignments, not universal defaults or ports available for reuse. Reserve heavy reruns and new services until the measured comparison window ends.

### New project setup or changed binding

1. Choose an owned, clean Git worktree at the exact indexed revision; keep each writing agent in a different worktree and HOME. A clean Git start is required; a dirty candidate cannot be made clean by deleting evidence or pretending edits are already indexed.
2. Use an intentionally selected local backend/database and a fresh task/current plan/bounded pack. Keep native tool permissions explicit. The installer generates `ask` defaults; witnessed Task 3/7 sessions allowed scoped read/glob/grep/list/skill and inspected edit/bash requests individually.
3. Follow the [create-only install and doctor commands](../integrations/opencode/README.md#install-into-an-owned-project), using actual returned IDs, the installed virtualenv path and the pinned 1.19.3 binary. Do not substitute the system interpreter or a different client version without validation.
4. Launch actual OpenCode from that worktree only after configuration review. A connected MCP status is not a completed task. If model availability fails, preserve the error; do not silently switch to a paid model or emulate the client.
5. Bind the actual new session/run. Then create and explicitly CLAIM its role assignment; a reviewer follows a RETURNED predecessor. These declarations are serialized coordination, not authenticated identities or filesystem enforcement.
6. Keep source inspection, frozen checks, complete candidate capture, review, human approval and approved execution as distinct steps. Never relabel an old execution as a test on a new revision.

### Migration and failure decisions

| Situation | Safe response | Must not claim/do |
| --- | --- | --- |
| Existing installer targets | Preserve project metadata and choose a reviewed fresh worktree for the upgrade. Installer refuses overwrite. | Delete installed state/config to force success. |
| Local telemetry v1 with unchanged binding | Runtime supports v1/v2; attempts create-only `telemetry-state.v1-backup.json`, retains existing backup if present, then uses v2 fields/defaults. Preserve original artifacts separately before any upgrade. | Treat old `delivered` as provider-consumption proof or assume this documents a fresh migration execution. |
| Binding fingerprint changed | Stop; preserve the old state and explicitly select fresh task/plan/pack/session/worktree bindings. | Reuse a session or rewrite identifiers to bypass mismatch. |
| Plan, policy or source changed | Revalidate current plan/pack, references, candidate and any later approval. New source snapshots retain old provenance as historical. | Inherit approval or carry a test result across revisions as newly executed. |
| Queue failures/quarantine/saturation | Preserve local receipts and error classifications; inspect doctor and immutable server receipts. | Clear queues/locks, infer zero usage, or call idle a successful task. |
| Temporary files lost after reboot | Reconcile durable graph records and verified backups; mark lost bytes unknown. Reconstruct under a new explicit run only if needed. | Recreate an old digest/run from prose or overwrite historical records. |
| Reviewer requests corrections | Return/transition explicit assignments using current expected versions; bounded worker correction, fresh capture and re-review. | Reviewer edits the implementation silently or approves different content. |
| Benchmark in progress | Read/draft locally; keep heavy tests, builds, imports, restarts and duplicate trials out of its measured window. | Blend setup attempts with scored trials or hide interference/waits. |

Private per-graph recovery dumps and agent homes are not portable public source artifacts. A per-key dump is not an atomic cross-graph backup, and restoring it into a different FalkorDB version requires separate compatibility verification. Recovery/restore drills and fresh backend+agent restart tests have not been newly performed by Task 8.

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

New proposal `prop_64084206f032410a923823abd797e75b` is PROPOSED, candidate digest `466f90e5884900baf4c575cbf6c55fb166359002c99a0d28f945f0a07f41c982`; worker RETURNED, no approval/execution. Native 403, plugin 19, frontend 37, typechecks and build passed at `8e83804`. Task 7 was subsequently authorized and completed: fresh reviewer accepted the exact bounded candidate after its own 39-pass run, assignment RETURNED. See the [independent review](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md). Task 9 was assigned to Agent 2 in its isolated comparison setup; this checkout does not own its results. Do not launch duplicate trials, integration, approval or deployment without authorization. The Task 3 API is loopback 8015; its PID/log and owned graph binding are under the persistent Task 3 root. Idle OpenCode is not task success.

## Historical recovery instructions — pre-reboot, not current state

1. Check SSH access; do not reboot shared services as a first step. Pending command outcome is unknown while disconnected.
2. Read `/tmp/chronos-behavioral-handoff-root` and `/tmp/chronos-public-pilot-v2-root`; inspect tmux panes, local state, API receipts and supported OpenCode exports before sending any prompt.
3. If a pilot prompt was started, retain that attempt even if timed out during operator/network interruption. Never replay it as a clean first attempt. The declared 900 s wall budget includes waits; use runner `stop` after deadline, then `collect` and classify interruption explicitly.
4. Copy complete candidate manifests, metadata-only test receipts and proposal status before declaring evidence complete. Raw exports may contain prompts/reasoning; keep them private and outside source archives.
5. Worker final candidate must match `e6693fb0e9e0089f36601496442e04e0fdfcc8cb7fbb7024796e1f50aca53e31`. Read proposal status first; do not resubmit under new keys merely because the old response was lost.
6. Complete fresh reviewer assignment only after worker RETURN; hand off exact captured bytes into reviewer-owned tree. Review against frozen checks/current evidence. Store honest declared review, not approval. Integrator materializes the same digest in a separately owned integration worktree and records independent pre/post-test tree observation.
7. Whole native tests use `run-isolated-regression.sh` in the VM working environment, a new disposable container and read-only corpus copies. Never aim the full suite at shared deployment graphs. The latest started run's exit/result is unconfirmed; inspect before rerunning.
8. Build and verify exact UI/API commit identities, complete desktop/mobile browser flow, then archive a clean exact commit with sanitized receipts. No push/merge or pending proposal approval is implicit.

## Historical pre-reboot demo outline — not the current recording script

1. Show exact API/UI build commit and selected source revision; distinguish application version from indexed code.
2. Open Agent activity; resume task and show immutable plan, explicit scope/truncation and mandatory current decision.
3. Show architect/worker assignment predecessor, role, allowed paths and claim version. Use actual TUI, not replayed text presented as live.
4. Inspect final behavioral diff and corrected forwarding/negation regression; show complete three-file digest and external 35-pass receipt as historical independent observation, not approved execution.
5. Show pending proposal evidence only if server acknowledgment/status is obtained. Explain ADR-002 → INC-007 → worker retry branch, why default remains unchanged and what remains unknown. Do not click approval.
6. Complete fresh reviewer handoff and show its actual returned review. Show pending/blocked telemetry separately from code correctness and task success.
7. If running the pilot, show both ordinary and graph conditions with equal frozen task/checks, and report failures/interventions without claiming token savings.
