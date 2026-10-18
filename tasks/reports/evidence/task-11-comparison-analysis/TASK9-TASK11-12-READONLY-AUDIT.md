# Task9 read-only audit for Task11/12 handoff

Audited at 2026-10-18T14:03:58.739223+00:00.

**Disposition: evidence integrity rechecked; conclusions require the qualifications below. This is a fresh read-only re-audit by the Task9 builder/operator, not an independent-person correctness certification, product-readiness approval, or review of Task11/12 integration/ZIP.**

Commit `4b81658c0c7ca010b69c6467c1c1b621f9deea61`; exact parent `8e83804448cf251a26735d70c5a66f5b0d26db67`. This audit wrote only this new standalone note under `/home/nakulmaurya13579/chronos-work/prerequisites-20261018T121225Z/task9/repository-handoff`. Existing commit, sealed evidence, candidates, receipts and services were not changed; no models/trials/tests/builds or integration actions were run. Git/hash/metadata checks only.

## 1. Supported conclusions and their limits

| Cell | Task / condition | Native outcome | External / selected regressions |
|---|---|---|---|
| 1 | structured-invalid-characters / ordinary | FINAL_RESPONSE | 3 / 991 passed |
| 2 | has-tool-lookup / ordinary | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 / 647 passed |
| 3 | structured-invalid-characters / graph | FINAL_RESPONSE | 3 / 995 passed |
| 4 | has-tool-lookup / graph | PERMISSION_STOP_NO_FINAL_RESPONSE | 2 / 647 passed |

- Exactly four retained one-shot cells in the frozen order. `payload/final-integrity-check.json` records attempts `[1,1,1,1]`, candidate revision/digests and later integrity check; frozen checks and individual verifier results support the bounded runtime-pass conclusion. This does not make four successful end-to-end agent completions.
- Cells 1/3 returned native final responses and passed bounded requirements/unintended-diff review. Cells 2/4 did not return final responses after operator rejected unowned shared temporary typechecker-config writes (`/tmp/opencode/pyrightconfig.json`, `/tmp/pyrightconfig.json`). Native error wording says “user rejected”; provenance identifies the operator. Do not call these provider failures, deadlines, voluntary successful finishes, or clean successes.
- Each lookup candidate has five new test functions missing return annotations. Ordinary/graph added four/two no-cover pragmas. Manual reviews say CHANGES_REQUESTED for conventions and NOT_PASS_UNRESOLVED_DIAGNOSTICS for typechecking. Pyright reported 15 versus 39 errors in differently scoped commands; the latter also checked the test file. Totals cannot be used to rank quality. Missing .venv/import-resolution clues do not prove every diagnostic pre-existing or environmental. Shell pipelines returned exit0 despite diagnostics.
- Selected regressions were `tests/shared` (prepared baseline984) versus `tests/server/mcpserver` (baseline642). Different added test cases explain differing totals, not stronger coverage/quality. No full SDK test suite, downstream compatibility certification, lint-everything result or ready-to-ship candidate is established.
- All four collector PIPE-capture JSON failures remain in `trial-*/frozen-collect-failure.log`; `collector-correction.json` documents regular-file capture with unchanged collector logic. This was collection repair, not a new measured attempt. It does not certify the harness end-to-end.
- Doctor results for graph cells show pending0 and completeness NOT_PROVEN; managed-context parts were recorded at the host, not proof of exact provider consumption. Cell3 had one native graph snapshot-inspection call; cell4 had no native MCP tool call. Static/scope12 and shallow-history limits remain.
- Original AGENT-COMPARISON-01 interruption is still unresolved historical evidence, not retrospectively scored or erased. No trial patches were integrated; no approval/merge/push/deploy is evidenced by this import.

## 2. Usage and wall comparisons — exact scope

The audit independently re-summed the imported completed-step records and checked report rows. It recomputed prompt-to-last-native-message intervals from the recorded timestamps. It did not query a provider or re-execute any candidate.

| Cell | Last-message wall seconds | Input | Output | Reasoning | Cache read |
|---|---:|---:|---:|---:|---:|
| 1 | 420.8 | 22,081 | 2,466 | 1,246 | 220,800 |
| 2 | 462.1 | 32,918 | 3,733 | 2,459 | 409,856 |
| 3 | 323.9 | 33,239 | 3,743 | 1,771 | 275,712 |
| 4 | 585.5 | 99,651 | 6,397 | 786 | 805,120 |

