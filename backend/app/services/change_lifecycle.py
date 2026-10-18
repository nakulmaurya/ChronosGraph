"""Durable immutable proposals. Browser decisions are not an OS/client sandbox.

No command supplied by an MCP client is executed here. Only the separate opt-in
local runner may mint LOCAL_WORKTREE_OBSERVED evidence.
"""
from contextlib import nullcontext
import hashlib
import json
import re
import time
import uuid
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.db.client import db_manager
from app.models import DiffImpactRequest
from app.services.common import read, tenant_exists
from app.services.diff_impact import simulate_diff, safe_path
from app.services.mutation_guard import mutation_guard, require_lease
from app.services.ownership import ownership_for_paths
from app.services.task_memory import policy_digest


class ProposalInput(BaseModel):
    tenant_graph: str
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')
    task_title: str = Field(min_length=1, max_length=300)
    proposed_files: dict[str, str | None] = Field(min_length=1, max_length=20)
    idempotency_key: str = Field(min_length=1, max_length=128)
    client_id: str = Field(default='mcp-agent', min_length=1, max_length=128)
    # Optional managed binding. All fields required together; legacy workflow retained.
    task_id: str | None = None
    plan_id: str | None = None
    pack_id: str | None = None
    agent_run_id: str | None = None
    overlay_digest: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    declared_rationale: str | None = Field(default=None, max_length=2000)


class DecisionInput(BaseModel):
    tenant_graph: str
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')
    proposal_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    approve: bool
    reason: str = Field(min_length=1, max_length=1000)


class ExecutionInput(BaseModel):
    tenant_graph: str
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')
    proposal_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    command_executed: str = Field(min_length=1, max_length=1000)
    exit_code: int = Field(strict=True, ge=-255, le=255)
    output_excerpt: str = Field(default='', max_length=8000)
    idempotency_key: str = Field(min_length=1, max_length=128)
    create_finding_summary: str | None = Field(default=None, min_length=1, max_length=500)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _node(tenant, label, ident):
    # Labels below are constants owned by this module, never user input.
    rows, _ = read(tenant, f'MATCH (n:{label} {{id:$id}}) RETURN n', {'id': ident})
    if not rows:
        raise HTTPException(404, 'Proposal or execution record not found in selected saved version')
    return dict(rows[0]['n'].properties)


def _revision(tenant, expected):
    if not re.fullmatch('[0-9a-f]{40}', expected):
        raise HTTPException(422, 'Require exact commit hash')
    rows, _ = read(tenant, 'MATCH (m:RepoMetadata) RETURN m.source_revision AS revision LIMIT 1')
    if not rows or rows[0]['revision'] != expected:
        raise HTTPException(409, 'Selected snapshot revision changed or has no metadata')


def _hashes(tenant, paths):
    rows, _ = read(tenant, '''MATCH (f) WHERE (f:File OR f:TrackedFile) AND f.path IN $paths AND f.sha256 IS NOT NULL
        RETURN f.path AS path,f.sha256 AS sha''', {'paths': paths})
    result = {}
    for r in rows:
        if r['path'] in result and result[r['path']] != r['sha']:
            raise HTTPException(409, 'Inventory and analysis source hashes disagree')
        result[r['path']] = r['sha']
    return result


def _rules(tenant, paths):
    rows, _ = read(tenant, '''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File)
        WHERE f.path IN $paths RETURN DISTINCT d.id AS id,d.rule AS rule ORDER BY id''', {'paths': paths})
    return rows


def _fresh(tenant, p, expected):
    if p['base_revision'] != expected:
        raise HTTPException(409, 'Proposal belongs to a different saved commit')
    reason = None
    try:
        _revision(tenant, expected)
        before = json.loads(p['base_file_shas_json'])
        actual = _hashes(tenant, list(before))
        if {path: actual.get(path) for path in before} != before:
            reason = 'STALE_SNAPSHOT'
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        reason = 'STALE_SNAPSHOT'
    if not reason and policy_digest(tenant, list(json.loads(p['proposed_files_json']))) != p['policy_digest']:
        reason = 'STALE_POLICY'
    if not reason and p.get('plan_id'):
        from app.services.task_runtime import validate_binding
        try:
            validate_binding(tenant, expected, p['task_id'], p['plan_id'], p['pack_id'],
                             p['agent_run_id'], p['overlay_digest'])
        except HTTPException as exc:
            if exc.status_code not in (404, 409):
                raise
            reason = 'STALE_TASK_CONTEXT'
    if reason:
        db_manager.query(tenant, '''MATCH (p:ChangeProposal {id:$id})
            SET p.status=$status,p.approved_proposal_hash=null''', {'id': p['id'], 'status': reason})
        p['status'] = reason
        p.pop('approved_proposal_hash', None)
    return reason


