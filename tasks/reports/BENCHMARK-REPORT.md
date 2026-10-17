# FINAL-BENCHMARK-01 — real-source workflow evaluation

## Verdict

**Functional regression gate: see the verification receipt. Benchmark acceptance:
NOT MET.** This is an engineering measurement, not an unconditional production,
hackathon, token-cost or safe-test-skipping claim. In particular, end-to-end
context lookup does not universally meet the requested 50 ms p95 target; the
saved GraphRAG-SDK import index has a material coverage gap.

| Repository | Files | Root p95 ms | Locate p95 ms | Neighbors p95 ms | Raw → slice bytes | Byte reduction | Candidate tests / total | Test-file reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FalkorDB/falkordb-py | 42 | 12.35 | 35.48 | 1.51 | 88,300 → 6,871 | 92.22% | 9 / 19 | 52.63% |
| FalkorDB/GraphRAG-SDK | 154 | 11.98 | 184.04 | 0.81 | 251,320 → 14,085 | 94.40% | 28 / 63 | 55.56% |
| FalkorDB/code-graph | 86 | 11.14 | 43.92 | 8.75 | 361,266 → 22,213 | 93.85% | 27 / 29 | 6.90% |
| modelcontextprotocol/python-sdk | 870 | 64.04 | 449.00 | 36.94 | 2,851,684 → 51,587 | 98.19% | 160 / 238 | 32.77% |

Full machine-readable results: [benchmark-results.json](benchmark-results.json).


## Reproduction

Requirements: the tested Linux/Python 3.13 environment, Node/npm, Docker, Git,
Chromium, installed locked backend/frontend dependencies, and all four seeded
source graphs in a dedicated local FalkorDB container. No source download,
repository test execution or hosted model is performed by the benchmark.

```sh
PYTHON_BIN="$PWD/.venv/bin/python" \
EVIDENCE_DIR=/tmp/chronos-workflow-benchmark \
bash scripts/verify-workflow-benchmarks.sh

# Browser gate: each approving/mutating suite gets its own fixture/DB/API/UI.
PYTHON_BIN="$PWD/.venv/bin/python" \
EVIDENCE_DIR=/tmp/chronos-workflow-ui \
bash scripts/verify-benchmark-release-ui.sh
```

The first runner read-only DUMPs the four source graphs and RESTOREs them into a
new native container. Measurement runs before the full test suite so appended test investigation history
cannot contaminate benchmark graph counts. Every repository evaluation also uses a uniquely named
owned graph and verifies its deletion. The native container is stopped in an EXIT
trap on success or failure. Tests/benchmark have separately bounded 900-second
runner timeouts. Set `BENCHMARK_ONLY=1` for measurement without full pytest;
`BENCHMARK_SAMPLES` defaults to 20. Missing required datasets fail, never skip.
The full run is intentionally not pointed at the deployed preview.

Standalone use **only inside an already isolated database**:

```sh
CHRONOSGRAPH_DISPOSABLE_BENCHMARK=1 FALKORDB_PORT=<isolated-port> \
PYTHONPATH=backend .venv/bin/python scripts/benchmark-workflow.py \
  --samples 20 --output tasks/reports/benchmark-results.json --strict-targets
```

`--strict-targets` writes JSON/Markdown measurements, then exits nonzero for a
missed 50 ms, 70% byte-reduction or 100% in-scope indexed-import-recall target.
The default measurement mode records misses without disguising them as correctness
failures. Thus a green functional pytest suite is **not** a green performance or
structural-quality acceptance gate. The 90% compression goal is reported as a
stretch target, not an artificial upper limit on larger measured reduction.

## Methodology and scope

- **Dataset:** four preloaded, captured Python source snapshots, not freshly
  fetched HEADs. Exact revisions, selected path/symbol, node/edge counts and a
  canonical source digest are in `benchmark-results.json`. Older snapshots lacking
  RepoMetadata remain explicitly empty there; per-file captured revisions are
  reported instead. These Python file counts are not whole mixed-language repo
  sizes.
- **Task selection:** highest indexed inbound-call function with a caller still
  resolved by the current conservative source analyzer, excluding test directories;
  qualified-name tie-break. This is one high-connectivity task per repository,
  not random sampling or a representative average of developer tasks. It changed
  after the initial probe accidentally admitted a test helper; initial numbers
  are not presented as final results.
- **Latency:** `perf_counter` wall-clock round trips on one local client, one
  excluded warm-up and 20 measured samples per operation. P95 is nearest rank
  `ceil(.95*N)-1`, not the second-largest value. Root, symbol-search and context
  numbers include complete service work and serialization where the service does
  it; neighborhood expansion is a DB round trip, not a server-internal execution
  profile. Raw samples/max are retained. Shared-VM load/cache effects apply;
  there is no production SLA, multi-client load result or confidence interval.
- **Copy/delete:** three separately measured native GRAPH.COPY operations; node
  count equality is checked, and GRAPH.DELETE timing includes graph-list absence
  verification. The replacement diff also records its own copy latency and
  verified cleanup.
- **Source coordinates:** compare service start/end against independent stdlib
  AST nodes and captured line slicing. Hash-valid source is required. The normal
  symbol reader's 8,000-byte truncation is honored, not mistaken for complete
  source. Returned 1–3 hop import routes are checked edge by edge; bounded result
  coverage is retained rather than claiming every reachable neighbor is returned.
