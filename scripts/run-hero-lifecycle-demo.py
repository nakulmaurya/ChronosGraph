"""Scripted REAL stdio MCP + observed pytest fixture. Not a hosted-model/IDE run.

Uses only an owned fixture checkout/tenant. --approve-fixture is explicit operator
preauthorization for this demo fixture, not evidence a human reviewed a UI action.
Requires a disposable FalkorDB with backend dependencies installed.
"""
import argparse
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport


def run(output, approve_fixture):
    if not approve_fixture:
        raise SystemExit('Pass --approve-fixture only to authorize execution of our owned synthetic fixture')
    # Reuse the same independently exercised owned Git fixture without copying a
    # second drifting implementation. pytest supplies only its fixture utilities.
    import tempfile
    from pytest import MonkeyPatch
    spec=importlib.util.spec_from_file_location('hero_fixture',Path(__file__).resolve().parents[1]/'backend/tests/test_change_lifecycle.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from app.services.change_lifecycle import decide, DecisionInput
    from app.services.worktree_runner import execute, WorktreeInput
    from app.services.company_brain import override_policy
    from app.models import PolicyOverrideRequest
    monkeypatch=MonkeyPatch()
    records=[]
    with tempfile.TemporaryDirectory(prefix='chronos-hero-') as tmp:
        fixture=module.hero.__wrapped__(Path(tmp),monkeypatch)
        tenant,revision,root,files=next(fixture)
        try:
            guard={'tenant_graph':tenant,'expected_revision':revision}
            server=Path(__file__).resolve().parents[1]/'backend/app/mcp_server/server.py'
            def transport():return PythonStdioTransport(server,python_cmd=sys.executable,cwd=str(server.parents[2]),
                env={**os.environ,'CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD':'1'},keep_alive=False)
            async def flow():
                async def call(client,name,args):
                    result=await client.call_tool(name,args)
                    assert not result.is_error
                    records.append({'tool':name,'data':result.data})
                    return result.data
                async with Client(transport()) as client:
                    tools=await client.list_tools();assert len(tools)==15
                    listing=await call(client,'discover_repositories',{'limit':50})
                    assert tenant in {r['tenant_graph'] for r in listing['repositories']}
                    await call(client,'inspect_repository_snapshot',guard)
                    ctx=await call(client,'locate_context',{**guard,'query':'calculate_discount','budget_bytes':8192})
                    assert 'tests/test_orders.py' in ctx['candidate_test_files']
                    assert any(len(r.get('via',[]))>=3 for r in ctx['related_importers'])
                    await call(client,'get_symbol_source',{**guard,'file_path':'core/pricing.py','symbol_name':'calculate_discount'})
                    bodies={'core/pricing.py':'def discounted_total(amount, tier):\n    return amount * 0.9 if tier == "gold" else amount\n'}
                    broken=await call(client,'propose_change_for_approval',{**guard,'task_title':'First: rename without caller fix','proposed_files':bodies,'idempotency_key':'hero-breaking'})
                    assert 'services/checkout.py:checkout' in broken['impact_summary']['potentially_broken_callers']
                    bodies['services/checkout.py']='from core.pricing import discounted_total\ndef checkout(amount):\n    return discounted_total(amount, "gold")\n'
                    fixed=await call(client,'propose_change_for_approval',{**guard,'task_title':'Coordinate pricing and checkout rename','proposed_files':bodies,'idempotency_key':'hero-coordinated'})
                    assert fixed['impact_summary']['potentially_broken_callers']==[]
                    decide(fixed['id'],DecisionInput(**guard,proposal_hash=fixed['proposal_hash'],approve=True,reason='Explicit --approve-fixture operator preauthorization'))
                    accepted=await call(client,'check_proposal_decision',{**guard,'proposal_id':fixed['id']});assert accepted['status']=='APPROVED'
                    observed=execute(fixed['id'],WorktreeInput(**guard,proposal_hash=fixed['proposal_hash'],idempotency_key='hero-observed',acknowledge_code_execution=True))
                    assert observed['exit_code']==0,observed
                    records.append({'operator_action':'OBSERVED_OWNED_WORKTREE_EXECUTION','data':observed})
                # New real server process, not memory retained in the previous client.
                async with Client(transport()) as client:
                    recalled=await call(client,'recall_task_memory',{**guard,'query':'Coordinate pricing','include_stale':True})
                    assert recalled['findings'][0]['status']=='CURRENT_AT_INDEXED_SNAPSHOT'
                    override_policy(PolicyOverrideRequest(tenant_graph=tenant,target_file_path='core/pricing.py',new_rule_text='DEMO: require finance review for discount contracts',rationale='Hero stale-policy evidence'))
                    stale=await call(client,'recall_task_memory',{**guard,'query':'Coordinate pricing','include_stale':True})
                    assert stale['findings'][0]['status']=='STALE'
                    result=await call(client,'check_proposal_decision',{**guard,'proposal_id':fixed['id']});assert result['status']=='STALE_POLICY'
            asyncio.run(flow())
            assert (root/'core/pricing.py').read_text()==files['core/pricing.py']
            Path(output).write_text(json.dumps({'evaluation_kind':'SCRIPTED_REAL_STDIO_AND_OBSERVED_FIXTURE_TESTS_NOT_HOSTED_MODEL_AGENT',
                'operator_approval_kind':'EXPLICIT_FIXTURE_CLI_PREAUTHORIZATION_NOT_WITNESSED_UI_REVIEW',
                'tenant_graph':tenant,'source_revision':revision,'model_calls':0,'steps':records},indent=2))
        finally:
            try:next(fixture)
            except StopIteration:pass
            monkeypatch.undo()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--approve-fixture',action='store_true')
    args=parser.parse_args();run(args.output,args.approve_fixture)
