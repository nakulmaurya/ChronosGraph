# T-09 command center checkpoint report

Status: **IN_PROGRESS — verified topic-branch checkpoint, not main release**.

## Shipped in this continuation
- Premium monochrome, graph-first repository command center at `/` and `/workbench`.
- Folder/file/function navigation, real dependencies, captured source/docstrings,
  bounded commit links, separate ownership evidence, real agent activity links.
- Opt-in one-click public GitHub import with isolated bounded worker and automatic
  selection of the completed saved version. No manual tenant/hash required.
- Existing diff sandbox, trusted findings, three-track demo and advanced workbench
  retained at documented routes.
- Four sequential persona self-reviews, fixes and stronger responsive verification.

## Evidence
- Backend: **164/164**, latest run 35.55 seconds.
- Frontend: **19/19**; typecheck and production build PASS.
- Browser: **54/54** (15 new, 39 preserved legacy checks).
- Actual separate FastMCP stdio integration: **5/5** calls; zero model calls.
- Live public Click import PASS; cross-origin and unsafe URL refusal PASS.
- 390/768/1560px layouts PASS; final mobile/desktop screenshots inspected visually.
- Accepted Decision ledgers identical before/after; owned disposable graphs removed.
- See `tasks/evidence/t09-command-center/` for compact receipts.

## Review correction worth preserving
An initially passing mobile-node assertion hid a blank React Flow viewport. Visual
inspection caught it, CSS was corrected, and tests now assert actual viewport
height and node intersection. Earlier evidence is retained outside Git. This is
not evidence of independent user testing; four personas were sequential self-reviews.

## Limits and handoff
The working UI indexes Python snapshots, not every language/runtime relation. Public
archive imports intentionally have no historical commits. History file navigation
opens indexed source, not historical source. The job API is local opt-in, not a
production multi-user service. Durable queues/quotas/private auth, incremental sync,
external-agent trial and final release acceptance remain open. No new video made.

See `docs/t09-command-center.md` for routes, tunnel, walkthrough, security boundary,
review matrix and reproducible interface details. Main remains unchanged.

Release hygiene: zero credential-pattern findings, forbidden tracked artifacts, fixture nodes or orphan test/sandbox graphs. This scoped scan is not a security audit.
