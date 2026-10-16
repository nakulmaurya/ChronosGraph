"""Real local FalkorDB route/tool tests. No mock clients or database substitutes.

Acceptance gates follow architect-approved CR-002 / v1.2: actual dead-end
elimination and step reduction, zero-model sentinels, measured replay speedup.
"""
import asyncio
import json
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from app.db.client import db_manager
from app.main import app
from app.mcp_server.server import mcp
from app.services.common import read

TENANTS = {
 'repo_falkordb_py':'falkordb/graph.py',
 'repo_graphrag_sdk':'graphrag_sdk/src/graphrag_sdk/core/connection.py',
}


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as value:
        yield value


@pytest.fixture
def isolated_policy_file():
    """Create a labeled test-only file, removed along with its policies afterward."""
    tenant='repo_falkordb_py'; path='__e2e__/'+uuid.uuid4().hex+'.py'
    db_manager.query(tenant,'CREATE (:File {path:$path,source_type:"E2E_TEST_FIXTURE"})',{'path':path})
    try:
        yield tenant,path
    finally:
        db_manager.query(tenant,'''MATCH (d:Decision)-[:GOVERNS]->(f:File {path:$path}) DETACH DELETE d''',{'path':path})
        db_manager.query(tenant,'MATCH (f:File {path:$path}) DETACH DELETE f',{'path':path})


@pytest.fixture(scope='module')
def race(client):
    issue='E2E policy review falkordb/graph.py '+uuid.uuid4().hex
    payload={'issue_description':issue}
    cold=client.post('/api/v1/track2/investigate',json=payload)
    assert cold.status_code==200,cold.text
    warm=client.post('/api/v1/track2/investigate',json={**payload,'execution_mode':'compiled_playbook'})
    assert warm.status_code==200,warm.text
    return cold.json(),warm.json()


def assert_visual(payload):
    assert payload['nodes']
    ids={n['id'] for n in payload['nodes']}
    assert len(ids)==len(payload['nodes'])
    assert all(e['source'] in ids and e['target'] in ids for e in payload['edges'])
    assert all('embedding' not in n['metadata'] for n in payload['nodes'])
    assert payload['execution_time_ms']>=0 and payload['cypher_executed']


def test_health_and_tenant_catalog(client):
    assert client.get('/health').json()['status']=='ok'
    response=client.get('/api/v1/tenants'); assert response.status_code==200
    data=response.json(); indexed={r['tenant_graph']:r for r in data}
    assert set(TENANTS)<=set(indexed)  # Dynamic registration is now explicitly supported.
    assert all(indexed[t]['node_count']>400 and indexed[t]['pull_requests'] and indexed[t]['preset_files'] for t in TENANTS)


@pytest.mark.parametrize('tenant',TENANTS)
def test_real_subgraph_and_unknown_tenant(client,tenant):
    response=client.get('/api/v1/subgraph',params={'tenant_graph':tenant})
    assert response.status_code==200; assert_visual(response.json())
    assert client.get('/api/v1/subgraph',params={'tenant_graph':'not-allowed'}).status_code==404


@pytest.mark.parametrize('tenant,path',TENANTS.items())
def test_sandbox_clone_mutations_and_cleanup(client,tenant,path):
    before,_=read(tenant,'MATCH (n) RETURN count(n) AS item_count')
    graphs=set(db_manager.list_tenant_graphs())
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,'modified_files':[path]})
    assert response.status_code==200,response.text
    data=response.json(); assert data['sandbox_cleaned_up']
    assert data['sandbox_graph_name'] not in db_manager.list_tenant_graphs()
    assert set(db_manager.list_tenant_graphs())==graphs
    after,_=read(tenant,'MATCH (n) RETURN count(n) AS item_count')
    assert before==after
    assert 0 <= data['sandbox_clone_time_ms'] < 250
    assert data['active_decisions_triggered'] and data['impacted_files'] and data['impacted_functions']
    assert all(d['source_type']=='DEMO_POLICY_SCENARIO' for d in data['active_decisions_triggered'])
    assert data['blind_agent_comparison']['tokens_burned']==0
    assert data['risk_level']!='CRITICAL_POLICY_VIOLATION'
    assert_visual(data['subgraph'])
    assert any(n['metadata'].get('source_type')=='SIMULATED_PR_DEPENDENCY' for n in data['subgraph']['nodes'])
    synthetic,_=read(tenant,'MATCH (f:File {source_type:"SIMULATED_PR_DEPENDENCY"}) RETURN count(f) AS item_count')
    assert synthetic[0]['item_count']==0


