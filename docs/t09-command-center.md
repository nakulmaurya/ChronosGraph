# T-09 developer command center — verified checkpoint

This supersedes the earlier CLI-only browser guide description for the **new** UI.
T-09 remains IN_PROGRESS on `build/t09-repo-workbench-and-trusted-memory`;
main is not merged. No new narrated video or external-model benchmark was made.

## Open the preview

The VM preview runs on loopback **3004 (UI)** and **8004 (API)**. Old 3000/8001
services were stopped at the user's request; older launch instructions are historical.
From a laptop with Google Cloud CLI and project access:

```bash
gcloud compute ssh nakulmaurya13579@instance-falkordb-hackathon \
  --project=amazon-ml-509907 --zone=us-central1-a -- -N \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:3004:127.0.0.1:3004 \
  -L 127.0.0.1:8004:127.0.0.1:8004
```

Keep the terminal open. Browse `http://127.0.0.1:3004/`; API documentation is
`http://127.0.0.1:8004/docs`. No public firewall port is needed.

| Route | Experience |
| --- | --- |
| `/` or `/workbench` | New repository command center |
| `/demo` | Retained three-track demo, wiki and MCP configuration |
| `/workbench/tools` | Retained advanced workbench and CLI import guide |

## Developer walkthrough

1. **Import repository**: paste a public GitHub Python repository, for example
   `https://github.com/pallets/click`. Leave branch at `main` and commit blank for
   the branch head resolved at import. Click import; the browser displays actual
   job status, then selects the completed saved version. No tenant identifier or
   copy/paste terminal command is needed. Failed jobs show a bounded error.
2. **Repository**: select folders to drill into real aggregated import links;
   search `Command`, open `src/click/core.py`, switch to **Functions**, and choose a
   definition to inspect captured source coordinates and docstrings. Pan/zoom
   the graph. Inspect imports and the files that import the selected file.
3. **Changes**: preview final Python source replacements/deletions in an isolated
   `GRAPH.COPY` graph. Review removed/added dependencies, candidate impact and
   cleanup. This does not edit source or establish safe-to-skip tests. The draft
   persists while navigating the map; a rejected request clears a stale result.
4. **History**: inspect genuinely indexed commit-to-file links. Public archive
   imports do not fetch commit history, so their empty history is intentional.
   Opening a changed file shows the selected saved snapshot, not the old commit's
   source and not a historical source diff.
5. **Ownership**: declared CODEOWNERS, Git authors and current local rules remain
   separate. Select a real file and trace its pinned ownership evidence.
6. **Agent activity**: connect an installed coding client through **Connect agent**.
   Actual ChronosGraph MCP tool invocations appear here and link back to files;
   ordinary browser REST reads are not fabricated agent activity. Source-bound
   findings remain agent-reported evidence, with stale hashes/policies flagged.

The automated demonstration creates a disposable two-commit Python repository,
uses a separate real FastMCP stdio client for locate/source/impact/save/recall, and
checks that the browser displays those events. This is **protocol integration**,
not an autonomous Claude/Cursor/OpenCode run, model-quality trial or A/B benchmark.
The test repository and public Click test import are removed after verification.

## Architecture and graph boundaries

New read-only `command_center.py` queries use `db_manager.ro_query` against native
FalkorDB. Real File `IMPORTS`, definition links, resolved `CALLS`, indexed commit
`MODIFIES`, policy and ownership data drive the UI. Folder links aggregate actual
file relationships; no artificial architecture edges are added. Native PageRank
remains the context-search tie-break, and changes use the existing verified clone
service. The FalkorDB engine remains the product core, not a decorative diagram.

Additive REST routes under `/api/v1`:
- `GET /repository/map?tenant_graph=...&prefix=...`
- `GET /repository/file?tenant_graph=...&file_path=...`
- `GET /repository/history?tenant_graph=...&commit=...`
- `GET /imports/capabilities`
- `POST /imports`, JSON `{ "url": "https://github.com/pallets/click", "branch": "main", "commit": "" }`
- `GET /imports/{job_id}`

