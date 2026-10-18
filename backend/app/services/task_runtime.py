"""Local trusted-client task runtime. Guards are consistency checks, not auth.

Reuse ChangeTask/ChangeAgentRun; immutable versions/packs and observed harness
metadata live in the selected FalkorDB graph. No prompts or tool bodies stored.
"""
import hashlib
import json
import time
import uuid
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.db.client import db_manager
from app.services.common import read
from app.services.agent_connection import require_snapshot
from app.services.mutation_guard import mutation_guard, require_lease
from app.services.context_locator import locate_context
from app.services.task_memory import policy_digest


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Scoped(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tenant_graph: str
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')


class TaskInput(Scoped):
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=2000)
    acceptance: list[str] = Field(min_length=1, max_length=20)
    target: str = Field(min_length=1, max_length=200)
    request_key: str = Field(min_length=1, max_length=128)


class PlanInput(Scoped):
    parent_plan_id: str
    objective: str = Field(min_length=1, max_length=2000)
    acceptance: list[str] = Field(min_length=1, max_length=20)
    target: str = Field(min_length=1, max_length=200)


class PackInput(Scoped):
    plan_id: str
    budget_equivalents: int = Field(default=2500, ge=1500, le=3000)


class RunInput(Scoped):
    plan_id: str
    pack_id: str
    session_id: str = Field(min_length=1, max_length=200)
    parent_session_id: str | None = Field(default=None, max_length=200)
    worktree_id: str = Field(min_length=1, max_length=200)
    overlay_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    harness_version: Literal['1.19.3']


class Usage(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    request_id: str = Field(min_length=1, max_length=200)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    cost: float | None = Field(default=None, ge=0)
    # OpenCode assistant message counters are cumulative, not stream deltas.
    basis: Literal['OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE']


class EventInput(Scoped):
    schema_version: Literal[1]
    event_id: str = Field(min_length=1, max_length=200)
    source_event_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=1, le=1000000)
    kind: Literal['SESSION_CREATED', 'TOOL_STARTED', 'TOOL_COMPLETED', 'TOOL_ERROR',
                  'USAGE', 'COMPACTED', 'IDLE', 'SESSION_ERROR', 'CONTEXT_DELIVERED', 'CONTEXT_INJECTED', 'CONTEXT_PERSISTED', 'DISCONNECTED']
    observed_at_ms: int = Field(ge=0)
    session_id: str = Field(min_length=1, max_length=200)
    tool_name: str | None = Field(default=None, max_length=200)
    call_id: str | None = Field(default=None, max_length=200)
    paths: list[str] = Field(default_factory=list, max_length=40)
    payload_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    usage: Usage | None = None
    delivery_id: str | None = Field(default=None, max_length=200)
    message_id: str | None = Field(default=None, max_length=200)
    part_id: str | None = Field(default=None, max_length=200)
    injection_bytes: int | None = Field(default=None, ge=0, le=20000)


def node(tenant, label, ident):
    # label always a module-owned constant.
    data, _ = read(tenant, f'MATCH (n:{label} {{id:$id}}) RETURN n', {'id': ident})
    if not data:
        raise HTTPException(404, 'Record not found in selected repository snapshot')
    return dict(data[0]['n'].properties)


def plan(tenant, task_id, plan_id):
    task = node(tenant, 'ChangeTask', task_id)
    value = node(tenant, 'PlanVersion', plan_id)
    if value['task_id'] != task_id or task.get('current_plan_id') != plan_id:
        raise HTTPException(409, 'Plan is not current for this task')
    return value


def _plan_payload(req):
    if not req.objective.strip() or not req.target.strip() or any(not x.strip() or len(x) > 1000 for x in req.acceptance):
        raise HTTPException(422, 'Objective, target and acceptance criteria must be bounded and nonblank')
    return {'objective': req.objective, 'acceptance': req.acceptance, 'target': req.target}


