"""Local-only trusted-user demo API. Do not expose mutation routes publicly."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from app.db.client import db_manager
from app.local_boundary import local_ui_origins
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
    'http://localhost:3004','http://127.0.0.1:3004'] + local_ui_origins(),allow_methods=['GET','POST'],allow_headers=['Content-Type','X-ChronosGraph-Action'])


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
        meta,_=read(tenant,"MATCH (m:RepoMetadata) RETURN m.repository AS repository,m.source_revision AS source_revision,m.selected_branch AS selected_branch,m.ingested_at AS ingested_at LIMIT 1")
        repo=meta[0]["repository"] if meta else REPOS.get(tenant,tenant)
        tenant_exists(tenant)
        count,_=read(tenant,'MATCH (n) RETURN count(n) AS node_count')
        edges,_=read(tenant,'MATCH ()-[r]->() RETURN count(r) AS edge_count')
        prs,_=read(tenant,'''MATCH (p:PullRequest) RETURN p.number AS number,p.title AS title,p.url AS url,
          p.source_type AS source_type,p.record_kind AS record_kind,p.commit_sha AS commit_sha
          ORDER BY coalesce(p.committed_at,p.merged_at,0) DESC,p.number LIMIT 40''')
        presets,_=read(tenant,'''MATCH (:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File)
        RETURN DISTINCT f.path AS path ORDER BY path LIMIT 10''')
        data.append({'tenant_graph':tenant,'repository':repo,
                     'source_revision':meta[0].get('source_revision') if meta else None,
                     'selected_branch':meta[0].get('selected_branch') if meta else None,
                     'ingested_at':meta[0].get('ingested_at') if meta else None,'node_count':count[0]['node_count'],
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


from app.services.workspace import workspace_snapshot


@app.get('/api/v1/workspace/snapshot')
def workspace_snapshot_metadata(tenant_graph: str):
    return workspace_snapshot(tenant_graph)


# Read-only developer command center; legacy APIs remain compatible.
from app.services.command_center import overview, file_detail, file_source, history

@app.get('/api/v1/repository/map')
def repository_map(tenant_graph: str, prefix: str='', after: str=''):
    return overview(tenant_graph,prefix,after)

@app.get('/api/v1/repository/search')
def repository_search(tenant_graph: str, query: str, after: str='', limit: int=50):
    from app.services.command_center import search_repository
    return search_repository(tenant_graph,query,after,limit)

@app.get('/api/v1/repository/file')
def repository_file(tenant_graph: str, file_path: str):
    return file_detail(tenant_graph,file_path)

@app.get('/api/v1/repository/file-source')
def repository_file_source(tenant_graph: str, file_path: str, expected_revision: str):
    return file_source(tenant_graph, file_path, expected_revision)


@app.get('/api/v1/repository/history')
def repository_history(tenant_graph: str, commit: str='', after: str='', change_after: str=''):
    return history(tenant_graph,commit,after,change_after)


from app.services.import_jobs import ImportRequest, authorize, enabled, start_import, receipt

@app.get('/api/v1/imports/capabilities')
def import_capabilities():
    return {'enabled':enabled(),'public_only':True,'single_worker':True,'timeout_seconds':300,
            'receipt_persistence':'REDIS_SEVEN_DAYS_API_RESTART_SAFE','client_request_id_supported':True}

@app.post('/api/v1/imports',status_code=202)
def import_start(body: ImportRequest, request: Request):
    authorize(request)
    return start_import(body)

@app.get('/api/v1/imports/{ident}')
def import_receipt(ident: str):
    return receipt(ident)


# Exact-proposal lifecycle: trusted loopback operator UI, never public authentication.
from app.services.change_lifecycle import (ProposalInput, DecisionInput, ExecutionInput,
    propose, list_proposals, decide, report)


def proposal_operator(request):
    if (request.url.hostname not in ('localhost', '127.0.0.1')
        or request.headers.get('origin') not in local_ui_origins()
        or request.headers.get('x-chronosgraph-action') != 'proposal-operator'):
        raise HTTPException(403, 'Use the configured loopback operator UI and explicit action header')


@app.get('/api/v1/proposals')
def proposal_list(tenant_graph: str, revision: str):
    return list_proposals(tenant_graph, revision)


@app.post('/api/v1/proposals')
def proposal_create(body: ProposalInput, request: Request):
    proposal_operator(request)
    return propose(body, actor='BROWSER_OPERATOR')


@app.post('/api/v1/proposals/{proposal_id}/decision')
def proposal_decision(proposal_id: str, body: DecisionInput, request: Request):
    proposal_operator(request)
    return decide(proposal_id, body)


@app.post('/api/v1/proposals/{proposal_id}/execution')
def proposal_execution(proposal_id: str, body: ExecutionInput, request: Request):
    proposal_operator(request)
    return report(proposal_id, body)

from app.services.worktree_runner import WorktreeInput, execute as execute_worktree, capabilities as runner_capabilities


@app.get('/api/v1/proposals/runner-capabilities')
def proposal_runner_capabilities(tenant_graph: str):
    tenant_exists(tenant_graph)
    return runner_capabilities(tenant_graph)


@app.post('/api/v1/proposals/{proposal_id}/execute-disposable-worktree')
def proposal_worktree_execution(proposal_id: str, body: WorktreeInput, request: Request):
    proposal_operator(request)
    return execute_worktree(proposal_id, body)

from pydantic import BaseModel, Field


class CommandPolicyInput(PolicyOverrideRequest):
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')


@app.post('/api/v1/command-center/policy-override')
def command_policy(body: CommandPolicyInput, request: Request):
    proposal_operator(request)
    return override_policy(body, expected_revision=body.expected_revision)
