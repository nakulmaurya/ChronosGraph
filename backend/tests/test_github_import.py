"""Real archive validation and native FalkorDB prepared-snapshot integration.

Synthetic bytes are explicitly archive fixtures, not mocked network/DB responses.
Live GitHub transport is exercised separately by the opt-in receipt command.
"""
import hashlib
import io
import os
from pathlib import Path
import stat
import uuid
import zipfile
import pytest
from app.db.client import db_manager
from app.ingestion.github_import import (MAX_ARCHIVE, archive_ownership, branch_name,
    import_public, repository_url, safe_path, unpack_verified, validate_tree, PublicGitHub)
from app.ingestion.ingest_repo import _ingest_repo, snapshot_stats
from app.services.common import read
from test_real_world_repos import client

REV='1'*40
TREE='2'*40


def fixture_archive(content=None):
    content=content or {'pkg/a.py':b'def helper():\n    return 1\n',
        'pkg/b.py':b'from pkg.a import helper\ndef run():\n    return helper()\n',
        '.github/CODEOWNERS':b'/pkg/ @fixture-owner\n','README.md':b'Python queries must be read-only.\n'}
    entries=[]
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('fixture-root/',b'')
        for path,data in content.items():
            entries.append({'path':path,'mode':'100644','type':'blob','size':len(data),
                'sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
            bundle.writestr('fixture-root/'+path,data)
    return {'sha':TREE,'truncated':False,'tree':entries}, buffer.getvalue()


@pytest.mark.parametrize('url',[
    'http://github.com/a/b','https://github.com.evil/a/b','https://user:secret@github.com/a/b',
    'https://github.com:443/a/b','https://github.com/a/b?token=no','https://github.com/a/b#x',
    'https://github.com/a/b/tree/main','file:///tmp/a','git@github.com:a/b',
    'https://127.0.0.1/a/b','https://github.com/a/%2e%2e','https://github.com//a/b',
    ' https://github.com/a/b','https://github.com/a/b\n'])
def test_strict_public_url_rejection(url):
    with pytest.raises(ValueError):repository_url(url)


def test_canonical_url_branch_and_path_guards():
    assert repository_url('https://github.com/pallets/click.git')==('pallets','click','https://github.com/pallets/click')
    assert branch_name('feature/local-intake')=='feature/local-intake'
    for value in ('main~1','../main','-x','a//b','a.lock','a/.b','main?x'):
        with pytest.raises(ValueError):branch_name(value)
    for value in ('../escape','a/../escape','a\\b','.git/config','x/.GIT/config','a:b','/absolute','a//b','a/./b','a\0b'):
        with pytest.raises(ValueError):safe_path(value)


def test_import_opt_in_and_arguments_fail_before_network():
    previous=os.environ.pop('CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT',None)
    try:
        with pytest.raises(ValueError,match='disabled'):import_public('https://github.com/a/b','main','repo_x',REV)
        os.environ['CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT']='1'
        with pytest.raises(ValueError,match='full expected'):import_public('https://github.com/a/b','main','repo_x','main')
        with pytest.raises(ValueError,match='full expected'):import_public('https://github.com/a/b','main','invalid',REV)
    finally:
        if previous is None:os.environ.pop('CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT',None)
        else:os.environ['CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT']=previous


def test_complete_tree_and_resource_guards():
    data,_=fixture_archive()
    assert len(validate_tree(data,TREE))==4
    for modified in ({**data,'truncated':True},{**data,'sha':'3'*40},{**data,'tree':[]}):
        with pytest.raises(ValueError):validate_tree(modified,TREE)
    entry=data['tree'][0]
    for mode,kind in [('120000','blob'),('160000','commit')]:
        with pytest.raises(ValueError,match='Symlinks'):validate_tree({**data,'tree':[{**entry,'mode':mode,'type':kind}]},TREE)
    with pytest.raises(ValueError,match='byte limit'):validate_tree({**data,'tree':[{**entry,'size':1_000_001}]},TREE)
    for extras in ([entry],[{**entry,'path':'PKG/A.py'}],[{**entry,'path':'pkg/a.py/child.py'}]):
        with pytest.raises(ValueError):validate_tree({**data,'tree':data['tree']+extras},TREE)
    with pytest.raises(ValueError,match='Python'):validate_tree({**data,'tree':[data['tree'][-1]]},TREE)


def test_verified_archive_and_hash_mismatch_fail_closed(tmp_path):
    data,archive=fixture_archive()
    files=validate_tree(data,TREE)
    unpack_verified(archive,files,tmp_path/'valid')
    assert (tmp_path/'valid/pkg/a.py').read_bytes()==b'def helper():\n    return 1\n'
    assert archive_ownership(tmp_path/'valid')['status']=='FOUND'
    files['pkg/a.py']['sha']='0'*40
    with pytest.raises(ValueError,match='Git blob'):unpack_verified(archive,files,tmp_path/'invalid')
    with pytest.raises(ValueError,match='compressed'):unpack_verified(b'x'*(MAX_ARCHIVE+1),files,tmp_path)


@pytest.mark.parametrize('name',['fixture-root/../escape.py','other-root/a.py','fixture-root/.git/config'])
def test_archive_path_escape_refused_before_write(tmp_path,name):
    data,_=fixture_archive()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as bundle:
        bundle.writestr('fixture-root/',b'')
        bundle.writestr(name,b'x')
    with pytest.raises(ValueError):unpack_verified(buffer.getvalue(),validate_tree(data,TREE),tmp_path/'out')
    assert not (tmp_path/'escape.py').exists()


def test_archive_symlink_duplicate_missing_and_size_mismatch(tmp_path):
    data,archive=fixture_archive()
    files=validate_tree(data,TREE)
    for mode in ('symlink','duplicate','missing','size'):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as bundle:
            bundle.writestr('fixture-root/',b'')
            if mode=='symlink':
                item=zipfile.ZipInfo('fixture-root/pkg/a.py');item.create_system=3
                item.external_attr=(stat.S_IFLNK|0o777)<<16
                bundle.writestr(item,b'/tmp/outside')
            elif mode=='duplicate':
                with pytest.warns(UserWarning):
                    bundle.writestr('fixture-root/pkg/a.py',b'def helper():\n    return 1\n');bundle.writestr('fixture-root/pkg/a.py',b'def helper():\n    return 1\n')
            elif mode=='size':bundle.writestr('fixture-root/pkg/a.py',b'wrong length')
        with pytest.raises(ValueError):unpack_verified(buffer.getvalue(),files,tmp_path/mode)


def test_archive_source_enters_real_graph_without_git_history_fabrication(client,tmp_path):
    data,archive=fixture_archive()
    files=validate_tree(data,TREE)
    unpack_verified(archive,files,tmp_path)
    tenant='repo_test_'+uuid.uuid4().hex
    try:
        result=_ingest_repo('https://github.com/fixture/explicit-archive',tenant,REV,False,
            snapshot_metadata={'connection_kind':'PUBLIC_GITHUB_ARCHIVE','selected_branch':'main',
                'workspace_check_status':'PINNED_AT_IMPORT'},
            prepared_snapshot={'source':(tmp_path,REV,'https://github.com/fixture/explicit-archive','fixture/explicit-archive'),
                'paths':['pkg/a.py','pkg/b.py'],'ownership_document':archive_ownership(tmp_path)})
        assert result['history_records']==0 and result['declared_ownership']['status']=='INDEXED'
        assert result['resolved_calls']==1
        rows,_=read(tenant,'MATCH (a:File)-[:IMPORTS]->(b:File) RETURN a.path AS a,b.path AS b')
        assert rows==[{'a':'pkg/b.py','b':'pkg/a.py'}]
        assert snapshot_stats(tenant)['functions']==2
        state=client.get('/api/v1/workspace/snapshot',params={'tenant_graph':tenant}).json()
        assert state['connection_kind']=='PUBLIC_GITHUB_ARCHIVE' and state['last_check']['status']=='PINNED_AT_IMPORT'
        owners=client.get('/api/v1/context/owners',params={'tenant_graph':tenant,'file_path':'pkg/a.py'}).json()
        assert owners['declarations'][0]['owner']=='@fixture-owner'
        rows,_=read(tenant,'MATCH (m:RepoMetadata) RETURN m.history_scope AS scope,m.history_limit AS lim')
        assert rows==[{'scope':'NOT_FETCHED_GITHUB_ARCHIVE','lim':0}]
        before=snapshot_stats(tenant)
        with pytest.raises(ValueError,match='already exists'):
            _ingest_repo('https://github.com/fixture/explicit-archive',tenant,REV,False,prepared_snapshot={})
        assert snapshot_stats(tenant)==before
    finally:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()


def test_transport_refuses_arbitrary_hosts_before_network():
    client=PublicGitHub()
    for url in ('http://api.github.com/repos/a/b','https://localhost/x','https://api.github.com.evil/x','https://user@api.github.com/x','https://api.github.com:443/x'):
        with pytest.raises(ValueError,match='allowed GitHub host'):client.get(url,100)


def test_failed_prepared_graph_is_removed_without_touching_existing_tenants(tmp_path):
    data,archive=fixture_archive()
    files=validate_tree(data,TREE)
    unpack_verified(archive,files,tmp_path)
    tenant='repo_test_'+uuid.uuid4().hex
    before=set(db_manager.list_tenant_graphs())
    with pytest.raises(KeyError):
        _ingest_repo('https://github.com/fixture/failing-archive',tenant,REV,False,
            prepared_snapshot={'source':(tmp_path,REV,'https://github.com/fixture/failing-archive','fixture/failing-archive'),
                'paths':['pkg/a.py','pkg/b.py'],'ownership_document':{'status':'FOUND'}})
    assert tenant not in db_manager.list_tenant_graphs()
    assert set(db_manager.list_tenant_graphs())==before


def test_exact_symbol_entry_point_outranks_incidental_filename_matches(tmp_path):
    from app.services.context_locator import locate_context
    data,archive=fixture_archive({'src/core.py':b'class Command:\n    pass\n',
        'tests/test_command_examples.py':b'def test_examples():\n    pass\n'})
    files=validate_tree(data,TREE);unpack_verified(archive,files,tmp_path)
    tenant='repo_test_'+uuid.uuid4().hex
    try:
        _ingest_repo('https://github.com/fixture/symbol-navigation',tenant,REV,False,
            prepared_snapshot={'source':(tmp_path,REV,'https://github.com/fixture/symbol-navigation','fixture/symbol-navigation'),
                'paths':list(files),'ownership_document':{'status':'ABSENT_AT_PINNED_REVISION'}})
        context=locate_context(tenant,'Command')
        assert context['entry_points'][0]['path']=='src/core.py'
        assert context['payload_bytes']<=4096 and context['coverage']['entry_limit']==3
    finally:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()
