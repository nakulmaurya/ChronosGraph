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
