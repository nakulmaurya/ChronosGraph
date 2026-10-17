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
- Add two semantic-label unit cases and nine desktop/mobile proposal regressions.

## Verification

- 34 frontend unit tests; TypeScript and production build pass.
- 71 browser checks: 50 existing regressions, 12 real native lifecycle, 9 new
  explicitly injected proposal read-failure/refresh checks; zero page errors.
- Backend unchanged from the 295-test verified native base; not represented as a
  fresh full-backend run for this frontend-only change.
- `pip check`: no broken requirements; npm production audit: zero known advisories
  at lookup time. Neither is a security guarantee.
- GitHub Actions run [39038815289](https://github.com/nakulmaurya/ChronosGraph/actions/runs/39038815289) passed for deployed application commit `46d1508`. Later documentation/test-only commit CI is checked separately.
- Read the explicit same-assistant four-persona/critique assessment in
  `tasks/reviews/FINAL-02-persona-critique.md`.

## Model/client gate

Official free DeepSeek catalog ID: `opencode/deepseek-v4.1-flash-free`, not a claim
that a Lite alias exists. The refreshed official CLI minimal request was refused
HTTP 403. A separate free GLM request was also refused before generation. No
independent review model or successful autonomous workflow is invented. Owner-local
OpenCode or another supported authenticated provider remains the path to that gate.

## Deployment

Verified application commit `46d1508` is deployed in a detached release worktree.
Both managed user services are active, linger is enabled, and the web/API bind only
to loopback ports 3004/8004. The previous checkout and an explicit rollback script
are preserved; no database reseed or main merge occurred. Host-worktree execution
remains disabled on this live preview. Browser public GitHub import is enabled.

Seven additional live-preview checks passed across desktop/mobile. The real Click
import POST was accepted, completed in five seconds, and opened its saved map. The
initial smoke test incorrectly waited for an obsolete manual-open button and timed
out; the corrected test recovered the same completed durable receipt and verified
map opening, without submitting a duplicate import. This is recorded separately
from the 71 isolated browser checks. No public repository code was executed.

See `FINAL-02-evidence/deployment.json`, `deployed-checks.json`, and
[preview access](../../docs/preview-access.md). The existing narrated video records
the base release; it is not a fresh recording of these presentation fixes.