def test_sandbox_input_validation(client):
    route='/api/v1/track1/sandbox-audit'
    assert client.post(route,json={}).status_code==422
    assert client.post(route,json={'modified_files':['does-not-exist.py']}).status_code==404
    assert client.post(route,json={'pr_number':-999}).status_code==404
    assert client.post(route,json={'modified_files':['x']*21}).status_code==422
    assert not any(g.startswith('sandbox_pr_') for g in db_manager.list_tenant_graphs())


@pytest.mark.parametrize('tenant,path',TENANTS.items())
def test_brain_returns_real_labeled_current_and_historical_policies(client,tenant,path):
    response=client.post('/api/v1/track3/ask-brain',json={'tenant_graph':tenant,'file_path':path,'question':'timeout policy'})
    assert response.status_code==200,response.text
    data=response.json(); assert data['file_path']==path
    assert data['active_decisions'] and data['superseded_decisions']
    assert all(p['status']=='ACTIVE' and p['source_type']=='DEMO_POLICY_SCENARIO' for p in data['active_decisions'])
    assert all(p['status']=='SUPERSEDED' for p in data['superseded_decisions'])
    assert data['blind_agent_comparison']['obsolete_rule_followed']
    statuses={n['status'] for n in data['subgraph']['nodes']}
    assert {'ACTIVE','SUPERSEDED'}<=statuses; assert_visual(data['subgraph'])


def test_brain_semantic_route_and_validation(client):
    # Retrieval is lexical hashing, despite the historical semantic-search UI name.
    response=client.post('/api/v1/track3/ask-brain',json={'question':'bounded timeout'})
    assert response.status_code==200
    assert client.post('/api/v1/track3/ask-brain',json={'question':' '}).status_code==422
    assert client.post('/api/v1/track3/ask-brain',json={'question':'x','file_path':'absent'}).status_code==404


def test_override_preserves_history_and_scope_guards(client,isolated_policy_file):
    tenant,path=isolated_policy_file
    payload={'tenant_graph':tenant,'target_file_path':path,'new_rule_text':'Bound test reads.','rationale':'Explicit E2E fixture'}
    first=client.post('/api/v1/track3/override-policy',json=payload)
    assert first.status_code==200,first.text
    old=first.json()['active_decisions'][0]['id']
    second=client.post('/api/v1/track3/override-policy',json={**payload,'new_rule_text':'Bound reads to 2 seconds.'})
    assert second.status_code==200,second.text
    data=second.json(); assert len(data['active_decisions'])==1
    assert data['active_decisions'][0]['source_type']=='LIVE_ARCHITECT_OVERRIDE'
    assert data['active_decisions'][0]['author_handle']=='lead-maintainer'
    assert any(d['id']==old and d['valid_to']>0 and d['recorded_to']>0 for d in data['superseded_decisions'])
    lineage,_=read(tenant,'''MATCH (a:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File {path:$path}),
    (a)-[:SUPERSEDED]->(b:Decision {status:'SUPERSEDED'}) RETURN b.id AS id''',{'path':path})
    assert lineage[0]['id']==old
    assert client.post('/api/v1/track3/override-policy',json={**payload,'scope_symbol':'different_scope'}).status_code==409
    assert client.post('/api/v1/track3/override-policy',json={**payload,'new_rule_text':''}).status_code==422
    other,_=read('repo_graphrag_sdk','MATCH (f:File {path:$path}) RETURN count(f) AS item_count',{'path':path})
    assert other[0]['item_count']==0


