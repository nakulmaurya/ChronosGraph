"""Real Git/FalkorDB tests, with explicit externally ingested repository coverage.

No mocks. Unit fixtures are disposable local Git repos/graphs and are removed.
External cases run when both CLI-ingested tenants exist; no silent network cloning.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import math
import subprocess
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo, backfill_history, snapshot_stats, repository_source
from app.main import app
from app.mcp_server.server import mcp
from app.services.common import read, tenant_exists, tenant_lock

EXTERNAL = ('repo_falkordb_code_graph','repo_mcp_python_sdk')


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def local_repo(tmp_path):
    root=tmp_path/'git-source';root.mkdir()
    subprocess.run(['git','init','--quiet',str(root)],check=True)
    files={'src/pkg/__init__.py':'', 'src/pkg/a.py':'raise RuntimeError("NEVER EXECUTE SOURCE")\ndef helper():\n    return 1\ndef run():\n    return helper()\n',
      'src/pkg/b.py':'from pkg.a import helper\ndef run():\n    return helper()\n',
      'src/pkg/c.py':'from pkg.b import run\ndef action():\n    return run()\n',
      'syntax_fixture.py':'def broken(:\n', '.venv/skip.py':'x=1\n', 'node_modules/skip.py':'x=1\n'}
    for path,text in files.items():
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Local Test Author','-c','user.email=fixture@example.invalid','commit','--quiet','-m','Real disposable fixture commit'],check=True)
    return root


@pytest.fixture
def ingested(local_repo):
    tenant='repo_test_'+uuid.uuid4().hex
    try:
        stats=ingest_repo(str(local_repo),tenant,seed_demo_policies=True)
        yield tenant,stats,local_repo
    finally:
        if tenant in db_manager.list_tenant_graphs():
            db_manager.get_graph(tenant).delete()


def test_local_git_ingestion_is_ast_only_normalized_and_idempotency_safe(ingested):
    tenant,stats,source=ingested
    assert stats['files']==5 and stats['functions']==4 and stats['resolved_calls']>=1
    assert len(stats['parse_errors'])==1
    graph=db_manager.get_graph(tenant)
    assert graph.ro_query('MATCH (f:File) RETURN f.path').result_set
    ranks=graph.ro_query('MATCH (f:File) RETURN f.pagerank').result_set
    assert math.isclose(sum(r[0] for r in ranks),1.0,abs_tol=1e-6)
    assert all(r[0]>=0 for r in ranks)
    assert graph.ro_query('MATCH (:File)-[r:IMPORTS]->(:File) RETURN count(r)').result_set[0][0]>=2
    assert graph.ro_query("MATCH (p:PullRequest {source_type:'GIT_COMMIT_HISTORY'}) RETURN p.number,p.record_kind,p.commit_sha").result_set[0][0]<0
    before=snapshot_stats(tenant)
    with pytest.raises(ValueError,match='already exists'):
        ingest_repo(str(source),tenant)
    assert snapshot_stats(tenant)==before


def test_append_only_history_backfill_is_idempotent(ingested):
    tenant,stats,source=ingested
    before=snapshot_stats(tenant)
    first=backfill_history(str(source),tenant,file_paths=['src/pkg/a.py'])
    second=backfill_history(str(source),tenant,file_paths=['src/pkg/a.py'])
    assert first==second and first['history_scope']=='path_targeted'
    assert snapshot_stats(tenant)==before
    with pytest.raises(ValueError,match='existing file paths'):
        backfill_history(str(source),tenant,file_paths=['absent.py'])


def test_dynamic_tenant_registration_and_safe_unknown_404(client,ingested):
    tenant,_,_=ingested
    assert tenant_exists(tenant)==tenant
    catalog=client.get('/api/v1/tenants').json()
    row=next(r for r in catalog if r['tenant_graph']==tenant)
    assert row['edge_count']>0 and row['indexed_record_count']==1 and row['preset_files']
    assert row['pull_requests'][0]['source_type']=='GIT_COMMIT_HISTORY'
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert len({id(x) for x in pool.map(tenant_lock,[tenant]*32)})==1
    before=set(db_manager.list_tenant_graphs())
    for name in ['repo_missing_'+uuid.uuid4().hex,'repo_UPPER','repo_bad-name','sandbox_pr_invalid']:
        assert client.get('/api/v1/subgraph',params={'tenant_graph':name}).status_code==404
    assert set(db_manager.list_tenant_graphs())==before


def test_unseeded_and_incomplete_graphs_remain_404(client):
    tenant='repo_test_'+uuid.uuid4().hex
    graph=db_manager.get_graph(tenant)
    try:
        graph.query("CREATE (:RepoMetadata {status:'INGESTING'}),(:File {path:'not_ready.py'})")
        assert client.get('/api/v1/subgraph',params={'tenant_graph':tenant}).status_code==404
        assert tenant not in {r['tenant_graph'] for r in client.get('/api/v1/tenants').json()}
    finally:
        graph.delete()


@pytest.mark.parametrize('source',['ext::danger','ssh://example.invalid/repo','https://user:secret@example.invalid/repo'])
def test_ingestor_refuses_credential_and_helper_urls(source):
    with pytest.raises(ValueError,match='credential-free'):
        repository_source(source)


@pytest.fixture(params=EXTERNAL)
def external(request):
    tenant=request.param
    if tenant not in db_manager.list_tenant_graphs():
        pytest.skip('Run explicit CLI ingestion for '+tenant+' before the external suite')
    policies,_=read(tenant,"MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File) RETURN f.path AS path ORDER BY f.pagerank DESC LIMIT 1")
    assert policies, 'Use --seed-demo-policies for the explicit external test scenario'
    return tenant,policies[0]['path']


def test_external_ast_pagerank_and_real_git_file_evidence(external):
    tenant,path=external
    stats=snapshot_stats(tenant)
    assert stats['files']>=10 and stats['functions']>10 and stats['edges']>10
    ranks,_=read(tenant,'MATCH (f:File) RETURN f.pagerank AS rank')
    assert all(math.isfinite(r['rank']) and r['rank']>=0 for r in ranks)
    assert math.isclose(sum(r['rank'] for r in ranks),1.0,abs_tol=1e-6)
    evidence,_=read(tenant,'''MATCH (c:Contributor)-[:AUTHORED]->(p:PullRequest)-[m:MODIFIES]->(f:File {path:$path})
      RETURN c.identity_kind AS identity,p.source_type AS source,p.commit_sha AS sha,p.url AS url,m.source_type AS edge_source''',{'path':path})
    assert evidence and all(r['source']=='GIT_COMMIT_HISTORY' and r['edge_source']=='GIT_COMMIT_HISTORY' and len(r['sha'])==40 and '/commit/' in r['url'] for r in evidence)


def test_external_rest_three_tracks_and_override_invalidation(client,external):
    tenant,path=external
    graph=db_manager.get_graph(tenant)
    snapshot,_=read(tenant,'MATCH (d:Decision)-[:GOVERNS]->(:File {path:$path}) RETURN d',{'path':path})
    originals=[dict(r['d'].properties) for r in snapshot];created=[]
    try:
        audit=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':[path]})
        assert audit.status_code==200,audit.text
        d=audit.json();assert d['sandbox_cleaned_up'] and d['recommended_reviewers'] and d['sandbox_graph_name'] not in db_manager.list_tenant_graphs()
        multi,_=read(tenant,'MATCH (a:File)-[:IMPORTS*2..3]->(f:File {path:$path}) WHERE a<>f RETURN DISTINCT a.path AS path',{'path':path})
        assert multi, 'Chosen real high-rank file must have actual multi-hop import evidence'
        assert set(r['path'] for r in multi)<=set(d['impacted_files'])
        brain=client.post('/api/v1/track3/ask-brain',json={'tenant_graph':tenant,'file_path':path,'question':'current rule'})
        assert brain.status_code==200 and brain.json()['active_decisions'] and brain.json()['superseded_decisions'] and brain.json()['top_experts']
        scenario='T05 external policy triage '+path+' '+uuid.uuid4().hex
        payload={'tenant_graph':tenant,'issue_description':scenario}
        cold=client.post('/api/v1/track2/investigate',json=payload);assert cold.status_code==200,cold.text
        warm=client.post('/api/v1/track2/investigate',json={**payload,'execution_mode':'compiled_playbook'})
        assert warm.status_code==200,warm.text
        assert cold.json()['total_steps_executed']==5 and warm.json()['total_steps_executed']==3
        assert sum(n['status']=='DEAD_END' for n in cold.json()['subgraph']['nodes'])==2
        assert not any(n['status']=='DEAD_END' for n in warm.json()['subgraph']['nodes'])
        states,_=read(tenant,'MATCH (:Investigation {id:$id})-[:HAS_STATE]->(s:StateNode) RETURN s.id AS id',{'id':cold.json()['investigation_id']})
        assert len(states)==6
        override=client.post('/api/v1/track3/override-policy',json={'tenant_graph':tenant,'target_file_path':path,'scope_symbol':'module_root',
          'new_rule_text':'T05 local verification: retain bounded read-only discovery.','rationale':'Explicit local test, not an upstream rule.'})
        assert override.status_code==200,override.text
        created += [r['id'] for r in override.json()['active_decisions'] if r['id'] not in {p['id'] for p in originals}]
        assert len(override.json()['superseded_decisions'])>=2
        assert client.post('/api/v1/track2/investigate',json={**payload,'execution_mode':'compiled_playbook'}).status_code==409
    finally:
        for ident in created:
            graph.query('MATCH (d:Decision {id:$id}) DETACH DELETE d',{'id':ident})
        for p in originals:
            graph.query('MATCH (d:Decision {id:$id}) SET d.status=$status,d.valid_to=$vt,d.recorded_to=$rt',{'id':p['id'],'status':p['status'],'vt':p.get('valid_to'),'rt':p.get('recorded_to')})


def test_external_five_fastmcp_tools_via_protocol(external):
    tenant,path=external
    graph=db_manager.get_graph(tenant)
    originals=graph.ro_query('MATCH (d:Decision)-[:GOVERNS]->(:File {path:$path}) RETURN d',{'path':path}).result_set
    snapshot=[dict(r[0].properties) for r in originals]; created=[]
    async def exercise():
        async with Client(mcp) as c:
            assert len(await c.list_tools())==5
            a=await c.call_tool('simulate_pr_blast_radius',{'modified_files':[path],'tenant_graph':tenant});assert not a.is_error and a.data['sandbox_cleaned_up']
            b=await c.call_tool('query_bitemporal_decisions',{'question':'current rule','file_path':path,'tenant_graph':tenant});assert not b.is_error and b.data['active_decisions']
            o=await c.call_tool('find_true_code_owners',{'file_path':path,'tenant_graph':tenant});assert not o.is_error and o.data
            issue='T05 MCP policy '+path+' '+uuid.uuid4().hex
            cold=await c.call_tool('run_or_compile_playbook',{'issue_description':issue,'tenant_graph':tenant});assert not cold.is_error and cold.data['total_steps_executed']==5
            warm=await c.call_tool('run_or_compile_playbook',{'issue_description':issue,'tenant_graph':tenant,'execution_mode':'compiled_playbook'});assert not warm.is_error and warm.data['total_steps_executed']==3
            override=await c.call_tool('record_decision_override',{'target_file_path':path,'tenant_graph':tenant,'scope_symbol':'module_root','new_rule_text':'T05 MCP explicit test rule.','rationale':'Local test; restore afterward.'})
            assert not override.is_error
            created.extend(r['id'] for r in override.data['active_decisions'] if r['id'] not in {p['id'] for p in snapshot})
    try:
        asyncio.run(exercise())
    finally:
        for ident in created: graph.query('MATCH (d:Decision {id:$id}) DETACH DELETE d',{'id':ident})
        for p in snapshot:
            graph.query('MATCH (d:Decision {id:$id}) SET d.status=$s,d.valid_to=$vt,d.recorded_to=$rt',{'id':p['id'],'s':p['status'],'vt':p.get('valid_to'),'rt':p.get('recorded_to')})


def test_ast_patch_clone_only_imports_calls_and_no_execution(client, ingested, tmp_path):
    from app.services.ast_patch import parse_patch, apply_patch
    tenant, _, _ = ingested
    sentinel = tmp_path / 'must-not-exist'
    code = f'''from .a import helper
raise RuntimeError("AST ONLY")
open({str(sentinel)!r}, "w").write("must not run")
def patched():
    return helper()
def caller():
    return patched()
'''
    before = snapshot_stats(tenant)
    with db_manager.ephemeral_sandbox(tenant) as (graph, name, _):
        deps = apply_patch(graph, parse_patch(code, 'src/pkg/b.py'), 'test_patch')
        assert 'src/pkg/a.py' in deps
        assert graph.ro_query("MATCH (:File {path:'src/pkg/b.py'})-[r:IMPORTS]->(:File {path:'src/pkg/a.py'}) RETURN r.source_type").result_set == [['AST_PATCH_SIMULATION']]
        links = graph.ro_query("MATCH (a:Function)-[r:CALLS {source_type:'AST_PATCH_SIMULATION'}]->(b:Function) RETURN a.qualified_name,b.qualified_name").result_set
        assert ['src/pkg/b.py:patched','src/pkg/a.py:helper'] in links
        assert ['src/pkg/b.py:caller','src/pkg/b.py:patched'] in links
        assert not graph.ro_query("MATCH (n {source_type:'SIMULATED_PR_DEPENDENCY'}) RETURN n").result_set
    assert name not in db_manager.list_tenant_graphs()
    response = client.post('/api/v1/track1/sandbox-audit', json={'tenant_graph': tenant,
        'modified_files': ['src/pkg/b.py'], 'proposed_code_patch': code})
    assert response.status_code == 200, response.text
    data = response.json()
    target = next(n for n in data['subgraph']['nodes'] if n['title']=='src/pkg/b.py')
    assert target['metadata']['patch_source_type']=='AST_PATCH_SIMULATION'
    assert target['metadata']['patch_resolved_calls']==2
    assert any(n['title']=='src/pkg/b.py:patched' for n in data['subgraph']['nodes'])
    assert any(e['relationship']=='CALLS' for e in data['subgraph']['edges'])
    assert target['metadata']['audit_target'] is True
    assert data['sandbox_cleaned_up']
    assert snapshot_stats(tenant)==before
    assert not sentinel.exists()
    assert not db_manager.get_graph(tenant).ro_query("MATCH (f:Function {qualified_name:'src/pkg/b.py:patched'}) RETURN f").result_set


@pytest.mark.parametrize('code', ['def broken(:', 'x=1\n'*9000, '\n'.join(f'import unknown_{i}' for i in range(501))], ids=['syntax-error','oversized-input','too-many-observations'])
def test_ast_patch_invalid_or_oversized_rejected_without_leaks(client, ingested, code):
    tenant, _, _ = ingested
    before = set(db_manager.list_tenant_graphs())
    response = client.post('/api/v1/track1/sandbox-audit', json={'tenant_graph': tenant,
        'modified_files': ['src/pkg/b.py'], 'proposed_code_patch': code})
    assert response.status_code==422
    assert set(db_manager.list_tenant_graphs())==before


def test_ast_patch_unresolved_calls_and_legacy_blank_fallback(client, ingested):
    tenant, _, _ = ingested
    body={'tenant_graph':tenant, 'modified_files':['src/pkg/b.py']}
    result=client.post('/api/v1/track1/sandbox-audit',json={**body,
        'proposed_code_patch':'import external_unknown\ndef probe(obj):\n    return obj.helper()\n'}).json()
    target=next(n for n in result['subgraph']['nodes'] if n['title']=='src/pkg/b.py')
    assert target['metadata']['patch_resolved_calls']==0
    assert target['metadata']['patch_unresolved_calls']==1
    assert 'obj.helper' in target['metadata']['patch_unresolved_expressions']
    for patch in [None, '', ' \n ']:
        response=client.post('/api/v1/track1/sandbox-audit',json={**body,'proposed_code_patch':patch})
        assert response.status_code==200
        assert any(n['metadata'].get('source_type')=='SIMULATED_PR_DEPENDENCY' for n in response.json()['subgraph']['nodes'])


def test_ast_patch_commit_scope_and_mcp_input(client, ingested):
    tenant, _, _ = ingested
    record=read(tenant,'MATCH (p:PullRequest)-[:MODIFIES]->(:File) RETURN p.number AS number LIMIT 1')[0][0]
    code='def patch_helper():\n    return 1\ndef patch_caller():\n    return patch_helper()\n'
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,
        'pr_number':record['number'],'proposed_code_patch':code})
    assert response.status_code==200, response.text
    assert any(n['metadata'].get('patch_source_type')=='AST_PATCH_SIMULATION' for n in response.json()['subgraph']['nodes'])
    async def check():
        async with Client(mcp) as c:
            r=await c.call_tool('simulate_pr_blast_radius',{'tenant_graph':tenant,
                'modified_files':['src/pkg/b.py'],'proposed_code_patch':code})
            assert not r.is_error
            assert r.data['sandbox_cleaned_up']
            assert any(n['metadata'].get('patch_source_type')=='AST_PATCH_SIMULATION' for n in r.data['subgraph']['nodes'])
    asyncio.run(check())


def test_external_ast_patch_is_real_and_clone_isolated(client, external):
    tenant,path=external
    before=snapshot_stats(tenant)
    code='def t06_verified_helper():\n    return 1\ndef t06_verified_patch():\n    return t06_verified_helper()\n'
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,
        'modified_files':[path],'proposed_code_patch':code})
    assert response.status_code==200,response.text
    data=response.json()
    target=next(n for n in data['subgraph']['nodes'] if n['metadata'].get('audit_target'))
    assert target['metadata']['patch_resolved_calls']==1
    assert target['metadata']['patch_source_type']=='AST_PATCH_SIMULATION'
    assert data['sandbox_cleaned_up'] and data['recommended_reviewers']
    assert snapshot_stats(tenant)==before

# T-07: real source/diff, static test candidates and deterministic payload size.
def test_t07_strict_diff_reconstruction_and_unicode():
    from app.services.unified_patch import patch_source
    from fastapi import HTTPException
    original = 'def café():\n    return "☕"\n'
    patch = '--- a/pkg.py\n+++ b/pkg.py\n@@ -1,2 +1,2 @@\n def café():\n-    return "☕"\n+    return "茶"\n'
    body, semantics = patch_source(patch,'pkg.py',original)
    assert body == original.replace('☕','茶') and semantics.startswith('VALIDATED_UNIFIED_DIFF')
    for bad in [patch.replace('a/pkg.py','a/other.py'),patch.replace('-1,2','-1,3'),patch+'--- a/other.py\n']:
        with pytest.raises(HTTPException): patch_source(bad,'pkg.py',original)
    with pytest.raises(HTTPException): patch_source(patch,'pkg.py',None)
    with pytest.raises(HTTPException): patch_source(patch,'pkg.py','different\n')
    assert patch_source('x = 1\n','pkg.py')[0]=='x = 1\n'
    assert patch_source('@@ -0,0 +1 @@\n+x=1\n','pkg.py','')[0]=='x=1\n'
    assert patch_source('@@ -1 +0,0 @@\n-x=1\n','pkg.py','x=1\n')[0]==''
    assert patch_source('@@ -1 +1 @@\n-x=1\n\\ No newline at end of file\n+x=2\n\\ No newline at end of file\n','pkg.py','x=1')[0]=='x=2'


def test_t07_diff_audit_test_candidates_and_cleanup(client,ingested):
    import difflib
    tenant,_,root = ingested
    graph=db_manager.get_graph(tenant)
    graph.query('''MATCH (f:File {path:'src/pkg/a.py'})
        CREATE (t:File {path:'tests/test_a.py',source_type:'E2E_TEST_FIXTURE'})-[:IMPORTS]->(f)
        CREATE (:File {path:'tests/test_unrelated.py',source_type:'E2E_TEST_FIXTURE'})''')
    source=(root/'src/pkg/a.py').read_text()
    diff=''.join(difflib.unified_diff(source.splitlines(True),source.replace('return 1','return 2').splitlines(True),
        fromfile='a/src/pkg/a.py',tofile='b/src/pkg/a.py'))
    before=set(db_manager.list_tenant_graphs())
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':['src/pkg/a.py'],'proposed_code_patch':diff})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['sandbox_cleaned_up'] and set(db_manager.list_tenant_graphs())==before
    assert data['impacted_test_files']==['tests/test_a.py'] and data['total_repo_test_files']==2
    assert data['test_suite_reduction_pct']==50 and data['recommended_pytest_command']=='pytest -- tests/test_a.py'
    assert any('helper' in s for s in data['patch_symbols_analyzed'])
    assert data['test_selection_basis']=='BOUNDED_STATIC_CANDIDATES_NOT_SAFE_SKIP_PROOF'
    assert all('source_text' not in n['metadata'] for n in data['subgraph']['nodes'])
    assert graph.ro_query("MATCH (n {source_type:'AST_PATCH_SIMULATION'}) RETURN count(n)").result_set[0][0]==0
    bad=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':['src/pkg/a.py'],
        'proposed_code_patch':diff.replace('return 1','return 999')})
    assert bad.status_code==422 and set(db_manager.list_tenant_graphs())==before


def test_t07_empty_selection_recommends_full_suite(client,ingested):
    tenant,_,_=ingested
    data=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':['src/pkg/a.py']}).json()
    assert data['impacted_test_files']==[] and data['recommended_pytest_command']=='pytest'
    assert data['total_repo_test_files']==0 and data['test_suite_reduction_pct']==0


def test_t07_context_sizes_exact_and_warm_baseline_preserved(client,ingested):
    tenant,_,root=ingested
    body={'tenant_graph':tenant,'issue_description':'Inspect src/pkg/a.py','execution_mode':'cold_multi_agent'}
    cold=client.post('/api/v1/track2/investigate',json=body)
    assert cold.status_code==200,cold.text
    data=cold.json()
    assert data['context_measurement_status']=='MEASURED_SOURCE_CHARS_DIV_4'
    sources=[(root/p).read_text() for p in data['context_candidate_files']]
    assert data['raw_files_context_chars']==sum(len(s) for s in sources)
    assert data['raw_files_context_bytes']==sum(len(s.encode('utf-8')) for s in sources)
    assert data['raw_files_context_tokens']==data['raw_files_context_chars']//4
    preview=data['compiled_context_slice_preview']
    assert data['compiled_slice_context_tokens']==len(preview)//4
    assert data['compiled_slice_context_bytes']==len(preview.encode('utf-8'))
    assert json.loads(preview)['target']=='src/pkg/a.py'
    assert data['model_calls']==data['tokens_used']==data['token_savings_pct']==0
    warm=client.post('/api/v1/track2/investigate',json={**body,'execution_mode':'compiled_playbook'})
    assert warm.status_code==200,warm.text
    for field in ['raw_files_context_tokens','compiled_context_slice_preview','context_candidate_files','context_token_reduction_pct']:
        assert warm.json()[field]==data[field]
    assert data['total_steps_executed']==5 and warm.json()['total_steps_executed']==3


def test_t07_missing_source_sizes_never_uses_loc(ingested):
    from app.services.context_slice import measure_context
    tenant,_,_=ingested
    graph=db_manager.get_graph(tenant)
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) REMOVE f.source_chars")
    result=measure_context(tenant,'src/pkg/a.py',['src/pkg/b.py'])
    assert result['context_measurement_status']=='SOURCE_SIZES_UNAVAILABLE'
    assert result['raw_files_context_tokens']==result['raw_files_context_bytes']==result['context_token_reduction_pct']==0
    assert result['compiled_context_slice_preview']


def test_t07_repository_extraction_is_source_linked_and_preserves_demo(client,ingested):
    from app.ingestion.repo_rules import extract_rules,enrich_repository
    tenant,_,root=ingested
    (root/'pyproject.toml').write_text('[project]\nrequires-python = ">=3.11"\n[tool.mypy]\nstrict = true\n')
    (root/'AGENTS.md').write_text('Queries must be read-only.\nSome nice Python code.\n```\nTests must never run.\n```\n')
    records=extract_rules(root,[])
    assert len(records)==3 and all(r['source_line']>=1 for r in records)
    graph=db_manager.get_graph(tenant)
    before=graph.ro_query("MATCH (d:Decision {source_type:'DEMO_POLICY_SCENARIO'}) RETURN count(d)").result_set
    count=enrich_repository(graph,root,'a'*40,'https://github.com/example/repo',[])
    assert count==3 and enrich_repository(graph,root,'a'*40,'https://github.com/example/repo',[])==3
    assert graph.ro_query("MATCH (d:Decision {source_type:'REPO_EXTRACTED_RULE'}) RETURN count(d)").result_set[0][0]==3
    assert graph.ro_query("MATCH (d:Decision {source_type:'DEMO_POLICY_SCENARIO'}) RETURN count(d)").result_set==before
    response=client.post('/api/v1/track3/ask-brain',json={'tenant_graph':tenant,'question':'Python requirements','file_path':'src/pkg/a.py'})
    assert response.status_code==200,response.text
    constraints=response.json()['repository_constraints']
    assert len(constraints)==3 and all('#L' in r['source_url'] for r in constraints)
    assert all(r['status']=='EXTRACTED' for r in constraints)


def test_t07_utf8_source_accounting_and_missing_diff_baseline(client,ingested):
    from app.ingestion.ast_parser import parse_python_source
    from app.services.context_slice import measure_context
    tenant,_,_=ingested
    text='def café():\n    return "☕"\n'
    item=parse_python_source(text,'unicode.py')['file']
    assert item['source_chars']==len(text) and item['source_utf8_bytes']==len(text.encode('utf-8'))
    graph=db_manager.get_graph(tenant)
    graph.query('MATCH (f:File {path:$path}) SET f.source_chars=$chars,f.source_utf8_bytes=$bytes',
        {'path':'src/pkg/a.py','chars':len(text),'bytes':len(text.encode('utf-8'))})
    result=measure_context(tenant,'src/pkg/a.py',[])
    assert result['raw_files_context_chars']==len(text) and result['raw_files_context_bytes']==len(text.encode('utf-8'))
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) REMOVE f.source_text")
    before=set(db_manager.list_tenant_graphs())
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':['src/pkg/a.py'],
        'proposed_code_patch':'@@ -1 +1 @@\n-x=1\n+x=2\n'})
    assert response.status_code==422 and set(db_manager.list_tenant_graphs())==before


def test_t07_pytest_path_quoting_and_modified_test_included(client,ingested):
    import shlex
    tenant,_,_=ingested
    path="tests/test_a; echo unsafe.py"
    db_manager.get_graph(tenant).query('CREATE (:File {path:$path,source_type:\'E2E_TEST_FIXTURE\'})',{'path':path})
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':[path]})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['impacted_test_files']==[path]
    assert shlex.split(data['recommended_pytest_command'])==['pytest','--',path]


def test_t07_utility_enrichment_idempotent_and_revision_guard(ingested):
    from app.ingestion.ingest_repo import enrich_utility
    tenant,_,root=ingested
    first=enrich_utility(str(root),tenant)
    before=snapshot_stats(tenant)
    assert enrich_utility(str(root),tenant)==first
    assert snapshot_stats(tenant)==before and first['measured_files']==5
    graph=db_manager.get_graph(tenant)
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) SET f.sha256='mismatched'")
    with pytest.raises(ValueError,match='hash mismatch'):
        enrich_utility(str(root),tenant)
    assert snapshot_stats(tenant)==before


# T-08 wiki compiler and compaction-safe context endpoints.
def test_t08_wiki_is_readonly_deterministic_and_links_resolve(client,ingested):
    import re
    tenant,_,_=ingested
    graph=db_manager.get_graph(tenant)
    before=snapshot_stats(tenant)
    result=client.post('/api/v1/ctx/compile-wiki',json={'tenant_graph':tenant})
    assert result.status_code==200,result.text
    d=result.json()
    assert d['model_calls']==0 and not d['exported']
    assert {'index.md','log.md'}<=set(d['pages'])
    assert d['pages']==client.post('/api/v1/ctx/compile-wiki',json={'tenant_graph':tenant}).json()['pages']
    for key,body in d['pages'].items():
        assert body.startswith('---\ntenant: ') and 'provenance_label:' in body
        assert not key.startswith('/') and '..' not in key
        for target in re.findall(r'\[\[([^]|]+)(?:\|[^]]*)?\]\]',body):
            assert target+'.md' in d['pages']
    assert d['wiki_lint_report']['superseded_decisions']
    assert not d['wiki_lint_report']['broken_wikilinks']
    assert snapshot_stats(tenant)==before
    page=client.get('/api/v1/ctx/wiki-page',params={'tenant_graph':tenant,'page':'index.md'})
    assert page.status_code==200 and page.json()['markdown']==d['pages']['index.md']
    assert client.get('/api/v1/ctx/wiki-page',params={'tenant_graph':tenant,'page':'../../etc/passwd'}).status_code==404
    assert all('NEVER EXECUTE SOURCE' not in body for body in d['pages'].values())


def test_t08_stats_measure_actual_payload_and_missing_metadata(client,ingested):
    from app.services.second_brain_wiki import compact_json
    tenant,_,_=ingested
    response=client.get('/api/v1/ctx/stats',params={'tenant_graph':tenant,'file_path':'src/pkg/a.py'})
    assert response.status_code==200,response.text
    d=response.json()
    graph=db_manager.get_graph(tenant)
    sizes=graph.ro_query('MATCH (f:File) RETURN f.source_utf8_bytes,f.source_chars').result_set
    assert d['raw_repo_bytes']==sum(r[0] for r in sizes)
    assert d['slice_bytes']==len(compact_json(d['slice']).encode('utf-8'))
    assert d['raw_repo_tokens_est']==d['raw_repo_bytes']//4
    assert d['slice_tokens_est']==d['slice_bytes']//4
    assert d['track1']['recommended_pytest_command']=='pytest'
    graph.query("MATCH (f:File {path:'src/pkg/a.py'}) REMOVE f.source_utf8_bytes")
    missing=client.get('/api/v1/ctx/stats',params={'tenant_graph':tenant}).json()
    assert missing['measurement_status']=='SOURCE_SIZES_UNAVAILABLE' and missing['raw_repo_bytes']==0


def test_t08_resume_strips_history_and_stale_playbook(client,ingested):
    tenant,_,_=ingested
    graph=db_manager.get_graph(tenant)
    graph.query("MATCH (d:Decision {status:'SUPERSEDED'}) SET d.rule='OLD_RULE_MUST_NOT_SURVIVE'")
    body={'tenant_graph':tenant,'issue_description':'Inspect src/pkg/a.py','execution_mode':'cold_multi_agent'}
    assert client.post('/api/v1/track2/investigate',json=body).status_code==200
    snap=client.post('/api/v1/ctx/compact-snapshot',json={'tenant_graph':tenant,'file_path':'src/pkg/a.py'})
    assert snap.status_code==200,snap.text
    d=snap.json();text=d['markdown']
    assert d['snapshot_bytes']==len(text.encode('utf-8'))<2048
    assert 'OLD_RULE_MUST_NOT_SURVIVE' not in text and 'inspect_candidate' not in text
    assert 'inspect_target → inspect_policies → verify_policy' in text
    graph.query("MATCH (d:Decision {status:'ACTIVE'}) SET d.rule='Current replacement policy'")
    stale=client.post('/api/v1/ctx/compact-snapshot',json={'tenant_graph':tenant,'file_path':'src/pkg/a.py'}).json()
    assert 'No current verified playbook' in stale['markdown']
    assert stale['fingerprint']!=d['fingerprint']
    wiki=client.post('/api/v1/ctx/compile-wiki',json={'tenant_graph':tenant}).json()
    assert wiki['wiki_lint_report']['pruned_dead_end_states'] and wiki['wiki_lint_report']['stale_playbooks']


def test_t08_export_is_safe_and_ledger_append_only(client,ingested,tmp_path,monkeypatch):
    import zipfile,io
    tenant,_,_=ingested
    root=tmp_path/'vaults';monkeypatch.setenv('CHRONOSGRAPH_VAULT_ROOT',str(root))
    body={'tenant_graph':tenant,'export':True}
    first=client.post('/api/v1/ctx/compile-wiki',json=body)
    assert first.status_code==200,first.text
    d=first.json();folder=Path(d['export_directory'])
    assert folder.is_relative_to(root) and (folder/'index.md').is_file()
    ledger=root/tenant/'log.md';old=ledger.read_text()
    assert client.post('/api/v1/track2/investigate',json={'tenant_graph':tenant,'issue_description':'Inspect src/pkg/a.py'}).status_code==200
    second=client.post('/api/v1/ctx/compile-wiki',json=body)
    assert second.status_code==200,second.text
    assert ledger.read_text().startswith(old) and len(ledger.read_text())>len(old)
    before=ledger.read_text()
    assert client.post('/api/v1/ctx/compile-wiki',json=body).status_code==200
    assert ledger.read_text()==before
    response=client.get('/api/v1/ctx/export',params={'tenant_graph':tenant,'file_path':'src/pkg/a.py'})
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert 'Target: src/pkg/a.py' in archive.read('ResumeSnapshot.md').decode('utf-8')
        assert {'index.md','log.md','ResumeSnapshot.md'}<=set(archive.namelist())
        assert all(not p.startswith('/') and '..' not in p for p in archive.namelist())
    ledger.unlink();ledger.symlink_to(tmp_path/'outside')
    assert client.post('/api/v1/ctx/compile-wiki',json=body).status_code==422
    assert not (tmp_path/'outside').exists()


def test_t08_portable_skill_contract():
    root=Path(__file__).resolve().parents[2]
    skill=(root/'skills/chronos-second-brain/SKILL.md').read_text()
    assert skill.startswith('---\nname: chronos-second-brain\n')
    for name in ['simulate_pr_blast_radius','query_bitemporal_decisions','find_true_code_owners','run_or_compile_playbook',
        'record_decision_override','Claude Code','Cursor','OpenCode','Antigravity','SUPERSEDED','/compact','untrusted']:
        assert name in skill
    assert 'not billed-token savings' not in skill or 'estimate' in skill


def test_t08_frontmatter_and_wikilink_injection_is_inert(client,ingested):
    tenant,_,_=ingested
    graph=db_manager.get_graph(tenant)
    graph.query("CREATE (:File {path:$path,source_type:'E2E_TEST_FIXTURE',source_chars:0,source_utf8_bytes:0,loc:0})",
        {'path':'../../evil]]|<script>\n---\ntest_.py'})
    d=client.post('/api/v1/ctx/compile-wiki',json={'tenant_graph':tenant}).json()
    assert not d['wiki_lint_report']['broken_wikilinks']
    assert all('[[../../evil' not in body and '<script>' not in body for body in d['pages'].values())
    assert d['wiki_lint_report']['isolated_files']
    from app.services.second_brain_wiki import byte_metrics
    assert byte_metrics(4,4,'longer summary')['context_saved_pct']<0


def test_t08_audit_measures_actual_compact_subset(client,ingested):
    from app.services.second_brain_wiki import compact_json
    tenant,_,_=ingested
    d=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':['src/pkg/a.py']}).json()
    metric=d['context_window_savings']
    assert metric['measurement_status']=='MEASURED_UTF8_BYTES'
    assert metric['slice_bytes']==len(compact_json(metric['slice']).encode('utf-8'))
    assert metric['slice']['pytest']==d['recommended_pytest_command']

# T-08 accepted builder extension: no synthetic graph stubs or source execution.
def test_t08_brain_slice_exact_connected_sizes_and_ast(client,ingested):
    tenant,_,_=ingested
    before=snapshot_stats(tenant)
    r=client.get('/api/v1/brain/wiki-slice',params={'tenant_graph':tenant,'file_path':'src/pkg/a.py'})
    assert r.status_code==200,r.text
    d=r.json();m=d['context_folding_stats'];text=d['wiki_markdown']
    assert 'tags: [second-brain, falkordb, context-mode]' in text and 'active_rules:' in text
    assert 'helper(' in text and '[[wiki/' in text and 'Two-clock lineage' in text
    assert m['slice_bytes']==len(text.encode('utf-8')) and m['slice_est_tokens']==len(text)//4
    rows=db_manager.get_graph(tenant).ro_query('MATCH (f:File) RETURN f.path,f.source_utf8_bytes,f.source_chars').result_set
    rows=[r for r in rows if r[0] in m['connected_files']]
    assert m['raw_files_bytes']==sum(r[1] for r in rows) and m['raw_est_tokens']==sum(r[2] for r in rows)//4
    assert d['model_calls']==0 and snapshot_stats(tenant)==before
    assert client.get('/api/v1/brain/wiki-slice',params={'tenant_graph':tenant,'file_path':'missing.py'}).status_code==404
    db_manager.get_graph(tenant).query("MATCH (f:File {path:'src/pkg/a.py'}) REMOVE f.source_chars")
    missing=client.get('/api/v1/brain/wiki-slice',params={'tenant_graph':tenant,'file_path':'src/pkg/a.py'}).json()
    assert missing['context_folding_stats']['measurement_status']=='SOURCE_SIZES_UNAVAILABLE'


def test_t08_brain_compact_excludes_stale_authority_and_observes_orphans(client,ingested):
    tenant,_,_=ingested
    graph=db_manager.get_graph(tenant)
    graph.query("MATCH (d:Decision {status:'SUPERSEDED'}) SET d.rule='OBSOLETE_NEVER_RECOVER'")
    assert client.post('/api/v1/track2/investigate',json={'tenant_graph':tenant,'issue_description':'Inspect src/pkg/a.py'}).status_code==200
    payload={'tenant_graph':tenant,'file_path':'src/pkg/a.py'}
    r=client.post('/api/v1/brain/lint-and-compact',json=payload)
    assert r.status_code==200,r.text
    d=r.json();text=d['precompact_resume_markdown']
    assert len(text.encode())<2048 and 'LESSON:' in text and '[[wiki/files/' in text
    assert 'OBSOLETE_NEVER_RECOVER' not in text and 'inspect_candidate' not in text
    assert d['dead_end_steps_pruned']==2 and d['active_rules_count']>0
    assert d['superseded_contradictions_blocked']>0 and 'Current playbook' in text
    orphan='sandbox_pr_t08_'+uuid.uuid4().hex
    db_manager.get_graph(orphan).query('CREATE (:Fixture)')
    try:
        assert client.post('/api/v1/brain/lint-and-compact',json=payload).json()['orphan_sandboxes_count']>=1
    finally:db_manager.get_graph(orphan).delete()
    graph.query("MATCH (d:Decision {status:'ACTIVE'}) SET d.rule='New current rule'")
    stale=client.post('/api/v1/brain/lint-and-compact',json=payload).json()
    assert stale['stale_playbooks_flagged']>0 and 'No current verified playbook' in stale['precompact_resume_markdown']


def test_t08_brain_three_layer_zip_is_readonly_pinned_and_all_links_resolve(client,ingested):
    import io,zipfile,re,json,yaml
    tenant,stats,_=ingested
    before=snapshot_stats(tenant)
    r=client.get('/api/v1/brain/obsidian-vault.zip',params={'tenant_graph':tenant,'file_path':'src/pkg/a.py'})
    assert r.status_code==200,r.text[:300]
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names=set(z.namelist())
        assert {'raw/repo_snapshot_manifest.json','wiki/index.md','wiki/log.md','_CLAUDE.md','SKILL.md','ResumeSnapshot.md'}<=names
        assert any(p.startswith('wiki/rules/') for p in names)
        manifest=json.loads(z.read('raw/repo_snapshot_manifest.json'))
        assert manifest['repositories'][0]['source_revision']==stats['source_revision']
        assert manifest['ast_stats']['Function']>0
        for p in names:
            assert '..' not in p and not p.startswith('/')
            if not p.endswith('.md'):continue
            body=z.read(p).decode()
            for dest in re.findall(r'\[\[([^]|]+)(?:\|[^]]*)?\]\]',body):assert dest+'.md' in names,(p,dest)
            if p.startswith('wiki/files/'):
                assert yaml.safe_load(body.split('---')[1])['tenant']==tenant
        assert 'LESSON:' in z.read('SKILL.md').decode() and 'LESSON:' in z.read('_CLAUDE.md').decode()
    assert snapshot_stats(tenant)==before
