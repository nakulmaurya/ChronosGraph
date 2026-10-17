"""Redis-backed local import receipts. Durable across API restarts, not DB loss.

Idempotency is retained for seven days. A receipt read reconciles a published
snapshot after a lost worker acknowledgement, or reports an interrupted deadline.
No automatic retry deletes or overwrites a partially indexed graph.
"""
import hashlib
import json
import re
import time
from fastapi import HTTPException
from redis.exceptions import WatchError

RETENTION = 7 * 86400
DEADLINE = 330
IDENT = re.compile(r'[a-f0-9]{32}\Z')


class ImportStore:
    def __init__(self, redis, prefix='chronosgraph:imports:v2:'):
        self.redis, self.prefix = redis, prefix

    def key(self, ident):
        if not IDENT.fullmatch(ident):
            raise HTTPException(422, 'Require a 32-character lowercase import request ID')
        return self.prefix + ident

    def create(self, ident, payload):
        key = self.key(ident)
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        active = self.prefix + 'active'
        for _ in range(12):
            with self.redis.pipeline() as pipe:
                try:
                    pipe.watch(key, active)
                    previous = pipe.get(key)
                    if previous:
                        job = json.loads(previous)
                        if job['fingerprint'] != fingerprint:
                            raise HTTPException(409, 'This request ID belongs to different import inputs; use a new request ID')
                        return job, False
                    owner = pipe.get(active)
                    owner = owner.decode() if isinstance(owner, bytes) else owner
                    if owner == ident:
                        # Another retry published between the two watched reads.
                        # Restart the transaction so its receipt is read first.
                        continue
                    if owner:
                        raise HTTPException(409, 'Another repository is importing; wait for its bounded worker deadline')
                    now = time.time()
                    job = {'id': ident, 'fingerprint': fingerprint, **payload,
                           'tenant_graph': 'repo_github_' + ident, 'created_at': now,
                           'deadline_at': now + DEADLINE, 'status': 'RUNNING',
                           'stage': 'Queued for a bounded public snapshot import', 'error': None, 'result': None}
                    pipe.multi()
                    pipe.set(key, json.dumps(job), ex=RETENTION)
                    pipe.set(active, ident, ex=DEADLINE + 10)
                    pipe.execute()
                    return job, True
                except WatchError:
                    continue
        raise HTTPException(503, 'Import coordination is busy; retry with the same request ID')

    def get(self, ident):
        data = self.redis.get(self.key(ident))
        if not data:
            raise HTTPException(404, 'Import receipt is unavailable or older than seven days; reload saved repositories')
        return json.loads(data)

    def finish(self, ident, status, stage, *, result=None, error=None):
        key, active = self.key(ident), self.prefix + 'active'
        for _ in range(12):
            with self.redis.pipeline() as pipe:
                try:
                    pipe.watch(key, active)
                    job = self.get(ident)
                    if job['status'] != 'RUNNING' and status != 'COMPLETE':
                        return job
                    job.update(status=status, stage=stage, result=result, error=error)
                    owned = pipe.get(active)
                    owned = owned.decode() if isinstance(owned, bytes) else owned
                    pipe.multi()
                    pipe.set(key, json.dumps(job), ex=RETENTION)
                    if owned == ident:
                        pipe.delete(active)
                    pipe.execute()
                    return job
                except WatchError:
                    continue
        raise HTTPException(503, 'Import status update is busy; reconcile the same receipt')

    def reconcile(self, ident, published):
        job = self.get(ident)
        # Publication is stronger evidence than a lost completion acknowledgement.
        if job['status'] != 'COMPLETE':
            result = published(job)
            if result:
                return self.finish(ident, 'COMPLETE', 'Ready to explore (reconciled publication)', result=result)
        if job['status'] == 'RUNNING' and time.time() > job['deadline_at']:
            return self.finish(ident, 'INTERRUPTED', 'Worker deadline passed; no ready snapshot confirmed',
                               error='Import was interrupted. Any incomplete graph is retained for operator review; retrying this request never creates another snapshot.')
        return job


def public_receipt(job):
    return {key: job[key] for key in ('id', 'status', 'stage', 'tenant_graph', 'error', 'result', 'created_at', 'deadline_at')}
