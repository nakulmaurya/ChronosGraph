# Full developer walkthrough — 23 minutes, 21 chapters

[Watch/download the MP4](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-final/ChronosGraph-full-developer-walkthrough.mp4) ·
[Guide and transcript PDF](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-final/ChronosGraph-walkthrough-guide-and-transcript.pdf) ·
[Captions SRT](https://github.com/nakulmaurya/ChronosGraph/releases/download/hackathon-final/ChronosGraph-full-walkthrough.srt)

[Release assets](https://github.com/nakulmaurya/ChronosGraph/releases/tag/hackathon-final)
are stored outside Git source history. The recording uses application baseline
`479e987`: real isolated UI actions and a scripted MCP stdio author, synthetic
narration, explanatory cards, paced actions and held screens. It demonstrates an
observed trusted-fixture pytest pass and policy stale invalidation; it is not a
live autonomous-model demo, deployment or general production-readiness claim.
The original saved source and existing preview were not changed.

Final media validation: 1,380.354 seconds; 1920×1200 H.264/AAC; 21 embedded MP4
chapters; complete decode returned no errors. Current code and remaining benchmark
limitations are described in [release status](current-release.md).

## Complete narrated transcript

# ChronosGraph — Full Developer Walkthrough

A narrated walkthrough of release `479e987`. Synthetic narration; real isolated browser/API recording; proposals published by a scripted real MCP stdio client, not a hosted-model performance test. Includes explanatory diagrams, paced actions and held recorded screens. Public Click import and trusted fixture test execution were observed. The live deployment was not changed.

## Chapter index

- **00:00** — What ChronosGraph is for
- **01:03** — How the pieces fit together
- **03:19** — Bring a public repository in
- **04:29** — Get your bearings in the repository
- **05:26** — Inspect functions and exact captured source
- **06:26** — Understand what changed—and what was not imported
- **07:24** — Connect your coding agent to the same snapshot
- **08:31** — Plan a change yourself, without an agent
- **09:28** — Catch an incomplete change before approval
- **10:31** — Review the coordinated fix
- **11:29** — Human approval is bound to exact contents
- **12:31** — Observe candidate tests in a disposable worktree
- **13:36** — Remember evidence, not just conversation
- **14:39** — Replay the useful investigation path
- **15:39** — Recover after a context reset
- **16:38** — Separate ownership, contributions and rules
- **17:42** — Make the connected knowledge portable
- **18:38** — Prove the stale-memory shield
- **19:39** — Use the same interface on real source graphs
- **20:42** — What the benchmark actually proved
- **21:49** — The intended everyday workflow and next steps

## 00:00 — What ChronosGraph is for

- A shared view for the developer and coding agent
- Connected context → review → observed evidence
- Not an autonomous replacement for engineering judgement

Welcome to the full ChronosGraph walkthrough. The way I intend this project to be used is as the shared command center between a developer and a coding agent. Your editor is where the code changes. Your agent helps investigate and implement. ChronosGraph makes the connected structure, proposed changes, governing decisions, and evidence visible to both of you. Instead of asking only, what does this file contain, you can ask, who calls this function, which modules depend on it, what policy governs it, and what should we test before accepting a change? We will follow a pricing change from discovery through review, real candidate test execution, memory, and invalidation. These are recorded actions against a real isolated backend. The proposal author is a scripted MCP client, not a live language model in this recording. The narration is synthetic. I will distinguish what works today from what still needs engineering before broader production use.

## 01:03 — How the pieces fit together

- Next.js command center + FastAPI
- Python structure and evidence in FalkorDB
- MCP tools for coding clients; exact snapshot guards

There are three interfaces to the same connected evidence. The browser command center is the human-facing interface. FastAPI exposes repository exploration, proposals, decisions, and controlled execution. The MCP server exposes tools that a compatible coding client can call. Underneath, FalkorDB stores captured files, Python definitions, resolved imports and calls, architecture decisions, proposals, execution records, and findings. A saved version is tied to an exact Git commit. The agent should discover the repository, inspect its snapshot, then pass the selected repository identifier and expected revision on subsequent calls. That keeps an investigation from silently switching to another saved version. Why use a graph here instead of only a text digest? Files, symbols, calls, decisions and findings have different relationships, and the task is often to traverse those relationships rather than summarize every file. Discovery paths use read-only graph queries. Context ranking combines lexical matches with native Page Rank evidence; that is not an external language-model answer. Graph Copy lets a proposed final state be analyzed without rewriting the saved source graph. Native shortest path supports the controlled procedural replay. The company-brain implementation also has vector retrieval support, but deterministic demonstration vectors must not be mistaken for measured model embeddings. Policy history distinguishes when a rule is valid from when the system recorded it. Finally, snapshot guards are consistency checks, not authentication. The current setup is for trusted local clients. Do not expose the mutation or execution endpoints as a public multi-user service without additional security engineering. The graph is not a perfect model of every possible runtime behavior. This implementation focuses on Python static structure, with bounded navigation and conservative resolution. A graph edge is useful evidence, but the absence of an edge is not proof that two pieces of code can never interact.

## 03:19 — Bring a public repository in

- Public GitHub URL; optional branch and commit
- Latest means resolved to a pinned commit at import
- Separate saved version; no imported code execution

The starting point for a new user is Import repository. Paste a public GitHub Python repository URL. Branch and commit hash are optional: the normal path resolves the repository's default branch and pins the selected commit when the import starts. The optional hash confirms the current branch head; it is not a historical commit picker. A mismatching hash stops the import rather than silently choosing different source. You do not need to invent an internal tenant identifier or run the old copy-and-paste terminal workflow. The import is a server-side job with a durable receipt, so closing a dialog is not the same as cancelling the backend job. Each successful import creates a separate saved version; it does not overwrite the older one. Public archive ingestion does not run repository code and does not fetch the whole commit history. Size and archive safety checks can reject unsupported repositories. Here we import the public Click project into the isolated demonstration instance, and then return to our small pricing repository for the connected-change workflow.

## 04:29 — Get your bearings in the repository

- Folders → files → dependencies
- Graph and keyboard-accessible table
- Saved commit stays visible while navigating

The repository view is your map, not just a decorative graph. Start at folders, then drill into a file. The explorer gives you a conventional navigation path, while the center shows the connected structure. You can switch between the visual graph and a table when the graph is too dense or when you prefer keyboard navigation. On the right, the inspector explains the selected file, its imports, what imports it, and its definitions. The commit shown in the header is the saved source version you are inspecting; it is not a promise of live workspace monitoring. In this example, pricing is used by checkout, checkout is used by the orders API, and an order test exercises that flow. That chain is what an agent can miss if it only reads the pricing file. The point is to keep the surrounding architecture available without forcing you to paste the entire repository into a chat.

## 05:26 — Inspect functions and exact captured source

- Definitions and resolved internal calls
- Source coordinates, not invented summaries
- Static coverage limits remain important

Switching to Functions makes the file's internal structure visible. Selecting calculate discount reveals the captured definition and its source lines. A coding agent can request the same evidence through get symbol source, rather than relying on an uncertain paraphrase. Locate context helps select relevant source and bounded connected neighbors for an investigation. Exact coordinates let you verify what the tool is talking about in your editor. Definitions, imports, and supported calls are reconstructed from Python syntax and scope information. Dynamic dispatch, decorators, generated code, and some inheritance patterns remain outside complete static proof. The UI should therefore help you inspect evidence, not imply that an attractive diagram is a complete runtime dependency model. The practical workflow is to use the graph to choose where to look, read the actual source, and then validate a concrete change with tests.

## 06:26 — Understand what changed—and what was not imported

- Commit-linked file changes from bounded local history
- Archive imports capture one source snapshot
- Current source inspection is not historical checkout

The History tab connects indexed commits to file changes. When a trusted local Git checkout has been indexed with bounded history, you can select a commit and inspect its linked changed files and recorded additions or deletions. This is useful during onboarding and change investigation: why did this module change, and which other files moved with it? There are two important boundaries. A public archive import captures source at one commit, so it does not magically bring the repository's entire history. And opening a file from the history panel inspects the current saved source, not a checkout of that historical commit. Deleted or unavailable historical source is not fabricated. For a developer, this means using the panel as a history index and jumping back to Git when a full historical diff or checkout is required. ChronosGraph complements normal version control rather than replacing it.

## 07:24 — Connect your coding agent to the same snapshot

- Configure the backend on the agent machine
- Discover → inspect → pass guards on every call
- 15 MCP tools; config export is not installed access

Connect agent prepares the MCP configuration and a selected-snapshot handoff. The paths must describe the machine where the agent's MCP process will run: the backend directory, Python executable, and FalkorDB connection must actually exist there. Copying a configuration is not the same as installing or authenticating a client. In the current release there are fifteen tools, including context discovery, exact source, proposals, decision checks, execution reports, policy operations, and memory. The safe handoff pattern is discover repositories, inspect the selected snapshot, then include that repository and exact expected revision on every subsequent call. A useful initial task is: investigate the discount calculation, show its callers and applicable rules, then propose a coordinated rename without applying it. The agent should stop for human review, not interpret context access as permission to edit or execute. In this demonstration those initial calls and proposals were made over real MCP stdio by the fixture client.

## 08:31 — Plan a change yourself, without an agent

- Load captured source; edit proposed source
- Preview before/after graph and candidate tests
- A local draft is not a durable approved proposal

You can also use ChronosGraph without waiting for a coding agent. The change planner loads the captured file beside an editable proposed version. Make a small edit, rename a function, or preview deleting the file, then compute the impact. The changed-region display helps you orient yourself, while the before and after dependency views show the bounded candidate scope. The graph preview does not write your checkout. In this example I rename the pricing function without updating checkout, so the result identifies a potentially broken downstream caller and recommends the order test. This is useful when planning a refactor before giving the implementation task to an agent. The browser draft is local working state, not the same thing as a durable MCP proposal with a human decision. For a reviewable agent change, use the proposal lifecycle we will look at next.

## 09:28 — Catch an incomplete change before approval

- Rename pricing only → checkout still calls the old symbol
- Replacement diff in a disposable GRAPH.COPY
- Potentially broken callers and candidate tests

Now open Changes and select the first proposal. The agent renamed the pricing function but did not update checkout. This is exactly the type of locally reasonable edit that breaks connected code. ChronosGraph creates a disposable graph copy, reconstructs the proposed final Python source, and compares the old and new dependency structure. It does not merely search for a changed filename. Here checkout is flagged as a potentially broken caller because it still depends on the old function. The preview also lists candidate files and tests reachable through the static structure, along with applicable rules and declared owners. None of this has changed the saved repository. The graph copy is cleaned up after analysis. The wording potentially broken is deliberate: static analysis provides a reason to investigate and test, not a universal compatibility verdict. This proposal is a review artifact, not an execution permission.

## 10:31 — Review the coordinated fix

- Pricing and checkout replacements in one proposal
- Added and removed imports/calls are inspectable
- Candidate pytest command is a recommendation

The second proposal changes pricing and checkout together. The new pricing definition and the updated import and call are part of the same proposed final state. With that coordinated replacement, the preview no longer flags the resolved checkout caller as broken. You can inspect each proposed file and the added versus removed imports and calls. The candidate order test remains relevant because it exercises the downstream flow. The suggested pytest command is a convenient starting point for verification; it is not permission to skip the rest of the suite. A zero count of flagged callers means no supported resolved callers were flagged, not that compatibility is guaranteed. This is the review experience I want: the agent submits an explicit connected plan, and the developer can compare its contents with source, rules, ownership, and likely impact in one place, instead of trusting a chat message saying everything should work.

## 11:29 — Human approval is bound to exact contents

- Exact proposal hash + base commit + source hashes
- Approve or reject with a reason
- Approval alone applies nothing

Approval is intentionally narrow. The record includes a proposal identifier, an exact content hash, the captured base revision, and the expected hashes of the touched source files. The operator reviews those contents and records a reason before approving. A different payload cannot inherit that approval. Before a decision or execution write, the backend rechecks the snapshot and relevant policy state, using a tenant mutation lock to avoid concurrent races. If the base source or governing policy is stale, the old permission should not remain silently usable. Notice the success message: the exact proposal is approved, and nothing has been applied. ChronosGraph is separating intention, authorization, and execution into different records. In ordinary use you should still review the patch, ask for missing coordinated files, and reject an incomplete proposal rather than treating the approve button as a shortcut around engineering review.

## 12:31 — Observe candidate tests in a disposable worktree

- Trusted local fixture; explicit operator action
- Apply approved replacements; observe pytest exit code
- Worktree isolation is not a security sandbox

Next comes observed execution. For this trusted local fixture, the operator explicitly enables the action and runs candidate tests in a disposable Git worktree. The runner checks the base bytes, applies the approved replacement bodies, runs the candidate pytest command with a timeout, records actual subprocess output and the exit code, and removes the temporary worktree. Here the order test passes with exit code zero. The evidence is labelled local worktree observed, which is stronger than an unverified client reporting that tests passed. But a worktree is filesystem separation, not a security sandbox. Repository tests can execute code with the runner's privileges, so this mode is appropriate only for trusted local repositories in the current design. It is not an invitation to execute arbitrary public imports. The original saved source stays unchanged. A passing candidate run is evidence for this proposal, not a production deployment or a comprehensive correctness proof.

## 13:36 — Remember evidence, not just conversation

- Real MCP activity and context-selection reasons
- Finding linked to source, policy, proposal and execution
- Current means current at the saved snapshot

Agent activity is where a developer can see the tool-visible work. These entries are real MCP calls, not invented internal agent thoughts and not ordinary browser reads. Context-selection details help explain why a file was returned. The passing candidate execution creates source-bound memory evidence linked to the proposal and observed execution. Its supporting source hashes and governing decisions define the conditions under which it is reusable. Current at indexed snapshot means the evidence still matches that captured version and policy state; it does not mean your working directory is continuously monitored. The proposed-result hashes remain separate from the captured base because we did not overwrite the original snapshot. This is useful across sessions: a later agent can recall the finding, inspect why it was considered valid, and decide what must be rechecked. It is more disciplined than storing a permanent natural-language claim that the pricing system works.

## 14:39 — Replay the useful investigation path

- Controlled policy investigation: five actions to three
- Native shortestPath retains the useful route
- Fewer tool actions—not measured LLM token savings

There is a second kind of memory here: a procedural playbook. Run the controlled policy investigation, then replay its verified path. The cold workflow explores five tool actions, including two dead ends. FalkorDB shortest path retains a useful route of three actions, and replay actually invokes the retained tools again. In this controlled scenario that is forty percent fewer tool actions. It is not a measurement of language-model intelligence or billed token savings, and this deterministic playbook is not an autonomous multi-agent team. Its role is to show how a connected record of investigation can preserve the useful route instead of repeating every wrong turn. Reuse still depends on the scenario and policy fingerprint matching. For a real developer, the intended pattern is to capture a useful investigation, replay only when its assumptions hold, and require a fresh investigation when those assumptions change.

## 15:39 — Recover after a context reset

- Prepare a measured ResumeSnapshot.md
- Capture the selected work and governing context
- Recovery is a handoff, not automatic omniscience

Prepare recovery note generates a compact Resume Snapshot Markdown handoff. The goal is to help a coding client resume after a context reset without rereading the full repository or reviving superseded instructions. The note captures the selected work and connected state in a bounded form. Its size is measured for the particular snapshot; there is no universal promise that every repository fits under a fixed number of bytes. The recovery workflow must keep current policy distinct from historical policy and must not promote obsolete rules back into authority. In practice, I would use this before a long agent session is compacted, at the end of an investigation, or when handing work to another developer. The receiving agent should still verify the selected revision and freshness conditions. A concise handoff improves continuity, but it does not replace reading the source and checking whether the underlying evidence is still valid.

## 16:38 — Separate ownership, contributions and rules

- Exact CODEOWNERS match and line
- Git touches are evidence, not declared ownership
- Current decisions stay distinct from superseded history

Ownership combines related evidence without pretending it is the same thing. Declared CODEOWNERS come from the matching rule and its source line; here the fixture declares the platform team. Git contribution records show authors and file touches in the indexed history, which may help identify context holders but do not establish declared ownership or verified GitHub identity. Architecture decisions are another layer: a current local rule can govern the selected file, while superseded decisions remain visible as history. Extracted repository constraints are labelled separately from an operator's local policy. For a maintainer, this separation matters. An agent should know whether it is following an active architecture decision, reading historical context, or inferring expertise from past commits. The fixture's pricing policy is a demonstration rule, not an upstream rule borrowed from an open-source project. Review the provenance before treating any displayed text as binding policy.

## 17:42 — Make the connected knowledge portable

- Preview [[Wikilink]] Markdown
- Download the three-layer Obsidian vault
- Export evidence; do not turn history into authority

The company-brain side of ChronosGraph is not limited to the browser. Preview the connected Wikilink note, then download the Obsidian vault ZIP. The export organizes connected repository knowledge into portable Markdown, so architecture, source references, and decision context can be inspected in another tool. This is useful for onboarding, a maintainer handoff, or retaining a readable explanation alongside a code change. It is not a replacement for the repository or the graph database, and a static export does not automatically stay synchronized with later edits. The three-layer organization is intended to keep high-level context, connected evidence, and source references understandable rather than dumping raw graph records into a folder. The important principle is the same as in the UI: preserve history and links, while making it clear which decisions are current and where the supporting evidence came from.

## 18:38 — Prove the stale-memory shield

- Record a new file-wide local policy
- Old decision remains history
- Prior proposal and finding become stale

Now change an assumption instead of changing the code. Record a new pricing policy with a reason and explicit confirmation. The old decision remains historical evidence, but the new active decision changes what may be reused. Return to Agent activity and the earlier finding is stale. Return to Changes and the proposal is stale policy. This is a core part of the design, not a cosmetic warning: yesterday's approval and test output cannot silently authorize work under today's changed rule. A source hash mismatch similarly requires revalidation. The correct response is to revisit the affected source and policy, generate a fresh proposal or investigation as appropriate, and gather new evidence. Do not erase the old record to make the status look green. For a developer supervising an agent, this gives memory a validity boundary and makes outdated confidence visible before it turns into another change.

## 19:39 — Use the same interface on real source graphs

- FalkorDB client, GraphRAG SDK, code-graph and MCP SDK
- Small fixture proves behavior; real repos reveal scale limits
- Missing ownership or history is not fabricated

The pricing example is deliberately small so every step can be inspected. The same command center can explore the captured FalkorDB Python client, GraphRAG SDK, code graph, and MCP Python SDK repositories. These are real source snapshots, not enlarged copies of the toy example. They show why folder-level navigation, bounded neighborhoods, and source-linked context matter as the repository grows. They also reveal limits that a small fixture would hide. Saved snapshots may lack declared ownership enrichment or full history, and older indexes can differ from the current analyzer. The application should show those absences rather than inventing maintainers or historical source. When using ChronosGraph on your own project, start by checking the snapshot revision and indexing scope, then inspect a few known dependencies before relying on the graph for a high-stakes review. The benchmark chapter shows the current measured strengths and weaknesses on these repositories.

## 20:42 — What the benchmark actually proved

- 333 backend tests; 34 frontend unit tests
- 92.22–98.19% focused byte reduction
- Latency and legacy-index targets are not all met

The latest benchmark batch adds repeatable isolated measurements, not just a performance slogan. All three hundred thirty-three backend tests passed with no failures or skips. Thirty-four frontend unit tests passed, along with type checking, production builds, and one hundred eighteen browser check executions. That browser count includes repeated recovery and setup suites; it is not one hundred eighteen new features. For one deterministically selected task per real repository, focused context slices were about ninety-two to ninety-eight percent smaller in bytes than the connected raw source baseline. That is byte reduction, not exact model-token or billing savings. Some targets failed: full context lookup was about one hundred eighty-four milliseconds at the ninety-fifth percentile on GraphRAG SDK, and four hundred forty-nine on the MCP SDK, above fifty milliseconds. The saved GraphRAG index also missed five hundred six expected absolute-import edges in the audited subset. Real runtime test-impact precision remains unmeasured.

## 21:49 — The intended everyday workflow and next steps

- Connect → investigate → propose → review → verify → recall
- Keep the editor, Git review and full test discipline
- Next: retrieval speed, fresh indexes, sandboxed runtime evaluation

Here is how I would use ChronosGraph day to day. Import or connect the repository and choose an exact saved version. Give the agent a bounded investigation task. Inspect the returned source and caller paths together. Ask for a coordinated proposal instead of an immediate edit. Review the diff, candidate impact, applicable decisions, and declared owners. Approve only the exact contents you understand. On trusted local projects, gather observed test evidence in a disposable worktree, or review a clearly labelled external execution report. Keep the normal pull-request process and full-suite discipline. Then retain a source-bound finding and a recovery note for the next session. The highest-priority next work is faster large-repository retrieval, new validated indexes where legacy snapshots are incomplete, and a genuinely sandboxed runtime failure oracle for test-impact accuracy. My intended product is a trustworthy review and context layer between people and coding agents, not another chat window or an unchecked autonomous code editor.

## Reference and scope

- Source release: https://github.com/nakulmaurya/ChronosGraph/tree/479e987
- Benchmark methodology and limitations: https://github.com/nakulmaurya/ChronosGraph/blob/479e987/tasks/reports/BENCHMARK-REPORT.md
- Raw benchmark results: https://github.com/nakulmaurya/ChronosGraph/blob/479e987/tasks/reports/benchmark-results.json
- Candidate tests are static recommendations, not safe-skip proof. Runtime precision and exact model-token savings are unmeasured. Public imports do not execute code. Worktrees are not security sandboxes.
