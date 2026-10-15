"""
Canonical OpenCypher Queries for ChronosGraph.
Strictly compliant with FalkorDB OpenCypher (No Neo4j APOC).
"""

CYPHER_BLAST_RADIUS_AUDIT = """
MATCH (target:File)
WHERE target.path IN $modified_files
OPTIONAL MATCH (downstream:File)-[:IMPORTS*1..3]->(target)
WITH target, collect(DISTINCT downstream.path) AS impacted_files
OPTIONAL MATCH (target)-[:DEFINES]->(fn_target:Function)<-[:CALLS*1..3]-(fn_down:Function)
WITH target, impacted_files, collect(DISTINCT fn_down.qualified_name) AS impacted_functions
OPTIONAL MATCH (d:Decision {status: 'ACTIVE'})-[:GOVERNS]->(target)
OPTIONAL MATCH (d)-[:SUPERSEDED]->(old_d:Decision)
WITH target, impacted_files, impacted_functions, collect(DISTINCT {
    id: d.id,
    rule: d.rule,
    rationale: d.rationale,
    source_url: d.source_url,
    superseded_rule: old_d.rule
  }) AS active_decisions
OPTIONAL MATCH (open_issue:Issue {state: 'OPEN'})-[:AFFECTS]->(affected:File)
WHERE affected.path IN impacted_files
RETURN
  target.path AS modified_file,
  coalesce(target.pagerank, 0.15) AS criticality_score,
  impacted_files,
  impacted_functions,
  active_decisions,
  collect(DISTINCT {
    number: open_issue.number,
    title: open_issue.title,
    url: open_issue.url
  }) AS related_open_issues
"""

CYPHER_FILE_OWNERSHIP_AND_LINEAGE = """
MATCH (f:File {path: $file_path})
OPTIONAL MATCH (c:Contributor)-[r:AUTHORED|REVIEWED]->(pr:PullRequest)-[m:MODIFIES]->(f)
WITH f, c, count(DISTINCT pr) AS pr_count, sum(coalesce(m.additions, 10) + coalesce(m.deletions, 5)) AS lines_touched, max(coalesce(pr.committed_at, pr.merged_at)) AS last_active,
  collect(DISTINCT pr.source_type) AS source_types, collect(DISTINCT pr.url) AS source_urls
ORDER BY pr_count DESC, lines_touched DESC
WITH f, collect(DISTINCT {
  login: c.login,
  name: c.name,
  identity_kind: coalesce(c.identity_kind, 'GITHUB_LOGIN'),
  source_types: source_types,
  source_urls: source_urls,
  url: head(source_urls),
  pr_count: pr_count,
  lines_touched: lines_touched,
  last_active: last_active
})[0..3] AS top_experts
OPTIONAL MATCH (active_d:Decision {status: 'ACTIVE'})-[:GOVERNS]->(f)
OPTIONAL MATCH (active_d)-[:SUPERSEDED]->(old_d:Decision)
RETURN
  f.path AS file_path,
  top_experts,
  collect(DISTINCT {
    active_id: active_d.id,
    active_rule: active_d.rule,
    active_rationale: active_d.rationale,
    active_url: active_d.source_url,
    valid_from: active_d.valid_from,
    superseded_id: old_d.id,
    superseded_rule: old_d.rule,
    superseded_url: old_d.source_url,
    superseded_at: old_d.valid_to
  }) AS decision_lineage
"""

CYPHER_SUPERSEDE_DECISION = """
MATCH (f:File {path: $file_path})
OPTIONAL MATCH (old_d:Decision {status: 'ACTIVE'})-[:GOVERNS]->(f)
SET old_d.status = 'SUPERSEDED',
    old_d.valid_to = $timestamp
WITH f, collect(old_d) AS old_decisions
CREATE (new_d:Decision {
  id: $new_id,
  scope_symbol: $scope_symbol,
  rule: $new_rule,
  rationale: $rationale,
  source_type: 'LIVE_ARCHITECT_OVERRIDE',
  source_url: $source_url,
  status: 'ACTIVE',
  valid_from: $timestamp,
  valid_to: 0,
  embedding: vecf32($embedding)
})
CREATE (new_d)-[:GOVERNS]->(f)
FOREACH (od IN old_decisions |
  CREATE (new_d)-[:SUPERSEDED {timestamp: $timestamp, reason: $rationale}]->(od)
)
RETURN new_d.id AS created_decision_id, size(old_decisions) AS superseded_count
"""

CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH = """
MATCH (inv:Investigation {id: $investigation_id})-[:HAS_STATE]->(start:StateNode {state_type: 'START'})
MATCH (inv)-[:HAS_STATE]->(goal:StateNode {state_type: 'VERIFIED_GOAL'})
WITH inv, shortestPath((start)-[:ACTION_TAKEN*1..12]->(goal)) AS golden_path
WITH inv, golden_path,
     [rel IN relationships(golden_path) | {
       agent: rel.agent_name,
       tool: rel.tool_name,
       cypher: rel.cypher_executed,
       tokens: rel.tokens_used,
       duration_ms: rel.duration_ms,
       outcome: rel.outcome
     }] AS compiled_steps,
     [n IN nodes(golden_path) | n.id] AS golden_node_ids
MATCH (inv)-[:HAS_STATE]->(s_all:StateNode)-[r_all:ACTION_TAKEN]->(s_next:StateNode)
RETURN
  compiled_steps,
  golden_node_ids,
  count(r_all) AS total_raw_steps,
  sum(r_all.tokens_used) AS total_raw_tokens,
  sum(r_all.duration_ms) AS total_raw_duration_ms,
  size(compiled_steps) AS pruned_step_count
"""

CYPHER_HYBRID_VECTOR_DECISION_SEARCH = """
CALL db.idx.vector.queryNodes('Decision', 'embedding', 4, vecf32($query_embedding))
YIELD node AS d, score
WHERE d.status = 'ACTIVE'
MATCH (d)-[:GOVERNS]->(f:File)
OPTIONAL MATCH (d)-[:SUPERSEDED]->(old_d:Decision)
OPTIONAL MATCH (c:Contributor)-[:AUTHORED]->(pr:PullRequest)-[:MODIFIES]->(f)
RETURN
  d.id AS decision_id,
  d.rule AS active_rule,
  d.rationale AS rationale,
  d.source_url AS source_url,
  score AS vector_distance,
  f.path AS governed_file,
  old_d.id AS superseded_id,
  old_d.rule AS superseded_rule,
  collect(DISTINCT c.login)[0..3] AS maintainers
ORDER BY score ASC
"""
