"""Bounded, serialized handoffs. Not a scheduler, auth boundary, or worker lease."""
import json
import time
import uuid
from typing import Literal
from fastapi import HTTPException
from pydantic import Field
from app.db.client import db_manager
from app.services import task_runtime as rt
from app.services.common import read
from app.services.mutation_guard import mutation_guard, require_lease


class AssignmentInput(rt.Scoped):
    plan_id: str
    pack_id: str
    run_id: str
    owner: str = Field(min_length=1, max_length=200)
    role: Literal['ARCHITECT', 'WORKER', 'REVIEWER']
    deliverable: str = Field(min_length=1, max_length=2000)
    allowed_paths: list[str] = Field(min_length=1, max_length=20)
    acceptance: list[str] = Field(min_length=1, max_length=20)
    predecessor_id: str | None = None


class TransitionInput(rt.Scoped):
    owner: str = Field(min_length=1, max_length=200)
    expected_version: int = Field(ge=0)
    action: Literal['CLAIM', 'RETURN', 'REQUEST_CORRECTION', 'CLOSE']
    candidate_digest: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    report: str = Field(min_length=1, max_length=4000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    unresolved: list[str] = Field(default_factory=list, max_length=20)


def listing(tenant, task):
    rows, _ = read(tenant, '''MATCH (:ChangeTask {id:$task})-[:HAS_ASSIGNMENT]->(a:TaskAssignment)
        RETURN a ORDER BY a.created_at,a.id LIMIT 51''', {'task': task})
    if len(rows)>50:
        raise HTTPException(409, 'Assignment retention exhausted; preserve evidence and start a new task')
    return [dict(row['a'].properties) for row in rows]


def create(task, req: AssignmentInput):
    with mutation_guard(req.tenant_graph) as lock:
        rt.require_snapshot(req.tenant_graph, req.expected_revision)
        rt.plan(req.tenant_graph, task, req.plan_id)
        pack=rt.fresh_pack(req.tenant_graph,task,req.pack_id)
        run=rt.node(req.tenant_graph,'ChangeAgentRun',req.run_id)
        if any(run.get(k)!=v for k,v in dict(task_id=task,plan_id=req.plan_id,pack_id=req.pack_id).items()):
            raise HTTPException(409,'Assignment requires the actual task/plan/pack-bound run')
        if pack['plan_id']!=req.plan_id:
            raise HTTPException(409,'Assignment pack belongs to another plan')
        rt.validate_proposal_scope(req.tenant_graph,task,req.pack_id,dict.fromkeys(req.allowed_paths))
        prior=listing(req.tenant_graph,task)
        if len(prior)>=50: raise HTTPException(409,'Assignment retention exhausted')
        if any(a['run_id']==req.run_id for a in prior):
            raise HTTPException(409,'Run already has an assignment; use its explicit correction transition')
        if req.predecessor_id and not any(a['id']==req.predecessor_id and a['status'] in ('RETURNED','CLOSED') for a in prior):
            raise HTTPException(409,'Handoff predecessor must be returned or closed in this task')
        if req.role=='WORKER' and any(a['role']=='WORKER' and a['worktree_id']==run['worktree_id'] for a in prior):
            raise HTTPException(409,'Writing workers require separately owned worktrees')
        props={**req.model_dump(exclude_none=True),'id':'assignment_'+uuid.uuid4().hex,'task_id':task,
            'worktree_id':run['worktree_id'],'status':'PENDING','version':0,'claim_version':0,
            'created_at':int(time.time()),'reports_json':'[]',
            'coordination_basis':'SERIALIZED_ONE_ACTIVE_ASSIGNMENT_PER_TASK_NO_WORKER_LEASE',
            'path_boundary':'ADVISORY_OUTSIDE_MEDIATED_PROPOSAL_CAPTURE'}
        require_lease(lock)
        db_manager.query(req.tenant_graph,'''MATCH (t:ChangeTask {id:$task}),(r:ChangeAgentRun {id:$run})
            CREATE (a:TaskAssignment) SET a=$props CREATE (t)-[:HAS_ASSIGNMENT]->(a)
            CREATE (a)-[:ASSIGNED_RUN]->(r)''',{'task':task,'run':req.run_id,'props':props})
        return props


def transition(task, ident, req: TransitionInput):
    with mutation_guard(req.tenant_graph) as lock:
        rt.require_snapshot(req.tenant_graph,req.expected_revision)
        a=rt.node(req.tenant_graph,'TaskAssignment',ident)
        rt.plan(req.tenant_graph,task,a['plan_id'])
        rt.fresh_pack(req.tenant_graph,task,a['pack_id'])
        if a['task_id']!=task or a['owner']!=req.owner or a['version']!=req.expected_version:
            raise HTTPException(409,'Stale assignment version, owner or task; reload explicit handoff')
        allowed={'CLAIM':('PENDING','CORRECTION_REQUESTED'),'RETURN':('CLAIMED',),
                 'REQUEST_CORRECTION':('RETURNED',),'CLOSE':('RETURNED',)}
        if a['status'] not in allowed[req.action]: raise HTTPException(409,'Invalid assignment transition')
        if req.action=='CLAIM':
            active=[p for p in listing(req.tenant_graph,task) if p['status']=='CLAIMED' and p['id']!=ident]
            if active: raise HTTPException(409,'Another assignment owns this serialized task; concurrent claims refused')
            a['claim_version']+=1
        a['status']={'CLAIM':'CLAIMED','RETURN':'RETURNED','REQUEST_CORRECTION':'CORRECTION_REQUESTED','CLOSE':'CLOSED'}[req.action]
        a['version']+=1
        reports=json.loads(a['reports_json']);reports.append({**req.model_dump(exclude_none=True),'version':a['version'],
            'claim_version':a['claim_version'],'observed_at':int(time.time()),'provenance':'LOCAL_CLIENT_DECLARED_NOT_TEST_ATTESTATION'})
        if len(reports)>100:raise HTTPException(409,'Assignment report retention exhausted')
        a['reports_json']=rt.canonical(reports)
        require_lease(lock)
        db_manager.query(req.tenant_graph,'MATCH (a:TaskAssignment {id:$id}) SET a=$props',{'id':ident,'props':a})
        return a


def validate_candidate(tenant, task, run, paths, assignment_id, claim_version):
    assignments=[a for a in listing(tenant,task) if a['run_id']==run]
    if not assignments:
        if assignment_id is not None or claim_version is not None:raise HTTPException(409,'Unknown assignment for run')
        return None
    a=assignments[0]
    if (a['role']!='WORKER' or a['status']!='CLAIMED' or a['id']!=assignment_id or a['claim_version']!=claim_version):
        raise HTTPException(409,'Only the current claimed worker can submit this assigned run; reload claim version')
    if set(paths)-set(a['allowed_paths']):raise HTTPException(409,'Candidate contains changes outside assignment allowed paths')
    return {'assignment_id':a['id'],'claim_version':a['claim_version'],'owner':a['owner']}
