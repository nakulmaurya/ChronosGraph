"""Native committed-source organizational case; explicitly owned synthetic data."""
import asyncio
import json
import shutil
import subprocess
import uuid
from pathlib import Path
import pytest
from fastmcp import Client
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo
from app.mcp_server.server import mcp
from app.models import BrainQueryRequest
from app.services.company_brain import ask_brain
from app.services.organization import organizational_context
from app.services.ownership import get_ownership
from test_real_world_repos import client


def commit(root, message='Owned synthetic case'):
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Synthetic Case Author','-c','user.email=example@example.invalid','commit','--quiet','-m',message],check=True)
    return subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()


@pytest.fixture
def case(tmp_path):
    root=tmp_path/'organization'
    shutil.copytree(Path(__file__).resolve().parents[2]/'examples/organization-case',root)
    subprocess.run(['git','init','--quiet',str(root)],check=True)
    commit(root)
    tenants=[]
    def ingest():
        tenant='repo_test_org_'+uuid.uuid4().hex;tenants.append(tenant)
        return tenant,ingest_repo(str(root),tenant)
    yield root,ingest
    for tenant in tenants:
        if tenant in db_manager.list_tenant_graphs(): db_manager.get_graph(tenant).delete()


def test_source_chain_team_supersession_and_actual_rest_mcp(case,client):
    root,ingest=case;tenant,stats=ingest()
    evidence=ask_brain(BrainQueryRequest(tenant_graph=tenant,file_path='client.py',question='Why not raise an exception, who reviews, and what makes this acceptable?')).organizational_evidence
    assert evidence['status']=='SOURCE_BACKED_REVIEW_REQUIRED' and not evidence['safe_to_approve']
    assert len(evidence['chains'])==2 and not evidence['gaps']
    active=next(c for c in evidence['chains'] if c['decision']['status']=='ACTIVE')
    assert active['decision']['data_kind']=='OWNED_SYNTHETIC'
    assert active['document']['source_revision']==stats['source_revision']
    assert active['motivating_incident']['path']=='incidents/INC-007.md'
    assert 'migration plan' in active['decision']['required_action']
    assert evidence['review_teams'][0]['name']=='Compatibility Platform'
    assert get_ownership(tenant,'client.py')['organizational_evidence']==evidence
    assert db_manager.get_graph(tenant).ro_query('MATCH (:Decision)-[:SUPERSEDED]->(:Decision) RETURN count(*)').result_set[0][0]==1
    response=client.post('/api/v1/track3/ask-brain',json={'tenant_graph':tenant,'file_path':'client.py','question':'Explain the timeout contract'});assert response.status_code==200
    assert response.json()['organizational_evidence']['status']==evidence['status']
    async def run():
        async with Client(mcp) as c:
            result=await c.call_tool('query_bitemporal_decisions',{'tenant_graph':tenant,'file_path':'client.py','question':'Who needs to review a timeout exception migration?'})
            assert result.data['organizational_evidence']['review_teams'][0]['owner']=='@chronos-example/compatibility'
    asyncio.run(run())


@pytest.mark.parametrize('remove,reason',[('SUPPORTED_BY','MISSING_DECISION_SOURCE'),('MOTIVATED_BY','MISSING_MOTIVATING_INCIDENT')])
def test_missing_source_refuses_definitive_answer(case,remove,reason):
    _,ingest=case;tenant,_=ingest();g=db_manager.get_graph(tenant)
    g.query(f"MATCH (:Decision {{status:'ACTIVE'}})-[r:{remove}]->() DELETE r")
    e=organizational_context(tenant,['client.py'])
    assert e['status']=='GAPS_OR_CONFLICTS' and reason in [r['reason'] for r in e['gaps']]
    assert not e['safe_to_approve']


