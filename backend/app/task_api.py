"""Project-scoped local bridge. Not a multi-user authentication boundary."""
from fastapi import APIRouter, HTTPException, Request
from app.local_boundary import local_ui_origins
from app.services import task_runtime as runtime

router = APIRouter(prefix='/api/v1/tasks', tags=['local-task-runtime'])


def local_bridge(request: Request):
    origin = request.headers.get('origin')
    if (request.url.hostname not in ('127.0.0.1', 'localhost')
            or request.headers.get('x-chronosgraph-action') != 'task-runtime'
            or (origin is not None and origin not in local_ui_origins())):
        raise HTTPException(403, 'Use the trusted loopback task bridge with explicit action header')


@router.post('')
def create(body: runtime.TaskInput, request: Request):
    local_bridge(request)
    return runtime.create_task(body)


@router.get('/{task_id}')
def detail(task_id: str, tenant_graph: str, expected_revision: str):
    return runtime.task_detail(tenant_graph, expected_revision, task_id)


@router.post('/{task_id}/plans')
def revise(task_id: str, body: runtime.PlanInput, request: Request):
    local_bridge(request)
    return runtime.revise_plan(task_id, body)


@router.post('/{task_id}/context-packs')
def pack(task_id: str, body: runtime.PackInput, request: Request):
    local_bridge(request)
    return runtime.build_pack(task_id, body)


@router.get('/{task_id}/context-packs/{pack_id}')
def get_pack(task_id: str, pack_id: str, tenant_graph: str, expected_revision: str):
    runtime.require_snapshot(tenant_graph, expected_revision)
    value = runtime.fresh_pack(tenant_graph, task_id, pack_id)
    if value['task_id'] != task_id:
        raise HTTPException(404, 'Context pack does not belong to selected task')
    runtime.plan(tenant_graph, task_id, value['plan_id'])
    return runtime.public_pack(value)


@router.post('/{task_id}/runs')
def bind(task_id: str, body: runtime.RunInput, request: Request):
    local_bridge(request)
    return runtime.bind_run(task_id, body)


@router.post('/{task_id}/runs/{run_id}/events')
def event(task_id: str, run_id: str, body: runtime.EventInput, request: Request):
    local_bridge(request)
    run = runtime.node(body.tenant_graph, 'ChangeAgentRun', run_id)
    if run.get('task_id') != task_id:
        raise HTTPException(404, 'Run does not belong to selected task')
    return runtime.record_event(run_id, body)


@router.get('/discovery/candidates')
def discover_candidates(tenant_graph: str, expected_revision: str, query: str):
    runtime.require_snapshot(tenant_graph, expected_revision)
    result = runtime.locate_context(tenant_graph, query, budget_bytes=4096)
    return {'selection_required':True, 'pack_created':False,
            'candidates':[{'path':e['path'],'why':e['why_included']} for e in result['entry_points']],
            'coverage':result['coverage']}
