"""Browser-job boundary tests; no network or source execution in these tests."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services import import_jobs as jobs

@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(jobs,'JOBS',{})
    monkeypatch.setattr(jobs,'ACTIVE',None)

def req(origin='http://localhost:3004',host='localhost',header='public-import'):
    return SimpleNamespace(url=SimpleNamespace(hostname=host),headers={'origin':origin,'x-chronosgraph-action':header})

def test_browser_import_requires_opt_in_loopback_origin_and_action(monkeypatch):
    monkeypatch.delenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT',raising=False)
    with pytest.raises(HTTPException): jobs.authorize(req())
    monkeypatch.setenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT','1')
    jobs.authorize(req())
    for r in (req(origin='https://evil.example'),req(host='evil.example'),req(header=''),req(origin='null')):
        with pytest.raises(HTTPException) as e: jobs.authorize(r)
        assert e.value.status_code==403

def test_invalid_inputs_never_start_worker():
    for url in ('file:///tmp/repo','https://github.com/owner/repo/tree/main','https://token@github.com/a/b','http://127.0.0.1/repo'):
        with pytest.raises(HTTPException): jobs.start_import(jobs.ImportRequest(url=url))
    with pytest.raises(HTTPException): jobs.start_import(jobs.ImportRequest(url='https://github.com/a/b',commit='wrong'))
    assert not jobs.JOBS

def test_only_one_active_job_and_receipts_are_copied(monkeypatch):
    class DeferredThread:
        def __init__(self,**kwargs): pass
        def start(self): pass
    monkeypatch.setattr(jobs.threading,'Thread',DeferredThread)
    first=jobs.start_import(jobs.ImportRequest(url='https://github.com/pallets/click',branch=''))
    assert first['tenant_graph'].startswith('repo_github_')
    assert first['branch']=='main'
    first['status']='FORGED'
    assert jobs.receipt(first['id'])['status']=='RUNNING'
    with pytest.raises(HTTPException) as exc: jobs.start_import(jobs.ImportRequest(url='https://github.com/a/b'))
    assert exc.value.status_code==409

def test_unknown_receipt_reports_restart_or_expiry():
    with pytest.raises(HTTPException) as e: jobs.receipt('unknown')
    assert e.value.status_code==404

def test_worker_failure_releases_capacity_and_hides_stderr(monkeypatch):
    import io
    class FailedProcess:
        pid=123; returncode=2
        def __init__(self,cmd,**kwargs):
            assert isinstance(cmd,list) and 'shell' not in kwargs
            kwargs['stdout'].write(b'{"error":"Repository exceeds expanded byte limit"}')
            kwargs['stderr'].write(b'SECRET HOST PATH SHOULD NOT LEAK')
        def communicate(self,*args,**kwargs): pass
    monkeypatch.setattr(jobs.subprocess,'Popen',FailedProcess)
    jobs.JOBS['one']={'status':'RUNNING'};jobs.ACTIVE='one'
    jobs._worker('one',{'url':'https://github.com/a/b'})
    assert jobs.JOBS['one']['status']=='FAILED' and jobs.ACTIVE is None
    assert 'exceeds expanded' in jobs.JOBS['one']['error']
    assert 'SECRET' not in str(jobs.JOBS)

def test_worker_deadline_kills_only_its_own_process_group(monkeypatch):
    class TimeoutProcess:
        pid=456;returncode=None
        def __init__(self,*args,**kwargs): assert kwargs['start_new_session'] is True
        def communicate(self,*args,**kwargs):
            assert kwargs['timeout']==300
            raise jobs.subprocess.TimeoutExpired('fixture',300)
        def wait(self): pass
    killed=[]
    monkeypatch.setattr(jobs.subprocess,'Popen',TimeoutProcess)
    monkeypatch.setattr(jobs.os,'killpg',lambda pid,sig:killed.append((pid,sig)))
    jobs.JOBS['one']={'status':'RUNNING'};jobs.ACTIVE='one'
    jobs._worker('one',{})
    assert killed==[(456,jobs.signal.SIGKILL)]
    assert jobs.JOBS['one']['status']=='FAILED' and jobs.ACTIVE is None
    assert 'incomplete snapshot' in jobs.JOBS['one']['error']
