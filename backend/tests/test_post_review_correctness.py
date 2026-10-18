"""Native regressions for the post-review correctness batch; no service mocks."""
import asyncio
import hashlib
import subprocess

import pytest
from fastapi import HTTPException
from fastmcp import Client
from app.db.client import db_manager
from app.mcp_server.server import mcp
from app.models import BrainQueryRequest, DiffImpactRequest
from app.services.company_brain import ask_brain
from app.services.context_locator import locate_context, symbol_source
from app.services.diff_impact import simulate_diff
from app.services.test_selection import is_test_file, selection_receipt
from test_real_world_repos import client, local_repo, ingested


@pytest.fixture
def unicode_source(ingested):
    tenant, _, _ = ingested
    text = 'def large():\n    return "' + 'é🙂漢' * 5000 + '"\n'
    digest = hashlib.sha256(text.encode()).hexdigest()
    graph = db_manager.get_graph(tenant)
    graph.query('CREATE (:File {path:$path,source_text:$text,sha256:$sha,source_revision:$revision})',
                {'path':'unicode.py','text':text,'sha':digest,'revision':'a'*40})
    return tenant, graph, text, digest


@pytest.mark.parametrize('symbol', ['__module__', 'large'])
@pytest.mark.parametrize('budget', [127, 7999, 8000])
def test_large_unicode_reconstruction_is_gapless_and_pinned(unicode_source, symbol, budget):
    tenant, _, text, digest = unicode_source
    parts, offset = [], 0
    while True:
        page = symbol_source(tenant,'unicode.py',symbol,offset,budget,
                             digest if offset else None,'a'*40 if offset else None)
        assert page['range_start_byte'] == offset
        assert page['returned_source_bytes'] == len(page['source'].encode()) <= budget
        assert page['range_end_byte'] - offset == len(page['source'].encode())
        assert page['source_revision'] == 'a'*40 and page['source_sha256'] == digest
        parts.append(page['source'])
        if page['next_start_byte'] is None:
            assert not page['has_more']
            break
        assert page['next_start_byte'] > offset
        offset = page['next_start_byte']
    assert ''.join(parts) == text
    assert hashlib.sha256(''.join(parts).encode()).hexdigest() == digest


def test_continuation_rejects_missing_pins_and_invalid_boundaries(unicode_source):
    tenant, _, text, digest = unicode_source
    middle = text.encode().index('🙂'.encode()) + 1
    cases = [(-1,8000,None,None), (1,8000,None,None),
             (middle,8000,digest,'a'*40), (len(text.encode())+1,8000,digest,'a'*40),
             (0,3,None,None),(0,8001,None,None)]
    for offset, budget, sha, revision in cases:
        with pytest.raises(HTTPException) as err:
            symbol_source(tenant,'unicode.py','__module__',offset,budget,sha,revision)
        assert err.value.status_code == 422


@pytest.mark.parametrize('change', ['revision', 'content'])
def test_continuation_refuses_mixed_revision_or_content(unicode_source, change):
    tenant, graph, text, digest = unicode_source
    first = symbol_source(tenant,'unicode.py','__module__')
    if change == 'revision':
        graph.query("MATCH (f:File {path:'unicode.py'}) SET f.source_revision=$revision", {'revision':'b'*40})
    else:
        new_text = text + '# changed\n'
        graph.query("MATCH (f:File {path:'unicode.py'}) SET f.source_text=$text,f.sha256=$sha",
                    {'text':new_text,'sha':hashlib.sha256(new_text.encode()).hexdigest()})
    with pytest.raises(HTTPException) as err:
        symbol_source(tenant,'unicode.py','__module__',first['next_start_byte'],8000,digest,'a'*40)
    assert err.value.status_code == 409


def test_rest_and_actual_mcp_expose_source_continuation(client, unicode_source):
    tenant, _, _, digest = unicode_source
    args = {'tenant_graph':tenant,'file_path':'unicode.py','symbol_name':'__module__','max_bytes':127}
    first = client.get('/api/v1/context/symbol-source',params=args)
    assert first.status_code == 200
    args.update(start_byte=first.json()['next_start_byte'],expected_source_sha256=digest,expected_source_revision='a'*40)
    response = client.get('/api/v1/context/symbol-source',params=args)
    assert response.status_code == 200
    async def run():
        async with Client(mcp) as connection:
            page = await connection.call_tool('get_symbol_source',args)
            assert not page.is_error
            assert page.data['source'] == response.json()['source']
    asyncio.run(run())


@pytest.mark.parametrize('path,expected', [('test_orders.py',True),('orders_test.py',True),
    ('tests/orders_test.py',True),('nested/test_orders.py',True),('tests/helpers.py',False),
    ('tests/conftest.py',False),('test_data/helper.py',False),('tests/test_notes.txt',False)])
