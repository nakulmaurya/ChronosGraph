"""Bounded real MCP invocation metadata, shared across stdio/API via FalkorDB."""
from functools import wraps
import inspect
import json
import logging
import re
import time
import uuid
from fastapi import HTTPException
from app.db.client import db_manager
from app.services.common import tenant_exists, tenant_lock, read

log = logging.getLogger(__name__)


def instrument(tool_name):
    def decorate(fn):
        signature = inspect.signature(fn)
        @wraps(fn)
        def wrapped(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments
            tenant = arguments.get('tenant_graph', 'repo_falkordb_py')
            # Validate before calling and never create an unknown tenant just to log it.
            tenant_exists(tenant)
            start = time.perf_counter()
            success, result_bytes, error_kind = False, 0, ''
            result = None
            try:
                # Reentrant local lock keeps check and operation together within this
                # process. It is deliberately not a cross-process authorization lock.
                with tenant_lock(tenant):
                    if arguments.get('expected_revision') is not None:
                        from app.services.agent_connection import require_snapshot
                        require_snapshot(tenant, arguments['expected_revision'])
                    result = fn(*args, **kwargs)
                result_bytes = len(json.dumps(result, ensure_ascii=False, separators=(',', ':'), default=str).encode('utf-8'))
                success = True
                return result
            except Exception as exc:
                error_kind = type(exc).__name__  # Never persist exception messages or arguments.
                raise
            finally:
                elapsed = round((time.perf_counter() - start) * 1000, 2)
                # Target paths only; no questions, code, diffs, commands, notes or secrets.
                paths = arguments.get('modified_files') or ([arguments['file_path']] if arguments.get('file_path') else [])
                paths = paths or ([arguments['target_file_path']] if arguments.get('target_file_path') else [])
                paths = paths or (result.get('changed_files', []) if isinstance(result, dict) else [])
                paths = [p for p in paths[:20] if isinstance(p, str) and len(p) <= 1024
                         and not p.startswith(('/', '.')) and not any(ord(c) < 32 for c in p)]
                try:
                    db_manager.query(tenant, '''CREATE (:AgentEvent {id:$id,timestamp:$now,
                        event_kind:'MCP_TOOL_CALL',tool_name:$tool,target_files:$paths,
                        duration_ms:$duration,outcome:$outcome,error_kind:$error,result_bytes:$bytes,
                        summary:$summary,result_measurement_basis:'JSON_VALUE_UTF8_PROTOCOL_ENVELOPE_EXCLUDED',source_type:'OBSERVED_MCP_INVOCATION'})''',
                        {'id': uuid.uuid4().hex, 'now': time.time_ns() // 1_000_000,
                         'tool': tool_name, 'paths': paths, 'duration': elapsed,
                         'outcome': 'SUCCESS' if success else 'ERROR', 'error': error_kind,
                         'bytes': result_bytes, 'summary': tool_name + (' completed' if success else ' failed')})
                    # Per-tenant retained latest 500, plus a small concurrent-write window.
                    db_manager.query(tenant, '''MATCH (e:AgentEvent) WITH e ORDER BY e.timestamp DESC,e.id DESC
                        SKIP 500 DELETE e''')
                except Exception:
                    # Mutation may already have committed: do not turn successful tools into
                    # misleading failures or mask the original failure. Explicit stderr notice.
                    log.warning('ChronosGraph activity recording unavailable for %s', tool_name)
        return wrapped
    return decorate


def activity(tenant_graph, cursor=None, limit=50):
    tenant = tenant_exists(tenant_graph)
    if not 1 <= limit <= 100 or (cursor and not re.fullmatch(r'[0-9]{1,20}:[a-f0-9]{32}', cursor)):
        raise HTTPException(422, 'Require limit 1..100 and an exact timestamp:id cursor')
    before, before_id = cursor.split(':') if cursor else ('0', '')
    data, _ = read(tenant, '''MATCH (e:AgentEvent) WHERE $before=0 OR e.timestamp<$before OR (e.timestamp=$before AND e.id<$before_id)
        RETURN e.id AS id,e.timestamp AS timestamp,e.tool_name AS tool_name,e.event_kind AS event_kind,
        e.target_files AS target_files,e.summary AS summary,e.duration_ms AS duration_ms,
        e.outcome AS outcome,e.error_kind AS error_kind,e.result_bytes AS result_bytes,
        e.source_type AS source_type,e.result_measurement_basis AS result_measurement_basis ORDER BY timestamp DESC,id DESC LIMIT $limit''',
        {'before': int(before), 'before_id': before_id, 'limit': limit})
    return {'tenant_graph': tenant, 'events': data, 'retention_limit': 500,
            'next_cursor': str(data[-1]['timestamp'])+':'+data[-1]['id'] if len(data) == limit else None,
            'scope': 'Observed ChronosGraph MCP calls only; no external agent thoughts or private Read calls.'}
