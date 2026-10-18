# ChronosGraph

## See what your coding agents change—and the evidence behind it.

A **visual oversight and shared-context layer for coding agents, powered by FalkorDB**.

ChronosGraph connects code dependencies, architectural decisions, ownership,
agent handoffs, and proposed patches. Developers can inspect the context behind
a change, review linked evidence, and retain control over approval.

**[Start the working project](#start-locally)** · **[Three-minute demo guide](docs/release-demo.md)** ·
**[Judge’s guide](docs/judges-guide.md)** · **[Current release](docs/current-release.md)**

## The developer problem

“The agent produced a patch. What might it affect, which constraints apply,
what did the reviewer check, and exactly what am I approving?”

For a developer supervising coding agents in an unfamiliar or evolving codebase,
a patch alone is not enough. ChronosGraph makes the captured relationships and
review evidence inspectable alongside the exact proposed contents. It complements
an agent, Git and real tests; it does not replace engineering judgment.

## One connected workflow

1. **Explore:** select an exact saved revision; follow a file’s imports, callers
   and definitions in the graph or equivalent table.
2. **Understand:** inspect governing decisions, their source excerpts and incident
   rationale, plus declared ownership. Superseded decisions remain history.
3. **Share context:** retain an immutable task plan and bounded, revision-aware
   context pack; hand a candidate from worker to a separate reviewer.
4. **Review:** inspect the exact candidate diff, declared rationale, bounded
   potential impact, reviewer report and actual test observations.
5. **Decide:** keep human approval separate from agent acceptance and execution.
   Reconsider evidence when its source or governing rules change.

The prepared `retry_after` example uses an **owned synthetic organization and
incident**. It shows recorded real OpenCode worker/reviewer activity, not a new
live model run. The candidate preserves the timeout result contract, forwards an
optional delay through the worker and adds regression tests. Its agent reviewer
accepted the bounded candidate after its own 39-check run; this is historical
observed evidence, **not human approval or integration**.

## Why FalkorDB is central

FalkorDB stores and traverses the connected source, decisions, task context,
assignments and evidence. Removing it removes repository navigation, applicable
rule lookup, task/handoff retrieval and proposal analysis—not just the drawing.
FastAPI and the MCP server use the same selected saved graph. Next.js presents
its captured relationships and review controls.

## All three hackathon tracks

| Track | The same connected workflow demonstrates |
| --- | --- |
| **Agents That Act on Connected Data** | Captured caller/dependency paths and governing decisions support investigation and proposal review. |
| **Agent Memory and Coordination** | Persistent task context, immutable plans and separate serialized worker/reviewer handoffs. Not an autonomous concurrent scheduler. |
| **Company Brain** | Code linked to architecture decisions, incident excerpts and explicitly mapped review teams. Synthetic organizational records are labeled. |

## Start locally

Requirements: Git, Bash, **Python 3.11+**, **Node 20.9+**, Docker and npm. The
witnessed development environment is Linux/Python 3.13/Node 24. Use WSL2 + Docker
on Windows; see [platform notes](docs/t09-platform-setup.md).

```sh
git clone https://github.com/nakulmaurya/ChronosGraph.git
cd ChronosGraph
git checkout main
bash scripts/start-local.sh
```

Open **http://127.0.0.1:3001**. The launcher installs dependencies, starts its own
loopback FalkorDB, seeds the configured public-source examples and starts API
8000 and frontend 3001. Initial downloads take time. Ctrl-C stops its owned
processes/container; **the default launcher database is ephemeral**. Do not point
its seeder at unrelated data. [Durability and recovery](docs/task-runtime-hardening-recovery.md)
and [OpenCode integration](integrations/opencode/README.md) are separate explicit
setups; a fresh clone does not recreate historical agent sessions.

For opt-in public repository imports:

```sh
CHRONOSGRAPH_ENABLE_BROWSER_IMPORT=1 bash scripts/start-local.sh
```

Click **Import repository** and provide a permitted public Python GitHub repository.
A saved import pins source; it does not run imported code. For the existing
persisted prepared example and trusted VM tunnel, follow [demo access](docs/preview-access.md).
The supported submission fallback is complete local setup, not a claimed public
multi-user deployment.

## Graph model and actual queries

These are implementation names, not a conceptual replacement schema:

- `(File)-[:IMPORTS]->(File)`, `(File)-[:DEFINES]->(Function)` and
  `(Function)-[:CALLS]->(Function)` support bounded dependency exploration.
- `(Decision)-[:GOVERNS]->(File)`, `SUPPORTED_BY` and `MOTIVATED_BY` links to
  `OrganizationalExcerpt`, and `SUPERSEDED` decision history connect requirements
  to pinned evidence. `(OrganizationTeam)-[:OWNS]->(File)` comes from explicit
  CODEOWNERS/team mapping, not inferred identity or access.
- `(ChangeTask)-[:HAS_PLAN]->(PlanVersion)-[:HAS_CONTEXT]->(ContextPack)`,
  `(ChangeTask)-[:HAS_ASSIGNMENT]->(TaskAssignment)-[:ASSIGNED_RUN]->(ChangeAgentRun)`
  and `(ChangeAgentRun)-[:USES_CONTEXT]->(ContextPack)` retain task continuity.

Example bounded query used in impact analysis:

```cypher
MATCH (target:File)
WHERE target.path IN $modified_files
OPTIONAL MATCH (downstream:File)-[:IMPORTS*1..3]->(target)
RETURN target.path, collect(DISTINCT downstream.path)
```

Inspect the real implementation:
[canonical Cypher](backend/app/db/queries.py),
[context locator](backend/app/services/context_locator.py),
[organization ingestion](backend/app/ingestion/organization.py),
[task/context records](backend/app/services/task_runtime.py),
[handoffs](backend/app/services/task_assignments.py),
[proposal lifecycle](backend/app/services/change_lifecycle.py).
`GRAPH.COPY` provides disposable graph analysis; it is not an OS security sandbox.
The controlled playbook uses `shortestPath` in the canonical query module; it is
not a learned general agent scheduler. [Architecture](docs/architecture.md).

## Verification and limitations

[Current release](docs/current-release.md) is the source of truth for the
application revision, current checks, deployment identity and video. Historical
receipts retain their original commit and scope; overlapping counts are not added.
The prepared candidate remains separate from the application release.

Analysis is Python-focused, static and bounded; omitted/dynamic relationships
are not proof of no impact. Agent acceptance is not human approval. Idle or
missing telemetry is not completion. Trusted local execution is not hostile-code
isolation, and loopback checks are not multi-user authentication.

The observed comparison **did not establish token, cost or speed savings**.
Unfavorable results and earlier benchmark limitations remain available in
[limitations and evaluation](docs/limitations-and-evaluation.md). No failure
history was deleted to improve the presentation.

## AI assistance and participant contribution

AI coding assistants were used for implementation, review assistance,
documentation, testing workflows and media preparation. Recorded reviewer
acceptance is an agent report, not a human audit. The participant defined and
iterated on the intended developer workflow and supplied the VM/project access;
this conversation records those inputs. The participant must supply their own
truthful account of personally written code, checks performed and technical
understanding in the organizer submission; no unobserved human verification is
claimed here. [Third-party notices](THIRD_PARTY_NOTICES.md).
