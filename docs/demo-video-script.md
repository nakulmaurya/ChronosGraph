# ChronosGraph T-08 — 2:45 second-brain demo runbook

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

Record the actual local product, not a slide/mock response. Four indexed repository
snapshots, truthful provenance badges and zero product model calls remain visible.
Counts grow with recorded investigations. Never narrate fixed node counts, test-skip
safety, context savings or speedup: use the successful take's measurements.

## Preflight and capture
- Run the full regression, frontend build/live smoke and release hygiene first.
- Use a disposable trusted local database and a matching backend/frontend checkout.
  Do not run ingestion, smoke or another policy writer during capture.
- `scripts/record-second-brain-demo.cjs` uses the frontend Playwright dependency and
  `/usr/bin/chromium`; configure `CHRONOSGRAPH_REPO`, `BACKEND_PYTHON`,
  `FRONTEND_URL`, `TEST_API_URL` and `CHRONOSGRAPH_RECORDING_DIR` for your machine.
  Defaults are the isolated T-08 ports 3003/8003 and the repository `.venv`.
- It records a continuous 1760×990 browser take, real response measurements,
  chapter PNGs and a policy-restoration receipt. A presentation-only cursor ring
  makes actual clicks visible; application data and controls are not fabricated.
- Stop on a failed request or timeline overrun. Restore captured original Decision
  properties and remove only the override IDs created by this take, even on failure.
  Never broadly reseed/delete unrelated records. Recording is single-writer local
  tooling, not a production transaction/undo mechanism.

## 0:00–0:25 — connected context instead of context flooding
Cycle FalkorDB/falkordb-py, GraphRAG-SDK, code-graph and MCP Python SDK. Point to
CONTRACT V1.4 and the measured source-byte HUD. Explain the connected second brain
and `/compact` recovery problem. The whole indexed repo vs focused lossy excerpt
comparison is deliberately different from affected-file audit and cold-candidate
measurements. It is not proof of equivalent information or billed token savings.

## 0:25–1:05 — GRAPH.COPY, AST impact and candidate tests
Select `falkordb/graph.py`. Enable the real AST snippet overlay with:

```python
from falkordb.query_result import QueryResult

def context_audit_patch(response):
    return QueryResult(response)
```

Run the clone-only audit. Show the top-right comparison, measured compact audit
subset, copyable candidate pytest command, actual impacted counts and verified
cleanup. Scroll to real commit-linked reviewers. Switch to MCP Python SDK and
audit `src/mcp/shared/dispatcher.py`. The patch is parsed, not executed; bounded
static reachability is advisory and full-suite CI remains the safety gate.

## 1:05–1:45 — shortestPath and compaction recovery
On falkordb-py run the exact same policy scenario cold and replayed. Show five
cold actions/two dead ends, then three retained actions/no replayed dead ends.
The two pruned branches remain dimmed, not erased. Open the wiki drawer:
ResumeSnapshot shows the target, ranked connected symbols, ACTIVE rule excerpts,
current verified steps and commit evidence; log.md shows real source events.
Narrate the 40% action reduction; leave actual timing and context ratios visible.

## 1:45–2:20 — live override and authoritative stale-memory refusal
Read the current `falkordb/graph.py` policy. Submit a confirmed, explicitly local
architect override. Show the old rule become SUPERSEDED. Return to Track 2:
normal replay is disabled; **Check backend replay guard** sends a genuine replay
request and surfaces the actual HTTP 409. No DOM-enabling trick or fake response.
Restore the saved policies before continuing. Existing stale playbooks stay
historical; only a matching current fingerprint may enter recovery context.

## 2:20–2:45 — Obsidian vault and portable agent workflow
Open index.md and follow an actual generated `[[wikilink]]` into an entity note
with YAML frontmatter/backlinks. Click Export Obsidian Vault: the server writes a
managed local immutable generation and the browser downloads the ZIP. Show MCP
config's Cursor and Antigravity/OpenCode tabs and the repository portable-skill
path. These are templates/guidance, not automatically installed IDE connections.

## Narration and output acceptance
Use an energetic developer-first voice; keep provenance and measurement caveats
in the UI rather than repeating negative disclaimers aloud. Cover all five native
MCP tools without claiming an IDE installation. A separate public neural TTS voice
may render the narration; that media-generation step is not a product LLM call.
Trim only the preflight lead-in, preserve actual continuous demo timing, pad a
caption band without cropping the product, and mux a 165-second H.264/AAC MP4.
Inspect each chapter, sampled final frames, clipping/loudness and speech timing.
Archive the real recording receipt and final hash with the handover evidence.
No public video upload or hackathon submission is implied by repository merge.
