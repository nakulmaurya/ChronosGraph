"""User-goal acceptance over real stdio, Git snapshots and native FalkorDB.

No hosted model or IDE is involved. The client behaves like an agent and verifies
source/impact/memory outcomes, not fixed tool counts or dashboard copy.
"""
import asyncio
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from fastapi import HTTPException
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo
from app.mcp_server.server import mcp
from app.services.agent_connection import discover_repositories, require_snapshot
from app.services.workspace import workspace_snapshot
from test_real_world_repos import local_repo, ingested

TOOLS = {
    'simulate_pr_blast_radius': {'modified_files': ['src/pkg/a.py']},
    'query_bitemporal_decisions': {'question': 'What governs helper?', 'file_path': 'src/pkg/a.py'},
    'record_decision_override': {'target_file_path': 'src/pkg/a.py', 'new_rule_text': 'MUST NOT APPLY', 'rationale': 'rejected guard'},
    'find_true_code_owners': {'file_path': 'src/pkg/a.py'},
    'run_or_compile_playbook': {'issue_description': 'Review policy src/pkg/a.py'},
    'simulate_diff_impact': {'file_bodies': {'src/pkg/a.py': 'def helper():\n    return 99\n'}},
    'locate_context': {'query': 'helper'},
    'get_symbol_source': {'file_path': 'src/pkg/a.py', 'symbol_name': 'helper'},
    'record_verified_finding': {'summary': 'MUST NOT SAVE', 'evidence_note': 'rejected guard', 'supporting_file_shas': {'src/pkg/a.py': '0'*64}},
    'recall_task_memory': {},
}


def source_state(tenant):
    graph = db_manager.get_graph(tenant)
    return {
        'files': graph.ro_query('MATCH (f:File) RETURN f.path,f.sha256,f.source_text ORDER BY f.path').result_set,
        'rules': graph.ro_query('MATCH (d:Decision) RETURN d.id,d.status,d.rule ORDER BY d.id').result_set,
        'memory': graph.ro_query('MATCH (m:VerifiedFinding) RETURN m.id ORDER BY m.id').result_set,
        'playbooks': graph.ro_query('MATCH (p:ProceduralPlaybook) RETURN p.id ORDER BY p.id').result_set,
    }


@pytest.mark.parametrize('tool_name', sorted(TOOLS))
def test_wrong_selected_version_rejects_each_tool_without_domain_mutation(ingested, tool_name):
    tenant, _, _ = ingested
    before = source_state(tenant)
    graphs = set(db_manager.list_tenant_graphs())
    async def run():
        async with Client(mcp) as client:
            tool = next(t for t in await client.list_tools() if t.name == tool_name)
            assert 'expected_revision' in tool.input_schema['properties']
            result = await client.call_tool(tool_name, {**TOOLS[tool_name],
                'tenant_graph': tenant, 'expected_revision': '0'*40}, raise_on_error=False)
            assert result.is_error, (tool_name, result)
    asyncio.run(run())
    assert source_state(tenant) == before
    assert set(db_manager.list_tenant_graphs()) == graphs
    events = db_manager.get_graph(tenant).ro_query('MATCH (e:AgentEvent) RETURN e.outcome,e.tool_name').result_set
    assert events == [['ERROR', tool_name]]


@pytest.mark.parametrize('revision', ['', 'main', 'A'*40, 'a'*39, 'a'*41, '../secret'])
def test_malformed_guard_fails_before_operation(ingested, revision):
    tenant, _, _ = ingested
    with pytest.raises(HTTPException) as exc:
        require_snapshot(tenant, revision)
    assert exc.value.status_code == 422


