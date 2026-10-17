"""Real API + FastMCP protocol, source/policy staleness and shared event storage."""
import asyncio
import hashlib
import json
import pytest
from fastmcp import Client
from app.db.client import db_manager
from app.mcp_server.server import mcp
from test_real_world_repos import client, local_repo, ingested


def sha(tenant, path='src/pkg/a.py'):
    return db_manager.get_graph(tenant).ro_query('MATCH (f:File {path:$path}) RETURN f.sha256', {'path': path}).result_set[0][0]


def save(client, tenant):
    response = client.post('/api/v1/memory/findings', json={'tenant_graph': tenant,
        'summary': 'helper source evidence', 'evidence_note': 'AST inspection: helper returns 1. No tests executed by this tool.',
        'supporting_file_shas': {'src/pkg/a.py': sha(tenant)}})
    assert response.status_code == 200, response.text
    return response.json()


def test_context_bounded_exact_payload_and_symbol_source(client, ingested):
    tenant, _, _ = ingested
    r = client.get('/api/v1/context/locate', params={'tenant_graph': tenant, 'query': 'helper a', 'budget_bytes': 2048})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['payload_bytes'] == len(r.content) <= 2048
    assert data['payload_token_equivalents'] == len(r.content.decode()) // 4
    assert data['entry_points'] and data['model_calls'] == 0
    assert 'PINNED_SNAPSHOT' in data['workspace_freshness']
    r = client.get('/api/v1/context/symbol-source', params={'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': 'helper'})
    assert r.status_code == 200, r.text
    assert r.json()['source'] == 'def helper():\n    return 1\n'
    assert (r.json()['start_line'], r.json()['end_line']) == (2, 3)
    assert r.json()['source_sha256'] == sha(tenant)


def test_memory_persists_recalls_and_stales_on_file_change(client, ingested):
    tenant, _, _ = ingested
    saved = save(client, tenant)
    assert saved['verification_basis'] == 'AGENT_REPORTED_EVIDENCE_NOT_INDEPENDENTLY_EXECUTED'
    response = client.get('/api/v1/memory/findings', params={'tenant_graph': tenant, 'query': 'helper'})
    assert response.status_code == 200, response.text
    assert response.json()['findings'][0]['id'] == saved['id']
    graph = db_manager.get_graph(tenant)
    graph.query('MATCH (f:File {path:$path}) SET f.sha256=$sha', {'path': 'src/pkg/a.py', 'sha': hashlib.sha256(b'changed').hexdigest()})
    response = client.get('/api/v1/memory/findings', params={'tenant_graph': tenant, 'query': 'helper'})
    assert not response.json()['findings'] and response.json()['stale_findings_in_scan'] == 1
    stale = client.get('/api/v1/memory/findings', params={'tenant_graph': tenant, 'include_stale': True}).json()['findings'][0]
    assert stale['stale_reasons'] == ['SUPPORTING_FILE_CHANGED_OR_MISSING']


def test_memory_stales_on_current_policy_change(client, ingested):
    tenant, _, _ = ingested
    save(client, tenant)
    graph = db_manager.get_graph(tenant)
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) CREATE (:Decision {id:'test_memory_policy',status:'ACTIVE',rule:'Read only'})-[:GOVERNS]->(f)")
    data = client.get('/api/v1/memory/findings', params={'tenant_graph': tenant, 'include_stale': True}).json()
    assert data['findings'][0]['status'] == 'STALE'
    assert 'GOVERNING_POLICY_CHANGED' in data['findings'][0]['stale_reasons']


def test_wrong_or_absent_evidence_hash_rejected(client, ingested):
    tenant, _, _ = ingested
    for evidence in ({}, {'src/pkg/a.py': 'wrong'}, {'missing.py': 'not-real'}):
        r = client.post('/api/v1/memory/findings', json={'tenant_graph': tenant, 'summary': 'test', 'evidence_note': 'test', 'supporting_file_shas': evidence})
        assert r.status_code in (409, 422), r.text
    assert client.get('/api/v1/memory/findings', params={'tenant_graph': tenant}).json()['findings'] == []


