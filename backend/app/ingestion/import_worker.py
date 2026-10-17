"""Dedicated process for bounded local browser jobs; downloaded code is never run."""
import json
import sys
from app.ingestion.github_import import inspect_remote, import_public


def main():
    payload=json.loads(sys.stdin.buffer.read(2048))
    try:
        pinned=inspect_remote(payload['url'],payload['branch'])
        expected=payload['commit'] or pinned['source_revision']
        result=import_public(payload['url'],payload['branch'],payload['tenant'],expected)
        print(json.dumps({k:result[k] for k in ('repository','source_revision','resolved_calls','unresolved_calls') if k in result}))
    except ValueError as exc:
        print(json.dumps({'error':str(exc)[:500]})); return 2
    except Exception:
        print(json.dumps({'error':'Public intake failed. Check repository size, supported archive content, connectivity, and operator logs.'})); return 2
    return 0

if __name__=='__main__': sys.exit(main())