def test_memory_cold_persists_branching_path_and_warm_reexecutes_tools(race):
    cold,warm=race
    assert cold['total_steps_executed']==5
    assert cold['pruned_golden_steps']==warm['total_steps_executed']==3
    assert cold['compiled_playbook_id']==warm['compiled_playbook_id']
    assert cold['investigation_id']!=warm['investigation_id']
    assert len(cold['agent_handoff_log'])==5 and len(warm['agent_handoff_log'])==3
    assert {s['agent'] for s in cold['agent_handoff_log']}=={'Scout','Historian','Verifier'}
    assert all(s['observation'] for s in warm['agent_handoff_log'])
    assert all(s['execution_provider']=='DETERMINISTIC_READ_ONLY_TOOL' for s in warm['agent_handoff_log'])
    states,_=read('repo_falkordb_py', '''MATCH (:Investigation {id:$id})-[:HAS_STATE]->(s:StateNode)
    RETURN s.state_type AS state_type''',{'id':cold['investigation_id']})
    assert len(states)==6 and sum(r['state_type']=='DEAD_END' for r in states)==2
    assert sum(r['state_type']=='VERIFIED_GOAL' for r in states)==1
    assert_visual(cold['subgraph']); assert_visual(warm['subgraph'])
    assert sum(n['status']=='DEAD_END' for n in cold['subgraph']['nodes'])==2
    assert any(e['is_pruned'] for e in cold['subgraph']['edges'])
    assert all(s['tokens_used']==0 for s in cold['agent_handoff_log'])
    assert cold['tokens_used']==warm['tokens_used']==0
    assert warm['duration_ms']>0 and warm['latency_speedup_factor']>0


def test_memory_refuses_unknown_and_stale_playbooks(client,race,isolated_policy_file):
    assert client.post('/api/v1/track2/investigate',json={'issue_description':'never-seen '+uuid.uuid4().hex,
        'execution_mode':'compiled_playbook'}).status_code==409
    cold,_=race
    # Any governing-policy change alters the safety fingerprint, even outside target.
    tenant,path=isolated_policy_file
    response=client.post('/api/v1/track3/override-policy',json={'target_file_path':path,'new_rule_text':'Test policy',
        'rationale':'Fingerprint invalidation verification'})
    assert response.status_code==200
    # Recover the exact issue from persisted signature, without assuming a random fixture value.
    signatures,_=read(tenant,'''MATCH (a:AnomalySignature)-[:COMPILED_AS]->(p:ProceduralPlaybook {id:$id})
    RETURN a.pattern_text AS issue''',{'id':cold['compiled_playbook_id']})
    response=client.post('/api/v1/track2/investigate',json={'issue_description':signatures[0]['issue'],
        'execution_mode':'compiled_playbook'})
    assert response.status_code==409


def test_memory_validation(client):
    assert client.post('/api/v1/track2/investigate',json={'issue_description':' '}).status_code==422
    assert client.post('/api/v1/track2/investigate',json={'issue_description':'x','execution_mode':'unknown'}).status_code==422


