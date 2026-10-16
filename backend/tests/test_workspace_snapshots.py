"""Native Git/FalkorDB connection and refresh regressions. No fake HTTP/DB."""
import hashlib
import os
import subprocess
import uuid
from pathlib import Path
import pytest
from app.db.client import db_manager
from app.ingestion.ingest_repo import git, snapshot_stats, writer_locks
from app.ingestion.workspace import (allowed_repository, bounded_python_tree, create_snapshot,
    freshness_check, inspect_workspace, require_clean_selected)
from app.models import FindingRequest
from app.services.task_memory import record_finding, recall_findings
from test_real_world_repos import client, local_repo


def commit(root, text='Snapshot revision'):
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','--quiet','-m',text],check=True)


@pytest.fixture
def connected(local_repo):
    # Explicit process configuration, never a client-supplied allowlist.
    previous = os.environ.get('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS')
    os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = str(local_repo.parent)
    branch = git(local_repo,'symbolic-ref','--short','HEAD')
    revision = git(local_repo,'rev-parse','HEAD')
    tenants = ['repo_test_'+uuid.uuid4().hex for _ in range(3)]
    try:
        stats = create_snapshot(str(local_repo),branch,tenants[0],revision)
        yield local_repo,branch,revision,tenants,stats
    finally:
        for tenant in tenants:
            if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()
        if previous is None:os.environ.pop('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS',None)
        else:os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = previous


