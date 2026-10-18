# Limitations and evaluation

ChronosGraph supports change integrity, review controls, shared context and
traceability. It does not guarantee safe/correct code, exhaustive runtime impact,
security isolation, provider billing accuracy or fully autonomous coordination.

- Python static analysis and graph neighborhoods are bounded. Dynamic imports,
  dispatch and omitted edges remain unresolved, not negative evidence.
- Persistent records depend on durable FalkorDB storage. The convenience local
  launcher is ephemeral; a ZIP is not a copy of historical graph state.
- Worker completion, agent reviewer verdict, tests, human approval and execution
  are separate. Partial transport telemetry cannot establish end-to-end success.
- A source-backed citation establishes a pinned evidence chain, not automatic
  policy applicability, verified ownership, authorization or human approval.
- Prepared examples use explicitly owned synthetic organizational records.
- Local trusted worktrees are not security sandboxes. Do not expose mutation or
  execution endpoints as an unauthenticated public multi-user service.
- No token/cost/speed advantage was established by the observed four-cell pilot.
  Both lookup trials were permission-stopped despite selected runtime checks
  passing; convention/typechecker diagnostics remain unresolved. Timing was mixed,
  graph input higher in both pairs, with provider/shared-resource uncertainty.

## Preserved evidence

- [Observed four-cell comparison](../tasks/reports/TASK-09-OBSERVED-COMPARISON.md)
- [Reconciled comparison analysis](../tasks/reports/TASK-11-COMPARISON-ANALYSIS.md)
- [Historical benchmark and structural audit](../tasks/reports/BENCHMARK-REPORT.md)
- [Earlier incomplete pilot](../tasks/reports/AGENT-COMPARISON-01.md)
- [Fresh bounded same-model reviewer](../tasks/reviews/TASK-07-INDEPENDENT-REVIEW-2026-10-18.md)
- [Scoped prior browser checks](../tasks/reports/TASK-10-READONLY-BROWSER-VERIFICATION.md)

These are dated observations, not freshly rerun full-suite claims. Sanitized
provenance may retain paths/usernames/session IDs; it is not anonymous. Raw private
exports, credentials and graph dumps are not part of the public source package.
