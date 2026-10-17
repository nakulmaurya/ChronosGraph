"""Keep an owned Git fixture alive for real browser approval/execution tests."""
import asyncio,importlib.util,json,os,signal,sys,tempfile,time
from pathlib import Path
from pytest import MonkeyPatch
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hero',root/'backend/tests/test_change_lifecycle.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
stop=False
def stopping(*_):
    global stop
    stop=True
signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
with tempfile.TemporaryDirectory(prefix='chronos-hero-ui-') as tmp:
    patch=MonkeyPatch();fixture=m.hero.__wrapped__(Path(tmp),patch)
    tenant,revision,checkout,files=next(fixture)
    try:
        click_tenant = None
        if os.environ.get("FINAL01_DEMO_IMPORT_CLICK") == "1":
            from app.ingestion.github_import import inspect_remote, import_public
            patch.setenv("CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT", "1")
            pinned = inspect_remote("https://github.com/pallets/click", "main")
            click_tenant = "repo_hero_demo_click"
            import_public("https://github.com/pallets/click", "main", click_tenant, pinned["source_revision"])
        async def publish():
            transport=PythonStdioTransport(root/'backend/app/mcp_server/server.py',python_cmd=sys.executable,cwd=str(root/'backend'),env={**os.environ,'CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD':'1'},keep_alive=False)
            async with Client(transport) as client:
                guard={'tenant_graph':tenant,'expected_revision':revision}
                await client.call_tool('inspect_repository_snapshot',guard)
                await client.call_tool('locate_context',{**guard,'query':'calculate_discount','budget_bytes':8192})
                await client.call_tool('get_symbol_source',{**guard,'file_path':'core/pricing.py','symbol_name':'calculate_discount'})
                bodies={'core/pricing.py':'def discounted_total(amount, tier):\n    return amount * 0.9 if tier == "gold" else amount\n'}
                broken=await client.call_tool('propose_change_for_approval',{**guard,'task_title':'Catch the incomplete pricing rename','proposed_files':bodies,'idempotency_key':'ui-breaking'})
                bodies['services/checkout.py']='from core.pricing import discounted_total\ndef checkout(amount):\n    return discounted_total(amount, "gold")\n'
                fixed=await client.call_tool('propose_change_for_approval',{**guard,'task_title':'Coordinate pricing and checkout rename','proposed_files':bodies,'idempotency_key':'ui-coordinated'})
                return broken.data,fixed.data
        broken,fixed=asyncio.run(publish())
        metadata={'tenant':tenant,'revision':revision,'root':str(checkout),'allowed_root':tmp,'broken':broken['id'],'fixed':fixed['id'],'proposal_hash':fixed['proposal_hash'],'click_tenant':click_tenant}
        Path(sys.argv[1]).write_text(json.dumps(metadata))
        while not stop:time.sleep(.2)
    finally:
        try:next(fixture)
        except StopIteration:pass
        patch.undo()