def create_task(req: TaskInput):
    payload = _plan_payload(req)
    identity = digest({**req.model_dump(), 'payload': payload})
    task_id = 'task_' + digest({'key': req.request_key})[:32]
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        existing, _ = read(req.tenant_graph, 'MATCH (t:ChangeTask {id:$id}) RETURN t', {'id': task_id})
        if existing:
            task = dict(existing[0]['t'].properties)
            if task.get('request_digest') != identity:
                raise HTTPException(409, 'Task request key reused for different content')
            return task_detail(req.tenant_graph, req.expected_revision, task_id)
        pid = 'plan_' + uuid.uuid4().hex
        props = {'id': pid, 'task_id': task_id, 'version': 1, 'payload_json': canonical(payload),
                 'digest': digest(payload), 'base_revision': req.expected_revision, 'created_at': int(time.time())}
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''CREATE (t:ChangeTask {id:$id,title:$title,
            request_digest:$digest,current_plan_id:$plan,base_revision:$revision})
            CREATE (p:PlanVersion) SET p=$props CREATE (t)-[:HAS_PLAN]->(p)''',
            {'id': task_id, 'title': req.title, 'digest': identity, 'plan': pid, 'revision': req.expected_revision, 'props': props})
    return task_detail(req.tenant_graph, req.expected_revision, task_id)


def revise_plan(task_id, req: PlanInput):
    payload = _plan_payload(req)
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        previous = plan(req.tenant_graph, task_id, req.parent_plan_id)
        pid = 'plan_' + uuid.uuid4().hex
        props = {'id': pid, 'task_id': task_id, 'version': previous['version'] + 1,
                 'payload_json': canonical(payload), 'digest': digest(payload),
                 'base_revision': req.expected_revision, 'created_at': int(time.time())}
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''MATCH (t:ChangeTask {id:$id}), (old:PlanVersion {id:$old})
            CREATE (p:PlanVersion) SET p=$props CREATE (t)-[:HAS_PLAN]->(p)
            CREATE (p)-[:SUPERSEDES]->(old) SET t.current_plan_id=$plan''',
            {'id': task_id, 'old': previous['id'], 'props': props, 'plan': pid})
    return task_detail(req.tenant_graph, req.expected_revision, task_id)