def test_actual_mcp_invocations_visible_via_rest_without_private_arguments(client, ingested):
    tenant, _, _ = ingested
    secret_marker = 'PRIVATE_NOTE_DO_NOT_LOG_123'
    async def run():
        async with Client(mcp) as c:
            names = {t.name for t in await c.list_tools()}
            assert {'locate_context', 'get_symbol_source', 'record_verified_finding',
                    'recall_task_memory', 'simulate_diff_impact', 'discover_repositories',
                    'inspect_repository_snapshot'} <= names
            context = await c.call_tool('locate_context', {'tenant_graph': tenant, 'query': 'helper'})
            assert not context.is_error, context
            source = await c.call_tool('get_symbol_source', {'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': 'helper'})
            assert not source.is_error
            saved = await c.call_tool('record_verified_finding', {'tenant_graph': tenant,
                'summary': 'helper observation', 'evidence_note': secret_marker,
                'supporting_file_shas': {'src/pkg/a.py': sha(tenant)}})
            assert not saved.is_error
            recalled = await c.call_tool('recall_task_memory', {'tenant_graph': tenant, 'query': 'helper'})
            assert not recalled.is_error and recalled.data['findings']
            diff = await c.call_tool('simulate_diff_impact', {'tenant_graph': tenant, 'file_bodies': {'src/pkg/a.py': 'def helper():\n    return 8\n'}})
            assert not diff.is_error and diff.data['sandbox_cleaned_up']
    asyncio.run(run())
    r = client.get('/api/v1/activity', params={'tenant_graph': tenant})
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data['events']) == 5
    assert {e['tool_name'] for e in data['events']} == {'locate_context', 'get_symbol_source', 'record_verified_finding', 'recall_task_memory', 'simulate_diff_impact'}
    assert all(e['outcome'] == 'SUCCESS' and e['duration_ms'] >= 0 and e['result_bytes'] > 0 for e in data['events'])
    assert secret_marker not in r.text and 'def helper' not in r.text
    first = client.get('/api/v1/activity', params={'tenant_graph': tenant, 'limit': 2}).json()
    second = client.get('/api/v1/activity', params={'tenant_graph': tenant, 'limit': 2, 'cursor': first['next_cursor']}).json()
    assert not {e['id'] for e in first['events']} & {e['id'] for e in second['events']}
    assert client.get('/api/v1/activity', params={'tenant_graph': tenant, 'cursor': 'invalid'}).status_code == 422


def test_failed_tool_is_observed_without_logging_exception_text(client, ingested):
    tenant, _, _ = ingested
    async def run():
        async with Client(mcp) as c:
            result = await c.call_tool('get_symbol_source', {'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': 'missing'}, raise_on_error=False)
            assert result.is_error
    asyncio.run(run())
    data = client.get('/api/v1/activity', params={'tenant_graph': tenant}).json()
    assert data['events'][0]['outcome'] == 'ERROR' and data['events'][0]['error_kind'] == 'HTTPException'


def test_empty_query_unknown_tenant_and_source_budget_validation(client, ingested):
    tenant, _, _ = ingested
    for query, budget in [('', 4096), ('helper', 1), ('helper', 8193)]:
        assert client.get('/api/v1/context/locate', params={'tenant_graph': tenant, 'query': query, 'budget_bytes': budget}).status_code == 422
    assert client.get('/api/v1/activity', params={'tenant_graph': 'repo_missing_invalid'}).status_code == 404


def test_repository_constraint_change_stales_finding_without_fake_governance(client, ingested):
    tenant, _, _ = ingested
    graph = db_manager.get_graph(tenant)
    graph.query("CREATE (:Decision {id:'constraint_1',rule:'Python >=3.11',scope:'repository',source_type:'REPO_EXTRACTED_RULE',status:'EXTRACTED'})")
    save(client, tenant)
    graph.query("MATCH (d:Decision {id:'constraint_1'}) SET d.rule='Python >=3.12'")
    data = client.get('/api/v1/memory/findings', params={'tenant_graph': tenant, 'include_stale': True}).json()
    assert data['findings'][0]['stale_reasons'] == ['GOVERNING_POLICY_CHANGED']


def test_tool_events_are_per_tenant_and_context_measurement_is_exact(client, ingested):
    tenant, _, _ = ingested
    # No calls were made in this fixture; previous tenants' logs do not leak.
    assert client.get('/api/v1/activity', params={'tenant_graph': tenant}).json()['events'] == []
    for budget in (2048, 4096, 8192):
        r = client.get('/api/v1/context/locate', params={'tenant_graph': tenant, 'query': 'helper', 'budget_bytes': budget})
        assert r.status_code == 200, r.text
        assert len(r.content) == r.json()['payload_bytes'] <= budget


