"""Local-only trusted-user demo API. Do not expose mutation routes publicly."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from app.db.client import db_manager
from app.ingestion.seed_repos import REPOS, seed_single_repo
from app.models import (SandboxAuditRequest,SandboxAuditResponse,BrainQueryRequest,
    PolicyOverrideRequest,PolicyLineageResponse,InvestigationRunRequest,InvestigationRunResponse,
    GraphSubgraphPayload)
from app.services.common import tenant_exists,registered_tenants,read,graph_payload
from app.services.sandbox_auditor import audit_sandbox
from app.services.company_brain import ask_brain,override_policy
from app.services.memory_compiler import run_investigation


@asynccontextmanager
async def lifespan(app):
    # Fail visibly rather than replace live data or silently serve an empty demo.
    db_manager.db.connection.ping()
    for tenant in REPOS:
        if tenant not in db_manager.list_tenant_graphs():
            seed_single_repo(tenant)
        else:
            files,_=read(tenant,'MATCH (f:File) RETURN count(f) AS item_count')
            if not files[0]['item_count']: seed_single_repo(tenant)
    yield


app=FastAPI(title='ChronosGraph',version='0.2.0',lifespan=lifespan,
    description='Local trusted-client graph demo. Not a production authorization boundary.')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://localhost:3001',
    'http://127.0.0.1:3000','http://127.0.0.1:3001',
    'http://localhost:3002','http://127.0.0.1:3002',
    'http://localhost:3003','http://127.0.0.1:3003',
    'http://localhost:3004','http://127.0.0.1:3004'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])


@app.exception_handler(RedisError)
async def database_error(request,exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503,content={'detail':'FalkorDB operation failed; check local database logs'})


@app.get('/health')
def health():
    return {'status':'ok' if db_manager.db.connection.ping() else 'unavailable'}


@app.get('/api/v1/tenants')
def tenants():
    data=[]
    for tenant in registered_tenants():
        meta,_=read(tenant,"MATCH (m:RepoMetadata) RETURN m.repository AS repository LIMIT 1")
        repo=meta[0]["repository"] if meta else REPOS.get(tenant,tenant)
        tenant_exists(tenant)
        count,_=read(tenant,'MATCH (n) RETURN count(n) AS node_count')
        edges,_=read(tenant,'MATCH ()-[r]->() RETURN count(r) AS edge_count')
        prs,_=read(tenant,'''MATCH (p:PullRequest) RETURN p.number AS number,p.title AS title,p.url AS url,
          p.source_type AS source_type,p.record_kind AS record_kind,p.commit_sha AS commit_sha
          ORDER BY coalesce(p.committed_at,p.merged_at,0) DESC,p.number LIMIT 40''')
        presets,_=read(tenant,'''MATCH (:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File)
        RETURN DISTINCT f.path AS path ORDER BY path LIMIT 10''')
        data.append({'tenant_graph':tenant,'repository':repo,'node_count':count[0]['node_count'],
                     'edge_count':edges[0]['edge_count'],'indexed_record_count':read(tenant,'MATCH (p:PullRequest) RETURN count(p) AS n')[0][0]['n'],
                     'pull_requests':prs,'preset_files':[r['path'] for r in presets] or [r['path'] for r in read(tenant,'MATCH (f:File) RETURN f.path AS path ORDER BY f.pagerank DESC,f.path LIMIT 10')[0]]})
    return data


@app.get('/api/v1/subgraph',response_model=GraphSubgraphPayload)
def subgraph(tenant_graph: str='repo_falkordb_py'):
    tenant_exists(tenant_graph)
    return graph_payload(tenant_graph)


@app.post('/api/v1/track1/sandbox-audit',response_model=SandboxAuditResponse)
def sandbox_audit(req: SandboxAuditRequest):
    return audit_sandbox(req)


@app.post('/api/v1/track3/ask-brain',response_model=PolicyLineageResponse)
def brain(req: BrainQueryRequest):
    return ask_brain(req)


@app.post('/api/v1/track3/override-policy',response_model=PolicyLineageResponse)
def policy(req: PolicyOverrideRequest):
    return override_policy(req)


@app.post('/api/v1/track2/investigate',response_model=InvestigationRunResponse)
def investigate(req: InvestigationRunRequest):
    return run_investigation(req)


# Additive context/wiki API. Five core MCP tool names remain unchanged.
from app.models import WikiCompileRequest
from app.services.second_brain_wiki import context_stats,compile_wiki,compact_snapshot


@app.get('/api/v1/ctx/stats')
def ctx_stats(tenant_graph: str='repo_falkordb_py',file_path: str | None=None):
    return context_stats(tenant_graph,file_path)


@app.post('/api/v1/ctx/compile-wiki')
def ctx_compile_wiki(req: WikiCompileRequest):
    return compile_wiki(req.tenant_graph,req.file_path,req.export)


@app.get('/api/v1/ctx/wiki-page')
def ctx_wiki_page(tenant_graph: str='repo_falkordb_py',page: str='index.md'):
    # Look up a generated key, never a filesystem path supplied by a client.
    result=compile_wiki(tenant_graph)
    if page not in result['pages']:
        raise HTTPException(404,'Generated wiki page not found')
    return {'tenant_graph':tenant_graph,'page':page,'markdown':result['pages'][page],
        'content_id':result['content_id'],'model_calls':0}


@app.post('/api/v1/ctx/compact-snapshot')
def ctx_compact_snapshot(req: WikiCompileRequest):
    return compact_snapshot(req.tenant_graph,req.file_path)


@app.get('/api/v1/ctx/export')
def ctx_export_download(tenant_graph: str='repo_falkordb_py',file_path: str | None=None):
    import io,zipfile
    from fastapi.responses import Response
    result=compile_wiki(tenant_graph,file_path)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        for path,body in result['pages'].items():
            info=zipfile.ZipInfo(path,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,body.encode('utf-8'))
        archive.writestr('ResumeSnapshot.md',result['resume_snapshot']['markdown'].encode('utf-8'))
    return Response(stream.getvalue(),media_type='application/zip',
        headers={'Content-Disposition':f'attachment; filename="{tenant_graph}-obsidian-vault.zip"'})


from app.services.second_brain_wiki import brain_wiki_slice,brain_lint_and_compact,brain_vault_zip

@app.get('/api/v1/brain/wiki-slice')
def brain_slice(tenant_graph: str='repo_falkordb_py',file_path: str | None=None):
    return brain_wiki_slice(tenant_graph,file_path)

@app.post('/api/v1/brain/lint-and-compact')
def brain_compact(req: WikiCompileRequest):
    return brain_lint_and_compact(req.tenant_graph,req.file_path)

@app.get('/api/v1/brain/obsidian-vault.zip')
def brain_download(tenant_graph: str='repo_falkordb_py',file_path: str | None=None):
    from fastapi.responses import Response
    return Response(brain_vault_zip(tenant_graph,file_path),media_type='application/zip',
        headers={'Content-Disposition':f'attachment; filename="{tenant_graph}-obsidian-vault.zip"'})


from app.models import DiffImpactRequest
from app.services.diff_impact import simulate_diff


@app.post('/api/v1/diff/impact')
def diff_impact(req: DiffImpactRequest):
    return simulate_diff(req)


from app.models import FindingRequest
from app.services.context_locator import locate_context,symbol_source
from app.services.task_memory import record_finding,recall_findings
from app.services.agent_activity import activity


@app.get('/api/v1/context/locate')
def context_locate(tenant_graph: str,query: str,budget_bytes: int=4096):
    return locate_context(tenant_graph,query,budget_bytes)


@app.get('/api/v1/context/symbol-source')
def context_symbol_source(tenant_graph: str,file_path: str,symbol_name: str):
    return symbol_source(tenant_graph,file_path,symbol_name)


@app.post('/api/v1/memory/findings')
def memory_record(req: FindingRequest):
    return record_finding(req)


@app.get('/api/v1/memory/findings')
def memory_recall(tenant_graph: str,query: str='',include_stale: bool=False,limit: int=10):
    return recall_findings(tenant_graph,query,include_stale,limit)


@app.get('/api/v1/activity')
def agent_activity(tenant_graph: str,cursor: str | None=None,limit: int=50):
    return activity(tenant_graph,cursor,limit)


@app.get('/api/v1/context/owners')
def context_owners(tenant_graph: str, file_path: str):
    from app.services.ownership import get_ownership
    return get_ownership(tenant_graph, file_path)
