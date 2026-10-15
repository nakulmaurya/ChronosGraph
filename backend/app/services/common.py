"""Bounded, parameterized graph access shared by the local demo services."""
from __future__ import annotations
import hashlib
import json
import re
import threading
from typing import Any
from fastapi import HTTPException
from app.db.client import db_manager
from app.ingestion.seed_repos import REPOS
from app.models import GraphSubgraphPayload, VisualNode, VisualEdge

TENANT_PATTERN = re.compile(r"repo_[a-z0-9_]+\Z")
LOCKS = {tenant: threading.RLock() for tenant in REPOS}
LOCKS_MASTER = threading.Lock()


def tenant_lock(tenant: str):
    """Single-process request locks; CLI ingestion also uses a Redis writer lock."""
    with LOCKS_MASTER:
        return LOCKS.setdefault(tenant, threading.RLock())


def tenant_exists(tenant: str) -> str:
    if not isinstance(tenant, str) or not TENANT_PATTERN.fullmatch(tenant):
        raise HTTPException(404, 'Unknown tenant graph')
    if tenant not in db_manager.list_tenant_graphs():
        raise HTTPException(404, 'Unknown or unseeded tenant graph')
    graph = db_manager.get_graph(tenant)
    meta = graph.ro_query('MATCH (m:RepoMetadata) RETURN m.status LIMIT 1').result_set
    if meta:
        valid = meta[0][0] == 'READY'
    else:
        # Backwards-compatible registration for pre-metadata source graphs.
        valid = bool(graph.ro_query('MATCH (f:File) RETURN f.path LIMIT 1').result_set)
    if not valid:
        raise HTTPException(404, 'Unknown or unseeded tenant graph')
    tenant_lock(tenant)
    return tenant


def registered_tenants():
    graphs = db_manager.list_tenant_graphs()
    ordered = [t for t in REPOS if t in graphs]
    ordered += sorted(t for t in graphs if t not in REPOS and TENANT_PATTERN.fullmatch(t))
    result = []
    for tenant in ordered:
        try:
            result.append(tenant_exists(tenant))
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
    return result


def bounded_text(value: str, name: str, maximum: int = 8000) -> str:
    if not value.strip() or len(value) > maximum:
        raise HTTPException(422, f'{name} must contain 1..{maximum} characters')
    return value.strip()


def rows(result) -> list[dict[str, Any]]:
    names = [column[1] for column in result.header]
    return [dict(zip(names, row)) for row in result.result_set]


def read(tenant: str, cypher: str, params=None):
    result, elapsed = db_manager.ro_query(tenant, cypher, params or {})
    return rows(result), elapsed


def check_file(tenant: str, path: str) -> str:
    bounded_text(path, 'file_path', 1024)
    found, _ = read(tenant, 'MATCH (f:File {path:$path}) RETURN f.path AS path', {'path': path})
    if not found:
        raise HTTPException(404, 'File is not present in this pinned repository snapshot')
    return path


def fingerprint(tenant: str) -> str:
    # Includes source and current rule state, so overrides invalidate cached playbooks.
    state, _ = read(tenant, '''MATCH (f:File) OPTIONAL MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(f)
    RETURN f.path AS path,f.sha256 AS sha,d.id AS policy,d.rule AS rule ORDER BY path,policy''')
    constraints, _ = read(tenant,"""MATCH (d:Decision {source_type:'REPO_EXTRACTED_RULE'})
        RETURN d.id AS id,d.rule AS rule,d.source_revision AS revision ORDER BY id""")
    return hashlib.sha256(json.dumps({'files':state,'repository_constraints':constraints}, sort_keys=True).encode()).hexdigest()


def graph_payload(tenant: str, paths=None, investigation_id=None, cypher='', elapsed=0.0,
                  impacted=False) -> GraphSubgraphPayload:
    params = {'paths': paths or [], 'inv': investigation_id or ''}
    if investigation_id:
        selection = '''MATCH (inv:Investigation {id:$inv})-[:HAS_STATE]->(n:StateNode)
        RETURN n UNION MATCH (n:Investigation {id:$inv}) RETURN n'''
    elif paths:
        selection = '''MATCH (n:File) WHERE n.path IN $paths RETURN n
        UNION MATCH (n:Decision)-[:GOVERNS]->(f:File) WHERE f.path IN $paths RETURN n
        UNION MATCH (f:File)-[:DEFINES]->(n:Function) WHERE f.path IN $paths RETURN n LIMIT 220'''
    else:
        selection = 'MATCH (n:File) RETURN n ORDER BY n.pagerank DESC LIMIT 50'
    result, query_ms = db_manager.ro_query(tenant, selection, params)
    records = list(result.result_set)
    if paths:
        # Ensure newly parsed clone-only definitions remain inspectable even if
        # the normal bounded function payload reaches its presentation limit.
        patches, patch_ms = db_manager.ro_query(tenant, '''MATCH (f:File)-[:DEFINES]->(n)
          WHERE f.path IN $paths AND n.source_type='AST_PATCH_SIMULATION'
          RETURN n LIMIT 500''', params)
        records = list(patches.result_set) + records
        query_ms += patch_ms
    nodes = {}
    for row in records:
        node = row[0]; p = {k:v for k,v in node.properties.items() if k != 'source_text'}
        p.pop('embedding', None)
        label = node.labels[0] if node.labels else 'Node'
        status = p.get('status', 'DEFAULT')
        if label == 'StateNode':
            status = 'DEAD_END' if p.get('state_type') == 'DEAD_END' else 'GOLDEN_PATH'
        elif impacted and label in {'File', 'Function'}:
            status = 'IMPACTED'
        if status not in {'ACTIVE','SUPERSEDED','IMPACTED','DEAD_END','GOLDEN_PATH','DEFAULT'}:
            status = 'DEFAULT'
        ident = str(node.id)
        nodes[ident] = VisualNode(id=ident, label=label,
            title=str(p.get('rule') or p.get('path') or p.get('qualified_name') or p.get('title') or p.get('id') or label),
            status=status, subtitle=p.get('source_type'), url=p.get('source_url') or p.get('url'), metadata=p)
    ids = [int(n) for n in nodes]
    result, edge_ms = db_manager.ro_query(tenant, '''MATCH (a)-[r]->(b)
    WHERE id(a) IN $ids AND id(b) IN $ids RETURN r LIMIT 500''', {'ids': ids})
    edges = []
    for row in result.result_set:
        edge = row[0]; source, target = str(edge.src_node), str(edge.dest_node)
        pruned = nodes[source].status == 'DEAD_END' or nodes[target].status == 'DEAD_END'
        edges.append(VisualEdge(id=str(edge.id), source=source,target=target,relationship=edge.relation,
            is_pruned=pruned,is_highlighted=edge.relation=='ACTION_TAKEN' and not pruned))
    return GraphSubgraphPayload(nodes=list(nodes.values()), edges=edges,
        cypher_executed=cypher or selection, execution_time_ms=round(elapsed+query_ms+edge_ms,2))