def test_discovery_is_paginated_read_only_and_excludes_incomplete_graphs(ingested):
    tenant, _, _ = ingested
    pending = 'repo_test_' + uuid.uuid4().hex
    try:
        db_manager.get_graph(pending).query("CREATE (:RepoMetadata {status:'INGESTING'})")
        graphs = set(db_manager.list_tenant_graphs())
        before = source_state(tenant)
        graph = db_manager.get_graph(tenant)
        nodes_before = graph.ro_query('MATCH (n) RETURN id(n),labels(n),properties(n) ORDER BY id(n)').result_set
        edges_before = graph.ro_query('MATCH ()-[r]->() RETURN id(r),type(r),properties(r) ORDER BY id(r)').result_set
        rows, cursor = [], ''
        while True:
            page = discover_repositories(cursor, 1)
            rows.extend(page['repositories'])
            if page['next_cursor'] is None:
                break
            assert page['next_cursor'] > cursor
            cursor = page['next_cursor']
        names = [r['tenant_graph'] for r in rows]
        assert names == sorted(set(names))
        assert tenant in names and pending not in names
        selected = next(r for r in rows if r['tenant_graph'] == tenant)
        assert selected['source_revision'] == workspace_snapshot(tenant)['source_revision']
        assert selected['snapshot_guard_available']
        assert source_state(tenant) == before
        assert graph.ro_query('MATCH (n) RETURN id(n),labels(n),properties(n) ORDER BY id(n)').result_set == nodes_before
        assert graph.ro_query('MATCH ()-[r]->() RETURN id(r),type(r),properties(r) ORDER BY id(r)').result_set == edges_before
        assert set(db_manager.list_tenant_graphs()) == graphs
    finally:
        db_manager.get_graph(pending).delete()


@pytest.mark.parametrize('cursor,limit', [('bad', 20), ('', 0), ('', 51), ('', True)])
def test_discovery_rejects_unbounded_or_invalid_inputs(cursor, limit):
    with pytest.raises(HTTPException) as exc:
        discover_repositories(cursor, limit)
    assert exc.value.status_code == 422


def test_missing_revision_cannot_be_guarded_and_unknown_tenant_is_not_created():
    tenant = 'repo_test_' + uuid.uuid4().hex
    missing = 'repo_missing_' + uuid.uuid4().hex
    try:
        db_manager.get_graph(tenant).query("CREATE (:File {path:'legacy.py'})")
        row = next(r for r in discover_repositories(limit=50)['repositories'] if r['tenant_graph'] == tenant)
        assert row['source_revision'] is None and not row['snapshot_guard_available']
        for name, code in [(tenant, 409), (missing, 404)]:
            with pytest.raises(HTTPException) as exc:
                require_snapshot(name, 'a'*40)
            assert exc.value.status_code == code
        assert missing not in db_manager.list_tenant_graphs()
    finally:
        db_manager.get_graph(tenant).delete()


