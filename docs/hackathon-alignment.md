# ChronosGraph — FalkorDB Graph Hacks alignment

Authoritative challenge page reviewed for this implementation slice:
https://www.wemakedevs.org/hackathons/falkordb#challenge

This is an engineering alignment checklist, not official organizer approval,
judging scores, registration, submission, prize eligibility or acceptance.

## Product pitch and primary track

**A coding-agent context companion that follows code dependencies, previews
replacement impact in a disposable graph, remembers source-bound findings and
traces current rules and declared owners to their source.**

Primary target: **Agents That Act on Connected Data**. Supporting capabilities
also map to **Agent Memory and Coordination** and **Company Brain**. Our UI's
three feature tracks are product workflows; they are not proof of eligibility
for any official prize category.

The official brief requires FalkorDB as the primary graph database supporting a
central part of the product. The graph must shape what the agent does, rather
than simply sit beside the application. Maintain these invariants:

| Challenge focus | ChronosGraph implementation / evidence |
| --- | --- |
| Follow connections and act | Native IMPORTS/CALLS traversals, GRAPH.COPY replacement before/after impact, proposed candidate tests; no automatic test execution |
| Algorithms as tools through MCP | Native PageRank context entry points; shortestPath verified playbook selection; actual FastMCP protocol tests |
| Remember across sessions | Persisted Finding nodes bound to source hashes and policy state; stale evidence filtered/flagged |
| Share agent state | FalkorDB-backed MCP event/finding storage visible across processes; no distributed-concurrency guarantee |
| Connect people, projects and decisions | Git contributors separated from declared CODEOWNERS; current/superseded governing decisions |
| Show the path behind an answer | Pinned file/symbol coordinates; OwnershipSource → OwnershipRule → File/DeclaredOwner graph paths with pattern, line, commit and hash |

## Selected upstream integration: CODEOWNERS evidence

Reuse only the pinned MIT parser from `sbdchd/codeowners`; preserve both upstream
copyright notices and license. See `THIRD_PARTY_NOTICES.md`.

A trusted CLI Git ingestion now reads the committed CODEOWNERS blob, applies
bounded supported GitHub-style rules, and writes ownership relationships into
FalkorDB. `/context/owners` and MCP `locate_context` read those graph paths.
The workbench can trace declared owner evidence separately from Git authors.

This makes ownership a graph-derived review-routing input for a coding agent.
It does not send a review request, verify a user's/team's GitHub permission,
execute code, or fabricate an autonomous-agent decision. The retrieval uses
GRAPH.RO_QUERY; it does not quietly consult a different in-memory graph backend.

First-existing source precedence: `.github/CODEOWNERS`, root `CODEOWNERS`, then
`docs/CODEOWNERS`. Last matching supported rule wins, including empty-owner
clearing rules. Unsupported patterns/invalid owner syntax are diagnosed/skipped.
The wrapper is a bounded subset, not guaranteed full GitHub parser parity.

Old accepted graph snapshots are **not** automatically rewritten. They return
`NOT_INDEXED_IN_THIS_SNAPSHOT`; a new CLI-ingested tenant reports indexed,
absent, partial or unsupported source status. Working-tree freshness remains
unchecked. No public importer, GitHub login or destructive backfill is added. A later local
workspace slice adds allowlisted CLI connections and explicit new-snapshot refresh
without changing accepted tenants; see `t09-local-workspaces.md`.

## Judge-facing demonstration priorities

Keep the story focused on one useful task, not a collection of upstream brands:

1. Ask the connected MCP client to investigate a targeted source change.
2. Show which graph relationships select source, callers, owners and rules.
3. Preview actual replacement impact with cleanup evidence; show missing/static
   coverage and candidate tests without claiming they are safe to skip.
4. Record a source-bound finding, resume in another session, then change the
   indexed source/policy and demonstrate that stale evidence is flagged.
5. Trace a recommendation back to its pinned source and show actual tool events.

Actual external-agent end-to-end demonstration and same-agent A/B tasks remain
**NOT RUN**. Native protocol/browser tests do not replace that submission gate.
No paid model credentials or new video are required/used by this slice.

## Submission / eligibility checks still required

The reviewed page states:
- Event dates: October 15–18, 2026; online; solo or teams up to four.
- General libraries/templates/infrastructure may be reused, but the submission
  and main FalkorDB implementation must be new work completed during the event.
- Coding assistants are allowed; the participant remains responsible for the
  code, architecture, security and correctness, and must be able to explain it.
- A live deployment is preferred. Undeployed projects need complete local setup
  instructions and a working demo video.

Verify the live event rules/deadline and preserve an honest commit timeline.
Because this repository contains earlier work, request organizer clarification
if necessary. Never backdate commits or label old core work newly built.
The owner must complete registration/team/submission and any required demo
assets. We have not registered or submitted on their behalf.

Do not add another database, full agent framework or broad arbitrary-code runner
just to claim integration. Prioritize safe import/freshness and a traceable real
agent workflow, then UI polish. T-09 remains IN_PROGRESS; main/production are
not authorized for merge/deploy by this alignment document.