def test_context_prioritizes_requested_symbol_beyond_first_five(client, ingested):
    tenant, _, _ = ingested
    graph = db_manager.get_graph(tenant)
    path = 'src/pkg/many.py'
    names = [f'decoy_{i}' for i in range(8)] + ['needle_target']
    source = '\n'.join(f'def {name}():\n    return {i}\n' for i, name in enumerate(names))
    graph.query('CREATE (:File {path:$path,source_text:$source,sha256:$sha,source_utf8_bytes:$size,pagerank:0})',
                {'path': path, 'source': source, 'sha': hashlib.sha256(source.encode()).hexdigest(), 'size': len(source.encode())})
    for i, name in enumerate(names):
        graph.query('MATCH (f:File {path:$path}) CREATE (f)-[:DEFINES]->(:Function {name:$name,qualified_name:$qualified,signature:$signature,start_line:$line,end_line:$end})',
                    {'path': path, 'name': name, 'qualified': path+':'+name,
                     'signature': name+'()', 'line': i*3+1, 'end': i*3+2})
    response = client.get('/api/v1/context/locate', params={'tenant_graph': tenant, 'query': 'needle_target', 'budget_bytes': 4096})
    assert response.status_code == 200, response.text
    data = response.json()
    entry = next(e for e in data['entry_points'] if e['path'] == path)
    assert entry['symbols'][0]['name'] == path+':needle_target'
    assert len(entry['symbols']) == 5
    assert data['coverage']['truncated'] is True
    assert data['payload_bytes'] == len(response.content) <= 4096


def test_module_source_includes_imports_and_hash(client, ingested):
    tenant, _, _ = ingested
    data = client.get('/api/v1/context/symbol-source', params={
        'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': '__module__'}).json()
    original = db_manager.get_graph(tenant).ro_query(
        'MATCH (f:File {path:$path}) RETURN f.source_text', {'path': 'src/pkg/a.py'}).result_set[0][0]
    assert data['source'] == original
    assert data['start_line'] == 1
    assert data['source_sha256'] == hashlib.sha256(original.encode()).hexdigest()
    assert data['qualified_name'].endswith(':__module__')
    assert data['truncated'] is False


def test_module_source_bounded_and_hash_checked(client, ingested):
    tenant, _, _ = ingested
    text = '#' + 'é' * 6000 + '\n'
    graph = db_manager.get_graph(tenant)
    graph.query('MATCH (f:File {path:$path}) SET f.source_text=$text, f.sha256=$sha',
        {'path': 'src/pkg/a.py', 'text': text, 'sha': hashlib.sha256(text.encode()).hexdigest()})
    params = {'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': '__module__'}
    response = client.get('/api/v1/context/symbol-source', params=params)
    assert response.status_code == 200
    data = response.json()
    assert data['truncated'] and len(data['source'].encode()) <= 8000
    assert data['source_bytes'] == len(text.encode())
    assert data['returned_source_bytes'] == 7999
    assert '\ufffd' not in data['source']
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.sha256='invalid'")
    assert client.get('/api/v1/context/symbol-source', params=params).status_code == 409


def test_missing_symbol_explains_captured_module_read(client, ingested):
    tenant, _, _ = ingested
    response = client.get('/api/v1/context/symbol-source', params={
        'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': 'missing'})
    assert response.status_code == 404
    assert '__module__' in response.json()['detail']


@pytest.mark.parametrize('text', ['', 'value = 1', 'value = 1\n'])
def test_module_line_counts_for_empty_and_newline_edges(client, ingested, text):
    tenant, _, _ = ingested
    db_manager.get_graph(tenant).query(
        'MATCH (f:File {path:$path}) SET f.source_text=$text, f.sha256=$sha',
        {'path': 'src/pkg/a.py', 'text': text, 'sha': hashlib.sha256(text.encode()).hexdigest()})
    response = client.get('/api/v1/context/symbol-source', params={
        'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': '__module__'})
    assert response.status_code == 200
    data = response.json()
    assert data['source'] == text and not data['truncated']
    assert data['end_line'] == len(text.splitlines())


def test_ambiguous_symbol_still_requires_qualification(client, ingested):
    tenant, _, _ = ingested
    text = 'def duplicate():\n    return 1\ndef duplicate():\n    return 2\n'
    db_manager.get_graph(tenant).query(
        'MATCH (f:File {path:$path}) SET f.source_text=$text, f.sha256=$sha',
        {'path': 'src/pkg/a.py', 'text': text, 'sha': hashlib.sha256(text.encode()).hexdigest()})
    response = client.get('/api/v1/context/symbol-source', params={
        'tenant_graph': tenant, 'file_path': 'src/pkg/a.py', 'symbol_name': 'duplicate'})
    assert response.status_code == 409


def test_parser_constructs_qualified_symbol_contract():
    from app.ingestion.ast_parser import parse_python_source
    parsed = parse_python_source('def f():\n    return 1\nclass C:\n    def method(self):\n        pass\n', 'module.py')
    assert parsed['functions'] and parsed['classes']
    assert all(':' in s['qualified_name'] for s in parsed['functions'] + parsed['classes'])
