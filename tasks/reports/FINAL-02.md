# FINAL-02 — persona review fixes and deployment follow-up

Base `2ce07d0`, branch `build/final-hackathon-release`.

## Implemented after the four-persona review

- Preserve proposal selection and review reason during refresh.
- Scope notices, acknowledgement and action state to repository/revision/proposal.
- Pause polling during mutations; ignore earlier-epoch list responses.
- Distinguish loading, empty, cached-on-failure and unavailable source comparison.
- Disable approval when the comparison is unavailable; explicit refresh recovery.
- Readable change summary, status labels and CODEOWNERS/rule presentation; raw
  hashes and JSON remain available under disclosures.
- Explain why an unconfigured public-archive snapshot cannot run host tests.
- Add two semantic-label unit cases and eight desktop/mobile proposal regressions.

## Verification

- 34 frontend unit tests; TypeScript and production build pass.
- 70 browser checks: 50 existing regressions, 12 real native lifecycle, 8 new
  explicitly injected proposal read-failure/refresh checks; zero page errors.
- Backend unchanged from the 295-test verified native base; not represented as a
  fresh full-backend run for this frontend-only change.
- `pip check`: no broken requirements; npm production audit: zero known advisories
  at lookup time. Neither is a security guarantee.
- Parent GitHub Actions run 39036789752 passed. New commit CI is a separate gate.
- Read the explicit same-assistant four-persona/critique assessment in
  `tasks/reviews/FINAL-02-persona-critique.md`.

## Model/client gate

Official free DeepSeek catalog ID: `opencode/deepseek-v4.1-flash-free`, not a claim
that a Lite alias exists. The refreshed official CLI minimal request was refused
HTTP 403. A separate free GLM request was also refused before generation. No
independent review model or successful autonomous workflow is invented. Owner-local
OpenCode or another supported authenticated provider remains the path to that gate.

## Deployment

A reversible loopback-only preview rollout is the next operational step after this
source gate. Record actual service health and runtime commit in a separate receipt.
No main merge, public exposure or hostile-code execution is authorized by this report.
The existing narrated video records the base release; this follow-up changes review
presentation/recovery, not its demonstrated lifecycle semantics.