def _public(tenant, p):
    output = dict(p)
    for key in list(output):
        if key.endswith('_json'):
            output[key[:-5]] = json.loads(output.pop(key))
    executions, _ = read(tenant, '''MATCH (:ChangeProposal {id:$id})-[:HAS_EXECUTION]->(e:ExecutionRecord)
        RETURN e ORDER BY e.recorded_at DESC,e.id LIMIT 20''', {'id': p['id']})
    output['executions'] = [dict(r['e'].properties) for r in executions]
    output['approval_scope'] = 'Exact immutable proposal only; not an external-client security boundary'
    return output


def propose(req: ProposalInput, actor='MCP_AGENT'):
    tenant = tenant_exists(req.tenant_graph)
    for path in req.proposed_files:
        safe_path(path)
    if sum(len((text or '').encode()) for text in req.proposed_files.values()) > 128000:
        raise HTTPException(422, 'Proposal bodies exceed 128000 bytes')
    if not req.task_title.strip() or not req.idempotency_key.strip() or not req.client_id.strip():
        raise HTTPException(422, 'Title, request key and client must not be blank')
    with mutation_guard(tenant) as lock:
        _revision(tenant, req.expected_revision)
        binding = [req.task_id, req.plan_id, req.pack_id, req.agent_run_id, req.overlay_digest]
        managed = any(value is not None for value in binding)
        if managed:
            if not all(binding):
                raise HTTPException(422, 'Managed proposals require task, plan, pack, run and overlay digest together')
            if not req.declared_rationale or not req.declared_rationale.strip():
                raise HTTPException(422, 'Managed proposals require a concise declared rationale, not hidden reasoning')
            from app.services.task_runtime import validate_binding
            validate_binding(tenant, req.expected_revision, *binding)
        hashes = _hashes(tenant, list(req.proposed_files))
        # None means absent at the base; additions are protected against later appearance.
        hashes = {p: hashes.get(p) for p in req.proposed_files}
        payload = {'tenant_graph': tenant, 'base_revision': req.expected_revision,
                   'base_file_shas': hashes, 'proposed_files': req.proposed_files}
        if managed:
            payload['managed_binding'] = binding
            payload['declared_rationale'] = req.declared_rationale
        proposal_hash = digest(payload)
        found, _ = read(tenant, 'MATCH (p:ChangeProposal {idempotency_key:$key}) RETURN p', {'key': req.idempotency_key})
        if found:
            existing = dict(found[0]['p'].properties)
            if existing['proposal_hash'] != proposal_hash:
                raise HTTPException(409, 'Request key already identifies different proposal inputs; use a new key')
            return _public(tenant, existing)
        impact = simulate_diff(DiffImpactRequest(tenant_graph=tenant, expected_revision=req.expected_revision,
                                                 file_bodies=req.proposed_files))
        rules = _rules(tenant, list(req.proposed_files))
        impact['active_rules'] = rules
        impact['declared_ownership'] = ownership_for_paths(tenant, list(req.proposed_files), limit=100, include_organization=True)
        ident = 'prop_' + uuid.uuid4().hex
        p = {'id': ident, 'idempotency_key': req.idempotency_key, 'task_title': req.task_title,
             'tenant_graph': tenant, 'base_revision': req.expected_revision, 'actor_principal': actor,
             'client_id': req.client_id, 'base_file_shas_json': canonical(hashes),
             'proposed_files_json': canonical(req.proposed_files), 'proposal_hash': proposal_hash,
             'impact_summary_json': canonical(impact), 'governing_decision_ids_json': canonical([r['id'] for r in rules]),
             'policy_digest': policy_digest(tenant, list(req.proposed_files)), 'status': 'PROPOSED',
             'touched_paths': sorted(req.proposed_files), 'created_at': int(time.time()), 'task_id': 'task_' + uuid.uuid4().hex,
             'agent_run_id': 'run_' + uuid.uuid4().hex}
        if managed:
            p.update(task_id=req.task_id, agent_run_id=req.agent_run_id, plan_id=req.plan_id,
                     pack_id=req.pack_id, overlay_digest=req.overlay_digest,
                     declared_rationale=req.declared_rationale or '', rationale_provenance='AGENT_DECLARED_NOT_HIDDEN_REASONING')
            require_lease(lock)
            db_manager.query(tenant, '''MATCH (r:ChangeAgentRun {id:$run}), (c:ContextPack {id:$pack})
                CREATE (p:ChangeProposal) SET p=$props CREATE (r)-[:PROPOSED]->(p)
                CREATE (p)-[:BASED_ON_CONTEXT]->(c)''',
                {'props': p, 'run': req.agent_run_id, 'pack': req.pack_id})
            return _public(tenant, p)
        require_lease(lock)
        db_manager.query(tenant, '''CREATE (p:ChangeProposal) SET p=$props
            CREATE (t:ChangeTask {id:$task,title:$title})-[:HAS_RUN]->
                (r:ChangeAgentRun {id:$run,client_id:$client,actor_principal:$actor})-[:PROPOSED]->(p)''',
            {'props': p, 'task': p['task_id'], 'title': req.task_title, 'run': p['agent_run_id'],
             'client': req.client_id, 'actor': actor})
        return _public(tenant, p)


