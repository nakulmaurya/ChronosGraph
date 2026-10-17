"""Opt-in, single-worker local browser intake. Public GitHub only; no shell or tokens.

Ephemeral receipts are lost on API restart. A killed worker may leave INGESTING
metadata requiring operator review; existing snapshots are never overwritten.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.parse import urlsplit
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.ingestion.github_import import repository_url, branch_name, SHA
from app.local_boundary import local_ui_origins

LOCK = threading.Lock()
JOBS = {}
ACTIVE = None
TTL = 3600

class ImportRequest(BaseModel):
    url: str = Field(max_length=300)
    branch: str = Field(default='main',max_length=200)
    commit: str = Field(default='',max_length=40)


def enabled():
    return os.environ.get('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT')=='1'


def authorize(request):
    if not enabled(): raise HTTPException(403,'Browser import is disabled by the operator. Local CLI import is still available.')
    # Local trusted-user service, not an internet multi-user authentication system.
    if (request.url.hostname not in ('localhost','127.0.0.1') or
        request.headers.get('origin') not in local_ui_origins() or
        request.headers.get('x-chronosgraph-action')!='public-import'):
        raise HTTPException(403,'Use an operator-configured loopback command center to start imports')


def start_import(body):
    global ACTIVE
    try:
        _,_,url=repository_url(body.url)
        branch=branch_name(body.branch.strip() or 'main')
        commit=body.commit.strip().lower()
        if commit and not SHA.fullmatch(commit): raise ValueError('Commit hash must contain exactly 40 hexadecimal characters')
    except ValueError as exc: raise HTTPException(422,str(exc)) from None
    with LOCK:
        now=time.time()
        for key in list(JOBS):
            if key!=ACTIVE and now-JOBS[key]['created_at']>TTL: del JOBS[key]
        if ACTIVE: raise HTTPException(409,'Another repository is importing. Wait for it to finish.')
        if len(JOBS)>=20: raise HTTPException(429,'Import receipt limit reached; retry after older receipts expire')
        ident=uuid.uuid4().hex
        tenant='repo_github_'+uuid.uuid4().hex
        job={'id':ident,'status':'RUNNING','stage':'Downloading and indexing a pinned public snapshot',
             'created_at':now,'url':url,'branch':branch,'tenant_graph':tenant,'error':None,'result':None}
        JOBS[ident]=job; ACTIVE=ident
    threading.Thread(target=_worker,args=(ident,{'url':url,'branch':branch,'commit':commit,'tenant':tenant}),daemon=True).start()
    return receipt(ident)


def receipt(ident):
    with LOCK:
        if ident not in JOBS: raise HTTPException(404,'Import receipt expired or the API restarted; reload indexed repositories')
        return dict(JOBS[ident])


def _worker(ident, payload):
    global ACTIVE
    proc=None
    try:
        env=dict(os.environ,CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT='1')
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            proc=subprocess.Popen([sys.executable,'-m','app.ingestion.import_worker'],stdin=subprocess.PIPE,
                stdout=output,stderr=errors,env=env,start_new_session=True)
            try: proc.communicate(json.dumps(payload).encode(),timeout=300)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait()
                raise ValueError('Import exceeded five minutes. Reload repositories; an incomplete snapshot may need operator cleanup.')
            output.seek(0); data=output.read(64001)
            if len(data)>64000: raise ValueError('Import receipt exceeded its size limit; reload repositories')
            result=json.loads(data) if data else {}
            if proc.returncode or 'error' in result:
                raise ValueError(result.get('error','Import worker failed; inspect operator logs. Existing snapshots are unchanged.'))
        with LOCK: JOBS[ident].update(status='COMPLETE',stage='Ready to explore',result=result)
    except Exception as exc:
        # Never return stderr/source contents/host paths to the browser.
        message=str(exc) if isinstance(exc,ValueError) else 'Import worker failed. Reload repositories or ask the operator to inspect logs.'
        with LOCK: JOBS[ident].update(status='FAILED',stage='Import stopped',error=message[:500])
    finally:
        with LOCK: ACTIVE=None
