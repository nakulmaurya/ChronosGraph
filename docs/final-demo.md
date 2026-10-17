# FINAL-01 narrated demo provenance

The release video is a 3:20 screen recording of actual actions in the default
Command Center against an owned native FalkorDB copy. It is not a slideshow of
invented states, a hosted-model agent run, or an IDE integration certification.
The narration is synthetic English speech. Media is distributed separately from
source; its probe/hash receipt is in `tasks/reports/FINAL-01-evidence/media.json`.

## Reproduce the screen recording

From an installed Linux checkout with Docker, Node dependencies, Chromium and a
native FalkorDB seed container containing the four documented demo graphs:

```sh
PYTHON_BIN=/absolute/path/to/backend/environment/bin/python \
FINAL01_DEMO_IMPORT_CLICK=1 \
FINAL01_BROWSER_SCRIPT=record-final-demo.mjs \
EVIDENCE_DIR=/absolute/path/outside/repository/final-demo \
bash scripts/verify-final-lifecycle-ui.sh
```

The optional Click import downloads a real public GitHub archive and requires
network access. No GitHub token or model call is used. The script builds a separate
UI at `127.0.0.1:3003`, API at `127.0.0.1:8005`, and disposable native DB copy; it
must not be pointed at production. Its cleanup owns only those started resources.
The source seed graphs are copied via native DUMP/RESTORE, not mutated.

The browser recorder holds eight 25-second chapters and emits its WebM plus
`recording.json`, screenshots and the actual exported Obsidian ZIP. The hero MCP
client authors synthetic-fixture proposals; browser controls approve the exact
hash and execute real trusted-host pytest in a disposable worktree. A worktree is
not an untrusted-code security sandbox.

## Chapters

1. Repository table, graph, functions and captured source.
2. Catch an incomplete pricing rename and its broken checkout caller.
3. Review the coordinated proposal, rules and owner; approve exact contents.
4. Observe the real candidate pytest exit and durable receipt.
5. Recall source-bound memory and replay five policy steps as three.
6. Generate a measured recovery note, inspect ownership and export the vault.
7. Override the policy and watch prior evidence become stale.
8. Tour real FalkorDB Python, Click and MCP Python SDK saved repositories.

The distributed render pads the recording with an 80px chapter caption, retains
real action timing, and adds synthetic narration (en-US-GuyNeural). Any short
initial page-load lead-in is trimmed using recorder metadata; there are no fabricated
success overlays. Readiness remains NOT READY until the separately documented
provider-backed coding-agent and independent-review gates are completed.