def test_default_pytest_filename_contract(path, expected):
    assert is_test_file(path) is expected


def test_deleted_tests_and_custom_collection_are_explicit():
    data = selection_receipt(['orders_test.py','tests/test_old.py','tests/helpers.py'],['tests/test_old.py'])
    assert data['candidate_test_files'] == ['orders_test.py','tests/test_old.py']
    assert data['runnable_candidate_test_files'] == ['orders_test.py']
    assert data['deleted_candidate_test_files'] == ['tests/test_old.py']
    assert data['custom_collection'] == 'UNKNOWN' and data['safe_to_skip_other_tests'] is False


def test_policy_current_candidates_cannot_be_starved_by_obsolete_neighbors(ingested):
    tenant, _, _ = ingested
    graph = db_manager.get_graph(tenant)
    graph.query('MATCH (d:Decision) DETACH DELETE d')
    question = 'timeout and connection policy'
    for index in range(8):
        graph.query("""MATCH (f:File {path:'src/pkg/a.py'}) CREATE (:Decision {
            id:$id,rule:$rule,status:'SUPERSEDED',embedding:vecf32($embedding)})-[:GOVERNS]->(f)""",
            {'id':f'obsolete_{index}','rule':question,'embedding':db_manager.embed_text(question)})
    graph.query("""MATCH (f:File {path:'src/pkg/b.py'}) CREATE (:Decision {
        id:'current',rule:'Use a bounded connection timeout',status:'ACTIVE',embedding:vecf32($embedding)})-[:GOVERNS]->(f)""",
        {'embedding':db_manager.embed_text('Use a bounded connection timeout')})
    legacy = graph.ro_query("""CALL db.idx.vector.queryNodes('Decision','embedding',4,vecf32($query))
        YIELD node,score RETURN node.status""", {'query':db_manager.embed_text(question)}).result_set
    assert len(legacy) == 4 and all(row[0] == 'SUPERSEDED' for row in legacy)
    answer = ask_brain(BrainQueryRequest(tenant_graph=tenant,question=question))
    assert answer.file_path == 'src/pkg/b.py'
    assert [r['id'] for r in answer.active_decisions] == ['current']


def test_discovery_and_diff_classify_helpers_suffix_and_deleted_tests(ingested):
    tenant, _, _ = ingested
    graph = db_manager.get_graph(tenant)
    source = 'from pkg.a import helper\ndef check():\n    return helper()\n'
    for path in ['tests/test_order.py','orders_test.py','tests/helpers.py']:
        graph.query("""MATCH (a:File {path:'src/pkg/a.py'}) CREATE (f:File {
            path:$path,source_text:$source,sha256:$sha,source_revision:$revision})-[:IMPORTS]->(a)""",
            {'path':path,'source':source,'sha':hashlib.sha256(source.encode()).hexdigest(),'revision':'a'*40})
    result = locate_context(tenant,'helper',8192)
    assert set(result['candidate_test_files']) == {'tests/test_order.py','orders_test.py'}
    assert result['test_collection']['custom_collection'] == 'UNKNOWN'
    impact = simulate_diff(DiffImpactRequest(tenant_graph=tenant,file_bodies={
        'src/pkg/a.py':'def helper():\n    return 2\n', 'tests/test_order.py':None}))
    assert set(impact['impacted_test_files']) == {'tests/test_order.py','orders_test.py'}
    assert impact['test_collection']['deleted_candidate_test_files'] == ['tests/test_order.py']
    assert 'tests/test_order.py' not in impact['recommended_pytest_command']
    assert 'orders_test.py' in impact['recommended_pytest_command']


def test_exact_path_and_symbol_use_bounded_inventory_with_lexical_fallback(ingested):
    tenant, _, _ = ingested
    path = locate_context(tenant, 'src/pkg/a.py', 8192)
    assert path['coverage']['entry_strategy'] == 'EXACT_PATH'
    assert path['coverage']['entry_inventory_files'] == 1
    assert path['entry_points'][0]['path'] == 'src/pkg/a.py'
    symbol = locate_context(tenant, 'helper', 8192)
    assert symbol['coverage']['entry_strategy'] == 'EXACT_SYMBOL'
    assert symbol['entry_points'][0]['path'] == 'src/pkg/a.py'
    assert {'src/pkg/b.py','src/pkg/c.py'} <= {r['path'] for r in symbol['related_importers']}
    qualified = locate_context(tenant, 'src/pkg/a.py:helper', 8192)
    assert qualified['coverage']['entry_strategy'] == 'EXACT_SYMBOL'
    assert qualified['entry_points'][0]['path'] == 'src/pkg/a.py'
    prose = locate_context(tenant, 'helper a', 8192)
    assert prose['coverage']['entry_strategy'] == 'LEXICAL_INVENTORY_FALLBACK'
    assert prose['entry_points']
