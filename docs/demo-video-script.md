# ChronosGraph — 2:45 screen-recording runbook

One recorded product walkthrough for the hackathon and an optional LinkedIn video.
This is an unpublished draft, not a claim of prize eligibility. Use a desktop
viewport (about 1560×1055), readable zoom and a clean local demo. Never narrate preset
milliseconds: keep actual measurements visible.

## Preflight — outside the recording
1. Run `bash scripts/start-local.sh`; open `http://127.0.0.1:3001`.
   For an already-running trusted database use `--db existing` instead.
2. On **FalkorDB/falkordb-py**, select **Crash-test clone**. Leave **Public snapshot PR**
   on **Choose files manually**, clear default `falkordb/asyncio/graph.py`, select
   only `falkordb/graph.py`.
3. Rehearse **Memory compiler** with exactly
   `Review current policy for falkordb/graph.py`. Do not change it between cold/replay.
   Rehearsals persist investigation records; header counts are not pristine seed counts.
4. Check **FalkorDB/GraphRAG-SDK** → **Time-travel rulebook** offers
   `graphrag_sdk/src/graphrag_sdk/core/connection.py`. Expand **Validity & provenance**
   and inspect the demo label. Return to the first tenant/track for the take.
5. Rehearse scrolling **MCP config** to all five tools. It is a template, not an
   installed IDE connection. Hide unrelated tabs/notifications. No credentials needed.
6. Stop and re-record a failed request after diagnosis. A replay below 1× is valid
   evidence; never edit footage to imply a failed operation succeeded.

## 0:00–0:25 — problem and real data
**Screen:** Show the header on **FalkorDB/falkordb-py**. Briefly open the tenant
selector to reveal both repositories, close it, point to all three track tabs.
Remain on **Crash-test clone**.

**Voiceover:**
“Coding agents need more than a list of matching files. ChronosGraph connects code,
policy history and reusable investigations on FalkorDB. These are two real public
repository snapshots. The policy scenarios are explicitly fictional, and this local
demo makes no model calls. Here are three things the graph lets us verify.”

## 0:25–1:10 — Track 01: audit a disposable clone
**Exact clicks and inputs:**
- 0:25–0:35: Show **Choose files manually**, only `falkordb/graph.py` selected.
  Enter `Assess downstream impact of a graph query change` in **Proposed change**.
- 0:35–0:47: Click **Run GRAPH.COPY audit**. Wait; point to **Cleanup VERIFIED**,
  the actual **GRAPH.COPY** duration and the focused graph.
- 0:47–1:00: Expand **Impacted files** and **Impacted functions**. Click an impacted
  node to show metadata; click **Clear selection**.
- 1:00–1:10: Open **Cypher flight log**, show the bounded traversal, then close it.

**Voiceover:**
“First, copy the graph, audit connected impact, then delete the copy. Imports and
calls expose potential downstream effects beyond a shallow lookup. The proposed
change is context only: this labeled dependency simulation is not executing a code
diff or predicting an outage. The inspector shows source evidence, actual timing
and verified cleanup; the flight log shows the query behind the result.”

## 1:10–2:05 — Track 02: compile and replay procedural memory
**Exact clicks and inputs:**
- 1:10–1:20: Click **Memory compiler**. Enter exactly
  `Review current policy for falkordb/graph.py` in **Policy triage scenario**.
- 1:20–1:37: Click **Run #1 · Cold triage**. Wait; show red dead-end branches and
  the cyan successful path. Expand **Action 1 · Scout** under **Tool handoff log**.
- 1:37–1:53: Without editing scenario or tenant, click **Run #2 · Compiled replay**.
  Show three actions and **40% fewer actions**. Point to actual cold/replay times
  and speedup, whether above or below 1×.
- 1:53–2:05: Briefly open **Cypher flight log**, show `shortestPath`, close it.

**Voiceover:**
“Scout, Historian and Verifier are deterministic graph tools, not hidden language
models. The cold investigation explores five actions, including two dead ends.
FalkorDB shortestPath compiles the successful route into three replayed actions:
40 percent fewer tool executions. Timing is measured, not guaranteed. Zero tokens
means no model was called, not measured token savings. Exact scenario and current
policy fingerprints guard replay; an override makes the old playbook stale.”

## 2:05–2:45 — Track 03: policy, history and MCP
**Exact clicks and inputs:**
- 2:05–2:13: Switch to **FalkorDB/GraphRAG-SDK**, click **Time-travel rulebook**.
  Under **Policy-governed file**, select
  `graphrag_sdk/src/graphrag_sdk/core/connection.py`.
- 2:13–2:26: Keep **Policy question** as
  `What is the current policy for this file, and what did it replace?`.
  Click **Read current policy**. Point to green **ACTIVE**, crossed-out **SUPERSEDED**,
  and expanded **Validity & provenance** temporal fields / `DEMO_POLICY_SCENARIO`.
  Do not record an override in this short take.
- 2:26–2:39: Open **MCP config**, scroll to show all five exposed tools:
  `simulate_pr_blast_radius`, `query_bitemporal_decisions`,
  `record_decision_override`, `run_or_compile_playbook`, `find_true_code_owners`.
  Follow actual modal ordering rather than changing the app.
- 2:39–2:45: Close the modal; end on the active policy and history graph.

**Voiceover:**
“Finally, ask for the current rule without losing what it replaced. This is the
second repository; policy provenance and valid-time versus recorded-time remain
inspectable. The MCP template exposes the same five tools to a local agent—it is
not an installed connection. Connected impact, retained history and verified replay:
all backed by queries, with the demo's limits visible.”

## Optional longer take — outside 2:45
Show a confirmed local **Record policy override**, preserved supersession and
stale-playbook HTTP 409 in a separate rehearsed recording. This mutates the tenant;
use a disposable local database. Reseeding is not a promised undo for overrides.
Do not impersonate a verified GitHub author: the UI labels the demo actor/trust boundary.

## Recording acceptance
- Both tenants, all three tracks, all five tools, cleanup, history and real timing visible.
- No token-savings, outage-proof, definitive-ownership or installed-IDE claims.
- No secrets or cropped failures presented as success. Rehearse to 165 seconds;
  do not invent a result to stay on time. No recording was produced by this task.
