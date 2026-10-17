# Quality batch 03 — snapshot-safe agent connection

Stacked on UI recovery 8d821c4; branch fix/quality-batch-03-agent-snapshot.

## Delivered
MCP discovery lists saved repository versions with commit hashes and cursor pagination. Explicit preflight confirms tenant/commit. All ten existing operation tools accept optional expected_revision, checked before the operation under the existing process-local reentrant lock. Legacy callers remain compatible; unguarded legacy defaults remain possible and are documented. Discovery/preflight are read-only and do not install a connection or establish automatic future-call binding.

The client modal now takes an explicit Python executable, backend cwd, database host/port and copies a data-only configuration. The command center passes its selected snapshot into a separate copyable agent handoff, refusing absent/invalid identity. The skill tells clients to discover, confirm, and pass tenant plus revision on every call.

## Verification
- Full native backend suite in disposable FalkorDB: **225 passed in 47.49s** (23 new cases).
- New stdio acceptance launches actual server processes, selects one of two same-path/different-commit repositories, reads exact source/hash, previews a helper rename, verifies caller/edge impacts and unchanged saved source, saves agent-reported evidence, reconnects a fresh process and recalls it without leaking to the other tenant.
- Parameterized rejection covers all ten operation tools with a wrong commit and checks no source/policy/finding/playbook mutation or leftover clone. Invalid commits, unknown tenants, incomplete graphs, unknown legacy revisions and pagination are also covered.
- Frontend: **27 unit tests passed**, typecheck and production build passed.
- Setup browser checks: **4 passed**, two repositories each at desktop/mobile widths; copied JSON config and exact tenant/commit handoff, invalid port refusal, Escape/focus restoration. No mutation POST requests or page errors.
- Existing UI recovery regression command rerun separately (see recovery.log).
- Initial run found an extension-brittle exact-tool-set test and a two-commit fixture using the cached original revision. Replaced count/set equality with required-capability contracts and explicitly pinned the second fixture commit; neither required dropping outcome assertions.

## Critique and limits
Vibe coder: selection now has a copyable next action, but does not connect their IDE for them. Junior: executable/database placement and saved-vs-live semantics are explicit. Senior: wrong-version mutations are blocked when the guard is supplied, but this is not authentication, cross-process locking or policy approval. Maintainer: old tools remain compatible; no existing graphs were migrated. Readiness: full product acceptance remains NO-GO; real coding-client work, approval loop and complete workflow demonstration remain open. This was sequential self-review, not independent agents.

No main merge, no preview replacement, no hosted model calls and no video.
