# POST-REVIEW-EVIDENCE-02 — organizational chains and predecessor memory

Status: **READY_FOR_REVIEW — bounded implementation and local acceptance**.
Predecessor commit: `f2be5f5`; branch: `build/post-review-correctness`.
No main merge, GitHub push, VM deployment or prize result is implied.

## Organizational reasoning

An opt-in committed `.chronosgraph/organization.json` manifest connects:

- Decision → SUPPORTED_BY → exact document excerpt.
- Decision → MOTIVATED_BY → incident excerpt.
- Decision → GOVERNS → captured Python file.
- OrganizationTeam → OWNS → file, only through a matching indexed CODEOWNERS team
  plus explicit team-name mapping. Git contributors are still separate evidence.
- New decision → SUPERSEDED → explicitly retired decision in the same conflict group.

Every excerpt includes full-document SHA-256, pinned revision and exact line range.
The manifest itself is hashed. Sources are regular committed UTF-8 Git blobs, not
uncommitted workspace replacements, symlinks, network fetches or model extraction.
A declared action/rationale remains authored manifest evidence, not independently
established truth. Missing decision/incident evidence, absent team mapping and
multiple active decisions in a declared conflict group are explicit gaps. No
response grants automatic approval. Conflicts outside explicitly declared groups
are NOT semantically detected.

`ask_brain`, declared ownership and saved proposal review expose the same chain.
The existing strict `query_bitemporal_decisions` MCP operation returns it; no extra
MCP tool was needed. Compact context does not embed the detailed chain: an early
2KB-payload regression was caught and corrected by keeping it in detailed views.

The included `examples/organization-case` is clearly labeled **OWNED_SYNTHETIC**:
ADR-002 retains a timeout result envelope because INC-007's fictional retry worker
uses it; a migration plan, contract tests and Compatibility Platform review are
explicit required actions. It is not an upstream bug or a real company incident.
The manifest format is illustrated in that example. Git CLI/local snapshot
refresh imports it automatically when committed; public archive intake does NOT
index organizational manifests in this slice. There are no new external connectors.

## Cross-snapshot memory contract

New findings accept `reuse_scope` through REST and existing MCP recording:

- `UNSPECIFIED` (default): predecessor evidence needs revalidation.
- `FILE_LOCAL`: explicit narrow claim; validate its supporting files and policy content.
- `STATIC_NEIGHBORHOOD`: also capture and compare one-hop IMPORTS/CALLS relationships
  touching supporting files, including endpoint source hashes. This is conservative
  static scope, NOT complete runtime/dynamic/transitive dependency coverage.

`recall_task_memory` and GET `/api/v1/memory/findings` return a separate
`historical_candidates` object. Only the declared immediate predecessor with the
same nonempty connection ID and repository is eligible. No global search/migration,
copy into current findings, transitive predecessor traversal, or hidden adoption.
Read-only validation classifies candidates as `VALID_FOR_THIS_SNAPSHOT`, `STALE`,
or `NEEDS_REVALIDATION`. Originals/provenance remain in the predecessor graph.
A subsequent refresh whose immediate predecessor has no findings will not silently
look farther back; this limit is intentional and explicit.

Across revisions, policy comparisons exclude generated revision-dependent IDs,
but retain rule/status/scope, rationale/action, manifest hashes and supporting
organizational document/incident hashes. Existing snapshot-local staleness guards
remain unchanged. Bounded evidence that overflows its scan is not marked valid.

Old execution/proposal evidence requires new-revision verification. Every historical
candidate says `test_execution_on_new_revision=false`; any saved verification
command is explicitly historical and was NOT run by recall. Validated evidence is
not proof that tests passed or the finding's original conclusion was correct.
Browser-created findings retain the safe unspecified default unless an explicit
scope is supplied by a recording client.

## Executed acceptance

