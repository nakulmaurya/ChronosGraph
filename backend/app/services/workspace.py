"""Read-only snapshot connection metadata. Never access host paths from HTTP."""
from app.services.common import tenant_exists, read


def workspace_snapshot(tenant_graph):
    tenant = tenant_exists(tenant_graph)
    records, _ = read(tenant, '''MATCH (m:RepoMetadata) RETURN m.repository AS repository,
      m.source_revision AS source_revision,m.connection_kind AS connection_kind,
      m.selected_branch AS selected_branch,m.parent_snapshot AS parent_snapshot,
      m.workspace_check_status AS last_check_status,m.workspace_checked_at AS checked_at,
      m.workspace_observed_revision AS observed_revision,m.workspace_dirty AS dirty,
      m.workspace_check_reasons AS reasons,m.import_tree_sha AS import_tree_sha,
      m.import_file_count AS import_file_count,m.import_archive_sha256 AS import_archive_sha256,
      m.import_selected_blob_verification AS import_blob_verification,
      m.history_scope AS history_scope LIMIT 1''')
    data = records[0] if records else {}
    # Legacy seeded graphs have per-file provenance but no RepoMetadata. Use it
    # only if every captured file agrees on exactly one non-null revision.
    if not data.get('source_revision'):
        revisions, _ = read(tenant, 'MATCH (f:File) RETURN DISTINCT f.source_revision AS revision LIMIT 2')
        if len(revisions)==1 and revisions[0]['revision']:
            data['source_revision']=revisions[0]['revision']
    return {'tenant_graph':tenant, 'repository':data.get('repository'),
            'source_revision':data.get('source_revision'),
            'connection_kind':data.get('connection_kind') or 'PINNED_SNAPSHOT_NO_LOCAL_CONNECTION',
            'selected_branch':data.get('selected_branch'), 'parent_snapshot':data.get('parent_snapshot') or None,
            'last_check':{'status':data.get('last_check_status') or 'NOT_CHECKED',
                          'checked_at':data.get('checked_at') or None,
                          'observed_revision':data.get('observed_revision'),
                          'dirty':data.get('dirty'), 'reasons':data.get('reasons') or []},
            'freshness_is_live':False, 'mutation_transport':'LOCAL_CLI_ONLY',
            'public_intake':None if data.get('connection_kind')!='PUBLIC_GITHUB_ARCHIVE' else {
                'tree_sha':data.get('import_tree_sha'),'tree_file_count':data.get('import_file_count'),
                'archive_sha256':data.get('import_archive_sha256'),
                'selected_blob_verification':data.get('import_blob_verification'),
                'history_scope':data.get('history_scope'),
                'scope':'PYTHON_AST_AND_SELECTED_SUPPORT_FILES_NOT_WHOLE_REPO_SEMANTICS'},
            'memory_carry_forward':{'mode':'READ_ONLY_ON_DEMAND_PREDECESSOR_VALIDATION','read_operation':'recall_task_memory','test_results_reexecuted':False},
            'sync_semantics':'NEW_IMMUTABLE_SNAPSHOT_OLD_GRAPH_AND_FINDINGS_UNCHANGED',
            'model_calls':0}
