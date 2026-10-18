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
from pydantic import BaseModel, ConfigDict, Field, model_validator
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
    expansion_paths: list[str] = Field(default_factory=list, max_length=20)


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
    request_id: str | None = Field(default=None, min_length=1, max_length=200)
    session_id: str | None = Field(default=None, max_length=200)
    message_id: str | None = Field(default=None, max_length=200)
    part_id: str | None = Field(default=None, max_length=200)
    provider_request_id: str | None = Field(default=None, max_length=200)
    provider_id: str | None = Field(default=None, max_length=200)
    model_id: str | None = Field(default=None, max_length=200)
    count_semantics: str | None = Field(default=None, max_length=300)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    cost: float | None = Field(default=None, ge=0)
    # OpenCode assistant message counters are cumulative, not stream deltas.
    basis: Literal['OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE','OPENCODE_COMPLETED_STEP_PART']

    @model_validator(mode='after')
    def valid_identity(self):
        if self.basis=='OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE' and not self.request_id:
            raise ValueError('Legacy message counter requires its historical request_id field')
        if self.basis=='OPENCODE_COMPLETED_STEP_PART' and (not all((self.session_id,self.message_id,self.part_id)) or self.request_id is not None):
            raise ValueError('Completed step requires session/message/part IDs, not a fabricated provider request ID')
        return self


class MessageCost(BaseModel):
    model_config = ConfigDict(extra='forbid',allow_inf_nan=False)
    message_id: str = Field(min_length=1,max_length=200)
    provider_id: str = Field(max_length=200)
    model_id: str = Field(max_length=200)
    cost: float = Field(ge=0)
    completed_at_ms: int | None = Field(default=None,ge=0)
    error_completion: bool = False
    basis: Literal['OPENCODE_MESSAGE_CUMULATIVE_COST_RECONCILIATION_ONLY']


class EventInput(Scoped):
    schema_version: Literal[1,2]
    event_id: str = Field(min_length=1, max_length=200)
    source_event_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=1, le=1000000)
    kind: Literal['SESSION_CREATED', 'TOOL_STARTED', 'TOOL_COMPLETED', 'TOOL_ERROR',
                  'USAGE', 'COMPACTED', 'IDLE', 'SESSION_ERROR', 'CONTEXT_DELIVERED', 'CONTEXT_INJECTED', 'CONTEXT_PERSISTED', 'USAGE_RECONCILIATION', 'USAGE_EXPORT_RECONCILED', 'DISCONNECTED']
    observed_at_ms: int = Field(ge=0)
    session_id: str = Field(min_length=1, max_length=200)
    tool_name: str | None = Field(default=None, max_length=200)
    call_id: str | None = Field(default=None, max_length=200)
    paths: list[str] = Field(default_factory=list, max_length=40)
    payload_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    usage: Usage | None = None
    message_cost: MessageCost | None = None
    reconciliation_message_count: int | None = Field(default=None,ge=0,le=100)
    export_may_be_truncated: bool | None = None
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


def analysis_scope(tenant, target, expansion_paths):
    """Resolve exact identity and bounded graph scope BEFORE presentation trimming."""
    from app.services.diff_impact import safe_path
    for path in expansion_paths:
        safe_path(path)
    roots, _ = read(tenant, 'MATCH (f:File {path:$target}) RETURN f.path AS path', {'target':target})
    if not roots and ' ' not in target:
        for label in ('Function', 'Class'):
            prop = 'qualified_name' if ':' in target else 'name'
            hits, _ = read(tenant, f'MATCH (f:File)-[:DEFINES]->(s:{label} {{{prop}:$target}}) RETURN DISTINCT f.path AS path LIMIT 3', {'target':target})
            roots.extend(hits)
    root_paths = sorted({r['path'] for r in roots})
    if len(root_paths) != 1:
        raise HTTPException(422, {'code':'NO_CONTEXT_TARGET' if not root_paths else 'AMBIGUOUS_CONTEXT_TARGET',
            'candidates':root_paths, 'action':'Discover candidates, then explicitly select an exact captured file or qualified symbol; no pack created'})
    seeds = sorted(set(root_paths + expansion_paths))
    related, _ = read(tenant, '''MATCH (f:File) WHERE f.path IN $paths
        MATCH (f)-[:IMPORTS*1..3]-(other:File)
        RETURN DISTINCT other.path AS path ORDER BY path LIMIT 101''', {'paths':seeds})
    calls, _ = read(tenant, '''MATCH (f:File)-[:DEFINES]->(s:Function)-[:CALLS]-(t:Function)<-[:DEFINES]-(other:File)
        WHERE f.path IN $paths RETURN DISTINCT other.path AS path ORDER BY path LIMIT 101''', {'paths':seeds})
    all_paths = sorted(set(seeds + [r['path'] for r in related + calls]))
    # Seeds are never lost even when bounded expansion is truncated.
    paths = seeds + [p for p in all_paths if p not in seeds][:100-len(seeds)]
    return {'exact_target':{'query':target,'path':root_paths[0]}, 'paths':sorted(paths),
            'import_horizon':3,'direct_call_horizon':1,'path_limit':100,
            'truncated':len(all_paths)>100 or len(related)>100 or len(calls)>100,
            'unresolved_relationships':'Dynamic/external calls and paths beyond these bounds are not proven covered',
            'expansion_handle':{'operation':'CREATE_NEW_PACK_WITH_EXPANSION_PATHS','target':target}}