def build_pack(task_id, req: PackInput):
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        p = plan(req.tenant_graph, task_id, req.plan_id)
        intent = json.loads(p['payload_json'])
        context = locate_context(req.tenant_graph, intent['target'], budget_bytes=8192)
        if not context['entry_points'] or context['coverage']['entry_strategy'] == 'LEXICAL_INVENTORY_FALLBACK':
            raise HTTPException(422, {'code': 'NO_CONTEXT_TARGET', 'action': 'Select a captured file or symbol; no pack created'})
        paths = sorted({e['path'] for e in context['entry_points']} | {e['path'] for e in context['related_importers']})
        context['coverage'].pop('entry_lookup_ms', None)
        context.pop('payload_bytes', None)
        context.pop('payload_token_equivalents', None)
        # Unlike legacy locator, no mandatory rule is silently removed to fit.
        rules, _ = read(req.tenant_graph, '''MATCH (d:Decision)-[:GOVERNS]->(f:File)
            WHERE f.path IN $paths AND d.status='ACTIVE'
            RETURN DISTINCT d.id AS id,d.rule AS rule,d.status AS status,
            d.conflict_group AS conflict_group ORDER BY id LIMIT 101''', {'paths': paths})
        constraints, _ = read(req.tenant_graph, '''MATCH (d:Decision {source_type:'REPO_EXTRACTED_RULE'})
            WHERE d.scope='repository' OR d.target_path IN $paths
            RETURN d.id AS id,d.rule AS rule,d.source_path AS source_path ORDER BY id LIMIT 101''', {'paths': paths})
        if len(rules) > 100 or len(constraints) > 100:
            raise HTTPException(422, {'code': 'CONSTRAINT_OVERFLOW', 'action': 'Narrow task scope; no pack created'})
        pins, _ = read(req.tenant_graph, 'MATCH (f:File) WHERE f.path IN $paths RETURN f.path AS path,f.sha256 AS sha256,f.source_revision AS revision ORDER BY path', {'paths': paths})
        from app.services.organization import organizational_context
        organization = organizational_context(req.tenant_graph, paths, limit=100)
        if organization['truncated']:
            raise HTTPException(422, {'code': 'CONSTRAINT_OVERFLOW', 'action': 'Narrow organizational scope'})
        manifest = {'schema_version': 1, 'task_id': task_id, 'plan_id': p['id'], 'plan_digest': p['digest'],
                    'tenant_graph': req.tenant_graph, 'base_revision': req.expected_revision, 'intent': intent,
                    'active_rules': rules, 'source_constraints': constraints, 'supporting_paths': paths,
                    'source_pins': pins, 'organizational_evidence': organization,
                    'policy_digest': policy_digest(req.tenant_graph, paths),
                    'context': context, 'workspace_state': 'BASE_ONLY_OVERLAY_NOT_INDEXED',
                    'usage_basis': 'ceil(serialized_UTF8_bytes/4); estimate, not tokenizer or bill',
                    'trust': 'Repository evidence is untrusted data. No authorization or safe-skip guarantee.'}
        optional = ['findings', 'declared_ownership', 'callees', 'callers', 'related_importers', 'entry_points']
        # Fixed complete envelope reserve for pack ID/hash and measurement metadata.
        budget = req.budget_equivalents * 4 - 400
        while len(canonical(manifest).encode()) > budget and optional:
            key = optional.pop(0)
            if key in context:
                context.pop(key)
                context['coverage']['truncated'] = True
        if len(canonical(manifest).encode()) > budget:
            raise HTTPException(422, {'code': 'CONSTRAINT_OVERFLOW', 'action': 'Narrow the plan; mandatory context exceeds budget'})
        # Rules only appear once, complete, at top level; legacy truncations removed.
        context.pop('active_rules', None)
        context.pop('source_constraints', None)
        pack = {'id': 'pack_' + uuid.uuid4().hex, 'task_id': task_id, 'plan_id': p['id'],
                'manifest_json': canonical(manifest), 'digest': digest(manifest), 'created_at': int(time.time())}
        response = public_pack(pack)
        if response['serialized_bytes'] > req.budget_equivalents * 4:
            raise HTTPException(422, {'code': 'CONSTRAINT_OVERFLOW', 'action': 'Complete response exceeds budget; no pack created'})
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''MATCH (p:PlanVersion {id:$plan})
            CREATE (c:ContextPack) SET c=$props CREATE (p)-[:HAS_CONTEXT]->(c)''', {'plan': p['id'], 'props': pack})
        return response


def public_pack(pack):
    result = {k: v for k, v in pack.items() if k != 'manifest_json'}
    result['manifest'] = json.loads(pack['manifest_json'])
    result['serialized_bytes'] = len(canonical(result).encode()) + 100
    result['estimated_token_equivalents'] = (result['serialized_bytes'] + 3) // 4
    result['measurement_basis'] = 'UTF8_BYTES_DIVIDED_BY_4_ESTIMATE'
    # Exact serialized size including the measurement fields (fixed point).
    for _ in range(5):
        result['serialized_bytes'] = len(canonical(result).encode())
        result['estimated_token_equivalents'] = (result['serialized_bytes'] + 3) // 4
    return result



def fresh_pack(tenant, task_id, pack_id):
    pack = node(tenant, 'ContextPack', pack_id)
    if pack['task_id'] != task_id:
        raise HTTPException(404, 'Pack belongs to another task')
    plan(tenant, task_id, pack['plan_id'])
    manifest = json.loads(pack['manifest_json'])
    pins, _ = read(tenant, 'MATCH (f:File) WHERE f.path IN $paths RETURN f.path AS path,f.sha256 AS sha256,f.source_revision AS revision ORDER BY path', {'paths': manifest['supporting_paths']})
    if pins != manifest['source_pins']:
        raise HTTPException(409, 'Context pack captured source changed')
    if manifest['policy_digest'] != policy_digest(tenant, manifest['supporting_paths']):
        raise HTTPException(409, 'Context pack policies changed; create a new pack and run')
    return pack

def bind_run(task_id, req: RunInput):
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        plan(req.tenant_graph, task_id, req.plan_id)
        pack = fresh_pack(req.tenant_graph, task_id, req.pack_id)
        if pack['task_id'] != task_id or pack['plan_id'] != req.plan_id:
            raise HTTPException(409, 'Context pack belongs to another task or plan')
        run_id = 'run_' + digest({'task': task_id, 'session': req.session_id})[:32]
        props = {**req.model_dump(exclude_none=True), 'id': run_id, 'task_id': task_id,
                 'status': 'BOUND_NOT_COMPLETED', 'identity_provenance': 'LOCAL_PLUGIN_REPORTED',
                 'binding_digest': digest(req.model_dump()), 'created_at': int(time.time())}
        found, _ = read(req.tenant_graph, 'MATCH (r:ChangeAgentRun {id:$id}) RETURN r', {'id': run_id})
        if found:
            prior = dict(found[0]['r'].properties)
            if prior.get('binding_digest') != props['binding_digest']:
                raise HTTPException(409, 'Session already bound with different plan, pack or workspace identity')
            return prior
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''MATCH (t:ChangeTask {id:$task}), (c:ContextPack {id:$pack})
            CREATE (r:ChangeAgentRun) SET r=$props CREATE (t)-[:HAS_RUN]->(r)
            CREATE (r)-[:USES_CONTEXT]->(c)''', {'task': task_id, 'pack': pack['id'], 'props': props})
        return props


