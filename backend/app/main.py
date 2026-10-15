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
from app.services.common import tenant_exists,read,graph_payload
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
    'http://127.0.0.1:3000','http://127.0.0.1:3001'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])


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
    for tenant,repo in REPOS.items():
        tenant_exists(tenant)
        count,_=read(tenant,'MATCH (n) RETURN count(n) AS node_count')
        prs,_=read(tenant,'MATCH (p:PullRequest) RETURN p.number AS number,p.title AS title,p.url AS url ORDER BY number LIMIT 10')
        presets,_=read(tenant,'''MATCH (:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File)
        RETURN DISTINCT f.path AS path ORDER BY path LIMIT 10''')
        data.append({'tenant_graph':tenant,'repository':repo,'node_count':count[0]['node_count'],
                     'pull_requests':prs,'preset_files':[r['path'] for r in presets]})
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
