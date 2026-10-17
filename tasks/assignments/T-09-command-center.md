# T-09 — Developer command center continuation

Status: IN_PROGRESS. Builder + integrator. User-authorized redesign, not a release verdict.

## Product direction
A visual interactive layer between developers and coding agents: understand the
repository, follow real dependencies, inspect definitions, plan changes, review
commit-linked evidence and see actual agent tool activity. Neutral black/white
visuals inspired by the restraint of Next.js, without copying branding or claiming
an affiliation. Keep technical provenance available through progressive disclosure.

## Explicit priority TODOs (user requested)
- [x] **Remove terminal friction:** one-click public GitHub import. Acceptance:
  local UI submits a bounded public-repository job, shows progress/failure, opens
  the completed saved version automatically or with a clear final action, preserves
  existing graphs, and refuses unsafe URLs, oversized content and cross-origin starts.
- [x] **Prove the integration workflow:** polished end-to-end builder/agent demonstration.
  Acceptance: import → explore → locate a real symbol → inspect source → preview
  change impact → actual MCP invocation visible → save/recall source-linked finding.
  Distinguish integration walkthrough from an actual external-model agent trial.
  No new narrated video requested; external-agent trial remains explicitly pending
  until actually run, and no paid calls are authorized.

## Implementation order
1. Read-only folder/repository map with real aggregated IMPORTS links; file and
   function drill-down; bounded inventory and visible coverage.
2. Premium monochrome graph-first workspace; separate changes/history/ownership/
   agent views; legacy demo and tools preserved.
3. Opt-in local browser import worker using the verified pinned public intake.
4. Native API, isolation/security and responsive browser checks.
5. Four explicit sequential self-review passes, corrections and reruns:
   vibe coder, new junior developer, senior developer, open-source maintainer.
   These are self-reviews, not four independent humans or proof of universal usability.
6. Broader inventory/language evidence, refresh ergonomics and external-agent
   evaluation remain separate tracked acceptance items; never invent history,
   runtime dispatch, CODEOWNERS identity or unobserved agent activity.

## Release gate
T-09 remains on its topic branch. No main merge/public production deployment
until full release gates and closure approval. Existing accepted graph policy state
must be restored; native test/browser suites run serially under the verification lock.

## Verified checkpoint
164 backend / 19 frontend / 54 browser checks, typecheck and build pass. Actual
public Click import and separate five-tool stdio MCP integration pass. Four
sequential self-reviews and final mobile/desktop visual inspection completed;
see tasks/reports/T-09-command-center.md and docs/t09-command-center.md.

- [ ] External-model coding-agent trial remains pending.
- [ ] Broader T-09 acceptance and authorized main integration remain pending.
