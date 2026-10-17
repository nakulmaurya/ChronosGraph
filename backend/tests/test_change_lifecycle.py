"""Native lifecycle/real subprocess tests. All fixture graphs/checkouts are owned."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
import uuid
import pytest
from fastapi import HTTPException
from app.db.client import db_manager
from app.ingestion.workspace import create_snapshot
from app.services.change_lifecycle import (propose, check, decide, report, list_proposals,
    ProposalInput, DecisionInput, ExecutionInput)
from app.services.company_brain import override_policy
from app.models import PolicyOverrideRequest
from app.services.task_memory import recall_findings
from app.services.worktree_runner import execute, WorktreeInput


@pytest.fixture
def hero(tmp_path, monkeypatch):
    root=tmp_path/'hero_payments_repo';root.mkdir()
    files={
        'core/__init__.py':'','services/__init__.py':'','api/__init__.py':'',
        'core/pricing.py':'def calculate_discount(amount, tier):\n    return amount * 0.9 if tier == "gold" else amount\n',
        'services/checkout.py':'from core.pricing import calculate_discount\ndef checkout(amount):\n    return calculate_discount(amount, "gold")\n',
        'api/orders.py':'from services.checkout import checkout\ndef place_order(amount):\n    return checkout(amount)\n',
        'tests/test_orders.py':'from api.orders import place_order\ndef test_order():\n    assert place_order(100) == 90\n',
        '.github/CODEOWNERS':'/core/pricing.py @platform-team\n'}
    for name,text in files.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
    git('init','-q');git('add','.');git('-c','user.name=Hero fixture','-c','user.email=fixture@example.invalid','commit','-qm','Owned hero fixture')
    revision=git('rev-parse','HEAD');branch=git('branch','--show-current');tenant='repo_test_'+uuid.uuid4().hex
    monkeypatch.setenv('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS',str(tmp_path))
    monkeypatch.setenv('CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION','1')
    monkeypatch.setenv('CHRONOSGRAPH_EXECUTION_REPOSITORIES',json.dumps({tenant:str(root)}))
    try:
        create_snapshot(str(root),branch,tenant,revision)
        for rule in ['DEMO: obsolete discount rule','DEMO: preserve gold checkout behavior']:
            override_policy(PolicyOverrideRequest(tenant_graph=tenant,target_file_path='core/pricing.py',new_rule_text=rule,rationale='Explicit synthetic hero scenario'))
        yield tenant,revision,root,files
    finally:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()


def request(hero, **kwargs):
    tenant,revision,_,_=hero
    return ProposalInput(tenant_graph=tenant,expected_revision=revision,task_title='Coordinate pricing rename',
        proposed_files=kwargs.pop('proposed_files',{'core/pricing.py':'def discounted_total(amount, tier):\n    return amount * 0.9 if tier == "gold" else amount\n'}),
        idempotency_key=kwargs.pop('idempotency_key',uuid.uuid4().hex),**kwargs)


def approve(hero,p):
    return decide(p['id'],DecisionInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],approve=True,reason='Human fixture approval'))


def fail(status,fn):
    with pytest.raises(HTTPException) as e:fn()
    assert e.value.status_code==status,e.value.detail


def test_preview_exact_idempotency_and_conflict(hero):
    graphs=set(db_manager.list_tenant_graphs());r=request(hero);p=propose(r)
    assert propose(r)['id']==p['id']
    fail(409,lambda:propose(r.model_copy(update={'proposed_files':{'core/pricing.py':'x=2\n'}})))
    assert set(db_manager.list_tenant_graphs())==graphs
    assert p['impact_summary']['sandbox_cleaned_up']
    assert 'services/checkout.py:checkout' in p['impact_summary']['potentially_broken_callers']
    assert 'tests/test_orders.py' in p['impact_summary']['impacted_test_files']
    assert p['impact_summary']['declared_ownership']['declarations'][0]['owner']=='@platform-team'
    assert p['governing_decision_ids']


def test_concurrent_same_key_returns_one_durable_proposal(hero):
    req=request(hero)
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda _:propose(req)['id'],range(3)))
    assert len(set(results))==1
    assert len(list_proposals(hero[0],hero[1])['proposals'])==1


def test_approval_wrong_hash_reject_and_terminal_decision(hero):
    p=propose(request(hero))
    body=DecisionInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash='0'*64,approve=True,reason='Human')
    fail(409,lambda:decide(p['id'],body))
    rejected=decide(p['id'],body.model_copy(update={'proposal_hash':p['proposal_hash'],'approve':False}))
    assert rejected['status']=='REJECTED'
    fail(409,lambda:approve(hero,p))


@pytest.mark.parametrize('mutation',['revision','hash','inventory','addition'])
def test_snapshot_staleness_blocks_approval(hero,mutation):
    req=request(hero)
    if mutation=='addition':req=req.model_copy(update={'proposed_files':{**req.proposed_files,'core/new.py':'x=1\n'}})
    p=propose(req);g=db_manager.get_graph(hero[0])
    if mutation=='revision':g.query("MATCH (m:RepoMetadata) SET m.source_revision=$r",{'r':'0'*40})
    elif mutation=='hash':g.query("MATCH (f:File {path:'core/pricing.py'}) SET f.sha256='changed'")
    elif mutation=='inventory':g.query("MATCH (f:TrackedFile {path:'core/pricing.py'}) SET f.sha256='changed'")
    else:g.query("CREATE (:File {path:'core/new.py',sha256:'appeared'})")
    fail(409,lambda:approve(hero,p))
    assert check(hero[0],hero[1],p['id'])['status']=='STALE_SNAPSHOT'


def test_new_rule_stales_approved_proposal(hero):
    p=propose(request(hero));approve(hero,p)
    override_policy(PolicyOverrideRequest(tenant_graph=hero[0],target_file_path='core/pricing.py',new_rule_text='DEMO: new policy',rationale='Exercise staleness'))
    assert check(hero[0],hero[1],p['id'])['status']=='STALE_POLICY'
    fail(409,lambda:approve(hero,p))


def test_unapproved_report_refused_and_report_cannot_mint_observed_provenance(hero):
    p=propose(request(hero))
    req=ExecutionInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],command_executed='pytest -- tests/test_orders.py',exit_code=0,
                       output_excerpt='Client says passed',idempotency_key=uuid.uuid4().hex,create_finding_summary='Client report')
    fail(409,lambda:report(p['id'],req));approve(hero,p)
    e=report(p['id'],req)
    assert e['provenance_kind']=='AGENT_REPORTED_UNVERIFIED'
    assert report(p['id'],req)['id']==e['id']
    fail(409,lambda:report(p['id'],req.model_copy(update={'exit_code':1})))
    assert check(hero[0],hero[1],p['id'])['status']=='APPROVED'
    assert recall_findings(hero[0])['findings'][0]['verification_basis']=='AGENT_REPORTED_UNVERIFIED'


def test_coordinated_fix_actual_worktree_execution_recall_and_policy_invalidation(hero):
    r=request(hero);r=r.model_copy(update={'proposed_files':{**r.proposed_files,'services/checkout.py':
        'from core.pricing import discounted_total\ndef checkout(amount):\n    return discounted_total(amount, "gold")\n'}})
    p=propose(r)
    assert p['impact_summary']['potentially_broken_callers']==[]
    approve(hero,p)
    req=WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key=uuid.uuid4().hex,acknowledge_code_execution=True)
    e=execute(p['id'],req)
    assert e['exit_code']==0,e['output_excerpt']
    assert e['provenance_kind']=='LOCAL_WORKTREE_OBSERVED' and 'passed' in e['output_excerpt']
    assert execute(p['id'],req)['id']==e['id']
    assert check(hero[0],hero[1],p['id'])['status']=='EXECUTED_VERIFIED'
    assert (hero[2]/'core/pricing.py').read_text()==hero[3]['core/pricing.py']
    assert len(subprocess.check_output(['git','-C',str(hero[2]),'worktree','list','--porcelain']).decode().split('worktree '))==2
    memory=recall_findings(hero[0])['findings'][0]
    assert memory['status']=='CURRENT_AT_INDEXED_SNAPSHOT' and memory['proposal_id']==p['id']
    override_policy(PolicyOverrideRequest(tenant_graph=hero[0],target_file_path='core/pricing.py',new_rule_text='DEMO: require a new discount review',rationale='Hero policy invalidation'))
    assert recall_findings(hero[0])['findings']==[]
    assert recall_findings(hero[0],include_stale=True)['findings'][0]['status']=='STALE'
    assert check(hero[0],hero[1],p['id'])['status']=='STALE_POLICY'


@pytest.mark.parametrize('fault',['disabled','ack','dirty','wrong_hash'])
def test_runner_refuses_before_executing_when_operator_guards_fail(hero,monkeypatch,fault):
    p=propose(request(hero));approve(hero,p)
    req=WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key=uuid.uuid4().hex,acknowledge_code_execution=True)
    if fault=='disabled':monkeypatch.delenv('CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION')
    elif fault=='ack':req=req.model_copy(update={'acknowledge_code_execution':False})
    elif fault=='dirty':(hero[2]/'new.txt').write_text('dirty')
    else:req=req.model_copy(update={'proposal_hash':'0'*64})
    fail(403 if fault=='disabled' else 422 if fault=='ack' else 409,lambda:execute(p['id'],req))


def test_durable_proposal_survives_new_python_process(hero):
    import os,sys
    p=propose(request(hero))
    code='from app.services.change_lifecycle import check; import json,sys; print(json.dumps(check(*sys.argv[1:])))'
    output=subprocess.check_output([sys.executable,'-c',code,hero[0],hero[1],p['id']],env=os.environ,text=True)
    assert json.loads(output)['proposal_hash']==p['proposal_hash']


def test_actual_failing_candidate_is_not_verified_success(hero):
    p=propose(request(hero));approve(hero,p)
    e=execute(p['id'],WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key=uuid.uuid4().hex,acknowledge_code_execution=True))
    assert e['exit_code']!=0 and e['provenance_kind']=='LOCAL_WORKTREE_OBSERVED'
    assert check(hero[0],hero[1],p['id'])['status']=='EXECUTED_FAILED'


def test_unknown_started_execution_is_not_automatically_repeated(hero):
    p=propose(request(hero));approve(hero,p);key=uuid.uuid4().hex
    db_manager.get_graph(hero[0]).query("CREATE (:ExecutionAttempt {idempotency_key:$key,status:'STARTED_OUTCOME_UNKNOWN'})",{'key':key})
    fail(409,lambda:execute(p['id'],WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key=key,acknowledge_code_execution=True)))
    assert check(hero[0],hero[1],p['id'])['executions']==[]
    db_manager.get_graph(hero[0]).query("MATCH (p:ChangeProposal {id:$id}),(a:ExecutionAttempt {idempotency_key:$key}) CREATE (p)-[:HAS_ATTEMPT]->(a)",{'id':p['id'],'key':key})
    fail(409,lambda:execute(p['id'],WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key='different-after-reload',acknowledge_code_execution=True)))


@pytest.mark.parametrize('headers',[{}, {'Origin':'https://attacker.invalid','X-ChronosGraph-Action':'proposal-operator'}, {'Origin':'http://127.0.0.1:3001'}])
def test_browser_decision_requires_explicit_local_operator_intent(hero,headers):
    from fastapi.testclient import TestClient
    from app.main import app
    p=propose(request(hero));client=TestClient(app,base_url='http://127.0.0.1')
    r=client.post('/api/v1/proposals/'+p['id']+'/decision',headers=headers,json={
        'tenant_graph':hero[0],'expected_revision':hero[1],'proposal_hash':p['proposal_hash'],'approve':True,'reason':'No valid browser intent'})
    assert r.status_code==403
    assert check(hero[0],hero[1],p['id'])['status']=='PROPOSED'


def test_real_loopback_decision_http_endpoint(hero):
    from fastapi.testclient import TestClient
    from app.main import app
    p=propose(request(hero));client=TestClient(app,base_url='http://127.0.0.1')
    r=client.post('/api/v1/proposals/'+p['id']+'/decision',headers={'Origin':'http://127.0.0.1:3001','X-ChronosGraph-Action':'proposal-operator'},json={
        'tenant_graph':hero[0],'expected_revision':hero[1],'proposal_hash':p['proposal_hash'],'approve':True,'reason':'Explicit fixture operator'})
    assert r.status_code==200,r.text
    assert r.json()['status']=='APPROVED'


@pytest.mark.parametrize('tool,args',[
    ('propose_change_for_approval',{'task_title':'Wrong base','proposed_files':{'core/pricing.py':'x=1\n'},'idempotency_key':'guard'}),
    ('check_proposal_decision',{'proposal_id':'prop_missing'}),
    ('report_proposal_execution',{'proposal_id':'prop_missing','proposal_hash':'0'*64,'command_executed':'pytest','exit_code':0,'output_excerpt':'No execution','idempotency_key':'guard'})])
def test_new_mcp_tools_require_exact_snapshot_before_domain_write(hero,tool,args):
    import asyncio
    from fastmcp import Client
    from app.mcp_server.server import mcp
    async def call():
        async with Client(mcp) as client:
            result=await client.call_tool(tool,{'tenant_graph':hero[0],'expected_revision':'0'*40,**args},raise_on_error=False)
            assert result.is_error
    asyncio.run(call())
    assert list_proposals(hero[0],hero[1])['proposals']==[]


def test_activity_exposes_only_bounded_structural_selection_reasons(hero):
    from app.services.agent_activity import instrument, activity
    @instrument('locate_context')
    def lookup(tenant_graph,expected_revision,query):
        return {'entry_points':[{'path':'core/pricing.py','why_included':'not persisted arbitrary source'}],
                'related_importers':[{'path':'api/orders.py','via':['api/orders.py','services/checkout.py','core/pricing.py']}],
                'private_source':'never persist this result body'}
    lookup(hero[0],hero[1],'a private natural-language question')
    event=activity(hero[0])['events'][0]
    assert event['target_files']==['core/pricing.py']
    assert event['selection_reasons'][1]['via']==['api/orders.py','services/checkout.py','core/pricing.py']
    assert 'private' not in json.dumps(event)


@pytest.mark.parametrize('mutation',['addition','revision'])
def test_all_additions_observed_receipt_and_absence_bound_memory(hero,mutation):
    bodies={'core/new_discount.py':'def discount(amount):\n    return amount * 0.9\n',
            'tests/test_new_discount.py':'from core.new_discount import discount\ndef test_discount():\n    assert discount(100) == 90\n'}
    p=propose(request(hero,proposed_files=bodies));approve(hero,p)
    result=execute(p['id'],WorktreeInput(tenant_graph=hero[0],expected_revision=hero[1],proposal_hash=p['proposal_hash'],idempotency_key='all-additions',acknowledge_code_execution=True))
    assert result['exit_code']==0,result
    recalled=recall_findings(hero[0],include_stale=True)['findings'][0]
    assert recalled['status']=='CURRENT_AT_INDEXED_SNAPSHOT'
    assert recalled['supporting_file_shas']=={}
    assert set(recalled['absent_base_files'])==set(bodies)
    g=db_manager.get_graph(hero[0])
    if mutation=='addition':g.query("CREATE (:TrackedFile {path:'core/new_discount.py',sha256:'appeared'})")
    else:g.query("MATCH (m:RepoMetadata) SET m.source_revision=$r",{'r':'0'*40})
    recalled=recall_findings(hero[0],include_stale=True)['findings'][0]
    assert recalled['status']=='STALE'
    assert ('ADDED_FILE_BASE_ABSENCE_CHANGED' if mutation=='addition' else 'SAVED_SNAPSHOT_CHANGED') in recalled['stale_reasons']
