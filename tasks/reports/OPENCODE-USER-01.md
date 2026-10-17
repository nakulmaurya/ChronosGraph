# OPENCODE-USER-01 — actual OpenCode integration and user acceptance

Branch: `build/final-hackathon-release`; base `87b2f4f`. Owned synthetic Python Git
fixture only; live preview/source graphs were not mutated by agent calls or tests.

## What changed

1. Corrected the diagnostic setup: official Build agent with `bash: ask` instead of
   denying all tools. The free DeepSeek model generated successfully. No custom
   provider endpoint, client-identity headers, access bypass or paid fallback.
2. Added `scripts/configure-opencode.py`: local stdio MCP configuration with strict
   snapshot guards, explicit permission prompts, no runner enablement, no keys and
   sharing disabled. Atomic owner-only publication refuses overwrite and cleans
   interrupted writes. `.gitignore` excludes the default machine-local config name.
3. Real model use exposed missing module/import retrieval. Existing
   `get_symbol_source` now supports explicit `__module__` captured-file reads,
   hash-checked and bounded to 8,000 UTF-8 bytes; missing symbols explain recovery.
   The MCP surface remains 15 tools. No live filesystem read is introduced.
4. Added configuration and source-read boundary regressions plus a real-model
   browser lifecycle test with an explicit fresh-session recall checkpoint.
5. Clarified that history-derived contributors/pr_count are not verified PR review
   authority. No claim that an agent's narration is a trusted execution receipt.

## Two launch paths tested in parallel

| Path | Observed outcome |
| --- | --- |
| Official interactive TUI, Build / DeepSeek Flash free | Minimal answer succeeded; real MCP proposal-authoring task completed |
| Official server + `run --attach` | Model answers persisted, but some CLI stream/exit waits timed out; not a passing command-exit check |
| Fresh official server HTTP API sessions | Returned real MCP context/current-memory/stale-memory answers normally |

The initial deny-all 403 was a configuration-specific failure. An upstream report
identified `bash: deny` vs `ask` as a reproduction; our normal-permission retest
recovered generation. It was incorrect to treat the earlier result as proof that
free models cannot run from this environment. Underlying provider classification
internals are not claimed proven.

Headless permission `ask` auto-rejected an unconfigured read tool during the first
attempt. Explicitly allowing only reviewed read calls corrected it. Arbitrary shell
commands and change execution were not auto-approved. The model's first source
attempt also guessed several nonexistent module-symbol names; those errors drove
the actual source-tool improvement and are disclosed rather than omitted.

## Witnessed real-model lifecycle

- Actual provider model chose tool calls and read complete captured pricing/checkout
  source, rather than receiving scripted replacement bodies.
- Deliberately incomplete proposal: broken caller `services/checkout.py:checkout`.
- Coordinated proposal: both files replaced; zero resolved broken callers flagged;
  candidate command `pytest -- tests/test_orders.py`; stopped at `PROPOSED`.
- Automated browser operator approved the exact proposal hash, acknowledged trusted
  fixture execution, and observed candidate pytest exit 0 / 1 passed in a disposable
  worktree. The model could not approve itself and did not report a fabricated run.
- New model session: `EXECUTED_VERIFIED`, `LOCAL_WORKTREE_OBSERVED`, finding
  `CURRENT_AT_INDEXED_SNAPSHOT`; distinguished CODEOWNERS from unverified Git authors.
- Browser operator replaced the fixture policy. Another fresh model session recalled
  `STALE` / `GOVERNING_POLICY_CHANGED`; proposal was `STALE_POLICY`.
- Saved base source remained unchanged, including after the observed test run.

The successful corrected authoring session made **11 completed MCP tool calls,
zero tool errors**; current and stale verification sessions made five each. Those
are MCP call counts, not LLM inference-call counts. The external model is real;
backend fields saying `model_calls: 0` describe deterministic backend operations,
not a claim that this external agent workflow consumed no inference.

## Verification

- **311 backend tests passed**, zero failures/skips, against a disposable native DB copy.
- **34 frontend unit tests passed**; typecheck and production build passed.
- Synthetic 5,000-file root-map p95: **47.34 ms** (12 samples; not a production SLA).
- Release hygiene is recorded separately in the evidence directory.

Twelve desktop/mobile UI lifecycle checks passed against the actual model-authored
proposal, with zero page errors, including exact approval, owned pytest, recovery
note, shortestPath replay, ZIP export and stale invalidation. They are a rerun with
new authorship provenance, not 12 newly distinct features added to prior totals.
The previous 71 isolated checks and seven deployed-preview checks remain historical
receipts and are not falsely represented as all freshly repeated in this run.

## Persona and critique follow-up

- **Builder:** model could finish a coordinated proposal and stop for approval;
  module-read friction was found in real use and fixed.
- **Junior:** source coordinates, owners, candidate tests and current/stale evidence
  were visible; no first-time human onboarding or screen-reader study was conducted.
- **Senior:** exact-hash browser approval, observed runner provenance and fresh-session
  stale enforcement held. Public hostile-code execution remains disabled.
- **Maintainer:** reusable setup, create-only config, boundary regressions and raw
  evidence summaries are supplied; attached CLI exit remains an upstream issue.
- **Separate critique-only model:** conditional trusted-local pass, no confirmed
  blocker in the selected snippets; requested boundary/config tests were added.
  See [review and disposition](../reviews/OPENCODE-USER-01-critique.md). This is a
  separate model session, not an independent human/full-repository security audit.

**Narration caveat:** the stale-session model imprecisely called the historical
browser decision “not an approval,” although approval had occurred and its hash
remains recorded. Correct interpretation: past approval exists; current policy
staleness prevents reuse. Its wording about Git review history was also broader
than unverified commit evidence warrants. The graph records/guards, not prose, are
source of truth. Raw final answers are retained with this caveat in the evidence.

## Outcome and remaining steps

**PASS for this bounded model → MCP → browser approval → observed owned tests →
fresh-session memory → stale-policy workflow.** Not blanket production readiness.
Owner acceptance, publication/submission/eligibility checks and any independent
human/full-repo review remain. The old narrated demo is not magically re-recorded.
The new source integration is pushed separately; the live preview remains verified
application `46d1508` unless a later deployment receipt explicitly replaces it.
No main merge, live DB reseed or public runner enablement occurred.
