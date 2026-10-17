# Testing ChronosGraph user outcomes

A green legacy demo suite is compatibility evidence, not product readiness. Preserve useful safety contracts; do not preserve an exact tool count or UI phrase just because an earlier demo used it.

## Current gates
1. `PYTHON_BIN=/path/to/installed/python CHRONOSGRAPH_SOURCE_CACHE=/path/to/cache bash scripts/verify-quality-batch1.sh`
   Runs the full backend suite in an owned native FalkorDB copy. The source database is read only. Docker and the four installed source graphs are prerequisites, not silently skipped coverage.
2. `cd frontend && npm test && npm run typecheck`
   Unit tests cover data contracts/layout helpers, explicit client config and source comparison, not browser integration by themselves.
3. `PYTHON_BIN=/path/to/installed/python CHRONOSGRAPH_SOURCE_CACHE=/path/to/cache bash scripts/verify-change-planning-ui.sh`
   Creates a disposable DB, a real Git fixture and owned API/UI on loopback 8005/3003. Builds the frontend for that API, runs native browser preview requests and verifies saved source/clone cleanup before stopping its owned processes/container. Refuses occupied ports rather than stopping an unknown app.
4. `npm run test:ui-recovery` / `npm run test:agent-setup` target an explicitly configured running UI. Recovery tests inject read failures; setup tests copy and inspect configuration. Neither is a real IDE integration or hosted-model demo.

## Behavioral oracles introduced in quality batches
- Wrong tenant/commit must not read another version, mutate policy/findings/playbooks, or create a sandbox.
- Two snapshots deliberately share paths but have different bodies/commits: reading the wrong one is a failure even if its JSON schema is valid.
- Real MCP subprocess reconnection must recall source-bound graph evidence without process-local memory or cross-tenant leakage.
- A breaking helper rename must identify the known downstream caller and removed CALLS edge. A surviving IMPORTS edge is not a surviving function call.
- Preview must leave both saved graph source and local fixture source unchanged and remove its clone.
- Source loads refuse corrupted hashes/revisions, absent bodies, missing files and oversized files rather than editing truncated data.
- Failed validation and wrong-version requests must clear stale UI successes. Candidate tests must navigate to real captured files.
- Graphs must preserve actual directed edges and isolated nodes, bound large views deterministically and disclose truncation.
- Import read failures stop polling without declaring server failure or duplicating a mutation.

## Avoid false confidence
Schema checks and synthetic baseline counts remain useful, but they are not the acceptance oracle alone. Prefer externally understandable expected relationships over regenerating expected values with the same production helper. Keep failure logs and failed attempts; fix the product or fixture based on evidence instead of lowering assertions. No mutation-testing score, complete coverage percentage, production-security certification or four-independent-agent approval is claimed.

Still open: actual coding-client task/approval/verification flow, durable import receipt recovery, full accessibility, performance/large-repository acceptance, CI orchestration, and release/deployment hardening. No single command here certifies release readiness.