| Check | Result |
| --- | --- |
| Full native backend suite, four pinned repository corpora | **374 passed**, zero failures/skips, 62.73 s |
| New organizational regressions | 11 passed as part of full suite |
| New predecessor-memory regressions | 8 passed as part of full suite |
| Frontend unit tests | **34 passed**, zero failures/skips |
| Typecheck and production build | PASS |
| Existing live API/DB browser smoke | **25 checks passed** |
| New source-chain, memory and saved-proposal browser checks at 1560/390px | **7 checks passed**, no uncaught browser errors |
| Wrong/missing/unsafe organizational source, symlink, invalid range, duplicate ID, invalid supersession | Refused; new failed graph cleaned up |
| Missing document/incident relationship and conflicting active decisions | Explicit gaps; no definitive approval |
| Unrelated documentation commit | Scoped historical finding remains reusable |
| Supporting source changes | STALE |
| Adjacent dependency implementation changes or relationship removal | STALE for recorded static scope |
| Governing policy change | STALE |
| Different connection, same filenames | Reuse refused |
| Legacy/unspecified scope and previous execution/proposal evidence | Needs revalidation; never a new test run |
| Scoped release hygiene | See accompanying receipt; not a security audit |

Receipts are in [post-review-evidence](post-review-evidence/). The earlier
correctness audit/profile are preserved in their original report, not relabeled
as freshly measured full-agent results for this implementation.

## Actual two-session protocol demonstration

`two-session-mcp.json` records real request/response evidence from **two separate
strict stdio MCP server processes**, with `keep_alive=false`:

1. First session locates `timeout_result`, reads captured source, asks for current
   decision/incident/team evidence, and records an explicit static-scope finding.
2. Independently executes the owned example's contract test on that original
   revision, recorded separately from the source-inspection finding.
3. Commits **only `release-notes.md`**; asserts the exact changed-path list.
4. Creates the new immutable snapshot through normal `create_snapshot` refresh.
5. Fresh server session receives only the new tenant and revision, not the prior
   transcript, finding ID, hashes or summary; recalls the validated historical
   candidate. The contract test is NOT relabeled or rerun at the new revision.
6. Creates a pending, unapproved/unexecuted exception-migration proposal so its
   review view can expose the organizational package.

This is a **scripted protocol acceptance**, not an autonomous model investigation,
new OpenCode session result or 18-run agent comparison. The original backend
process is replaced between MCP sessions; the DB process stays running. A durable
VM/backend/database restart acceptance remains NOT RUN.

Reproduce with the configured native DB and project dependencies:

```bash
python -m pytest backend/tests/test_organization_evidence.py backend/tests/test_memory_carryforward.py -v
# Omit --keep-graphs for a standalone protocol check with automatic cleanup.
python scripts/demo-evidence-continuity.py --output /tmp/two-session.json --keep-graphs
(cd frontend && EVIDENCE_RECEIPT=/tmp/two-session.json node tests/organization-memory-smoke.mjs)
# After UI checks, delete only the retained UUID graph names from that receipt.
# demo-cleanup.json records the actual cleanup performed for this delivery.
```

The example runs pytest only against its owned synthetic source, never arbitrary
imported repository code. Native tests and the script do not call a paid model.

## Deployment blocker and next acceptance

The VM host fingerprint matched the previously recorded value, but SSH still
rejected the current key for `nakulmaurya13579` (`Permission denied (publickey)`).
No VM files, containers or graphs were accessed/modified. Confirm key installation
for the correct account before retrying; no security requirement should be disabled.

Next: restore actual SSH authentication, inspect VM worktrees read-only, import
this topic branch without overwriting work, run image/durability parity, rebuild
and independently audit a selected durable snapshot, and show commit/snapshot
revision parity in the preview. Then execute the stronger real-repository agent
tasks and fair 18/12-run comparison with ordinary baseline handoffs. Blog/video/
README submission polishing follows evidence, not new feature breadth.
