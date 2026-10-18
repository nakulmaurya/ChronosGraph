# Graph model and queries

ChronosGraph uses native FalkorDB queries to connect code, project knowledge and
change-review records. These are implementation names, not a replacement schema.

## Code relationships

- `(File)-[:IMPORTS]->(File)`
- `(File)-[:DEFINES]->(Function)`
- `(Function)-[:CALLS]->(Function)`

The bounded impact query begins with the following excerpt from
[`CYPHER_BLAST_RADIUS_AUDIT`](../backend/app/db/queries.py):

```cypher
MATCH (target:File)
WHERE target.path IN $modified_files
OPTIONAL MATCH (downstream:File)-[:IMPORTS*1..3]->(target)
WITH target, collect(DISTINCT downstream.path) AS impacted_files
```

The full query also collects captured callers and governing decisions. These are
potentially affected relationships, not exhaustive runtime impact.

## Project knowledge

`Decision` nodes connect to `File` through `GOVERNS`, to pinned
`OrganizationalExcerpt` evidence through `SUPPORTED_BY` and `MOTIVATED_BY`, and
to older decisions through `SUPERSEDED`. Explicit CODEOWNERS/team mapping supplies
`(OrganizationTeam)-[:OWNS]->(File)`; it does not verify team identity or access.

[Organizational ingestion](../backend/app/ingestion/organization.py) ·
[Context lookup](../backend/app/services/context_locator.py)

## Tasks and review

- `(ChangeTask)-[:HAS_PLAN]->(PlanVersion)-[:HAS_CONTEXT]->(ContextPack)`
- `(ChangeTask)-[:HAS_ASSIGNMENT]->(TaskAssignment)-[:ASSIGNED_RUN]->(ChangeAgentRun)`
- `(ChangeAgentRun)-[:USES_CONTEXT]->(ContextPack)`

Task context retains source/plan identity; assignments keep worker and reviewer
handoffs explicit. Proposed contents have their own review lifecycle, separate
from an agent's returned assessment.

[Task records](../backend/app/services/task_runtime.py) ·
[Assignments](../backend/app/services/task_assignments.py) ·
[Proposal lifecycle](../backend/app/services/change_lifecycle.py)

## Other graph operations

`GRAPH.COPY` supports disposable analysis graphs, not operating-system isolation.
The canonical query module also contains the controlled `shortestPath` playbook
query; this is not a general autonomous scheduler.

[Architecture](architecture.md) · [Limitations](limitations-and-evaluation.md)