- Graph input is descriptively higher in each matched task pair; elapsed direction is mixed. Do not pool these into an efficiency ranking, infer a graph causal effect or claim speed/token/cost savings. One fixed-order attempt per cell, different stopping states and uncontrolled provider cache prevent that conclusion.
- Preserve input/output/reasoning/cache categories as reported, not as a fabricated additive billable total. Cache-write0 and harness cost0 are observations; free charge0 is not paid-equivalent savings. Retry usage remains UNKNOWN.
- Last-message wall includes operator/tool/provider/network time and is not provider-only latency. For permission-stopped cells it is not successful-answer time; separate terminal-observation and collection clocks remain in `trials.csv`/receipts. Startup is outside the declared prompt-issued900-second budget. Operator-only delay was not independently isolated, so do not subtract invented wait durations.
- Cell1 overlapped Agent1 Task7 free-model and small pytest/export/hash work. All runs used a shared VM/provider; later cells must not be advertised as proven uncontended.
- Native read counts include failed reads and repeated paths/offsets, not total source access, redundant work or token savings. Shell source probes are separately classified. Error-status tools are 0/1/0/2; cell1 additionally has a nonzero shell probe. “No provider message errors observed” is narrower than “no errors”.

## 3. Import integrity, exclusions and disclosure review

PASS on this audit:
- Exact parent/commit, 59 additions only in the two allowed path scopes; worktree clean.
- All53 original manifest entries match committed blobs; all54 extracted payload files including original manifest match original sanitized archive bytes. Archive SHA-256 remains `d10680bf885c3f2e166be261010e25cb854336096122be76745be988001aa156`.
- Historical `tasks/reports/AGENT-COMPARISON-01.md` is byte-identical to the base. Ten actual relative Markdown links in the new wrapper resolve in the committed tree. Results protocol digest matches committed `payload/frozen/protocol.json`.
- Per-cell test counts, completed-step token totals, last-message wall arithmetic, candidate-digest references and tool-error counts agree with the report/receipts. These are record-consistency checks, not independent regeneration from private provider exports.
- No imported private-export/reasoning structures, model-home/config/database dumps, .ssh/.env contents, credentials, dependencies, services, Git metadata, final ZIP, or private archive were found in the added package. The embedded sanitized archive was opened read-only and each of its file bytes compared, not treated as an opaque exempt binary. Targeted credential/key/token/JWT and raw-export/reasoning scans returned no matches. This is not an exhaustive security audit.
- Payload DOES intentionally include public upstream candidate patches, native diagnostic output, session/message/tool IDs, VM username/absolute paths, timestamps, digests and example test URLs. “Sanitized” is not “anonymous”, “contains no paths/identifiers”, or proof that the whole future ZIP is secret-free. Public redistribution should explicitly review acceptable provenance exposure. Do not silently redact sealed originals; make a separately derived redacted package if required.

## 4. Missing/cautionary provenance and package findings

### A. Upstream attribution notice needs final-packaging review
The new evidence contains public Python SDK code context in `payload/trial-*/candidate.patch` and some native diff output. Source URL and exact revision are recorded, but no upstream MIT copyright/permission notice was found in the 59-file import. The inspected pinned SDK LICENSE says “Copyright (c) 2024 Anthropic, PBC”; the application root LICENSE instead names its own2026 copyright holder. Preserve upstream attribution/license notice in a separately authorized Task11/12 notices/readme location if distributing copied substantial portions; review the applicable requirement rather than asserting automatic noncompliance or legal clearance. Do not modify the sealed payload to insert it.

### B. Sanitized evidence is not a self-contained rerunnable benchmark
The import excludes full source worktrees/environments, actual agent homes/config/state, full raw native model exports and private graph snapshots. `analyze.py` expects original `/data/raw/...` private inputs. The included frozen runner has historical defaults API8015/DB6381, not the actual isolated Task6/9 API8016/DB6386. Protocol status PREDECLARED_NOT_EXECUTED is the frozen configuration, not current execution status. The wrapper explicitly warns against executing imported scripts; the README should repeat evidence-only/no rerun. Do not advertise ready-to-run reproduction or let a reviewer launch those defaults.

### C. Some proof is deliberately referenced outside the imported payload
The sealed observed report points to VM `TASK9-COMPLETE.json`, private exports, `sealed-inputs/`, graph dumps, sidecars and second-copy status. Those are private/VM provenance references, not relative repository files or included public artifacts. Candidate digests here are attestations plus patch content; full canonical candidate manifests/files and raw native exports are not imported. Sanitized receipts permit many arithmetic/hash checks but not independent re-derivation of all model identities, source states, startup launch timestamps, raw message-level usage or private backup restoration. Backup hash verification is not a restore test. Link reviewers to included files for public claims and label external proof as retained/private.

