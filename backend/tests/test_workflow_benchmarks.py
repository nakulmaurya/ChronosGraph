"""Native workflows: real-source probes plus a known-answer developer task.

Use scripts/verify-workflow-benchmarks.sh. Missing seed graphs FAIL rather than
skip. Latency/compression ambitions are report targets; use --strict-targets to
turn hardware/workload-dependent targets into a separate acceptance gate.
"""
import difflib
import hashlib
import os
from pathlib import Path
import subprocess
import uuid

import pytest
from fastapi import HTTPException
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo
from app.models import DiffImpactRequest, FindingRequest, InvestigationRunRequest, PolicyOverrideRequest
from app.services.company_brain import override_policy
from app.services.context_locator import locate_context, symbol_source
from app.services.diff_impact import simulate_diff
from app.services.memory_compiler import run_investigation
from app.services.second_brain_wiki import compact_snapshot
from app.services.task_memory import record_finding, recall_findings
from app.services.workflow_benchmark import (DATASETS, evaluate_repository, percentile,
    reduction, is_test, audit_absolute_imports, captured, owned_copy)


@pytest.fixture(scope='module', params=DATASETS)
def measured_repository(request):
    assert os.environ.get('CHRONOSGRAPH_DISPOSABLE_BENCHMARK') == '1', 'Use the isolated workflow runner'
    assert request.param in db_manager.list_tenant_graphs(), 'Required real repository must be seeded'
    return evaluate_repository(request.param, samples=5)


def test_real_multihop_coordinates_and_bounded_latency_receipt(measured_repository):
    row = measured_repository
    assert row['source_coordinate_check'] == 'PASS_STDLIB_AST_AND_CAPTURED_LINES'
    assert row['returned_import_routes_valid']
    assert row['task']['resolved_inbound_calls'] > 0
    for receipt in row['latency'].values():
        assert receipt['samples'] == 5 and receipt['warmups'] == 1
        assert 0 <= receipt['p50_ms'] <= receipt['p95_ms'] <= receipt['max_ms']
    assert row['ownership']['basis'] == 'DECLARED_AT_PINNED_COMMIT_NOT_VERIFIED_IDENTITY_OR_ACCESS'


def test_real_diff_candidates_and_dependency_evidence(measured_repository):
    row = measured_repository
    impact = row['impact']
    assert impact['sandbox_cleaned_up'] and row['owned_graph_cleaned_up']
    assert impact['potentially_broken_callers'], 'Renamed real function had indexed callers'
    assert any(e['relationship'] == 'CALLS' and e['target'] == row['task']['qualified_name'] for e in impact['removed_dependencies'])
    assert impact['test_suite_reduction_pct'] == reduction(impact['total_python_test_files'], impact['candidate_count'])
    assert impact['test_impact_precision'] is None  # Runtime failure oracle is deliberately not invented.


def test_real_exact_bytes_and_honest_token_estimates(measured_repository):
    row = measured_repository
    assert row['model_calls'] == 0
    folding = row['folding']
    assert folding['raw_files_bytes'] > 0 and folding['slice_bytes'] > 0
    assert folding['byte_reduction_pct'] == round(100*(1-folding['slice_bytes']/folding['raw_files_bytes']), 3)
    assert folding['exact_model_token_count'] is None and folding['billed_token_savings'] is None
    assert row['targets']['byte_reduction_at_least_70pct'] == (folding['byte_reduction_pct'] >= 70)
    assert row['resume_bytes'] < 1900


def test_real_independent_import_audit_and_cleanup(measured_repository):
    audit = measured_repository['import_accuracy']
    assert audit['eligible_files'] > 0 and audit['expected_edges'] > 0
    assert audit['true_positive_edges'] <= min(audit['expected_edges'], audit['indexed_edges_in_scope'])
    for key in ('precision', 'recall'):
        assert audit[key] is None or 0 <= audit[key] <= 1
    assert measured_repository['clone_delete']['cleanup_verified']


