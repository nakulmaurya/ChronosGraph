#!/usr/bin/env bash
# Disposable crash/restart test of the exact Compose image + REDIS_ARGS contract.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PYTHON_BIN:-"$ROOT/.venv/bin/python"}
IMAGE='falkordb/falkordb@sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a'
NAME="chronos-persistence-$(date +%s)-$$"
VOLUME="$NAME-data"
cleanup(){ docker rm -f "$NAME" >/dev/null 2>&1 || true; docker volume rm "$VOLUME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker volume create "$VOLUME" >/dev/null
docker run -d --name "$NAME" -e BROWSER=0 -e REDIS_ARGS='--appendonly yes' -v "$VOLUME:/var/lib/falkordb/data" -p 127.0.0.1::6379 "$IMAGE" >/dev/null
export PYTHONPATH="$ROOT/backend" FALKORDB_HOST=127.0.0.1 FALKORDB_PORT=$(docker port "$NAME" 6379/tcp | awk -F: '{print $NF}')
"$PY" - <<'PY'
import time
from redis import Redis
from app.services.import_state import ImportStore
r=Redis(host='127.0.0.1',port=int(__import__('os').environ['FALKORDB_PORT']))
for _ in range(60):
    try:r.ping();break
    except Exception:time.sleep(.5)
else:raise SystemExit('Persistence fixture failed to start')
config=r.config_get('appendonly')
assert str(next(iter(config.values()))).strip("b'")=="yes",config
r.execute_command('GRAPH.QUERY','repo_test_persistence',"CREATE (:RepoMetadata {status:'READY',repository:'fixture/persistence'})")
ImportStore(r).create('a'*32,{'url':'https://github.com/pallets/click','branch':'','commit':''})
time.sleep(2)  # Default every-second fsync: do not claim zero-loss power failure.
assert r.info('persistence')['aof_last_write_status']=='ok'
print('AOF enabled; native graph and durable receipt written in isolated volume.')
PY
docker kill --signal=KILL "$NAME" >/dev/null
docker start "$NAME" >/dev/null
export FALKORDB_PORT=$(docker port "$NAME" 6379/tcp | awk -F: '{print $NF}')
"$PY" - <<'PY'
import os,time
from redis import Redis
from app.services.import_state import ImportStore
r=Redis(host='127.0.0.1',port=int(os.environ['FALKORDB_PORT']))
for _ in range(60):
    try:r.ping();break
    except Exception:time.sleep(.5)
else:raise SystemExit('Persistence fixture failed to restart')
assert ImportStore(r).get('a'*32)['status']=='RUNNING'
result=r.execute_command('GRAPH.RO_QUERY','repo_test_persistence','MATCH (m:RepoMetadata) RETURN m.repository')
assert b'fixture/persistence' in repr(result).encode(),result
print('PASS crash/restart restored graph + import receipt; no production database accessed.')
PY
