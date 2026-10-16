"""Read-only snapshot connection metadata. Never access host paths from HTTP."""
from app.services.common import tenant_exists, read


def workspace_snapshot(tenant_graph):
    tenant = tenant_exists(tenant_graph)
    records, _ = read(tenant, '''MATCH (m:RepoMetadata) RETURN m.repository AS repository,
      m.source_revision AS source_revision,m.connection_kind AS connection_kind,
      m.selected_branch AS selected_branch,m.parent_snapshot AS parent_snapshot,
      m.workspace_check_status AS last_check_status,m.workspace_checked_at AS checked_at,
      m.workspace_observed_revision AS observed_revision,m.workspace_dirty AS dirty,
      m.workspace_check_reasons AS reasons LIMIT 1''')
    data = records[0] if records else {}
    return {'tenant_graph':tenant, 'repository':data.get('repository'),
            'source_revision':data.get('source_revision'),
            'connection_kind':data.get('connection_kind') or 'PINNED_SNAPSHOT_NO_LOCAL_CONNECTION',
            'selected_branch':data.get('selected_branch'), 'parent_snapshot':data.get('parent_snapshot') or None,
            'last_check':{'status':data.get('last_check_status') or 'NOT_CHECKED',
                          'checked_at':data.get('checked_at') or None,
                          'observed_revision':data.get('observed_revision'),
                          'dirty':data.get('dirty'), 'reasons':data.get('reasons') or []},
            'freshness_is_live':False, 'mutation_transport':'LOCAL_CLI_ONLY',
            'sync_semantics':'NEW_IMMUTABLE_SNAPSHOT_OLD_GRAPH_AND_FINDINGS_UNCHANGED',
            'model_calls':0}
