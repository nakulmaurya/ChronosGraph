"""Opt-in loopback intake with Redis receipts and independently bounded workers."""
import os
import subprocess
import sys
import threading
import uuid
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.db.client import db_manager
from app.ingestion.github_import import repository_url, branch_name, SHA
from app.local_boundary import local_ui_origins
from app.services.import_state import ImportStore, public_receipt


class ImportRequest(BaseModel):
    url: str = Field(max_length=300)
    branch: str = Field(default='', max_length=200)
    commit: str = Field(default='', max_length=40)
    request_id: str = Field(default='', max_length=32)


def store():
    return ImportStore(db_manager.db.connection)


def enabled():
    return os.environ.get('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT') == '1'


def authorize(request):
    if not enabled():
        raise HTTPException(403, 'Browser import is disabled by the operator. Local CLI import is still available.')
    if (request.url.hostname not in ('localhost', '127.0.0.1') or
        request.headers.get('origin') not in local_ui_origins() or
        request.headers.get('x-chronosgraph-action') != 'public-import'):
        raise HTTPException(403, 'Use an operator-configured loopback command center to start imports')


def published(job):
    tenant = job['tenant_graph']
    if tenant not in db_manager.list_tenant_graphs():
        return None
    rows = db_manager.get_graph(tenant).ro_query('''MATCH (m:RepoMetadata)
      WHERE m.status='READY' AND m.import_job_id=$id
      RETURN m.repository,m.source_revision LIMIT 1''', {'id': job['id']}).result_set
    return {'repository': rows[0][0], 'source_revision': rows[0][1]} if rows else None


def receipt(ident):
    return public_receipt(store().reconcile(ident, published))


def launch(ident):
    env = dict(os.environ, CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT='1')
    process = subprocess.Popen([sys.executable, '-m', 'app.ingestion.import_worker', '--job', ident],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env=env, start_new_session=True)
    # Reap while this API lives; no lifecycle state is owned by this thread.
    threading.Thread(target=process.wait, daemon=True).start()


def start_import(body):
    try:
        _, _, url = repository_url(body.url)
        branch = branch_name(body.branch.strip()) if body.branch.strip() else ''
        commit = body.commit.strip().lower()
        if commit and not SHA.fullmatch(commit):
            raise ValueError('Commit hash must contain exactly 40 hexadecimal characters')
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    ident = body.request_id or uuid.uuid4().hex  # Legacy clients lack lost-ack protection.
    state = store()
    job, created = state.create(ident, {'url': url, 'branch': branch, 'commit': commit})
    if created:
        try:
            launch(ident)
        except OSError:
            state.finish(ident, 'FAILED', 'Worker could not start', error='Operator must check the local Python environment; no repository code was executed.')
    return receipt(ident)
