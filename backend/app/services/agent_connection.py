"""Read-only agent discovery and explicit snapshot preflight; no session authority."""
import re
from fastapi import HTTPException
from app.ingestion.seed_repos import REPOS
from app.services.common import registered_tenants, tenant_exists
from app.services.workspace import workspace_snapshot


def require_snapshot(tenant_graph, expected_revision):
    """Fail closed when the caller's selected saved version cannot be confirmed."""
    if not isinstance(expected_revision, str) or not re.fullmatch(r'[0-9a-f]{40}', expected_revision):
        raise HTTPException(422, 'expected_revision must be the exact lowercase 40-character commit hash from discovery')
    snapshot = workspace_snapshot(tenant_graph)
    if snapshot['source_revision'] != expected_revision:
        raise HTTPException(409, 'Selected snapshot does not match expected_revision; discover repositories again before continuing')
    return snapshot


def discover_repositories(cursor='', limit=20):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
        raise HTTPException(422, 'Require limit 1..50')
    if cursor and not re.fullmatch(r'repo_[a-z0-9_]+', cursor):
        raise HTTPException(422, 'Use the next_cursor returned by repository discovery')
    names = [t for t in sorted(registered_tenants()) if t > cursor]
    repositories = []
    for tenant in names[:limit]:
        snapshot = workspace_snapshot(tenant)
        revision = snapshot['source_revision']
        repositories.append({
            'tenant_graph': tenant,
            'repository': snapshot['repository'] or REPOS.get(tenant, tenant),
            'source_revision': revision,
            'selected_branch': snapshot['selected_branch'],
            'snapshot_guard_available': bool(revision and re.fullmatch(r'[0-9a-f]{40}', revision)),
            'workspace_freshness': snapshot['last_check']['status'],
        })
    return {'repositories': repositories,
            'next_cursor': names[limit-1] if len(names) > limit else None,
            'selection_required': True,
            'scope': 'Saved indexed versions only; not live workspaces. Select tenant_graph and source_revision explicitly.',
            'model_calls': 0}


def inspect_repository_snapshot(tenant_graph, expected_revision):
    tenant = tenant_exists(tenant_graph)
    snapshot = require_snapshot(tenant, expected_revision)
    return {'snapshot': snapshot, 'accepted': True,
            'tool_arguments': {'tenant_graph': tenant, 'expected_revision': expected_revision},
            'guard_scope': 'Commit identity at invocation, not live workspace freshness, policy approval or authorization. Pass these arguments on every tool call.',
            'model_calls': 0}