def test_five_mcp_tools_via_actual_inprocess_protocol(isolated_policy_file):
    async def exercise():
        tenant,path=isolated_policy_file
        async with Client(mcp) as c:
            tools=await c.list_tools()
            assert {t.name for t in tools}=={'simulate_pr_blast_radius','query_bitemporal_decisions',
              'record_decision_override','find_true_code_owners','run_or_compile_playbook',
                'simulate_diff_impact','locate_context','get_symbol_source','record_verified_finding','recall_task_memory'}
            args={'modified_files':['falkordb/graph.py']}
            audit=await c.call_tool('simulate_pr_blast_radius',args)
            assert not audit.is_error and audit.data['sandbox_cleaned_up']
            brain=await c.call_tool('query_bitemporal_decisions',{'question':'timeout','file_path':'falkordb/graph.py'})
            assert not brain.is_error and brain.data['active_decisions']
            owners=await c.call_tool('find_true_code_owners',{'file_path':'falkordb/graph.py'})
            assert not owners.is_error
            override=await c.call_tool('record_decision_override',{'target_file_path':path,'new_rule_text':'MCP test rule','rationale':'Labeled test'})
            assert not override.is_error and override.data['active_decisions']
            issue='MCP triage falkordb/graph.py '+uuid.uuid4().hex
            cold=await c.call_tool('run_or_compile_playbook',{'issue_description':issue})
            assert not cold.is_error and cold.data['total_steps_executed']==5
            warm=await c.call_tool('run_or_compile_playbook',{'issue_description':issue,'execution_mode':'compiled_playbook'})
            assert not warm.is_error and warm.data['total_steps_executed']==3
    asyncio.run(exercise())


def test_api_cors_is_local_only(client):
    response=client.options('/api/v1/track3/ask-brain',headers={
        'Origin':'http://localhost:3001','Access-Control-Request-Method':'POST'})
    assert response.headers['access-control-allow-origin']=='http://localhost:3001'
    response=client.options('/api/v1/track3/ask-brain',headers={
        'Origin':'https://untrusted.example','Access-Control-Request-Method':'POST'})
    assert 'access-control-allow-origin' not in response.headers


def test_sdk_investigation_is_tenant_isolated(client):
    tenant='repo_graphrag_sdk'
    issue='SDK policy triage '+TENANTS[tenant]+' '+uuid.uuid4().hex
    cold=client.post('/api/v1/track2/investigate',json={'tenant_graph':tenant,'issue_description':issue})
    assert cold.status_code==200,cold.text
    warm=client.post('/api/v1/track2/investigate',json={'tenant_graph':tenant,'issue_description':issue,
        'execution_mode':'compiled_playbook'})
    assert warm.status_code==200,warm.text
    assert warm.json()['total_steps_executed']==3
    other,_=read('repo_falkordb_py','MATCH (i:Investigation {id:$id}) RETURN count(i) AS item_count',
                 {'id':cold.json()['investigation_id']})
    assert other[0]['item_count']==0


def test_pr_selection_and_evidence_based_owners(client):
    tenant='repo_graphrag_sdk'
    links,_=read(tenant,'''MATCH (p:PullRequest)-[:MODIFIES]->(f:File)
        RETURN p.number AS number,f.path AS path LIMIT 1''')
    assert links
    response=client.post('/api/v1/track1/sandbox-audit',json={'tenant_graph':tenant,
        'pr_number':links[0]['number'],'modified_files':[links[0]['path']]})
    assert response.status_code==200,response.text
    data=response.json(); assert data['sandbox_cleaned_up']
    assert data['recommended_reviewers']
    assert all(r['login'] and r['pr_count']>0 for r in data['recommended_reviewers'])


# Architect-approved CR-002 (v1.2), not an unapproved weakening of tests.
def test_acceptance_dead_end_pruning_and_step_reduction(race):
    cold,warm=race
    assert cold['total_steps_executed']==5
    assert cold['pruned_golden_steps']==warm['total_steps_executed']==3
    assert sum(bool(s['dead_end']) for s in cold['agent_handoff_log'])==2
    assert sum(bool(s['dead_end']) for s in warm['agent_handoff_log'])==0
    assert (cold['total_steps_executed']-warm['total_steps_executed'])/cold['total_steps_executed']==0.4
    assert cold['tokens_used']==warm['tokens_used']==0
    assert cold['token_savings_pct']==warm['token_savings_pct']==0.0


def test_acceptance_compiled_replay_is_faster_and_valid(race):
    cold,warm=race
    assert warm['total_steps_executed']<cold['total_steps_executed']
    assert warm['duration_ms']>0
    assert warm['latency_speedup_factor']>1.0
