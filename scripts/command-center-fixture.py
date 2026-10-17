"""Disposable native Git + actual stdio MCP walkthrough. No external LLM calls.

Invoked by the serial verification harness, not an app endpoint. It never executes
fixture source. Caller owns cleanup of the returned repo_test_ graph.
"""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from fastmcp import Client
from app.ingestion.ingest_repo import ingest_repo
from app.db.client import db_manager


def run(output):
    tenant='repo_test_'+uuid.uuid4().hex
    try:
        with tempfile.TemporaryDirectory(prefix='chronosgraph-command-demo-') as tmp:
            root=Path(tmp)/'command-center-example';root.mkdir()
            files={'src/pkg/__init__.py':'', 'src/pkg/a.py':'raise RuntimeError("DO NOT EXECUTE FIXTURE")\ndef helper():\n    """Return the configured demo value."""\n    return 1\ndef run():\n    return helper()\n',
              'src/pkg/b.py':'from pkg.a import helper\ndef run():\n    return helper()\n',
              'src/pkg/c.py':'from pkg.b import run\ndef action():\n    return run()\n',
              'tests/test_a.py':'from pkg.a import helper\ndef test_helper():\n    assert helper() == 1\n',
              'CODEOWNERS':'# Declared fixture reviewers\n/src/pkg/a.py @fixture-reviewer\n'}
            for path,text in files.items():
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
            def git(*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
            git('init','--quiet');git('add','.')
            git('-c','user.name=Workflow fixture','-c','user.email=fixture@example.invalid','commit','--quiet','-m','Add linked modules and helper')
            (root/'src/pkg/c.py').write_text(files['src/pkg/c.py']+'# Updated caller documentation\n')
            git('add','.');git('-c','user.name=Workflow fixture','-c','user.email=fixture@example.invalid','commit','--quiet','-m','Document downstream caller')
            stats=ingest_repo(str(root),tenant,seed_demo_policies=True)
        sha=db_manager.get_graph(tenant).ro_query("MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256").result_set[0][0]
        async def workflow():
            config={'mcpServers':{'chronosgraph':{'command':sys.executable,'args':['-m','app.mcp_server.server'],
                'env':{'PYTHONPATH':os.environ['PYTHONPATH'],'CHRONOSGRAPH_SOURCE_CACHE':os.environ['CHRONOSGRAPH_SOURCE_CACHE']}}}}
            steps=[]
            async with Client(config) as client:
                for tool,args in [
                  ('locate_context',{'query':'helper'}),
                  ('get_symbol_source',{'file_path':'src/pkg/a.py','symbol_name':'helper'}),
                  ('simulate_diff_impact',{'file_bodies':{'src/pkg/b.py':'def run():\n    return 42\n'}}),
                  ('record_verified_finding',{'summary':'Workflow helper evidence','evidence_note':'Captured helper returns 1; observed source only. No fixture test command executed.','supporting_file_shas':{'src/pkg/a.py':sha}}),
                  ('recall_task_memory',{'query':'Workflow helper'})]:
                    result=await client.call_tool(tool,{'tenant_graph':tenant,**args})
                    assert not result.is_error
                    if tool=='simulate_diff_impact':assert result.data['sandbox_cleaned_up']
                    if tool=='recall_task_memory':assert result.data['findings']
                    steps.append({'tool':tool,'status':'PASS'})
            return steps
        steps=asyncio.run(workflow())
        Path(output).write_text(json.dumps({'tenant_graph':tenant,'stats':stats,'steps':steps,
            'evaluation_kind':'SCRIPTED_REAL_STDIO_MCP_INTEGRATION_NOT_EXTERNAL_MODEL_AGENT','model_calls':0},indent=2))
    except BaseException:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()
        raise

if __name__=='__main__':run(sys.argv[1])