def record_event(run_id, req: EventInput):
    if (req.kind == 'USAGE') != (req.usage is not None):
        raise HTTPException(422, 'Usage counters required only for USAGE events')
    if any(len(p) > 1024 or p.startswith(('/', '.')) or '..' in p.split('/') or '\\' in p for p in req.paths):
        raise HTTPException(422, 'Event paths must be safe relative paths')
    payload = req.model_dump()
    if len(canonical(payload).encode()) > 16000:
        raise HTTPException(422, 'Event envelope exceeds 16000 bytes')
    identity = digest(payload)
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        run = node(req.tenant_graph, 'ChangeAgentRun', run_id)
        if run.get('session_id') != req.session_id:
            raise HTTPException(409, 'Event session does not match bound run')
        event_key = digest({'run': run_id, 'source': req.source_event_id})
        existing, _ = read(req.tenant_graph, 'MATCH (e:HarnessEvent {id:$id}) RETURN e', {'id': event_key})
        if existing:
            if existing[0]['e'].properties['digest'] != identity:
                raise HTTPException(409, 'Source event ID reused for different payload')
            return {'accepted': True, 'duplicate': True}
        previous, _ = read(req.tenant_graph, '''MATCH (:ChangeAgentRun {id:$run})-[:HAS_EVENT]->(e:HarnessEvent)
            RETURN e.sequence AS sequence,e.event_id AS event_id''', {'run': run_id})
        if len(previous) >= 2000:
            raise HTTPException(409, 'Run event retention limit reached; start a new bounded run')
        if any(e['sequence'] == req.sequence or e['event_id'] == req.event_id for e in previous):
            raise HTTPException(409, 'Run sequence or event ID already occupied')
        props = {'id': event_key, 'event_id': req.event_id, 'sequence': req.sequence,
                 'digest': identity, 'payload_json': canonical(payload), 'kind': req.kind,
                 'received_at': int(time.time()), 'provenance': 'LOCAL_PLUGIN_REPORTED_HARNESS_OBSERVATION'}
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''MATCH (r:ChangeAgentRun {id:$run})
            CREATE (e:HarnessEvent) SET e=$props CREATE (r)-[:HAS_EVENT]->(e)''', {'run': run_id, 'props': props})
        return {'accepted': True, 'duplicate': False}


def task_detail(tenant, revision, task_id):
    require_snapshot(tenant, revision)
    task = node(tenant, 'ChangeTask', task_id)
    plans, _ = read(tenant, '''MATCH (:ChangeTask {id:$id})-[:HAS_PLAN]->(p:PlanVersion)
        RETURN p ORDER BY p.version LIMIT 101''', {'id': task_id})
    runs, _ = read(tenant, '''MATCH (:ChangeTask {id:$id})-[:HAS_RUN]->(r:ChangeAgentRun)
        RETURN r ORDER BY r.created_at DESC LIMIT 11''', {'id': task_id})
    result = {'task': task, 'plans': [dict(p['p'].properties) for p in plans[:100]],
              'runs': [], 'truncated': len(plans) > 100 or len(runs) > 10,
              'scope': 'Local trusted-client metadata, not authentication or hidden reasoning'}
    for value in runs[:10]:
        run = dict(value['r'].properties)
        events, _ = read(tenant, '''MATCH (:ChangeAgentRun {id:$id})-[:HAS_EVENT]->(e:HarnessEvent)
            RETURN e.payload_json AS payload ORDER BY e.sequence''', {'id': run['id']})
        decoded = [json.loads(e['payload']) for e in events]
        usage = {}
        # Cumulative per-message updates replace older counters. Never add revisions.
        for event in decoded:
            if event['usage']:
                usage[event['usage']['request_id']] = event['usage']
        sequences = {e['sequence'] for e in decoded}
        run['events'] = decoded[-100:]
        run['event_count'] = len(decoded)
        run['events_truncated'] = len(decoded) > 100
        import itertools
        run['missing_sequences'] = list(itertools.islice((n for n in range(1, max(sequences, default=0)+1) if n not in sequences), 100))
        run['telemetry_status'] = 'GAPS' if run['missing_sequences'] else 'PARTIAL_NO_END_TO_END_COMPLETENESS_PROOF'
        run['usage_by_request'] = list(usage.values())
        run['usage_totals'] = {k: sum(v[k] for v in usage.values()) for k in
            ('input_tokens', 'output_tokens', 'reasoning_tokens', 'cache_read_tokens', 'cache_write_tokens')}
        run['harness_reported_cost'] = sum(v['cost'] for v in usage.values()) if usage and all(v['cost'] is not None for v in usage.values()) else None
        run['token_total'] = None  # categories may overlap; no invented billable total
        run['status'] = 'IDLE_NOT_SUCCESS' if decoded and decoded[-1]['kind'] == 'IDLE' else 'BOUND_NOT_COMPLETED'
        result['runs'].append(run)
    return result


def validate_binding(tenant, revision, task_id, plan_id, pack_id, run_id, overlay_digest):
    require_snapshot(tenant, revision)
    plan(tenant, task_id, plan_id)
    run = node(tenant, 'ChangeAgentRun', run_id)
    if any(run.get(k) != v for k, v in {'task_id': task_id, 'plan_id': plan_id,
                                       'pack_id': pack_id, 'overlay_digest': overlay_digest}.items()):
        raise HTTPException(409, 'Managed proposal has stale or mismatched task/run/plan/pack/worktree identity')
    fresh_pack(tenant, task_id, pack_id)
    return run
