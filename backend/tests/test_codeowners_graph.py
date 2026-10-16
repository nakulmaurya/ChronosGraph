"""Native Git/FalkorDB + actual MCP ownership evidence; no source execution."""
import asyncio
import hashlib
import subprocess
import uuid
from pathlib import Path
import pytest
from fastmcp import Client
from app.db.client import db_manager
from app.ingestion.codeowners import parse_rules, committed_document
from app.ingestion.ingest_repo import ingest_repo
from app.mcp_server.server import mcp
from test_real_world_repos import client, local_repo, ingested


def commit(root):
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '--quiet', '-m', 'Pinned owner declarations'], check=True)


@pytest.fixture
def owned_repo(local_repo):
    (local_repo/'.github').mkdir()
    text = '* @default-owner\n/src/pkg/a.py @source-team/core @reviewer\n/src/pkg/b.py\n!*.py @not-supported\n'
    (local_repo/'.github/CODEOWNERS').write_text(text)
    (local_repo/'CODEOWNERS').write_text('* @wrong-location\n')
    commit(local_repo)
    tenant = 'repo_test_'+uuid.uuid4().hex
    try:
        stats = ingest_repo(str(local_repo), tenant)
        yield tenant, stats, local_repo, text
    finally:
        if tenant in db_manager.list_tenant_graphs():
            db_manager.get_graph(tenant).delete()


def test_last_match_clears_and_github_unsupported_syntax_is_diagnostic():
    parser, errors, count = parse_rules('* @default\n*.py @python\n/src/clear.py\n!*.py @bad\n[a-z].py @bad\n\\#bad @bad\n*.ts invalid-owner\n')
    assert parser.of('src/a.py') == [('USERNAME', '@python')]
    assert parser.of('src/clear.py') == []
    assert parser.matching_line('src/clear.py')[1] == 3
    assert count == 4 and len(errors) == 4
    assert parser.of('src/a.ts') == [('USERNAME', '@default')]


def test_space_paths_and_directory_globs():
    parser, errors, count = parse_rules('/docs/ @docs\n/src/a\\ b.py @space\n')
    assert not errors and not count
    assert parser.of('docs/deep/a.md') == [('USERNAME', '@docs')]
    assert parser.of('src/a b.py') == [('USERNAME', '@space')]
    assert not parser.of('other/docs/a.md')


@pytest.mark.parametrize('text', ['x'*65537, '\n'*2001])
def test_oversize_rules_rejected(text):
    with pytest.raises(ValueError):
        parse_rules(text)


def test_graph_owner_paths_have_exact_source_and_are_not_git_contributors(client, owned_repo):
    tenant, stats, root, text = owned_repo
    assert stats['declared_ownership']['status'] == 'PARTIAL_INVALID_RULES_SKIPPED'
    assert stats['declared_ownership']['invalid_rule_count'] == 1
    r = client.get('/api/v1/context/owners', params={'tenant_graph': tenant, 'file_path': 'src/pkg/a.py'})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['source_document']['path'] == '.github/CODEOWNERS'
    assert data['source_document']['sha256'] == hashlib.sha256(text.encode()).hexdigest()
    assert data['source_document']['revision'] == stats['source_revision']
    assert {d['owner'] for d in data['declarations']} == {'@source-team/core', '@reviewer'}
    assert all(d['source_line'] == 2 for d in data['declarations'])
    assert data['workspace_freshness'] == 'PINNED_SNAPSHOT_WORKSPACE_NOT_CHECKED'
    graph = db_manager.get_graph(tenant)
    assert graph.ro_query("MATCH (o:DeclaredOwner) WHERE o:Contributor RETURN count(o)").result_set[0][0] == 0
    assert graph.ro_query("MATCH (:OwnershipSource)-[:DEFINES_OWNERSHIP_RULE]->(:OwnershipRule)-[:APPLIES_TO]->(:File {path:'src/pkg/a.py'}) RETURN count(*)").result_set[0][0] == 1
    cleared = client.get('/api/v1/context/owners', params={'tenant_graph': tenant, 'file_path': 'src/pkg/b.py'}).json()
    assert cleared['declarations'][0]['owner'] is None
    assert cleared['declarations'][0]['source_line'] == 3
    # Query the pinned graph, never this now-edited workspace CODEOWNERS text.
    (root/'.github/CODEOWNERS').write_text('* @changed-not-indexed\n')
    assert client.get('/api/v1/context/owners', params={'tenant_graph': tenant, 'file_path': 'src/pkg/a.py'}).json() == data


def test_actual_mcp_context_includes_graph_ownership_and_remains_byte_bounded(owned_repo):
    tenant, _, _, _ = owned_repo
    async def run():
        async with Client(mcp) as c:
            result = await c.call_tool('locate_context', {'tenant_graph': tenant, 'query': 'helper', 'budget_bytes': 8192})
            assert not result.is_error
            data = result.data
            assert any(d['owner'] == '@reviewer' for d in data['declared_ownership']['declarations'])
            assert data['payload_bytes'] <= 8192
            tiny = await c.call_tool('locate_context', {'tenant_graph': tenant, 'query': 'helper', 'budget_bytes': 2048})
            assert not tiny.is_error and tiny.data['payload_bytes'] <= 2048
            if len(tiny.data['declared_ownership']['declarations']) < len(data['declared_ownership']['declarations']):
                assert tiny.data['declared_ownership']['truncated']
                assert tiny.data['coverage']['truncated']
    asyncio.run(run())


def test_absent_unknown_and_missing_files_remain_distinct(client, ingested):
    tenant, stats, _ = ingested
    assert stats['declared_ownership']['status'] == 'ABSENT_AT_PINNED_REVISION'
    r = client.get('/api/v1/context/owners', params={'tenant_graph': tenant, 'file_path': 'src/pkg/a.py'})
    assert r.json()['status'] == 'ABSENT_AT_PINNED_REVISION'
    assert r.json()['declarations'] == []
    assert client.get('/api/v1/context/owners', params={'tenant_graph': tenant, 'file_path': '../outside.py'}).status_code == 404
    assert client.get('/api/v1/context/owners', params={'tenant_graph': 'repo_missing', 'file_path': 'a.py'}).status_code == 404


def test_symlink_policy_is_not_followed_or_replaced_by_lower_precedence(local_repo):
    (local_repo/'.github').mkdir()
    (local_repo/'outside.txt').write_text('* @secret-target\n')
    (local_repo/'.github/CODEOWNERS').symlink_to('../outside.txt')
    (local_repo/'CODEOWNERS').write_text('* @fallback-not-used\n')
    commit(local_repo)
    revision = subprocess.check_output(['git', '-C', str(local_repo), 'rev-parse', 'HEAD']).decode().strip()
    assert committed_document(local_repo, revision) == {'status': 'UNSUPPORTED_SOURCE_MODE', 'path': '.github/CODEOWNERS'}