def test_real_stdio_choose_version_read_preview_and_recall_after_reconnect(ingested, local_repo):
    tenant, _, source = ingested
    revision = workspace_snapshot(tenant)['source_revision']
    # A different commit with the same paths catches wrong-snapshot fallbacks.
    (local_repo/'src/pkg/a.py').write_text('def helper():\n    return 200\n')
    subprocess.run(['git', '-C', str(local_repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(local_repo), '-c', 'user.name=Local Test Author',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'Different saved version'], check=True)
    other = 'repo_test_' + uuid.uuid4().hex
    try:
        latest = subprocess.check_output(['git', '-C', str(local_repo), 'rev-parse', 'HEAD'], text=True).strip()
        ingest_repo(str(local_repo), other, ref=latest)
        other_revision = workspace_snapshot(other)['source_revision']
        assert other_revision != revision
        before = source_state(tenant)
        other_before = source_state(other)
        graphs = set(db_manager.list_tenant_graphs())
        server = Path(__file__).resolve().parents[1]/'app/mcp_server/server.py'
        def transport():
            return PythonStdioTransport(server, python_cmd=sys.executable,
                cwd=str(server.parents[2]), env={**os.environ, "CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD": "1"}, keep_alive=False)
        async def run():
            async with Client(transport()) as client:
                tools = {t.name: t for t in await client.list_tools()}
                assert set(TOOLS) | {'discover_repositories', 'inspect_repository_snapshot'} <= tools.keys()
                assert set(tools['inspect_repository_snapshot'].input_schema['required']) == {'tenant_graph', 'expected_revision'}
                for name in TOOLS:
                    assert {'tenant_graph', 'expected_revision'} <= set(tools[name].input_schema['required'])
                missing_guard = await client.call_tool('locate_context', {'query': 'helper', 'tenant_graph': tenant}, raise_on_error=False)
                assert missing_guard.is_error
                missing_tenant = await client.call_tool('locate_context', {'query': 'helper', 'expected_revision': revision}, raise_on_error=False)
                assert missing_tenant.is_error
                page = await client.call_tool('discover_repositories', {'limit': 50})
                assert not page.is_error
                assert {tenant, other} <= {r['tenant_graph'] for r in page.data['repositories']}
                opened = await client.call_tool('inspect_repository_snapshot', {'tenant_graph': tenant, 'expected_revision': revision})
                args = opened.data['tool_arguments']
                assert args == {'tenant_graph': tenant, 'expected_revision': revision}
                wrong = await client.call_tool('inspect_repository_snapshot', {'tenant_graph': other, 'expected_revision': revision}, raise_on_error=False)
                assert wrong.is_error
                located = await client.call_tool('locate_context', {**args, 'query': 'helper'})
                entry = next(e for e in located.data['entry_points'] if e['path'] == 'src/pkg/a.py')
                body = await client.call_tool('get_symbol_source', {**args, 'file_path': entry['path'], 'symbol_name': 'helper'})
                assert body.data['source'] == 'def helper():\n    return 1\n'
                assert body.data['source_sha256'] == entry['sha256']
                assert entry['revision'] == revision
                preview = await client.call_tool('simulate_diff_impact', {**args, 'file_bodies': {'src/pkg/a.py': 'def renamed():\n    return 8\n'}})
                assert preview.data['sandbox_cleaned_up']
                assert 'src/pkg/b.py:run' in preview.data['potentially_broken_callers']
                assert {'src/pkg/a.py', 'src/pkg/b.py', 'src/pkg/c.py'} <= set(preview.data['impacted_files'])
                assert any(d['source'] == 'src/pkg/b.py:run' and d['target'] == 'src/pkg/a.py:helper' for d in preview.data['removed_dependencies'])
                assert preview.data['final_file_hashes']['src/pkg/a.py'] == hashlib.sha256(b'def renamed():\n    return 8\n').hexdigest()
                assert source_state(tenant) == before  # Preview never applies to saved source.
                saved = await client.call_tool('record_verified_finding', {**args,
                    'summary': 'helper rename requires caller review',
                    'evidence_note': 'Static preview found b.py:run calling the removed helper. No test executed.',
                    'supporting_file_shas': {entry['path']: entry['sha256']}})
                assert saved.data['verification_basis'] == 'AGENT_REPORTED_EVIDENCE_NOT_INDEPENDENTLY_EXECUTED'
                finding_id = saved.data['id']
            # A fresh server process must recall graph-backed evidence, not local session memory.
            async with Client(transport()) as client:
                recalled = await client.call_tool('recall_task_memory', {**args, 'query': 'rename'})
                assert [f['id'] for f in recalled.data['findings']] == [finding_id]
                assert recalled.data['findings'][0]['status'] == 'CURRENT_AT_INDEXED_SNAPSHOT'
                separate = await client.call_tool('recall_task_memory', {'tenant_graph': other, 'expected_revision': other_revision})
                assert not separate.data['findings']
        asyncio.run(run())
        assert set(db_manager.list_tenant_graphs()) == graphs  # No leftover clone.
        assert source_state(other) == other_before
        after = source_state(tenant)
        assert after['files'] == before['files'] and after['rules'] == before['rules']
    finally:
        if other in db_manager.list_tenant_graphs():
            db_manager.get_graph(other).delete()
