"""Selected-file preview user goals over actual HTTP/native graphs."""
import hashlib
import pytest
from app.db.client import db_manager
from app.services.diff_impact import dependency_view
from app.services.workspace import workspace_snapshot
from test_real_world_repos import client, local_repo, ingested


def test_load_full_file_then_preview_breaking_change_without_applying(client, ingested):
    tenant, _, source = ingested
    revision = workspace_snapshot(tenant)['source_revision']
    args = {'tenant_graph': tenant, 'expected_revision': revision}
    before_graphs = set(db_manager.list_tenant_graphs())
    source_before = (source/'src/pkg/a.py').read_text()
    loaded = client.get('/api/v1/repository/file-source', params={**args, 'file_path': 'src/pkg/a.py'})
    assert loaded.status_code == 200, loaded.text
    captured = loaded.json()
    assert captured['source'] == source_before
    assert not captured['truncated']
    assert captured['source_bytes'] == len(source_before.encode())
    assert captured['source_sha256'] == hashlib.sha256(source_before.encode()).hexdigest()
    replacement = 'def renamed():\n    return 8\n'
    preview = client.post('/api/v1/diff/impact', json={**args, 'file_bodies': {'src/pkg/a.py': replacement}})
    assert preview.status_code == 200, preview.text
    result = preview.json()
    assert result['sandbox_cleaned_up']
    assert 'src/pkg/b.py:run' in result['potentially_broken_callers']
    expected_edge = {'source': 'src/pkg/b.py', 'target': 'src/pkg/a.py'}
    assert expected_edge in result['dependency_graphs']['before']['edges']
    # Import still exists syntactically; the removed CALLS edge is separately reported.
    assert expected_edge in result['dependency_graphs']['after']['edges']
    assert any(d['relationship'] == 'CALLS' and d['target'] == 'src/pkg/a.py:helper' for d in result['removed_dependencies'])
    for view in result['dependency_graphs'].values():
        assert all(e['source'] in view['paths'] and e['target'] in view['paths'] for e in view['edges'])
    assert set(db_manager.list_tenant_graphs()) == before_graphs
    assert client.get('/api/v1/repository/file-source',params={**args,'file_path':'src/pkg/a.py'}).json() == captured
    assert (source/'src/pkg/a.py').read_text() == source_before


@pytest.mark.parametrize('kind', ['read', 'preview'])
def test_wrong_version_fails_without_cloning_or_changing_source(client, ingested, kind):
    tenant, _, _ = ingested
    before = set(db_manager.list_tenant_graphs())
    args = {'tenant_graph': tenant, 'expected_revision': '0'*40}
    if kind == 'read':
        result = client.get('/api/v1/repository/file-source', params={**args,'file_path':'src/pkg/a.py'})
    else:
        result = client.post('/api/v1/diff/impact', json={**args,'file_bodies':{'src/pkg/a.py':None}})
    assert result.status_code == 409, result.text
    assert set(db_manager.list_tenant_graphs()) == before


@pytest.mark.parametrize('fault,status', [('missing',404), ('absent_source',422), ('oversized',422), ('hash',409), ('revision',409)])
def test_editor_never_returns_partial_or_unverified_source(client, ingested, fault, status):
    tenant, _, _ = ingested
    args = {'tenant_graph':tenant,'expected_revision':workspace_snapshot(tenant)['source_revision'],'file_path':'src/pkg/a.py'}
    graph = db_manager.get_graph(tenant)
    if fault == 'missing': args['file_path'] = '../host.py'
    elif fault == 'absent_source': graph.query("MATCH (f:File {path:'src/pkg/a.py'}) REMOVE f.source_text")
    elif fault == 'oversized': graph.query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.source_text=$text",{'text':'#'+'x'*256001})
    elif fault == 'hash': graph.query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.sha256='wrong'")
    else: graph.query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.source_revision=$rev",{'rev':'0'*40})
    result = client.get('/api/v1/repository/file-source',params=args)
    assert result.status_code == status, result.text
    assert 'source' not in result.json()


def test_deleted_file_is_absent_from_after_graph_not_falsely_runnable(client, ingested):
    tenant, _, _ = ingested
    result = client.post('/api/v1/diff/impact', json={'tenant_graph':tenant,
        'expected_revision':workspace_snapshot(tenant)['source_revision'], 'file_bodies':{'src/pkg/a.py':None}})
    assert result.status_code == 200,result.text
    data = result.json()
    assert 'src/pkg/a.py' in data['dependency_graphs']['before']['paths']
    assert 'src/pkg/a.py' not in data['dependency_graphs']['after']['paths']
    assert all(e['target'] != 'src/pkg/a.py' for e in data['dependency_graphs']['after']['edges'])


def test_graph_boundaries_are_deterministic_and_never_fabricate_edges():
    paths = [f'{i:03}.py' for i in range(40)]
    deps = {('IMPORTS',a,b) for a in paths for b in paths if a != b}
    changed = ['039.py']
    view = dependency_view(deps,paths,paths,changed)
    assert view == dependency_view(deps,reversed(paths),paths,changed)
    assert len(view['paths']) == 30 and view['paths'][0] == '039.py'
    assert len(view['edges']) == 120 and view['nodes_truncated'] and view['edges_truncated']
    assert all(('IMPORTS', e['source'], e['target']) in deps for e in view['edges'])
