# FINAL-02 — four-persona review and critique-only gate

Date: 2026-10-17. Reviewed base: `2ce07d0`; follow-up UI fixes on
`build/final-hackathon-release`. This is a same-assistant, evidence-backed review
using four role lenses followed by an adversarial second pass. It is **not** four
independent people or a successfully delegated independent model review.

## Method and boundaries

Reviewed the default Command Center, proposal UI, API/MCP boundaries, lifecycle,
trusted execution runner, ownership, policy/memory freshness, dependency manifests,
CI workflow and earlier native evidence. Ran targeted new read-failure tests plus
the full existing browser suite. Backend code is unchanged from the 295-test native
verified base. No claim that merely reading every line or having green tests proves
production readiness. No real first-time user or screen-reader audit was witnessed.

## 1. Vibe coder / builder — can I understand and finish the task?

**Finding:** the proposal screen was an audit dump before an explanation. Refresh
also discarded the selected proposal, and transient notices could describe the
previous selection. A failed captured-source read was not differentiated clearly
from loading while approval remained available.

**Corrections:** concise changed-file / flagged-caller / candidate-test summary;
readable status labels while retaining exact backend state; human-readable current
rules and CODEOWNERS matches, raw evidence behind a second disclosure; exact hashes
remain available. Selection and review reason survive refresh. Notices and execution
acknowledgement are scoped to the selected proposal. Failed comparison blocks
approval and has an explicit retry; missing local execution configuration is explained.

**Evidence:** desktop/mobile proposal regression plus the real approval → observed
pytest → memory → policy-stale browser workflow. **Bounded acceptance: PASS.**
**Residual:** a genuine new user's onboarding success remains unobserved. Public
archive imports cannot run host tests without a separately trusted local checkout.

## 2. Junior developer — can I follow relationships without misleading myself?

**Finding:** an unavailable proposal list could look empty; a failed comparison
could look as though it was still loading. Tool jargon obscured the next action.

**Corrections:** separate initial loading, known empty, failed list, failed source
comparison and action errors. Retained data is explicitly labelled last-loaded;
mutations are disabled during a list read outage. Refresh preserves review context.
Readable labels say candidate tests passed, not that the deployed product is correct.
Owners show file, matching pattern and source line; source-of-truth JSON is retained.

**Evidence:** eight new browser checks across 1560/390px, existing semantic table
keyboard drilldown and prior inventory/history/recovery tests; no horizontal overflow
in checked journeys. **Bounded acceptance: PASS.**
**Residual:** no full WCAG/screen-reader audit; Python static reachability is not
runtime tracing, and inventory visibility is not semantic support for every language.

## 3. Senior developer — do freshness, concurrency and execution claims hold?

**Finding:** a list response begun before a mutation could overwrite the mutation's
newer UI state. Closing/changing context must not imply cancellation of server work.

**Corrections:** pause polling during actions and reject list results from an older
mutation epoch. Reset/abort action state on selected repository/revision change;
deduplicate displayed execution receipts. Keep the server's durable ambiguous-run
marker, exact approval hash and base/policy revalidation as the actual safety guards.
Client cancellation is not described as cancelling server execution.

**Evidence:** real native runner tests at the base; new UI regressions; full lifecycle
rerun with observed pytest and stale-policy checks; typecheck/build. **Bounded
trusted-local acceptance: PASS.**
**Residual:** the API is not multi-user authentication; worktrees are not hostile-code
sandboxes; lease checks are not exactly-once arbitrary OS side effects. The 60s lease
and unknown-attempt recovery limitations remain documented. Do not expose mutations
publicly or enable the runner for untrusted archives.

## 4. Open-source maintainer — can this be reviewed, repeated and maintained?

**Finding:** the initial proposal component was compressed and hard to audit. New
UX fixes needed executable regression coverage, not only screenshots.

**Corrections:** formatted proposal component with separated error/state lifetimes;
typed human-readable status helper with two unit cases; a reproducible proposal
failure-injection browser script with explicit scope. Existing tests stay intact.
Current README points to this follow-up rather than rewriting historical receipts.

**Evidence:** 34 frontend unit tests, 70 browser checks, production build/typecheck;
`pip check` clean; npm production advisory lookup reported zero known advisories
at review time. Parent GitHub CI passed. **Bounded source-review acceptance: PASS.**
**Residual:** new review commit CI and deployment must be checked separately. Shared
async request state could be extracted further. Demo scripts' pytest fixture reuse
is documented technical debt. Package advisory lookup is not a security audit.

## Critique-only second pass — challenge the coding team's conclusions

1. **Reject unconditional READY:** 70 browser checks do not demonstrate an autonomous
   model choosing the change. The stdio hero is scripted and browser approval is
   automated, not a separate witnessed human study.
2. **Reject fictional independent sign-off:** official OpenCode 1.19.3 lists free
   models. The refreshed DeepSeek Flash free request and an alternate official GLM
   free request both received HTTP 403 before generation in this environment. This
   is an access limitation here, not proof that free models do not exist or cannot
   work on the owner's computer. No provider identity restriction was bypassed.
3. **Reject production-security claims:** local origin/header checks express intent,
   not authentication; observed trusted pytest is real but does not isolate malicious
   code. No automatic main merge or arbitrary public test runner is justified.
4. **Accept the bounded fixes:** executable tests demonstrate refresh preservation,
   clearer ownership evidence, source/list failure recovery and guarded approval.
   The existing real lifecycle still passes; there is no mocked mutation success.
5. **Require deployment evidence:** process health, exact runtime revision, loopback
   bindings and rollback path must be recorded after cutover, not inferred from CI.

## Verdict

**PASS for the tested trusted-local preview workflow, with the limitations above.**
**NOT READY for unconditional FINAL-01/hackathon submission sign-off.**

Remaining gates: successful provider-backed coding-client evaluation, independent
critique-only reviewer, owner review/publication/submission and event eligibility
confirmation. Deployment outcome is recorded separately in FINAL-02 evidence.