def test_local_connection_disabled_and_root_escape_refused(local_repo):
    original = os.environ.pop('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS', None)
    try:
        with pytest.raises(ValueError,match='disabled'):allowed_repository(str(local_repo))
        os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = str(local_repo/'src')
        with pytest.raises(ValueError,match='outside'):allowed_repository(str(local_repo))
        os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = str(local_repo.parent)
        with pytest.raises(ValueError,match='Only allowlisted'):allowed_repository('https://github.com/a/b')
        with pytest.raises(ValueError,match='in-root .git'):allowed_repository(str(local_repo/'src'))
        escape = local_repo/'src'/'outside';escape.symlink_to(local_repo.parent, target_is_directory=True)
        os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = str(local_repo/'src')
        with pytest.raises(ValueError,match='outside'):allowed_repository(str(escape))
    finally:
        if original is None:os.environ.pop('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS',None)
        else:os.environ['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = original


def test_connection_metadata_read_only_api_and_no_local_path_disclosure(client,connected):
    root,branch,revision,tenants,stats = connected
    assert stats['source_revision']==revision and stats['selected_branch']==branch
    assert stats['preflight']['python_files']==5
    data = client.get('/api/v1/workspace/snapshot',params={'tenant_graph':tenants[0]})
    assert data.status_code==200,data.text
    value=data.json()
    assert value['source_revision']==revision and value['selected_branch']==branch
    assert value['last_check']['status']=='MATCHED_AT_CHECK' and value['last_check']['checked_at']
    assert not value['freshness_is_live'] and value['mutation_transport']=='LOCAL_CLI_ONLY'
    assert str(root) not in data.text and str(root.parent) not in data.text
    before=snapshot_stats(tenants[0])
    for _ in range(2):assert client.get('/api/v1/workspace/snapshot',params={'tenant_graph':tenants[0]}).json()==value
    assert snapshot_stats(tenants[0])==before
    assert client.get('/api/v1/workspace/snapshot',params={'tenant_graph':'repo_missing_'+uuid.uuid4().hex}).status_code==404
    assert client.post('/api/v1/workspace/snapshot',json={'source':str(root)}).status_code==405
    assert client.get('/api/v1/workspace/snapshot',params={'tenant_graph':'repo_falkordb_py'}).json()['last_check']['status']=='NOT_CHECKED'


def test_explicit_check_flags_dirty_and_moved_branch_then_clean_refresh_preserves_old_graph(client,connected):
    root,branch,revision,tenants,_=connected
    old,new,_=tenants
    from app.services.common import read
    sha=read(old,"MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256 AS sha")[0][0]['sha']
    record_finding(FindingRequest(tenant_graph=old,summary='Original helper evidence',
        evidence_note='Captured source only; no command executed.',supporting_file_shas={'src/pkg/a.py':sha}))
    baseline=snapshot_stats(old)
    (root/'src/pkg/a.py').write_text('def helper():\n    return 42\n')
    result=freshness_check(str(root),branch,old)
    assert result['status']=='CHANGED' and result['reasons']==['UNCOMMITTED_OR_UNTRACKED_CHANGES']
    with pytest.raises(ValueError,match='dirty'):
        create_snapshot(str(root),branch,new,revision,previous_tenant=old,expected_base=revision)
    assert new not in db_manager.list_tenant_graphs()
    commit(root)
    updated=git(root,'rev-parse','HEAD')
    assert freshness_check(str(root),branch,old)['reasons']==['BRANCH_ADVANCED_OR_REWRITTEN']
    with pytest.raises(ValueError,match='Expected base'):
        create_snapshot(str(root),branch,new,updated,previous_tenant=old,expected_base='0'*40)
    with pytest.raises(ValueError,match='HEAD/selected'):
        create_snapshot(str(root),branch,new,revision,previous_tenant=old,expected_base=revision)
    refreshed=create_snapshot(str(root),branch,new,updated,previous_tenant=old,expected_base=revision)
    assert refreshed['source_revision']==updated and refreshed['parent_snapshot']==old
    assert snapshot_stats(old)==baseline
    assert recall_findings(old,'Original')['findings']
    assert not recall_findings(new,'Original')['findings']
    assert read(old,"MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256 AS sha")[0][0]['sha']==sha
    assert read(new,"MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.sha256 AS sha")[0][0]['sha']==hashlib.sha256((root/'src/pkg/a.py').read_bytes()).hexdigest()
    assert client.get('/api/v1/workspace/snapshot',params={'tenant_graph':new}).json()['parent_snapshot']==old


def test_no_overwrite_wrong_connection_branch_and_untracked_guard(connected):
    root,branch,revision,tenants,_=connected
    before=snapshot_stats(tenants[0])
    with pytest.raises(ValueError,match='already exists'):create_snapshot(str(root),branch,tenants[0],revision)
    git(root,'branch','alternate')
    with pytest.raises(ValueError,match='Source or branch'):freshness_check(str(root),'alternate',tenants[0])
    for bad in ('-main','HEAD~1','main..bad','refs/heads/'+branch):
        with pytest.raises(ValueError):inspect_workspace(root,bad)
    (root/'new-untracked.txt').write_text('Not silently synchronized')
    with pytest.raises(ValueError,match='dirty'):create_snapshot(str(root),branch,tenants[1],revision)
    assert snapshot_stats(tenants[0])==before
    assert tenants[1] not in db_manager.list_tenant_graphs()


def test_git_hooks_and_fsmonitor_not_executed_by_connection(connected):
    root,branch,revision,tenants,_=connected
    marker=root.parent/'never-execute'
    hook=root/'.git/hooks/post-checkout';hook.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');hook.chmod(0o755)
    monitor=root/'.git/monitor.sh';monitor.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');monitor.chmod(0o755)
    git(root,'config','core.fsmonitor',str(monitor))
    os.environ['GIT_INDEX_FILE']=str(root.parent/'wrong-index')
    try:
        stats=create_snapshot(str(root),branch,tenants[1],revision)
        assert stats['source_revision']==revision and not marker.exists()
    finally:os.environ.pop('GIT_INDEX_FILE',None)


def test_symlink_python_and_source_size_fail_before_graph_write(connected):
    root,branch,revision,tenants,_=connected
    (root/'link.py').symlink_to(root/'src/pkg/a.py')
    commit(root)
    with pytest.raises(ValueError,match='non-regular'):create_snapshot(str(root),branch,tenants[1],git(root,'rev-parse','HEAD'))
    assert tenants[1] not in db_manager.list_tenant_graphs()
    (root/'link.py').unlink();(root/'oversized.py').write_text('#' * 1_000_001)
    commit(root)
    with pytest.raises(ValueError,match='byte limits'):create_snapshot(str(root),branch,tenants[1],git(root,'rev-parse','HEAD'))
    assert tenants[1] not in db_manager.list_tenant_graphs()


def test_writer_conflict_is_refused_without_new_tenant(connected):
    root,branch,revision,tenants,_=connected
    with writer_locks(str(root),tenants[1]):
        with pytest.raises(ValueError,match='Another ingestion'):
            create_snapshot(str(root),branch,tenants[1],revision)
    assert tenants[1] not in db_manager.list_tenant_graphs()


def test_cli_connect_check_and_guard_failure_are_real_processes(local_repo):
    env = os.environ.copy()
    env['CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS'] = str(local_repo.parent)
    branch=git(local_repo,'symbolic-ref','--short','HEAD');revision=git(local_repo,'rev-parse','HEAD')
    tenant='repo_test_'+uuid.uuid4().hex
    import sys,json
    command=[sys.executable,'-m','app.ingestion.workspace']
    args=['--source',str(local_repo),'--branch',branch,'--tenant',tenant]
    try:
        result=subprocess.run(command+['connect',*args,'--expected-head',revision],env=env,capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['source_revision']==revision
        result=subprocess.run(command+['check',*args],env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==0 and json.loads(result.stdout)['status']=='MATCHED_AT_CHECK'
        result=subprocess.run(command+['refresh',*args],env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==2 and '--expected-head' in result.stderr
        assert str(local_repo) not in result.stderr
    finally:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()


def test_refresh_reconciles_added_deleted_renamed_files_without_mutating_source_or_old_graph(connected):
    root,branch,revision,tenants,_=connected
    old,new,_=tenants
    before=snapshot_stats(old)
    git(root,'mv','src/pkg/b.py','src/pkg/renamed.py')
    git(root,'rm','src/pkg/c.py')
    (root/'src/pkg/new.py').write_text('from pkg.renamed import run\ndef added():\n    return run()\n')
    (root/'CODEOWNERS').write_text('/src/pkg/new.py @new-reviewer\n')
    commit(root,'Rename delete add in selected workspace')
    updated=git(root,'rev-parse','HEAD')
    create_snapshot(str(root),branch,new,updated,previous_tenant=old,expected_base=revision)
    graph=db_manager.get_graph(new)
    paths={r[0] for r in graph.ro_query('MATCH (f:File) RETURN f.path').result_set}
    assert 'src/pkg/b.py' not in paths and 'src/pkg/c.py' not in paths
    assert {'src/pkg/new.py','src/pkg/renamed.py'} <= paths
    assert graph.ro_query("MATCH (:File {path:'src/pkg/new.py'})-[:IMPORTS]->(:File {path:'src/pkg/renamed.py'}) RETURN count(*)").result_set[0][0]==1
    assert graph.ro_query("MATCH (r:OwnershipRule)-[:APPLIES_TO]->(:File {path:'src/pkg/new.py'}), (r)-[:DECLARES_OWNER]->(o) RETURN o.name").result_set[0][0]=='@new-reviewer'
    assert snapshot_stats(old)==before
    assert git(root,'rev-parse','HEAD')==updated and not git(root,'status','--porcelain')


def test_local_remote_query_metadata_is_not_persisted(connected):
    root,branch,revision,tenants,_=connected
    git(root,'remote','add','origin','https://example.invalid/team/repo.git?session=fixture-private-metadata')
    stats=create_snapshot(str(root),branch,tenants[1],revision)
    graph=db_manager.get_graph(tenants[1])
    urls=graph.ro_query('MATCH (n) WHERE n.source_url IS NOT NULL RETURN n.source_url').result_set
    assert all('fixture-private-metadata' not in str(row[0]) for row in urls)
    assert stats['repository']==root.name


def test_workspace_inspection_does_not_refresh_the_sources_git_index(connected):
    root,branch,revision,_,_=connected
    index=root/'.git/index';original=index.read_bytes()
    source=root/'src/pkg/a.py';stat=source.stat()
    os.utime(source,ns=(stat.st_atime_ns,stat.st_mtime_ns+5_000_000_000))
    observed=inspect_workspace(root,branch)
    assert not observed['dirty'] and observed['selected_revision']==revision
    assert index.read_bytes()==original