- **Byte folding:** exact UTF-8 bytes of unique, captured, three-hop import/call
  candidate files versus the exact compiled wiki Markdown note. Raw source is
  decoded captured Python text, not binary archive size. The wiki is a focused
  summary with signatures/policy/links—not a semantically equivalent source
  replacement. `chars//4` estimates are reported separately. Exact tokenizer
  counts and billed-token/cost savings are null; no external model is called.
- **Selective tests:** rename one real function while leaving callers unchanged;
  inspect the actual replacement-diff result. Denominator is captured Python
  files matching default `test_*.py` / `*_test.py` names, excluding conftest and
  helper-only files in a tests directory. It is not collected pytest cases and
  does not account for custom collection configuration. Reduction means candidate
  file count versus this denominator, not permission to skip other tests.
- **Precision:** runtime test-impact precision/recall are explicitly **null**.
  Running arbitrary third-party pytest on this host is not a safe oracle. A
  known-answer owned Git fixture independently proves one expected three-hop
  candidate of two test files (50% reduction), import/call replacement, broken
  caller detection and full saved-source preservation. That fixture result is
  not advertised as real-repository runtime precision.
- **Structural audit:** independent stdlib AST resolves unambiguous absolute
  module imports, including nested `src/` roots. Relative-import files, parse
  failures and ambiguous modules are outside the oracle. Precision/recall cover
  only that subset; a zero denominator is N/A, never 100%. CALLS index drift is a
  comparison to the current application resolver, **not** an independent runtime
  call-accuracy score.
- **Ownership:** the four saved snapshots report `NOT_INDEXED_IN_THIS_SNAPSHOT`.
  No owner is fabricated. The owned fixture verifies the exact declared
  `@platform-team` rule. Real-snapshot CODEOWNERS enrichment/absence must be
  checked before claiming complete ownership retrieval across this corpus.

## Findings requiring follow-up

1. **Context lookup latency:** full file/symbol scanning and subsequent
   policy/ownership/memory reads remain expensive on the larger snapshots.
   Profile and improve retrieval, then repeat the identical task manifests. Do
   not substitute the much smaller neighborhood DB latency for full context time.
2. **Legacy GraphRAG-SDK import index:** the independent audit finds 506 expected
   absolute-import edges but zero indexed edges in scope. The harness also audits
   the current source reparse separately, allowing an old snapshot-index gap to be
   distinguished from a current resolver failure. Existing snapshots were not
   silently rewritten to improve the benchmark. Re-import/reindex into a new
   saved version, validate against the same oracle, and deliberately migrate the
   selected UI snapshot if accepted.
3. **CALLS index drift:** saved graphs and current conservative reparse differ.
   Counts/examples are retained, not hidden by choosing only easy assertions.
   Runtime dispatch, decorators, inherited behavior and dynamic calls remain
   outside complete static proof.
4. **Real test precision:** still needs an isolated execution environment,
   dependency-reproducible repositories and a mutation/failure oracle. Until then,
   never present candidate reduction as validated safe skipping.
5. **Breadth:** add more task manifests, cold-cache/multi-client trials and
   independently reviewed ground truth before making general performance claims.

## Recovery and regression hardening

The owned fixture runs cold triage, shortestPath replay and bounded recovery
compilation. SUPERSEDED rule content must not enter ResumeSnapshot. Both a real
policy override and an altered captured file SHA immediately stale the finding;
old playbook replay returns 409. A changed file SHA also makes source retrieval
return 409. These mutations are confined to owned fixtures.

An initial full run exposed an invalid assumption that old indexed calls all
remain resolved by today's analyzer. The harness now reports that drift and
requires a currently resolved caller for the rename workload; it does not weaken
source staleness guards. The initial live smoke also caught an obsolete 10-tool
assertion. It now checks all 15 tool names and the current actionable network-recovery contract. A first aggregate browser attempt
shared an already approved/staled proposal between suites; the final runner
allocates fresh fixtures for independently mutating suites. Failed attempts are
not included as passes.

## Verification receipt

- **333 backend tests passed**, zero failures and skips, in **121.13 seconds** on the final pristine-copy run. This includes 22 new workflow tests.
- **34 frontend unit tests passed**, zero failures/skips; typecheck and production builds passed.
- **118 browser check executions passed** across desktop/mobile, proposal review, the observed lifecycle, recovery, agent setup and change planning. This is **96 checks excluding repeated recovery/setup suite executions**, not 118 new or distinct features. Fault-recovery checks intentionally inject transport errors; successful lifecycle execution uses the real owned backend fixture.
- Isolated hygiene found **zero credential patterns, forbidden tracked artifacts or orphan test/sandbox graphs**. The staged release-tree scan is recorded separately in the evidence directory.
- Machine-readable receipts: [verification.json](FINAL-BENCHMARK-01-evidence/verification.json), [browser-verification.json](FINAL-BENCHMARK-01-evidence/browser-verification.json), and [isolated-hygiene.json](FINAL-BENCHMARK-01-evidence/isolated-hygiene.json).

The measured tree was based on `d678e246747e771efbe7b0cf89319f20dc20de06` with these changes uncommitted. The raw report records exact harness/evaluator SHA-256 hashes to identify the evaluated code. Native database image: `sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a`. Measurements are sequential single-client observations on a shared 4-logical-CPU Linux VM, not a dedicated-host SLA. **The functional gates passed; the benchmark acceptance targets did not all pass.**

CI runs the known-answer workflow subset without downloading external sources.
The full seeded four-repository gate is reproduced with the isolated runner above;
a green CI subset is not represented as the full real-corpus benchmark.

The release branch is the handoff target. No main merge, VM deployment, live graph
reseed, external model call or untrusted repository execution is part of this task.
