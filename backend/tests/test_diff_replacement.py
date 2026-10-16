"""Native GRAPH.COPY regression: full replacement is not an additive overlay."""
import difflib
import pytest
from app.db.client import db_manager
from app.services.diff_impact import reconstruct, safe_path
from fastapi import HTTPException
from test_real_world_repos import client, local_repo, ingested  # native disposable Git fixture


def digest(tenant):
    graph = db_manager.get_graph(tenant)
    return [graph.ro_query(q).result_set for q in [
        'MATCH (f:File) RETURN f.path,f.sha256 ORDER BY f.path',
        'MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a.qualified_name,b.qualified_name ORDER BY a.qualified_name,b.qualified_name',
        'MATCH (a:File)-[:IMPORTS]->(b:File) RETURN a.path,b.path ORDER BY a.path,b.path',
        'MATCH (f:Function) RETURN f.qualified_name,f.signature ORDER BY f.qualified_name',
    ]]


def test_replacement_removes_edges_retains_before_impact_and_base(client, ingested):
    tenant, _, _ = ingested
    before = digest(tenant)
    graphs = set(db_manager.list_tenant_graphs())
    # b previously imports/calls a.helper; replacement removes both.
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant,
        'file_bodies': {'src/pkg/b.py': 'def run():\n    return 42\n'}})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['semantics'] == 'FULL_FILE_REPLACEMENT' and data['sandbox_cleaned_up']
    assert {'relationship': 'IMPORTS', 'source': 'src/pkg/b.py', 'target': 'src/pkg/a.py'} in data['removed_dependencies']
    assert {'relationship': 'CALLS', 'source': 'src/pkg/b.py:run', 'target': 'src/pkg/a.py:helper'} in data['removed_dependencies']
    assert 'src/pkg/c.py' in data['impacted_files']
    assert digest(tenant) == before and set(db_manager.list_tenant_graphs()) == graphs


def test_removed_symbol_and_signature_report_inbound_callers(client, ingested):
    tenant, _, _ = ingested
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': {
        'src/pkg/a.py': 'def helper(required):\n    return required\n'}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert 'src/pkg/a.py:helper' in d['removed_or_signature_changed_symbols']
    assert 'src/pkg/a.py:run' in d['removed_or_signature_changed_symbols']
    assert 'src/pkg/b.py:run' in d['potentially_broken_callers']
    assert d['model_calls'] == 0
    assert 'syntax_fixture.py' in d['parse_coverage']['before_failed_files']
    assert 'syntax_fixture.py' in d['parse_coverage']['after_failed_files']


def test_multifile_rename_delete_add_and_new_resolution(client, ingested):
    tenant, _, root = ingested
    a = (root/'src/pkg/a.py').read_text()
    b = (root/'src/pkg/b.py').read_text()
    diff = 'diff --git a/src/pkg/a.py b/src/pkg/renamed.py\nsimilarity index 100%\nrename from src/pkg/a.py\nrename to src/pkg/renamed.py\n'
    diff += 'diff --git a/src/pkg/b.py b/src/pkg/b.py\n' + ''.join(difflib.unified_diff(
        b.splitlines(True), [], fromfile='a/src/pkg/b.py', tofile='/dev/null'))
    new = 'from pkg.renamed import helper\ndef test_helper():\n    return helper()\n'
    diff += 'diff --git a/tests/test_new.py b/tests/test_new.py\nnew file mode 100644\n' + ''.join(difflib.unified_diff(
        [], new.splitlines(True), fromfile='/dev/null', tofile='b/tests/test_new.py'))
    before = digest(tenant)
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': diff})
    assert r.status_code == 200, r.text
    d = r.json()
    assert 'src/pkg/a.py' not in d['final_file_hashes'] and 'src/pkg/b.py' not in d['final_file_hashes']
    assert {'relationship': 'CALLS', 'source': 'tests/test_new.py:test_helper', 'target': 'src/pkg/renamed.py:helper'} in d['added_dependencies']
    assert d['recommended_pytest_command'] == 'pytest -- tests/test_new.py'
    assert 'src/pkg/c.py' in d['pre_patch_impacted_files']
    assert digest(tenant) == before