def validate_proposal_scope(tenant, task_id, pack_id, paths):
    value = fresh_pack(tenant, task_id, pack_id)
    manifest = json.loads(value['manifest_json'])
    allowed = manifest.get('analysis_scope', {}).get('paths', manifest['supporting_paths'])
    outside = sorted(set(paths)-set(allowed))
    if outside:
        raise HTTPException(409, {'code':'CONTEXT_SCOPE_EXPANSION_REQUIRED','paths':outside,
            'action':'Create an expanded pack with these expansion_paths, review mandatory policies, and bind a fresh run before proposing'})


def build_pack(task_id, req: PackInput):
    with mutation_guard(req.tenant_graph) as lease:
        require_snapshot(req.tenant_graph, req.expected_revision)
        p = plan(req.tenant_graph, task_id, req.plan_id)
        intent = json.loads(p['payload_json'])
        scope = analysis_scope(req.tenant_graph, intent['target'], req.expansion_paths)
        paths = scope['paths']
        context = locate_context(req.tenant_graph, scope['exact_target']['path'], budget_bytes=8192, trim_presentation=False)
        # Deduplicate before trimming or rejecting, not afterwards.
        context.pop('active_rules', None)
        context.pop('source_constraints', None)
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
        if len(rules)>100 or len(constraints)>100:
            raise HTTPException(422, {'code':'CONSTRAINT_OVERFLOW','action':'Constraint query exceeded its bound; narrow scope'})
        by_id = {r['id']:r for r in rules}
        for constraint in constraints:
            if constraint['id'] in by_id:
                by_id[constraint['id']].update({k:v for k,v in constraint.items() if k not in ('id','rule')})
        constraints = [c for c in constraints if c['id'] not in by_id]
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
                    'exact_target':scope['exact_target'], 'analysis_scope':scope,
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
    if (req.kind == 'USAGE_RECONCILIATION') != (req.message_cost is not None):
        raise HTTPException(422, 'Message cost is reconciliation only')
    if req.usage and req.usage.basis=='OPENCODE_COMPLETED_STEP_PART' and req.usage.session_id!=req.session_id:
        raise HTTPException(409, 'Step usage session does not match event')
    if any(len(p) > 1024 or p.startswith(('/', '.')) or '..' in p.split('/') or '\\' in p for p in req.paths):
        raise HTTPException(422, 'Event paths must be safe relative paths')
    payload = req.model_dump()
    legacy_keys = {'tenant_graph','expected_revision','schema_version','event_id','source_event_id','sequence','kind',
                   'observed_at_ms','session_id','tool_name','call_id','paths','payload_digest','usage'}
    # Keep the v1 canonical retry identity: newly introduced null defaults are not history.
    payload = {k:v for k,v in payload.items() if k in legacy_keys or v is not None}
    if req.usage and req.usage.basis=='OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE':
        old_usage_keys = {'request_id','input_tokens','output_tokens','reasoning_tokens','cache_read_tokens','cache_write_tokens','cost','basis'}
        payload['usage'] = {k:v for k,v in payload['usage'].items() if k in old_usage_keys}
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
        sequences = {e['sequence'] for e in decoded}
        run['events'] = decoded[-100:]
        run['event_count'] = len(decoded)
        run['events_truncated'] = len(decoded) > 100
        import itertools
        run['missing_sequences'] = list(itertools.islice((n for n in range(1, max(sequences, default=0)+1) if n not in sequences), 100))
        run['telemetry_status'] = 'GAPS' if run['missing_sequences'] else 'PARTIAL_NO_END_TO_END_COMPLETENESS_PROOF'
        from app.services.harness_usage import aggregate
        run.update(aggregate(decoded))
        lifecycle = [e for e in decoded if e['kind'] in {'IDLE', 'SESSION_ERROR', 'DISCONNECTED', 'TOOL_STARTED', 'SESSION_CREATED'}]
        latest = lifecycle[-1]['kind'] if lifecycle else None
        run['status'] = {'IDLE': 'IDLE_NOT_SUCCESS', 'SESSION_ERROR': 'SESSION_ERROR',
                         'DISCONNECTED': 'DISCONNECTED'}.get(latest, 'BOUND_NOT_COMPLETED')
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
