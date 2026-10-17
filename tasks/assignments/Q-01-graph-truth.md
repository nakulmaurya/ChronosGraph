# Quality batch 01 — graph truth

Base: 31717cf62ecacc148a2ecec564305729c19b5240.
Branch: fix/quality-batch-01-graph-truth.

Addresses review Q01 (shadowed call false positives) and Q02 (ingestion/simulation resolution drift).

- [x] Collect lexical binding evidence without running source.
- [x] Fail closed for parameters, rebindings and ambiguous source roots.
- [x] Share canonical dependency analysis across both ingestion entry points and simulation.
- [x] Add pure and native no-op parity regressions.
- [x] Run compatibility gates and record results: 202 backend tests pass in a disposable native database.
- [x] Critique the implementation and state unresolved limitations; see batch report.

Next batch: Q03–Q06 UI recovery, accessible import dialog and automated failure tests.
Later batches: developer/agent workflow, history/import lifecycle, scale and release hardening.

Do not reseed/overwrite existing user graphs or call this a full runtime Python resolver.
No main merge or preview replacement as part of this isolated batch.