def check(tenant, expected, proposal_id, conflict=False):
    with mutation_guard(tenant) as lock:
        p = _node(tenant, 'ChangeProposal', proposal_id)
        reason = _fresh(tenant, p, expected)
        require_lease(lock)
        if reason and conflict:
            raise HTTPException(409, reason)
        return _public(tenant, p)


def list_proposals(tenant, expected):
    tenant_exists(tenant)
    _revision(tenant, expected)
    rows, _ = read(tenant, '''MATCH (p:ChangeProposal) RETURN p.id AS id
        ORDER BY p.created_at DESC,p.id DESC LIMIT 51''')
    return {'proposals': [check(tenant, expected, r['id']) for r in rows[:50]],
            'truncated': len(rows) > 50, 'limit': 50}


def decide(proposal_id, req: DecisionInput):
    with mutation_guard(req.tenant_graph) as lock:
        p = _node(req.tenant_graph, 'ChangeProposal', proposal_id)
        reason = _fresh(req.tenant_graph, p, req.expected_revision)
        if reason:
            raise HTTPException(409, reason)
        if p['proposal_hash'] != req.proposal_hash:
            raise HTTPException(409, 'Decision must name the exact proposal hash')
        target = 'APPROVED' if req.approve else 'REJECTED'
        if p['status'] == target:
            return _public(req.tenant_graph, p)
        if p['status'] != 'PROPOSED':
            raise HTTPException(409, 'Decision is final; submit a new immutable proposal for a revision')
        if not req.reason.strip():
            raise HTTPException(422, 'Decision reason is required')
        require_lease(lock)
        db_manager.query(req.tenant_graph, '''MATCH (p:ChangeProposal {id:$id})
            SET p.status=$status,p.approved_proposal_hash=$hash,p.decision_actor='BROWSER_OPERATOR',
                p.decision_reason=$reason,p.decided_at=$now
            CREATE (p)-[:HAS_DECISION]->(:HumanDecision {id:$decision,proposal_hash:$proposal_hash,
                actor:'BROWSER_OPERATOR',status:$status,reason:$reason,decided_at:$now})''',
            {'id': proposal_id, 'status': target, 'hash': p['proposal_hash'] if req.approve else None,
             'proposal_hash': p['proposal_hash'], 'reason': req.reason, 'now': int(time.time()),
             'decision': 'decision_' + uuid.uuid4().hex})
        return _public(req.tenant_graph, _node(req.tenant_graph, 'ChangeProposal', proposal_id))


def report(proposal_id, req: ExecutionInput):
    """Untrusted external report; callers cannot mint observed provenance."""
    return _record_execution(proposal_id, req, 'AGENT_REPORTED_UNVERIFIED', 'MCP_OR_API_CLIENT', '')