### D. Full diff whitespace is not green
The original import verification covers a staged checkpoint before adding its copied diagnostic log. A fresh final committed full-diff check returned exit2 across 10 paths. This includes the nine original hashed log/patch/profile files AND `import-whitespace-check.txt`, whose copied diagnostics themselves preserve whitespace. The new-wrapper/import-JSON/checksum scoped check still passes (exit0). Do not say “all diff checks passed” for the evidence-import commit. This is an evidence-format warning, distinct from the historical trial candidate diff-check passes. Keep original bytes unchanged.

## 5. Suggested concise README wording (for integrator to adapt)

> **Task9: observed pilot, not an efficiency or readiness win.** Four sequential one-shot free-model OpenCode trials were retained. All four frozen runtime check sets passed; only the two invalid-character trials returned native final answers. Both lookup trials were permission-stopped and retain convention/typechecker findings. Graph input was higher in both task pairs and wall timing was mixed; cache, operator waits, shared resources, differing stop states and one attempt per cell prevent causal speed/cost/token-saving claims. See `tasks/reports/TASK-09-OBSERVED-COMPARISON.md` and `tasks/reports/evidence/task-09-observed-comparison/payload/comparison-results.json`. Imported scripts are historical evidence only, not a supported rerun workflow. Earlier incomplete comparison evidence remains unchanged.

## 6. Suggested review-brief wording and evidence map

> Review evidence integrity separately from product readiness. Verify exact Task9 import commit `4b81658c0c7ca010b69c6467c1c1b621f9deea61` against base `8e83804448cf251a26735d70c5a66f5b0d26db67`, original archive checksum, all53 payload manifest entries, and unchanged earlier report. Read both `trial-02/manual-review.json` and `trial-04/manual-review.json` before describing lookup outcomes. Retain all permission, typechecker, convention, collection, usage and timing caveats. Confirm separately that Task11/12 integration and final package preserve these disclosures and exclude private archives/homes/dumps/credentials. Add appropriate upstream attribution notices outside the sealed payload and review retained provenance identifiers before redistribution. This Task9 audit does not accept Task11/12 or authorize merge/deployment.

Exact repository paths (all `trial-*` paths expand under the payload prefix below):
- Wrapper: `tasks/reports/TASK-09-OBSERVED-COMPARISON.md`.
- Evidence prefix: `tasks/reports/evidence/task-09-observed-comparison/`.
- Public records prefix: `tasks/reports/evidence/task-09-observed-comparison/payload/`.
- Hashes: `tasks/reports/evidence/task-09-observed-comparison/source/task9-sanitized-evidence.tar.gz.sha256` and `tasks/reports/evidence/task-09-observed-comparison/payload/SHA256-MANIFEST.json`.
- Configuration: `tasks/reports/evidence/task-09-observed-comparison/payload/frozen/protocol.json`, `frozen/runner.py`, `frozen/accept_has_tool.py`, `frozen/accept_invalid_chars.py`.
- Outcomes/usage: `tasks/reports/evidence/task-09-observed-comparison/payload/comparison-results.json`, `trials.csv`, `trial-01/receipt.json` through `trial-04/receipt.json`.
- Requirement/convention/native outcome review: `tasks/reports/evidence/task-09-observed-comparison/payload/trial-*/manual-review.json`.
- Actual commands/errors/typechecker output: `tasks/reports/evidence/task-09-observed-comparison/payload/trial-*/tool-trace.json` and `native-check-output.json`.
- Runtime checks: `tasks/reports/evidence/task-09-observed-comparison/payload/trial-*/acceptance.log`, `existing-regressions.log`, `diff-check.log`; candidate diffs `candidate.patch`.
- Collection failures/correction: `tasks/reports/evidence/task-09-observed-comparison/payload/trial-*/frozen-collect-failure.log`, `collector-correction.json`.
- Integrity: `tasks/reports/evidence/task-09-observed-comparison/payload/final-integrity-check.json`; graph transport caveats `trial-03/post-trial-doctor.json`, `trial-04/post-trial-doctor.json`.
- Import/check-format evidence: `tasks/reports/evidence/task-09-observed-comparison/import-verification.json`, `import-whitespace-check.txt`.
- Original incomplete record, intentionally unchanged: `tasks/reports/AGENT-COMPARISON-01.md`.
- VM-only handoff metadata/transfer instructions: `/home/nakulmaurya13579/chronos-work/prerequisites-20261018T121225Z/task9/repository-handoff/HANDOFF.json`, `TRANSFER.md`, `SHA256SUMS`. Do not assume these are in the repository import.

## 7. Audit boundary and final actions

No change to the existing commit or sealed receipts is requested. Integrator should preserve caveats, review upstream notices and acceptable provenance exposure, and independently inspect the actual Task11/12 package. This audit did not inspect its contents, run Task10 live UI checks, regenerate a benchmark, restore a database, or approve readiness.
