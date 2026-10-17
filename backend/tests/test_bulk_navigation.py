"""Native regression gates for inventory, paging and absent historical files."""
import subprocess
import uuid
import pytest
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo
from app.services.command_center import overview, search_repository, file_detail, history


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()


def test_mixed_inventory_and_deleted_history_are_distinct_from_python_analysis(tmp_path):
    root=tmp_path/'mixed';root.mkdir();git(root,'init','-q')
    git(root,'config','user.name','Local fixture');git(root,'config','user.email','fixture@example.invalid')
    for path,text in {'a.py':'def helper():\n    return 1\n','web/app.ts':'export const value = 1;','README.md':'Guide',
                      'dist/generated.js':'generated','deleted.txt':'old'}.items():
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    (root/'shortcut.py').symlink_to('a.py')
    git(root,'add','.');git(root,'commit','-qm','Initial mixed source')
    (root/'deleted.txt').unlink();(root/'README.md').write_text('New guide')
    git(root,'add','.');git(root,'commit','-qm','Delete and document')
    sha=git(root,'rev-parse','HEAD');tenant='repo_test_'+uuid.uuid4().hex
    try:
        ingest_repo(str(root),tenant)
        data=overview(tenant)
        assert data['counts']['TrackedFile']==5 and data['counts']['File']==1
        assert data['inventory_basis']=='ALL_TRACKED_PATHS'
        ts=file_detail(tenant,'web/app.ts')
        assert ts['file']['language']=='TypeScript' and ts['symbols']==[]
        assert ts['file']['analysis_status']=='UNSUPPORTED_LANGUAGE'
        assert file_detail(tenant,'dist/generated.js')['file']['analysis_status']=='EXCLUDED'
        assert file_detail(tenant,'shortcut.py')['file']['analysis_status']=='UNSUPPORTED_ENTRY'
        assert search_repository(tenant,'app.ts')['entry_points'][0]['path']=='web/app.ts'
        changes={r['path']:r for r in history(tenant,sha)['changes']}
        assert changes['deleted.txt']['status']=='D' and changes['README.md']['status']=='M'
        assert 'deleted.txt' not in {n['path'] for n in data['nodes']}
    finally:
        if tenant in db_manager.list_tenant_graphs():db_manager.get_graph(tenant).delete()


def test_large_paged_inventory_search_and_history_have_no_unreachable_tail():
    tenant='repo_test_'+uuid.uuid4().hex;g=db_manager.get_graph(tenant)
    try:
        g.query("CREATE (:RepoMetadata {status:'READY',repository:'fixture/paging'})")
        paths=[f'folder{i:03}/needle.ts' for i in range(245)]
        g.query('UNWIND $paths AS p CREATE (:TrackedFile {path:p,language:"TypeScript",analysis_status:"UNSUPPORTED_LANGUAGE"})',{'paths':paths})
        commits=[{'sha':f'{i:040x}','time':i} for i in range(85)]
        g.query("UNWIND $rows AS r CREATE (:PullRequest {record_kind:'COMMIT',commit_sha:r.sha,committed_at:r.time,title:'Fixture'})",{'rows':commits})
        last=commits[0]['sha']
        g.query("MATCH (p:PullRequest {commit_sha:$sha}) UNWIND $paths AS path CREATE (p)-[:CHANGED]->(:CommitFileChange {path:path,status:'D',additions:0,deletions:1})",{'sha':last,'paths':paths})
        found=[];cursor=''
        while True:
            page=overview(tenant,after=cursor);found += [r['path'] for r in page['nodes']]
            if not page['next_cursor']:break
            cursor=page['next_cursor']
        assert found==[f'folder{i:03}/' for i in range(245)]
        assert overview(tenant,'folder244/')['nodes'][0]['path']==paths[-1]
        found=[];cursor=''
        while True:
            page=search_repository(tenant,'needle',after=cursor);found += [r['path'] for r in page['entry_points']]
            if not page['next_cursor']:break
            cursor=page['next_cursor']
        assert found==paths
        found=[];cursor=''
        while True:
            page=history(tenant,after=cursor);found += [r['sha'] for r in page['commits']]
            if not page['next_cursor']:break
            cursor=page['next_cursor']
        assert len(found)==85 and len(set(found))==85
        found=[];cursor=''
        while True:
            page=history(tenant,last,change_after=cursor);found += [r['path'] for r in page['changes']]
            if not page['change_next_cursor']:break
            cursor=page['change_next_cursor']
        assert found==paths
    finally:g.delete()