@pytest.fixture
def workflow_repo(tmp_path):
    root = tmp_path/'workflow'; root.mkdir()
    files = {'core/__init__.py':'', 'services/__init__.py':'', 'api/__init__.py':'',
        'core/pricing.py':'def discount(amount):\n    return amount - 1\n',
        'core/alternative.py':'def price(amount):\n    return amount - 2\n',
        'services/checkout.py':'from core.pricing import discount\ndef checkout(amount):\n    return discount(amount)\n',
        'api/orders.py':'from services.checkout import checkout\ndef order(amount):\n    return checkout(amount)\n',
        'tests/test_orders.py':'from api.orders import order\ndef test_order():\n    assert order(10) == 9\n',
        'tests/test_unrelated.py':'def test_unrelated():\n    assert True\n',
        '.github/CODEOWNERS':'/core/pricing.py @platform-team\n'}
    for path, text in files.items():
        dest = root/path; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(text)
    subprocess.run(['git','init','--quiet',str(root)], check=True)
    subprocess.run(['git','-C',str(root),'add','.'], check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Benchmark Fixture','-c','user.email=benchmark@example.invalid','commit','--quiet','-m','Known-answer workflow'], check=True)
    tenant = 'repo_test_workflow_'+uuid.uuid4().hex
    try:
        ingest_repo(str(root), tenant)
        graph = db_manager.get_graph(tenant)
        for ident, status, rule in [('bench_active','ACTIVE','Benchmark current policy'), ('bench_old','SUPERSEDED','OBSOLETE_NEVER_RESUME')]:
            graph.query('''MATCH (f:File {path:'core/pricing.py'})
                CREATE (d:Decision {id:$id,status:$status,rule:$rule,scope_symbol:'module_root',source_type:'BENCHMARK_FIXTURE',embedding:$embedding})-[:GOVERNS]->(f)''',
                {'id':ident,'status':status,'rule':rule,'embedding':db_manager.embed_text(rule)})
        yield tenant, graph, files
    finally:
        if tenant in db_manager.list_tenant_graphs(): db_manager.get_graph(tenant).delete()


def test_known_answer_three_hop_discovery_and_declared_ownership(workflow_repo):
    tenant, _, _ = workflow_repo
    data = locate_context(tenant, 'discount', 8192)
    assert any(r['via'] == ['tests/test_orders.py','api/orders.py','services/checkout.py','core/pricing.py'] for r in data['related_importers'])
    assert 'tests/test_orders.py' in data['candidate_test_files']
    assert {r['owner'] for r in data['declared_ownership']['declarations']} == {'@platform-team'}
    assert [r['id'] for r in data['active_rules']] == ['bench_active']
    assert symbol_source(tenant,'core/pricing.py','discount')['source'] == 'def discount(amount):\n    return amount - 1\n'


def test_known_answer_unified_diff_and_coordinated_edge_replacement(workflow_repo):
    tenant, graph, files = workflow_repo
    before = captured(graph)
    patch = ''.join(difflib.unified_diff(files['core/pricing.py'].splitlines(True),
        'def renamed(amount):\n    return amount - 1\n'.splitlines(True), fromfile='a/core/pricing.py', tofile='b/core/pricing.py'))
    breaking = simulate_diff(DiffImpactRequest(tenant_graph=tenant, unified_diff=patch))
    assert breaking['potentially_broken_callers'] == ['services/checkout.py:checkout']
    coordinated = simulate_diff(DiffImpactRequest(tenant_graph=tenant, file_bodies={
        'core/pricing.py':'def renamed(amount):\n    return amount - 1\n',
        'services/checkout.py':'from core.alternative import price\ndef checkout(amount):\n    return price(amount)\n'}))
    assert coordinated['potentially_broken_callers'] == []
    for relationship, source, old_target, new_target in [
        ('IMPORTS','services/checkout.py','core/pricing.py','core/alternative.py'),
        ('CALLS','services/checkout.py:checkout','core/pricing.py:discount','core/alternative.py:price')]:
        assert {'relationship':relationship,'source':source,'target':old_target} in coordinated['removed_dependencies']
        assert {'relationship':relationship,'source':source,'target':new_target} in coordinated['added_dependencies']
    selected = {p for p in coordinated['impacted_test_files'] if is_test(p)}
    assert selected == {'tests/test_orders.py'}
    assert reduction(sum(is_test(p) for p in before), len(selected)) == 50
    assert captured(graph) == before and coordinated['sandbox_cleaned_up']
    audit = audit_absolute_imports(before, graph)
    assert audit['precision'] == audit['recall'] == 1


@pytest.mark.parametrize('mutation', ['policy', 'file_sha'])
def test_recovery_active_only_and_immediate_memory_playbook_shield(workflow_repo, mutation):
    tenant, graph, _ = workflow_repo
    issue = 'Review policy core/pricing.py'
    run_investigation(InvestigationRunRequest(tenant_graph=tenant,issue_description=issue))
    warm = InvestigationRunRequest(tenant_graph=tenant,issue_description=issue,execution_mode='compiled_playbook')
    assert run_investigation(warm).execution_mode == 'compiled_playbook'
    snapshot = compact_snapshot(tenant,'core/pricing.py')
    assert snapshot['snapshot_bytes'] < 1900
    assert 'Benchmark current policy' in snapshot['markdown'] and 'OBSOLETE_NEVER_RESUME' not in snapshot['markdown']
    sha = graph.ro_query("MATCH (f:File {path:'core/pricing.py'}) RETURN f.sha256").result_set[0][0]
    record_finding(FindingRequest(tenant_graph=tenant,summary='benchmark observation',evidence_note='Captured source inspection only; no pytest executed',supporting_file_shas={'core/pricing.py':sha}))
    assert recall_findings(tenant)['findings'][0]['status'] == 'CURRENT_AT_INDEXED_SNAPSHOT'
    if mutation == 'policy':
        override_policy(PolicyOverrideRequest(tenant_graph=tenant,target_file_path='core/pricing.py',new_rule_text='New benchmark policy',rationale='Test stale guard'))
        reason = 'GOVERNING_POLICY_CHANGED'
    else:
        graph.query("MATCH (f:File {path:'core/pricing.py'}) SET f.sha256=$sha", {'sha':hashlib.sha256(b'changed').hexdigest()})
        reason = 'SUPPORTING_FILE_CHANGED_OR_MISSING'
        with pytest.raises(HTTPException) as err: symbol_source(tenant,'core/pricing.py','discount')
        assert err.value.status_code == 409
    assert not recall_findings(tenant)['findings']
    stale = recall_findings(tenant, include_stale=True)['findings'][0]
    assert stale['status'] == 'STALE' and reason in stale['stale_reasons']
    with pytest.raises(HTTPException) as err: run_investigation(warm)
    assert err.value.status_code == 409


def test_metric_edge_cases_and_nearest_rank_percentile():
    assert percentile(list(range(1,21))) == 19
    assert percentile([1,2,3]) == 3
    assert reduction(0,0) is None and reduction(2,0) == 100 and reduction(2,2) == 0
    assert is_test('nested/test_x.py') and is_test('x_test.py')
    assert not is_test('tests/conftest.py') and not is_test('tests/data.json')
    with pytest.raises(ValueError): reduction(1,2)
    with pytest.raises(ValueError): percentile([])


def test_owned_graph_is_removed_even_when_workflow_raises(workflow_repo):
    tenant, _, _ = workflow_repo
    names = set(db_manager.list_tenant_graphs())
    with pytest.raises(RuntimeError, match='intentional workflow failure'):
        with owned_copy(tenant):
            raise RuntimeError('intentional workflow failure')
    assert set(db_manager.list_tenant_graphs()) == names