def test_added_file_resolves_previously_unresolved_imports_and_calls(client, ingested):
    tenant, _, _ = ingested
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': {
        'src/pkg/b.py': 'from pkg.new import helper\ndef run():\n    return helper()\n',
        'src/pkg/new.py': 'def helper():\n    return 7\n'}})
    assert r.status_code == 200, r.text
    assert {'relationship': 'CALLS', 'source': 'src/pkg/b.py:run', 'target': 'src/pkg/new.py:helper'} in r.json()['added_dependencies']


@pytest.mark.parametrize('bodies', [
    {'../escape.py': 'x=1'}, {'/tmp/escape.py': 'x=1'}, {'bad.py': 'def broken(:'},
    {'missing.py': None}, {'file.js': 'x=1'}, {'.git/hook.py': 'x=1'},
])
def test_invalid_final_states_fail_closed(client, ingested, bodies):
    tenant, _, _ = ingested
    before = digest(tenant)
    graphs = set(db_manager.list_tenant_graphs())
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': bodies})
    assert r.status_code == 422, r.text
    assert digest(tenant) == before and set(db_manager.list_tenant_graphs()) == graphs


def test_unified_diff_exact_baseline_and_deleted_test_not_recommended(client, ingested):
    tenant, _, root = ingested
    source = (root/'src/pkg/b.py').read_text()
    diff = ''.join(difflib.unified_diff(source.splitlines(True), ['def run():\n','    return 9\n'],
                                      fromfile='a/src/pkg/b.py', tofile='b/src/pkg/b.py'))
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': diff})
    assert r.status_code == 200, r.text
    bad = diff.replace('from pkg.a import helper', 'from wrong import helper')
    assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': bad}).status_code == 422
    assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant}).status_code == 422
    assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': diff, 'file_bodies': {'x.py': ''}}).status_code == 422


def test_pure_rename_overwrite_and_quoted_paths_rejected(client, ingested):
    tenant, _, _ = ingested
    for old, new in [('src/pkg/a.py','src/pkg/b.py'), ('../escape.py','src/pkg/new.py')]:
        patch = f'diff --git a/{old} b/{new}\nsimilarity index 100%\nrename from {old}\nrename to {new}\n'
        assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': patch}).status_code == 422


def test_async_signature_change_and_capture_integrity_guard(client, ingested):
    tenant, _, _ = ingested
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': {'src/pkg/a.py': 'async def helper():\n    return 1\n'}})
    assert r.status_code == 200, r.text
    assert 'src/pkg/a.py:helper' in r.json()['removed_or_signature_changed_symbols']
    db_manager.get_graph(tenant).query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.sha256='mismatch'")
    assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': {'src/pkg/a.py': 'x=1\n'}}).status_code == 409


def test_symlink_file_mode_rejected_and_pre_state_test_union(client, ingested):
    tenant, _, _ = ingested
    patch = 'diff --git a/link.py b/link.py\nnew file mode 120000\n--- /dev/null\n+++ b/link.py\n@@ -0,0 +1 @@\n+target\n'
    assert client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'unified_diff': patch}).status_code == 422
    graph = db_manager.get_graph(tenant)
    source = 'from pkg.a import helper\ndef test_helper():\n    return helper()\n'
    import hashlib
    graph.query('''CREATE (f:File {path:'tests/test_removed.py',source_text:$text,sha256:$sha})
        WITH f MATCH (a:File {path:'src/pkg/a.py'}) CREATE (f)-[:IMPORTS]->(a)''',
        {'text': source, 'sha': hashlib.sha256(source.encode()).hexdigest()})
    r = client.post('/api/v1/diff/impact', json={'tenant_graph': tenant, 'file_bodies': {
        'src/pkg/a.py': None, 'tests/test_removed.py': None}})
    assert r.status_code == 200, r.text
    assert 'tests/test_removed.py' in r.json()['impacted_test_files']
    assert 'tests/test_removed.py' not in r.json()['recommended_pytest_command']
