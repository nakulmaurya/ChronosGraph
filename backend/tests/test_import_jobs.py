"""Native Redis receipt tests. Worker transport failures are explicitly injected."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import json
import time
import uuid
import pytest
from fastapi import HTTPException
from app.db.client import db_manager
from app.services import import_jobs as jobs
from app.services.import_state import ImportStore

@pytest.fixture
def state(monkeypatch):
    redis=db_manager.db.connection
    prefix='chronosgraph:test-import:'+uuid.uuid4().hex+':'
    value=ImportStore(redis,prefix)
    monkeypatch.setattr(jobs,'store',lambda:value)
    monkeypatch.setattr(jobs,'launch',lambda ident:None)
    yield value
    keys=list(redis.scan_iter(prefix+'*'))
    if keys:redis.delete(*keys)

def req(origin='http://localhost:3004',host='localhost',header='public-import'):
    return SimpleNamespace(url=SimpleNamespace(hostname=host),headers={'origin':origin,'x-chronosgraph-action':header})

def test_browser_import_requires_opt_in_loopback_origin_and_action(monkeypatch):
    monkeypatch.delenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT',raising=False)
    with pytest.raises(HTTPException):jobs.authorize(req())
    monkeypatch.setenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT','1');jobs.authorize(req())
    for r in (req(origin='https://evil.example'),req(host='evil.example'),req(header=''),req(origin='null')):
        with pytest.raises(HTTPException) as exc:jobs.authorize(r)
        assert exc.value.status_code==403

def body(**kwargs):
    return jobs.ImportRequest(url='https://github.com/pallets/click',request_id=uuid.uuid4().hex,**kwargs)

def test_invalid_inputs_never_publish_a_job(state):
    for url in ('file:///tmp/repo','https://github.com/a/b/tree/main','https://token@github.com/a/b','http://127.0.0.1/repo'):
        with pytest.raises(HTTPException):jobs.start_import(jobs.ImportRequest(url=url))
    with pytest.raises(HTTPException):jobs.start_import(body(commit='wrong'))
    assert list(state.redis.scan_iter(state.prefix+'*'))==[]

def test_lost_ack_retry_is_idempotent_after_new_service_instance(state):
    request=body();first=jobs.start_import(request)
    fresh=ImportStore(state.redis,state.prefix)
    assert fresh.get(request.request_id)['tenant_graph']==first['tenant_graph']
    again=jobs.start_import(request)
    assert first==again
    assert 'fingerprint' not in again and 'url' not in again
    assert len([k for k in state.redis.scan_iter(state.prefix+'*') if not str(k).endswith('active')])==1
    with pytest.raises(HTTPException) as exc:jobs.start_import(jobs.ImportRequest(url='https://github.com/a/other',request_id=request.request_id))
    assert exc.value.status_code==409

def test_concurrent_retry_creates_one_job_and_launch(state,monkeypatch):
    launches=[];monkeypatch.setattr(jobs,'launch',lambda ident:launches.append(ident))
    request=body()
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:jobs.start_import(request),range(8)))
    assert len({r['tenant_graph'] for r in results})==1 and launches==[request.request_id]
    with pytest.raises(HTTPException) as exc:jobs.start_import(body())
    assert exc.value.status_code==409

def test_publication_after_lost_completion_ack_reconciles(state):
    request=body();first=jobs.start_import(request)
    result={'source_revision':'a'*40,'repository':'fixture/repo'}
    state.finish(request.request_id,'INTERRUPTED','Synthetic missing worker')
    reconciled=ImportStore(state.redis,state.prefix).reconcile(request.request_id,lambda _:result)
    assert reconciled['status']=='COMPLETE' and reconciled['result']==result
    assert jobs.start_import(request)['tenant_graph']==first['tenant_graph']

def test_deadline_reports_interruption_without_relaunch_or_deletion(state):
    request=body();first=jobs.start_import(request)
    job=state.get(request.request_id);job['deadline_at']=time.time()-1
    state.redis.set(state.key(request.request_id),json.dumps(job))
    result=jobs.receipt(request.request_id)
    assert result['status']=='INTERRUPTED' and 'operator review' in result['error']
    assert jobs.start_import(request)['status']=='INTERRUPTED'
    assert jobs.start_import(body())['tenant_graph']!=first['tenant_graph']

def test_launch_failure_is_terminal_and_releases_shared_capacity(state,monkeypatch):
    def failed(_):raise OSError('SECRET HOST PATH MUST NOT LEAK')
    monkeypatch.setattr(jobs,'launch',failed)
    result=jobs.start_import(body())
    assert result['status']=='FAILED' and 'SECRET' not in str(result)
    assert state.redis.get(state.prefix+'active') is None

def test_receipt_missing_invalid_and_old_finish_cannot_unlock_new_job(state):
    with pytest.raises(HTTPException) as exc:state.get(uuid.uuid4().hex)
    assert exc.value.status_code==404
    with pytest.raises(HTTPException):state.get('../escape')
    one=body();jobs.start_import(one);state.finish(one.request_id,'FAILED','Injected')
    two=body();jobs.start_import(two)
    state.finish(one.request_id,'COMPLETE','Reconciled',result={'source_revision':'a'*40})
    assert state.redis.get(state.prefix+'active')==two.request_id


def test_receipt_survives_a_fresh_api_process_and_does_not_relaunch(state):
    import subprocess,sys
    ident=uuid.uuid4().hex
    script='''
import json,sys
from fastapi.testclient import TestClient
from app.main import app
from app.services import import_jobs as jobs
from app.services.import_state import ImportStore
from app.db.client import db_manager
jobs.store=lambda:ImportStore(db_manager.db.connection,sys.argv[1])
jobs.launch=lambda _:None
client=TestClient(app)
if sys.argv[3]=='create':
    result=jobs.start_import(jobs.ImportRequest(url='https://github.com/pallets/click',request_id=sys.argv[2]))
else:
    result=client.get('/api/v1/imports/'+sys.argv[2]).json()
print(json.dumps(result,sort_keys=True))
'''
    first=subprocess.check_output([sys.executable,'-c',script,state.prefix,ident,'create'],text=True)
    second=subprocess.check_output([sys.executable,'-c',script,state.prefix,ident,'read'],text=True)
    assert json.loads(first)==json.loads(second)
    assert json.loads(second)['status']=='RUNNING'
