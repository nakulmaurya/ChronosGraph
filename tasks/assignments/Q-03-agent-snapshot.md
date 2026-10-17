# Quality batch 03 — explicit agent selection and snapshot safety

- [x] Discover registered saved versions over MCP, with bounded pagination.
- [x] Require explicit tenant and commit for preflight; guard every operation when expected_revision is supplied.
- [x] Preserve legacy operation signatures/defaults without presenting them as safe selection.
- [x] Build data-only client configuration with explicit Python/backend/database settings.
- [x] Copy the selected browser snapshot into a guarded agent handoff; refuse absent identity.
- [x] Exercise a real stdio subprocess across source lookup, diff preview and memory reconnect.
- [x] Test wrong-version rejection on all ten operations without domain writes/clones.
- [x] Retain compatibility gates and add user-outcome tests, not exact tool counts.

Scope: Q07 partial. No IDE installation, real hosted coding-client session, task/approval state machine or authorization added. This is not complete Q08.
