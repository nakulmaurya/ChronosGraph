"""Independent local import worker. No repository code is executed."""
import argparse
import json
import signal
import sys
from app.ingestion.github_import import inspect_remote, import_public


def execute(payload, job_id=''):
    pinned = inspect_remote(payload['url'], payload['branch'])
    expected = payload['commit'] or pinned['source_revision']
    return import_public(payload['url'], pinned['selected_branch'], payload['tenant'], expected, job_id=job_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job')
    args = parser.parse_args()
    if not args.job:  # Retain the documented legacy stdin transport.
        payload = json.loads(sys.stdin.buffer.read(2048))
        try:
            print(json.dumps(execute(payload)))
            return 0
        except Exception:
            print(json.dumps({'error': 'Public intake failed; no source code executed.'}))
            return 2
    from app.services.import_jobs import store, published
    state = store()
    job = state.get(args.job)
    lease = state.redis.lock(state.prefix + args.job + ':worker', timeout=340, blocking_timeout=0)
    if not lease.acquire(blocking=False):
        return 2
    def expired(*_):
        raise TimeoutError('Worker deadline exceeded')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(300)
    try:
        if job['status'] != 'RUNNING':
            return 0
        result = execute({**job, 'tenant': job['tenant_graph']}, args.job)
        state.finish(args.job, 'COMPLETE', 'Ready to explore', result={k: result[k] for k in ('repository', 'source_revision', 'resolved_calls', 'unresolved_calls') if k in result})
        return 0
    except Exception as exc:
        # Ready metadata wins if publication completed before a lost acknowledgement.
        if published(job):
            state.reconcile(args.job, published)
            return 0
        message = str(exc)[:500] if isinstance(exc, ValueError) else 'Import interrupted or failed. Check local service configuration; existing snapshots are unchanged.'
        state.finish(args.job, 'FAILED', 'Import stopped', error=message)
        return 2
    finally:
        signal.alarm(0)
        lease.release()


if __name__ == '__main__':
    sys.exit(main())
