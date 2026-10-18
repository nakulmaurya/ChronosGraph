"""Read-only graph paths from selected files to declared owner source evidence."""
from app.services.organization import organizational_context
from app.services.common import tenant_exists, check_file, read, tenant_lock


def ownership_for_paths(tenant, paths, limit=8, include_organization=False):
    metadata, _ = read(tenant, '''MATCH (m:RepoMetadata)
      RETURN m.ownership_index_status AS status,m.ownership_source_path AS path,
      m.ownership_source_sha256 AS sha256,m.ownership_source_revision AS revision,
      m.ownership_source_url AS source_url,m.ownership_invalid_rule_count AS invalid_rule_count LIMIT 1''')
    meta = metadata[0] if metadata else {}
    declarations, _ = read(tenant, '''MATCH (s:OwnershipSource)-[:DEFINES_OWNERSHIP_RULE]->(r:OwnershipRule)-[:APPLIES_TO]->(f:File)
      WHERE f.path IN $paths OPTIONAL MATCH (r)-[:DECLARES_OWNER]->(o:DeclaredOwner)
      RETURN f.path AS file_path,r.pattern AS pattern,r.source_line AS source_line,
      o.name AS owner,o.kind AS owner_kind
      ORDER BY file_path,owner LIMIT $limit''', {'paths': paths, 'limit': limit+1})
    result = {'status': meta.get('status') or 'NOT_INDEXED_IN_THIS_SNAPSHOT',
            'source_document': {k: meta.get(k) for k in ('path', 'sha256', 'revision', 'source_url')},
            'invalid_rule_count': meta.get('invalid_rule_count') or 0,
            'declarations': declarations[:limit], 'truncated': len(declarations) > limit,
            'basis': 'DECLARED_AT_PINNED_COMMIT_NOT_VERIFIED_IDENTITY_OR_ACCESS',
            'workspace_freshness': 'PINNED_SNAPSHOT_WORKSPACE_NOT_CHECKED'}
    if include_organization:
        result['organizational_evidence'] = organizational_context(tenant,paths)
    return result


def get_ownership(tenant_graph, file_path):
    tenant = tenant_exists(tenant_graph)
    with tenant_lock(tenant):
        check_file(tenant, file_path)
        return {'tenant_graph': tenant, 'file_path': file_path,
                **ownership_for_paths(tenant, [file_path], limit=20, include_organization=True), 'model_calls': 0}
