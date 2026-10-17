# FINAL-01 — integrated change lifecycle and three-track Command Center

Branch: `build/final-hackathon-release`. Base: `6048a29820fd5ca57528181d9ffe5ce68fc417e3`.
Date: 2026-10-17. **Overall verdict: NOT READY for unconditional final submission.**
The bounded trusted-local implementation is verified below; a real provider-backed
coding-model evaluation is blocked. Main/live preview were not automatically replaced.

## Deliverables

### 1. Durable lifecycle — implemented and native-tested

- Tenant-graph task/run, immutable ChangeProposal, HumanDecision, ExecutionRecord,
  ChangeVerification and linked TaskFinding records; exact payload/base hashes.
- Same-key replay and different-payload conflict, Redis cross-process mutation lease,
  snapshot/hash/policy revalidation and stale approval invalidation.
- Three required-revision MCP tools, plus REST list/create/decision/report/capability/
  execution endpoints. Surface is 15 total: discovery + preflight + 13 operations.
  Discovery is not snapshot-bound; strict-mode guards the legacy operations.
- Only the explicit trusted local runner mints observed provenance. External reports
  remain unverified, even with exit zero. Real tests execute in a disposable Git
  worktree with bounded output/timeout and finally cleanup; not an OS sandbox.
- Durable started-attempt markers block ambiguous reruns with the same or a new key.
- Memory binds captured base revision/hashes and absent-at-base additions, with
  proposed result hashes kept separately. A new-file-only run can still retain a
  real execution receipt and invalidate memory when those absent files appear.
- Approval is not transferable: changed bodies require a new immutable proposal/key.

### 2. Default Command Center — integrated and browser-tested

- Changes: pending/recent proposals, exact hash/base evidence, captured-source
  comparison, dependency changes, broken callers, candidate pytest command,
  applicable rules/owners, explicit approve/reject and trusted-runner controls.
- Agent activity: real MCP stream, bounded actual import-path selection evidence
  (not private query/source bodies), current/stale source-bound findings, native
  five-to-three deterministic replay and measured recovery note.
- Ownership: declared CODEOWNERS separate from contribution evidence, active and
  crossed-out superseded policy history, inline guarded override, linked-note
  preview and actual Obsidian ZIP download.
- Graph/Table toggle with semantic table/buttons. Table preference now survives
  folder navigation; desktop/mobile real browser keyboard activation is checked.
- Local origin/header checks are explicit operator intent checks, not authentication.

### 3. Hero integration — real tools pass; model-backed gate blocked

Owned local Git payments fixture: pricing → checkout → orders → order test;
synthetic ACTIVE/SUPERSEDED rule and `.github/CODEOWNERS` `@platform-team`.

`scripts/run-hero-lifecycle-demo.py` exercised real FastMCP stdio:
discovery/preflight → context/source → broken rename → coordinated proposal →
explicit fixture CLI preauthorization → actual worktree pytest → new server/client
session recall → live policy override → stale memory/proposal. This is an actual
protocol/subprocess run but **scripted, not a hosted model or installed IDE agent**.

`scripts/verify-final-lifecycle-ui.sh` independently exercised actual browser approval,
observed execution, memory, replay, recovery, vault export and stale invalidation.
No success routes are mocked in this lifecycle harness. The previous recovery suite
retains its explicitly injected read/lost-ack failure cases.

**Real coding-client attempt:** official `opencode-ai` CLI 1.19.3 listed
`opencode/deepseek-v4.1-flash-free`. A narrowly permitted synthetic-fixture MCP
configuration was prepared; no host filesystem/shell editing was authorized.
The provider returned **HTTP 403 FreeTierError before generation**, despite using
the official CLI. No model-created proposal, token count or successful agent run is
claimed. No headers/identity were spoofed and no access restriction was bypassed.
A supported authenticated provider/client run remains required for the stronger
“external coding model completed the workflow” claim.

### 4. License and documentation — implemented

- Root MIT LICENSE, Copyright (c) 2026 Nakul Arvind Maurya, explicitly authorized
  by the owner request; third-party notices retained.
- README now leads with the product workflow, default-UI verification matrix,
  exact 15-tool list/guard exceptions, tested environment and trusted-runner limits.
