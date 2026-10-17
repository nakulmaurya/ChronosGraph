# Quality batch 01 — graph correctness checkpoint

Base: `31717cf62ecacc148a2ecec564305729c19b5240`.
Branch: `fix/quality-batch-01-graph-truth`.

## Implemented
- Lexical binding evidence for parameters, assignments, imports, nested function scopes, class scopes, exception aliases and pattern captures.
- Fail closed for rebindings, global/nonlocal declarations, dynamic lambda/comprehension scopes and conflicting source roots.
- Closest lexical binding wins; methods do not implicitly close over class namespaces.
- Conservative receiver handling rejects reassigned receivers/methods and staticmethod parameters named self.
- One canonical dependency analyzer is used by trusted/local ingestion, seeded ingestion and replacement simulation.
- Existing seed graphs are read-only on ordinary reseeding. An analyzer update must not append new edges into a saved old snapshot. Explicit destructive reset remains explicit; prefer importing a new tenant instead.
- Added pure resolution regressions, native initial-graph/canonical-source parity, no-op replacement parity and existing-seed read-only tests.
- Added checked-in `scripts/verify-quality-batch1.sh`: copy the four source graphs with Redis DUMP/RESTORE into a disposable native Docker instance, run compatibility tests there and remove only the owned container on exit. It uses the exact locally installed image ID, not a new pull.

## Verification
- Pure parser/dependency plus replacement subset: **61 passed**, repeated three times.
- Final full backend suite: **202 passed in 31.64 seconds**; prior suite had 164 tests, 38 new regressions added.
- Full suite ran against an isolated native FalkorDB copy, not the preview database. The disposable container was stopped afterward.
- First targeted run had one opaque 503 from a native multi-file replacement test. A diagnostic rerun, three repeated subset runs and the final full suite passed. Root cause was not established; preserve this as an unresolved intermittent observation, not a fixed defect claim.
- An intermediate full run caught two old-snapshot reseeding count changes; the read-only snapshot preservation fix was added before the final passing full run.

## Critique / boundaries
This closes the two reproduced resolver cases for newly analyzed source, not complete Python runtime dispatch. Dynamic dispatch, decorators, rebinding and uncertain expressions intentionally lose edges rather than invent certainty. Source syntax is not a guarantee of runtime behavior. Cross-module runtime rebinding, monkey-patching and execution order are outside this static contract.

No existing user graph was migrated/rebuilt. Legacy graphs retain old analyzer output and require explicit new-snapshot ingestion for corrected relationships. New data parity is covered by disposable fixtures; the complete upstream repositories were not re-ingested with the corrected analyzer in this batch.

No UI source changes in this checkpoint, no main merge, no preview restart, no claim of product readiness. Review roles were sequential self-review, not independent agents. Q03–Q25 remain pending except for the bounded verification-isolation improvement above.
