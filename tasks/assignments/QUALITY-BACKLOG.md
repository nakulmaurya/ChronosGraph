# Quality backlog — product acceptance remains NO-GO

Review baseline: 31717cf. Batches are isolated/stacked; not merged into main.

## Implemented, bounded verification complete or underway
- Q01/Q02: scope-aware dependency resolution and shared analysis; 202 backend tests passed. Existing saved graphs are preserved, not silently corrected; reimport needed for new analysis.
- Q03–Q05: repository state reset, map retry, lost-receipt recovery; desktop/mobile browser gates.
- Q06: named dialog and keyboard/focus behavior. Full accessibility audit remains open.
- Q24 partial: checked-in disposable native DB verification and UI failure regression command. Not a complete CI release harness.

## Next: one real developer + agent workflow (P1)
- Q07 partial delivered: real stdio discovery/preflight, optional per-call commit guards, selected-snapshot handoff and client config validation. Still validate an actual coding-client session; preflight is not persistent session binding.
- Q08: session/task/evidence/change/human-decision/verification linkage; real coding-client demonstration.
- Q09 bounded first iteration delivered: selected existing Python file → complete captured source → readable source comparison → native before/after import graphs and clickable candidates. Still add persistent drafts, richer function-level evidence and multi-file/add/rename UI.

## Import, repository and history completeness
- Q10/Q11: bounded import history; deleted/non-Python changed paths; historical source scope and commit pagination.
- Q12: full file inventory with explicit language/parse coverage, not a Python graph presented as all code.
- Q13/Q14/Q15: cross-file calls, separate paginated search, navigable limits and measured large-repo graph UX.
- Q16: deep links, browser navigation, distinguishable snapshot versions.
- Q17/Q19: standard launch/import configuration, default branch, commit semantics and durable/reconciled lifecycle.

## Reliability and release gates
- Q18: safe loopback deployment defaults, pinned database image, explicit trusted-local boundary.
- Q20/Q21: index/cleanup error visibility and cross-process mutation semantics.
- Q22: measured FalkorDB plans, query limits/timeouts and polling/resource budgets.
- Q23: extract screen/data components, remove hidden fetches and unify graph primitives.
- Q24 remainder: isolated checked-in full release orchestration, CI, failure tests and real agent acceptance.
- Q25: dependency locks, authoritative setup/docs/skill, owner-chosen LICENSE and maintainer handoff.

No independent agent review has been performed. Four persona reviews and critique-only readiness review must validate completed tasks, not inferred feature completeness. Do not claim percentage completion from the number of checked boxes.