Map inventory caps at 10,000 Python files / 20,000 import edges, 120 displayed
folder/file groups and 600 displayed aggregate links. File details cap definitions
at 160, each import direction at 80 and touching call links at 160; the canvas
shows at most 60 definitions or 20 files per dependency direction. Coverage notices
identify bounded views. This is not complete all-language repository indexing or
proof of runtime dispatch. Docstrings are bounded AST data, never instructions;
only newly indexed snapshots receive the new docstring fields.

### Opt-in local browser imports

The API must be launched with `CHRONOSGRAPH_ENABLE_BROWSER_IMPORT=1`. This is enabled
only on the isolated preview. The API checks a loopback Host, an exact frontend
Origin (`http://localhost:3004` or `http://127.0.0.1:3004`), and the custom
`X-ChronosGraph-Action: public-import` header. These are cross-origin protections
for a **trusted local single-user** preview, not production authentication or
multitenant authorization. Another frontend port needs an explicit origin-policy
change; the default local launcher does not silently enable this feature.

One active job runs in a separate Python subprocess, without a shell, with a
300-second wall timeout; on timeout its own process group is killed. Receipts
are process-local, capped at 20, and expire after an hour when starting later jobs.
A restart loses receipts: this is not a durable queue. Imports allocate unique
saved graphs and never overwrite existing snapshots. Safe pinned public intake
retains its tree/blob/archive/size checks, credential-free fixed-host URL handling,
no symlinks/submodules and no source execution. No new upstream code was vendored.
A failed/killed import can leave an incomplete INGESTING graph for operator review;
there is no crash-recovery sweeper, total saved-graph quota or private GitHub auth.
Keep the API loopback-only. Do not expose this job API publicly.

## Four sequential self-review passes

These are assistant self-reviews supported by native/browser evidence, **not four
independent people** or universal usability approval. All corrected passes passed
for this bounded Python-snapshot prototype.

| Perspective | Acceptance and corrections |
| --- | --- |
| Vibe coder | Import without tenant/SHA jargon; automatic selection; useful first map; real agent event links. Actual Click import completed. |
| Junior developer | Folder → file → definition → captured source and docstring; incoming/outgoing dependencies named clearly. Search result layout corrected on mobile. |
| Senior developer | Real replacement relationship removal and verified cleanup; preserve draft across map navigation; reject unsafe paths and clear stale impact; avoid misleading query timing. |
| OSS maintainer | Only real commit links; current snapshot vs historical source explicit; CODEOWNERS separate from authors; no invented public archive history; cross-origin imports refused. |

A first browser selector was ambiguous and corrected to the repository combobox.
More importantly, an earlier DOM-node assertion passed while mobile canvas screenshots
were blank. That false-positive evidence was retained, the React Flow container
height/position fixed, and the test strengthened to check the actual viewport is
at least 350px high with visible node intersections at 390/768/1560px. Final mobile
and desktop screenshots were visually inspected, not just accepted from green tests.
The canvas is now monochrome; source text/inspector readability and search layout
were also corrected.

## Verification receipts

Latest serial native run: **164 backend tests**, **19 frontend unit tests**,
typecheck and production build pass; **15 command-center + 24 legacy demo + 10
legacy workbench + 5 CLI guide = 54 browser checks** pass. Five actual separate
stdio MCP calls pass with zero model calls. Browser import tested live on Click.
All five views checked at 390/768/1560px; no browser runtime errors.

Accepted four-tenant Decision ledgers were identical before/after:
`646a5f7cd34ec667d83a63f5cbaeb70d1d712e70c3d21a3087bb8b4cb7097497`.
Only owned temporary graphs were removed; no test/sandbox graphs remained.
Compact evidence: `tasks/evidence/t09-command-center/`.
Raw logs/screenshots and earlier unsuccessful visual attempts remain outside Git
at `~/t09-evidence/command-center/` on the VM.

## Still open before T-09 release

- Actual external coding-agent session and fair comparative evaluation.
- Broader non-Python inventory/language semantics; full historical source diffs.
- Incremental refresh/live workspace monitoring, durable jobs, storage quotas,
  private authorization and hosted multi-user deployment hardening.
- Wider accessibility/usability review, other OS execution and release approval.
- Main merge/deployment only after acceptance; no new video in this task.
