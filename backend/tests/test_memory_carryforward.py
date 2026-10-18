"""Actual Git commits, immutable refresh and native DB; no transcript handoff."""
import json
import os
import subprocess
import sys
import uuid
import pytest
from app.db.client import db_manager
from app.ingestion.workspace import create_snapshot
from app.ingestion.ingest_repo import git, snapshot_stats
from app.models import FindingRequest
from app.services.task_memory import record_finding,recall_findings
from app.services.memory_carryforward import predecessor_candidates
from test_workspace_snapshots import connected, local_repo, commit
from test_real_world_repos import client


def finding(old,scope='STATIC_NEIGHBORHOOD'):
    g=db_manager.get_graph(old)
    sha=g.ro_query("MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256").result_set[0][0]
    return record_finding(FindingRequest(tenant_graph=old,summary='Helper contract investigation',
        evidence_note='Historical source inspection; pytest was not executed.',
        supporting_file_shas={'src/pkg/a.py':sha},reuse_scope=scope,verification_command='pytest (not executed)'))


def refresh(c,modify):
    root,branch,revision,tenants,_=c
    modify(root);commit(root,'Actual change of repository state')
    return create_snapshot(str(root),branch,tenants[1],git(root,'rev-parse','HEAD'),previous_tenant=tenants[0],expected_base=revision)


def historical(new):
    return recall_findings(new,'Helper')['historical_candidates']['findings'][0]


def test_unrelated_doc_reuse_and_two_fresh_process_sessions_preserve_provenance(connected,client):
    root,branch,revision,tenants,_=connected;old,new,_=tenants
    # Session one records only the explicit source evidence and static scope.
    code="""import json,sys
from app.models import FindingRequest
from app.db.client import db_manager
from app.services.task_memory import record_finding
t=sys.argv[1];sha=db_manager.get_graph(t).ro_query(\"MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256\").result_set[0][0]
print(json.dumps(record_finding(FindingRequest(tenant_graph=t,summary='Helper contract investigation',evidence_note='Source inspection only; no test executed.',supporting_file_shas={'src/pkg/a.py':sha},reuse_scope='STATIC_NEIGHBORHOOD'))))
"""
    first=subprocess.run([sys.executable,'-c',code,old],capture_output=True,text=True,check=True)
    ident=json.loads(first.stdout)['id'];baseline=snapshot_stats(old)
    stats=refresh(connected,lambda r:(r/'notes.md').write_text('Unrelated documentation.'))
    # Session two receives no prior transcript, finding ID, file list or evidence.
    code="import json,sys;from app.services.task_memory import recall_findings;print(json.dumps(recall_findings(sys.argv[1])))"
    second=subprocess.run([sys.executable,'-c',code,new],capture_output=True,text=True,check=True)
    data=json.loads(second.stdout);candidate=data['historical_candidates']['findings'][0]
    assert candidate['id']==ident and candidate['status']=='VALID_FOR_THIS_SNAPSHOT'
    assert candidate['origin_tenant']==old and candidate['origin_revision']==revision
    assert candidate['validated_for_revision']==stats['source_revision']
    assert candidate['test_execution_on_new_revision'] is False
    assert 'NOT_EXECUTED' in candidate['verification_command_basis']
    assert not data['findings'] and snapshot_stats(old)==baseline
    assert client.get('/api/v1/memory/findings',params={'tenant_graph':new}).json()['historical_candidates']['findings'][0]['id']==ident
    assert db_manager.get_graph(new).ro_query('MATCH (n:VerifiedFinding) RETURN count(n)').result_set[0][0]==0


@pytest.mark.parametrize('change,reason',[
    ('support','SUPPORTING_FILE_CHANGED_OR_MISSING'),
    ('neighbor','RECORDED_DEPENDENCY_NEIGHBORHOOD_CHANGED'),
    ('edge','RECORDED_DEPENDENCY_NEIGHBORHOOD_CHANGED'),
    ('policy','GOVERNING_POLICY_CHANGED')])
def test_real_commit_changes_invalidate_recorded_scope(connected,change,reason):
    root,_,_,tenants,_=connected;old,new,_=tenants
    if change=='policy':
        (root/'README.md').write_text('Queries must use read-only queries.\n');commit(root)
        # First fixture snapshot predates this policy; use actual refresh for policy addition.
    finding(old)
    def modify(r):
        if change=='support': (r/'src/pkg/a.py').write_text('def helper():\n    return 44\n')
        elif change=='neighbor': (r/'src/pkg/b.py').write_text('from pkg.a import helper\ndef run():\n    return helper()+7\n')
        elif change=='edge': (r/'src/pkg/b.py').write_text('def run():\n    return 5\n')
        else: (r/'README.md').write_text('Queries must never mutate state.\n')
    refresh(connected,modify)
    c=historical(new);assert c['status']=='STALE' and reason in c['stale_reasons']
    assert not c['test_execution_on_new_revision']


def test_unspecified_scope_and_old_execution_never_become_new_verification(connected):
    root,_,_,tenants,_=connected;old,new,_=tenants
    f=finding(old,'UNSPECIFIED')
    refresh(connected,lambda r:(r/'notes.md').write_text('Only docs'))
    c=historical(new);assert c['status']=='NEEDS_REVALIDATION' and c['reuse_scope']=='UNSPECIFIED'
    g=db_manager.get_graph(old)
    g.query('MATCH (m:VerifiedFinding {id:$id}) SET m.execution_id=$execution,m.base_revision=$revision',
            {'id':f['id'],'execution':'observed-old-run','revision':git(root,'rev-parse','HEAD~1')})
    c=historical(new);assert c['execution_id']=='observed-old-run'
    assert 'PREVIOUS_EXECUTION_OR_PROPOSAL_REQUIRES_NEW_REVISION_VERIFICATION' in c['revalidation_reasons']
    assert not c['test_execution_on_new_revision']


def test_file_local_scope_is_explicit_and_legacy_needs_revalidation(connected):
    _,_,_,tenants,_=connected;old,new,_=tenants
    f=finding(old,'FILE_LOCAL')
    refresh(connected,lambda r:(r/'src/pkg/b.py').write_text('def entirely_changed_neighbor():\n    return 7\n'))
    assert historical(new)['status']=='VALID_FOR_THIS_SNAPSHOT'
    db_manager.get_graph(old).query('MATCH (m:VerifiedFinding {id:$id}) REMOVE m.reuse_validation_json',{'id':f['id']})
    assert historical(new)['status']=='NEEDS_REVALIDATION'


def test_same_filenames_different_connection_and_missing_parent_are_refused(connected):
    root,_,_,tenants,_=connected;old,new,_=tenants;finding(old)
    refresh(connected,lambda r:(r/'notes.md').write_text('Only docs'))
    g=db_manager.get_graph(new)
    g.query("MATCH (m:RepoMetadata) SET m.connection_id='different-repository'")
    assert predecessor_candidates(new,[],10)['status']=='CROSS_CONNECTION_REUSE_REFUSED'
    g.query("MATCH (m:RepoMetadata) SET m.parent_snapshot='repo_nonexistent_parent'")
    assert predecessor_candidates(new,[],10)['status']=='PREDECESSOR_UNAVAILABLE_OR_INVALID'
