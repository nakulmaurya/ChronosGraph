"""Two fresh strict stdio MCP servers, actual commit refresh, owned synthetic case.

This is a scripted protocol acceptance demonstration, NOT an autonomous model
run, agent comparison or evidence that a historical test ran on a new revision.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from app.db.client import db_manager
from app.ingestion.workspace import create_snapshot
from app.services.change_lifecycle import propose,ProposalInput


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def commit(root,message):
    git(root,'add','.')
    git(root,'-c','user.name=Owned Synthetic Demo','-c','user.email=example@example.invalid','commit','-qm',message)
    return git(root,'rev-parse','HEAD')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--keep-graphs',action='store_true',help='Retain owned UUID graphs for subsequent UI validation; clean up explicitly')
    args=parser.parse_args();output=Path(args.output)
    if output.exists():raise ValueError('Refuse to overwrite evidence')
    tenants=['repo_test_evidence_'+uuid.uuid4().hex for _ in range(2)]
    previous=os.environ.get('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS')
    report={'scope':'OWNED_SYNTHETIC_SCRIPTED_MCP_NOT_AUTONOMOUS_AGENT_EVALUATION','trace':[]}
    success=False
    try:
        with tempfile.TemporaryDirectory(prefix='chronosgraph-owned-') as temp:
            root=Path(temp)/'source';shutil.copytree(ROOT/'examples/organization-case',root)
            git(root,'init','-q');revision=commit(root,'Owned synthetic source-backed organization')
            branch=git(root,'branch','--show-current');os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS']=temp
            old,new=tenants
            first=create_snapshot(str(root),branch,old,revision)
            def transport():
                server=ROOT/'backend/app/mcp_server/server.py'
                return PythonStdioTransport(server,python_cmd=sys.executable,cwd=str(ROOT/'backend'),
                    env={**os.environ,'CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD':'1'},keep_alive=False)
            async def call(client,name,arguments):
                result=await client.call_tool(name,arguments)
                report['trace'].append({'tool':name,'arguments':arguments,'result':result.data})
                return result.data
            async def investigate():
                async with Client(transport()) as c:
                    pin={'tenant_graph':old,'expected_revision':revision}
                    found=await call(c,'locate_context',{**pin,'query':'timeout_result','budget_bytes':8192})
                    source=await call(c,'get_symbol_source',{**pin,'file_path':'client.py','symbol_name':'__module__'})
                    await call(c,'query_bitemporal_decisions',{**pin,'file_path':'client.py',
                        'question':"Why cannot timeout_result simply raise, who reviews the migration, and what makes it acceptable?"})
                    await call(c,'record_verified_finding',{**pin,'summary':'Timeout envelope preserves the existing retry branch',
                        'evidence_note':'Captured source plus ADR-002 and INC-007. Existing retry consumer uses the result envelope. No test execution claimed by this finding.',
                        'supporting_file_shas':{'client.py':source['source_sha256']},'reuse_scope':'STATIC_NEIGHBORHOOD'})
                    assert any(r['path']=='worker.py' for r in found['related_importers'])
            asyncio.run(investigate())
            # Actual independent checks execute only this owned example, not arbitrary imported source.
            test=subprocess.run([sys.executable,'-m','pytest','tests/test_contract.py','-q'],cwd=root,
                env={**os.environ,'PYTHONPATH':str(root)},capture_output=True,text=True,timeout=30)
            assert test.returncode==0,test.stdout+test.stderr
            report['independent_owned_example_checks']={'revision':revision,'exit_code':test.returncode,'output':test.stdout}
            # A real docs-only commit, then the normal local snapshot refresh integration.
            (root/'release-notes.md').write_text('Unrelated documentation change; no contract or dependency changes.\n')
            updated=commit(root,'Unrelated documentation')
            changed_paths=git(root,'diff','--name-only',revision,updated).splitlines()
            assert changed_paths==['release-notes.md'],changed_paths
            report['actual_changed_paths_between_sessions']=changed_paths
            second=create_snapshot(str(root),branch,new,updated,previous_tenant=old,expected_base=revision)
            async def resume():
                # No original conversation, finding ID, file hashes or summary supplied.
                async with Client(transport()) as c:
                    return await call(c,'recall_task_memory',{'tenant_graph':new,'expected_revision':updated})
            memory=asyncio.run(resume())
            candidate=memory['historical_candidates']['findings'][0]
            assert candidate['status']=='VALID_FOR_THIS_SNAPSHOT' and candidate['test_execution_on_new_revision'] is False
            proposal=propose(ProposalInput(tenant_graph=new,expected_revision=updated,task_title='Review timeout exception migration',
                proposed_files={'client.py':'def timeout_result():\n    raise TimeoutError("timeout")\n'},idempotency_key=uuid.uuid4().hex))
            # This proposal records a review package only: never approved or executed.
            report.update(first_snapshot=first,second_snapshot=second,retained_tenants=tenants if args.keep_graphs else [],
                proposal_id=proposal['id'],proposal_status=proposal['status'],new_revision_test_execution=False,
                historical_finding=candidate,observed_mcp_server_sessions=2,
                limitation='Immediate declared predecessor only; scoped static revalidation is not dynamic dependency completeness. No backend/database durability restart or autonomous model comparison.')
            success=True
    finally:
        if previous is None:os.environ.pop('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS',None)
        else:os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS']=previous
        if not args.keep_graphs or not success:
            for tenant in tenants:
                if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()
        report['owned_graphs_cleaned_up']=all(t not in db_manager.list_tenant_graphs() for t in tenants)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(output),'sessions':2,'historical_status':candidate['status'],'new_revision_test_execution':False,'retained_tenants':report['retained_tenants']}))


if __name__=='__main__':main()