- Blog draft adds scope-aware resolution, true replacement diff, CODEOWNERS vs
  contribution history, receipts and the proposal/approval/observed-memory loop.
- Platform claims distinguish witnessed Linux/Python 3.13/Docker from macOS and
  Windows WSL2 setup guidance. Historical reports are not silently rewritten.

### 5. Verification, review and media

| Gate | Observed result |
| --- | --- |
| Full backend, owned native copy of four demo graphs | **295 passed, 0 failed, 0 skipped**, 68.62s; 27 new lifecycle/activity cases over the 268-test base |
| Frontend unit | **32 passed, 0 failed, 0 skipped** |
| TypeScript and production build | Passed; production browser harness rebuilds with its owned API URL |
| Existing browser regressions | **50 checks**, zero page errors: change planning 18, recovery 18, agent setup 4, bulk inventory/link/import recovery 10 |
| New real lifecycle browser harness | **12 checks**, zero page errors, desktop 1560/mobile 390, table keyboard activation and actual approval/execution/staleness |
| Real scripted stdio lifecycle | Passed, reconnect/new server and observed pytest, not a model evaluation |
| 5,000-file synthetic navigation, 12 samples/operation | p95 root **107.97 ms**, folder 39.48, exact-path tail search 41.64, symbol search 25.11, inspector 10.66 |
| Import receipts | Existing seven-day Redis retention/crash-recovery implementation retained; durability depends on configured Redis persistence |
| Release hygiene | Staged heuristic scan: no credential-pattern findings, forbidden tracked artifacts, orphan sandbox/test graphs or fixture nodes in four source graphs |
| Narrated media | Completed 3:20 real Command Center recording, H.264/AAC 1560×1080; probe, SHA-256 and audio levels in `FINAL-01-evidence/media.json`. Actual exported vault ZIP validated (17 entries). Synthetic voiceover, not a claim of a human narrator or hosted-model agent |
| Independent critique agent | Not available as a separate successful agent run; persona/critique review explicitly identifies its single-assistant basis |

Native benchmark scope: 5,000 tracked files, 1,000 Python files/functions/imports;
single-client local reads, not import throughput or a production capacity promise.
Earlier run root p95 was 45.62ms; the concurrent final verification run was 107.97ms.
Both are observations, not latency guarantees. No measured model-token savings.

VM evidence directory: `~/t09-evidence/final-01/` (not assumed available to every
reader). Reproducible scripts and a compact evidence index are in this repository.
Use `full-native-additions/backend-full.log`, `lifecycle-ui-release`,
`previous-browser-release`, `hero-stdio.json`, frontend final logs, and hygiene JSON.

## Critique-discovered corrections and failure history

1. Initial fixture SHA check wrongly assumed TrackedFile always had SHA-256;
   inventory stores Git blob hashes in older records. Check available SHA-256
   sources and reject disagreement rather than inventing a missing hash.
2. Coordinated rename initially retained a false broken-caller flag; compare the
   caller's final expressions and keep conservative flags for retained calls.
3. Browser table preference reset on folder load. Lifted the controlled state;
   the first shared-component typecheck then exposed another caller, corrected
   with a compatible controlled/uncontrolled interface. Full production rerun passed.
4. A crash marker originally only blocked the same request key. Now any unresolved
   attempt on that proposal blocks retries after reload/new key too.
5. Final review found new-file-only execution could lose its receipt while creating
   memory. Added absence/revision-bound memory and actual passing subprocess tests
   for additions, then reran all 295 tests.
6. Narration timing/render compatibility issues were corrected in media tooling;
   failed attempts are not described as successful recordings.

## Remaining gates / bounded non-goals

**Blocker:** provider-backed coding-agent/client evaluation did not run successfully.
**Owner actions:** review the video/blog, confirm event-period/new-work eligibility
with organizers, publish/submit required links and use supported model credentials
if choosing another real-agent evaluation. No prize/eligibility guarantee is made.
**Release actions:** review/merge and deploy the new branch deliberately. This work
does not silently replace the currently running VM or main.

Broader authenticated multi-user approval, hostile-code sandboxing, richer language/
type resolution, multi-host load testing and replacement of every legacy route are
not represented as completed. See the critique-only review for persona assessments.