def _record_execution(proposal_id, req, provenance, runner, worktree_revision, lease=None):
    tenant = req.tenant_graph
    with (nullcontext(lease) if lease else mutation_guard(tenant)) as lock:
        p = _node(tenant, 'ChangeProposal', proposal_id)
        if _fresh(tenant, p, req.expected_revision):
            raise HTTPException(409, p['status'])
        if p['proposal_hash'] != req.proposal_hash or p.get('approved_proposal_hash') != req.proposal_hash:
            raise HTTPException(409, 'Execution requires approval of this exact proposal hash')
        payload_hash = digest({'proposal_id': proposal_id, **req.model_dump(), 'provenance': provenance,
                               'runner': runner, 'worktree_revision': worktree_revision})
        found, _ = read(tenant, 'MATCH (e:ExecutionRecord {idempotency_key:$key}) RETURN e', {'key': req.idempotency_key})
        if found:
            e = dict(found[0]['e'].properties)
            if e['payload_hash'] != payload_hash:
                raise HTTPException(409, 'Execution request key already identifies different inputs')
            return e
        if p['status'] != 'APPROVED':
            raise HTTPException(409, 'Proposal is not approved for execution')
        observed = provenance == 'LOCAL_WORKTREE_OBSERVED'
        status = ('EXECUTED_VERIFIED' if req.exit_code == 0 else 'EXECUTED_FAILED') if observed else 'APPROVED'
        e = {'id': 'exec_' + uuid.uuid4().hex, 'idempotency_key': req.idempotency_key,
             'proposal_id': proposal_id, 'proposal_hash': req.proposal_hash, 'runner_principal': runner,
             'provenance_kind': provenance, 'worktree_revision': worktree_revision,
             'command_executed': req.command_executed, 'exit_code': req.exit_code,
             'output_excerpt': req.output_excerpt, 'recorded_at': int(time.time()), 'payload_hash': payload_hash,
             'verification_status': 'CANDIDATE_TESTS_PASSED' if observed and req.exit_code == 0 else
                 'CANDIDATE_TESTS_FAILED' if observed else 'UNVERIFIED_CLIENT_REPORT'}
        finding = None
        if req.create_finding_summary:
            # Bind memory to the base evidence context, not a claim the saved graph was patched.
            base_hashes = json.loads(p['base_file_shas_json'])
            hashes = {k: v for k, v in base_hashes.items() if v is not None}
            absent = sorted(k for k,v in base_hashes.items() if v is None)
            finding = {'id': 'finding_' + uuid.uuid4().hex, 'summary': req.create_finding_summary,
                       'evidence_note': ('Observed disposable-worktree candidate test result. ' if observed else 'Unverified external report. ')
                           + 'Saved base snapshot remains unchanged; proposed result hashes are separate.',
                       'supporting_files': sorted(base_hashes), 'file_shas_json': canonical(hashes),
                       'absent_base_files_json': canonical(absent), 'base_revision': p['base_revision'],
                       'policy_digest': policy_digest(tenant, list(base_hashes)), 'created_at': time.time_ns() // 1_000_000,
                       'verification_command': req.command_executed, 'verification_basis': provenance,
                       'source_type': 'PROPOSAL_EXECUTION_EVIDENCE', 'proposal_id': proposal_id,
                       'execution_id': e['id'], 'governing_decision_ids_json': p['governing_decision_ids_json'],
                       'result_file_hashes_json': canonical(json.loads(p['impact_summary_json'])['final_file_hashes'])}
            e['finding_id'] = finding['id']
        require_lease(lock)
        query = '''MATCH (p:ChangeProposal {id:$id}) SET p.status=$status
            CREATE (p)-[:HAS_EXECUTION]->(e:ExecutionRecord) SET e=$props
            CREATE (e)-[:HAS_VERIFICATION]->(:ChangeVerification {id:$verification,status:$verification_status,
                provenance_kind:$provenance,exit_code:$exit_code})'''
        params = {'id': proposal_id, 'status': status, 'props': e, 'verification': 'verify_' + uuid.uuid4().hex,
                  'verification_status': e['verification_status'], 'provenance': provenance, 'exit_code': req.exit_code}
        if finding:
            query += ' CREATE (e)-[:PRODUCED_FINDING]->(f:VerifiedFinding:TaskFinding) SET f=$finding'
            params['finding'] = finding
        db_manager.query(tenant, query, params)
        return e