def test_conflicting_current_sources_and_missing_ownership_are_explicit(case):
    root,ingest=case;p=root/'.chronosgraph/organization.json';data=json.loads(p.read_text())
    data['decisions'][0]['status']='ACTIVE';data['decisions'][1].pop('supersedes')
    data['teams']=[];p.write_text(json.dumps(data));commit(root)
    tenant,_=ingest();e=organizational_context(tenant,['client.py'])
    reasons={g['reason'] for g in e['gaps']}
    assert e['status']=='GAPS_OR_CONFLICTS'
    assert {'UNRESOLVED_ACTIVE_DECISIONS_IN_SAME_CONFLICT_GROUP','NO_EXPLICIT_CODEOWNERS_TEAM_MAPPING'} <= reasons
    assert not e['review_teams'] and not e['safe_to_approve']


@pytest.mark.parametrize('mutation',['missing','symlink','range','traversal','duplicate','supersession'])
def test_invalid_manifest_fails_and_cleans_new_graph(case,mutation):
    root,ingest=case;p=root/'.chronosgraph/organization.json';data=json.loads(p.read_text())
    if mutation=='missing': (root/'docs/ADR-002.md').unlink()
    elif mutation=='symlink':
        (root/'docs/ADR-002.md').unlink();(root/'docs/ADR-002.md').symlink_to('../incidents/INC-007.md')
    elif mutation=='range': data['decisions'][1]['document']['end_line']=999
    elif mutation=='traversal': data['decisions'][1]['document']['path']='../outside.md'
    elif mutation=='duplicate': data['decisions'][1]['id']=data['decisions'][0]['id']
    else: data['decisions'][1]['supersedes']='absent'
    p.write_text(json.dumps(data));commit(root)
    before=set(db_manager.list_tenant_graphs())
    with pytest.raises(ValueError): ingest()
    assert set(db_manager.list_tenant_graphs())==before


def test_pinned_blob_not_dirty_workspace_and_no_manifest_no_claim(case):
    root,ingest=case;(root/'docs/ADR-002.md').write_text('UNCOMMITTED MALICIOUS REPLACEMENT')
    tenant,_=ingest();e=organizational_context(tenant,['client.py'])
    assert 'Timeouts must retain' in next(c for c in e['chains'] if c['decision']['status']=='ACTIVE')['document']['excerpt']
    (root/'.chronosgraph/organization.json').unlink();commit(root)
    other,_=ingest();empty=organizational_context(other,['client.py'])
    assert empty['status']=='NO_ORGANIZATIONAL_EVIDENCE' and not empty['review_requirements']


def test_proposal_citation_requires_current_relevant_hash_pinned_chain(case):
    from fastapi import HTTPException
    from app.services.change_lifecycle import propose, check, ProposalInput
    root,ingest=case;tenant,stats=ingest()
    chain=next(c for c in organizational_context(tenant,['client.py'])['chains'] if c['decision']['status']=='ACTIVE')
    ref={'decision_id':chain['decision']['id'],'excerpt_id':chain['document']['id'],'source_sha256':chain['document']['sha256']}
    args=dict(tenant_graph=tenant,expected_revision=stats['source_revision'],task_title='Observed compatibility review',
        proposed_files={'client.py':(root/'client.py').read_text()+'\n# Candidate requires compatibility review\n'},idempotency_key='source-backed-proposal')
    p=propose(ProposalInput(**args,evidence_refs=[ref]))
    assert p['validated_evidence']['status']=='EXPLICIT_CITATIONS_VALIDATED'
    assert p['validated_evidence']['references'][0]['chains'][0]['motivating_incident']['path']=='incidents/INC-007.md'
    with pytest.raises(HTTPException):
        propose(ProposalInput(**{**args,'idempotency_key':'bad-citation'},evidence_refs=[{**ref,'decision_id':'unknown'}]))
    with pytest.raises(HTTPException):
        propose(ProposalInput(**{**args,'idempotency_key':'bad-hash'},evidence_refs=[{**ref,'source_sha256':'a'*64}]))
    doc=chain['document']['path']
    db_manager.query(tenant,'MATCH (f:TrackedFile {path:$path}) SET f.sha256=$sha',{'path':doc,'sha':'f'*64})
    assert check(tenant,stats['source_revision'],p['id'])['status']=='STALE_CITED_EVIDENCE'
