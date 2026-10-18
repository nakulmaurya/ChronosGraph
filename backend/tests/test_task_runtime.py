"""Real FalkorDB task-runtime acceptance. No HTTP or graph substitutes."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from app.db.client import db_manager
from app.services import task_runtime as rt
from app.services.change_lifecycle import ProposalInput, propose, check
from app.services.common import read
from test_real_world_repos import local_repo, ingested


def setup(ingested):
    tenant, stats, _ = ingested
    revision = read(tenant, 'MATCH (m:RepoMetadata) RETURN m.source_revision AS revision')[0][0]['revision']
    scope = dict(tenant_graph=tenant, expected_revision=revision)
    task = rt.create_task(rt.TaskInput(**scope, title='Coordinated helper edit', objective='Keep caller behavior',
        acceptance=['Existing caller continues returning 1'], target='src/pkg/a.py', request_key='runtime-test'))
    tid, pid = task['task']['id'], task['task']['current_plan_id']
    pack = rt.build_pack(tid, rt.PackInput(**scope, plan_id=pid))
    run = rt.bind_run(tid, rt.RunInput(**scope, plan_id=pid, pack_id=pack['id'], session_id='ses_actual',
        worktree_id='owned-test-worktree', overlay_digest='a'*64, harness_version='1.19.3'))
    return scope, tid, pid, pack, run


def event(scope, seq=1, kind='IDLE', **kw):
    return rt.EventInput(**scope, schema_version=1, event_id=f'event-{seq}', source_event_id=f'actual-{seq}',
        sequence=seq, kind=kind, observed_at_ms=1, session_id='ses_actual', payload_digest='b'*64, **kw)


def test_task_pack_run_immutable_identity_and_full_budget(ingested):
    scope, tid, pid, pack, run = setup(ingested)
    assert len(rt.canonical(pack).encode()) == pack['serialized_bytes'] <= 10000
    assert pack['manifest']['source_pins'] and pack['manifest']['intent']['acceptance']
    assert pack['manifest']['workspace_state'] == 'BASE_ONLY_OVERLAY_NOT_INDEXED'
    same = rt.bind_run(tid, rt.RunInput(**scope, plan_id=pid, pack_id=pack['id'], session_id='ses_actual',
        worktree_id='owned-test-worktree', overlay_digest='a'*64, harness_version='1.19.3'))
    assert same['id'] == run['id']
    with pytest.raises(HTTPException) as e:
        rt.bind_run(tid, rt.RunInput(**scope, plan_id=pid, pack_id=pack['id'], session_id='ses_actual',
            worktree_id='different-tree', overlay_digest='a'*64, harness_version='1.19.3'))
    assert e.value.status_code == 409


def test_duplicate_out_of_order_gap_and_idle_not_success(ingested):
    scope, tid, _, _, run = setup(ingested)
    later = event(scope, 3)
    rt.record_event(run['id'], later)
    assert rt.record_event(run['id'], later)['duplicate']
    detail = rt.task_detail(scope['tenant_graph'], scope['expected_revision'], tid)['runs'][0]
    assert detail['missing_sequences'] == [1, 2] and detail['status'] == 'IDLE_NOT_SUCCESS'
    rt.record_event(run['id'], event(scope, 1))
    rt.record_event(run['id'], event(scope, 2))
    detail = rt.task_detail(scope['tenant_graph'], scope['expected_revision'], tid)['runs'][0]
    assert not detail['missing_sequences'] and len(detail['events']) == 3
    with pytest.raises(HTTPException) as e:
        rt.record_event(run['id'], later.model_copy(update={'kind': 'SESSION_ERROR'}))
    assert e.value.status_code == 409


def test_cumulative_usage_replaces_updates_without_double_count(ingested):
    scope, tid, _, _, run = setup(ingested)
    counters = dict(request_id='message-a', input_tokens=100, output_tokens=10, reasoning_tokens=2,
                    cache_read_tokens=50, cache_write_tokens=0, cost=0.0, basis='OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE')
    # Arrival order deliberately differs from source sequence.
    rt.record_event(run['id'], event(scope, 2, 'USAGE', usage=rt.Usage(**{**counters, 'output_tokens':20})))
    rt.record_event(run['id'], event(scope, 1, 'USAGE', usage=rt.Usage(**counters)))
    report = rt.task_detail(scope['tenant_graph'], scope['expected_revision'], tid)['runs'][0]
    assert report['usage_totals']['output_tokens'] == 20
    assert report['usage_totals']['input_tokens'] == 100
    assert report['harness_reported_cost'] == 0 and report['token_total'] is None


def test_plan_revision_invalidates_pack_run_and_managed_proposal(ingested):
    scope, tid, pid, pack, run = setup(ingested)
    proposal = propose(ProposalInput(**scope, task_title='Bound helper proposal', proposed_files={
        'src/pkg/a.py':'def helper():\n    return 1\ndef run():\n    return helper()\n'},
        idempotency_key='bound-proposal', task_id=tid, plan_id=pid, pack_id=pack['id'],
        agent_run_id=run['id'], overlay_digest='a'*64, declared_rationale='Retain helper result for indirect caller'))
    assert proposal['task_id'] == tid and proposal['agent_run_id'] == run['id']
    counts = read(scope['tenant_graph'], 'MATCH (t:ChangeTask) RETURN count(t) AS n')[0]
    assert counts[0]['n'] == 1
    rt.revise_plan(tid, rt.PlanInput(**scope, parent_plan_id=pid, objective='New agreed behavior',
        acceptance=['New requirements explicitly reviewed'], target='src/pkg/a.py'))
    assert check(scope['tenant_graph'], scope['expected_revision'], proposal['id'])['status'] == 'STALE_TASK_CONTEXT'
    with pytest.raises(HTTPException):
        rt.build_pack(tid, rt.PackInput(**scope, plan_id=pid))


def test_mandatory_rule_overflow_rejected_not_silently_trimmed(ingested):
    tenant, _, _ = ingested
    db_manager.query(tenant, '''MATCH (f:File {path:'src/pkg/a.py'})
        CREATE (:Decision {id:'huge',status:'ACTIVE',rule:$rule})-[:GOVERNS]->(f)''', {'rule':'Mandatory policy ' * 1200})
    with pytest.raises(HTTPException) as e:
        setup(ingested)
    assert e.value.status_code == 422 and e.value.detail['code'] == 'CONSTRAINT_OVERFLOW'
    assert read(tenant, 'MATCH (p:ContextPack) RETURN count(p) AS n')[0][0]['n'] == 0


def test_cross_tenant_run_and_changed_source_rejected(ingested):
    scope, tid, pid, pack, run = setup(ingested)
    with pytest.raises(HTTPException):
        rt.record_event(run['id'], event(scope).model_copy(update={'session_id':'other-session'}))
    db_manager.query(scope['tenant_graph'], "MATCH (f:File {path:'src/pkg/a.py'}) SET f.sha256=$sha", {'sha':'e'*64})
    with pytest.raises(HTTPException) as e:
        rt.validate_binding(scope['tenant_graph'], scope['expected_revision'], tid, pid, pack['id'], run['id'], 'a'*64)
    assert e.value.status_code == 409


def test_concurrent_event_retry_creates_one_receipt(ingested):
    scope, tid, _, _, run = setup(ingested)
    receipt = event(scope)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda _: rt.record_event(run['id'], receipt), range(4)))
    assert sum(not r['duplicate'] for r in outcomes) == 1
    assert rt.task_detail(scope['tenant_graph'], scope['expected_revision'], tid)['runs'][0]['event_count'] == 1


def test_policy_change_rejects_reloading_pack(ingested):
    scope, tid, _, pack, _ = setup(ingested)
    db_manager.query(scope['tenant_graph'], '''MATCH (f:File {path:'src/pkg/a.py'})
        CREATE (:Decision {id:'new-current-rule',status:'ACTIVE',rule:'Keep result exactly one'})-[:GOVERNS]->(f)''')
    with pytest.raises(HTTPException) as err:
        rt.fresh_pack(scope['tenant_graph'], tid, pack['id'])
    assert err.value.status_code == 409


def test_rest_bridge_explicit_loopback_intent_and_scope(ingested):
    from fastapi.testclient import TestClient
    from app.main import app
    scope, tid, pid, pack, run = setup(ingested)
    c = TestClient(app, base_url='http://127.0.0.1:8011')
    payload = dict(**scope, plan_id=pid)
    route = f'/api/v1/tasks/{tid}/context-packs'
    assert c.post(route, json=payload).status_code == 403
    assert c.post(route, json=payload, headers={'X-ChronosGraph-Action':'task-runtime','Origin':'https://untrusted.example'}).status_code == 403
    response = c.get(f'/api/v1/tasks/{tid}', params=scope)
    assert response.status_code == 200 and response.json()['task']['id'] == tid
    response = c.post(f'/api/v1/tasks/not-this-task/runs/{run["id"]}/events', json=event(scope).model_dump(), headers={'X-ChronosGraph-Action':'task-runtime'})
    assert response.status_code == 404
    wrong_revision = {**scope, 'expected_revision':'f'*40}
    assert c.get(f'/api/v1/tasks/{tid}',params=wrong_revision).status_code == 409


def test_unresolved_target_cannot_create_empty_context_pack(ingested):
    tenant, _, _ = ingested
    revision = read(tenant, 'MATCH (m:RepoMetadata) RETURN m.source_revision AS revision')[0][0]['revision']
    scope = dict(tenant_graph=tenant, expected_revision=revision)
    task = rt.create_task(rt.TaskInput(**scope, title='Missing context', objective='Inspect an unknown target',
        acceptance=['Source target is independently identified'], target='no_such_unique_target_94875.py', request_key='missing-target'))
    with pytest.raises(HTTPException) as failure:
        rt.build_pack(task['task']['id'], rt.PackInput(**scope, plan_id=task['task']['current_plan_id']))
    assert failure.value.status_code == 422
    assert failure.value.detail['code'] == 'NO_CONTEXT_TARGET'
    assert read(tenant, 'MATCH (p:ContextPack) RETURN count(p) AS n')[0][0]['n'] == 0


def test_managed_proposal_requires_declared_rationale(ingested):
    scope, tid, pid, pack, run = setup(ingested)
    with pytest.raises(HTTPException) as failure:
        propose(ProposalInput(**scope, task_title='Missing rationale', proposed_files={'src/pkg/a.py':'def helper():\n    return 1\n'},
            idempotency_key='missing-rationale', task_id=tid, plan_id=pid, pack_id=pack['id'],
            agent_run_id=run['id'], overlay_digest='a'*64, declared_rationale='   '))
    assert failure.value.status_code == 422
    assert 'declared rationale' in failure.value.detail
