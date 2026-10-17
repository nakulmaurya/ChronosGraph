#!/usr/bin/env bash
# Run backend compatibility checks in a disposable native FalkorDB instance.
# Requires Docker and an installed backend environment. Never reseeds the source DB.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PYTHON_BIN:-"$ROOT/.venv/bin/python"}
SOURCE_CONTAINER=${SOURCE_FALKORDB_CONTAINER:-chronosgraph-local-6142}
SOURCE_PORT=${SOURCE_FALKORDB_PORT:-6379}
OUT=${EVIDENCE_DIR:-"${TMPDIR:-/tmp}/chronosgraph-quality-batch1-$$"}
mkdir -p "$OUT"
IMAGE=$(docker inspect --format '{{.Image}}' "$SOURCE_CONTAINER")
NAME="chronos-quality-batch1-$(date +%s)-$$"
ID=$(docker run --rm -d --name "$NAME" -p 127.0.0.1::6379 "$IMAGE")
cleanup() { docker stop "$ID" >/dev/null 2>&1 || true; }
trap cleanup EXIT
PORT=$(docker port "$ID" 6379/tcp | awk -F: '{print $NF}')
export PYTHONPATH="$ROOT/backend:$ROOT/backend/tests"
SOURCE_FALKORDB_PORT="$SOURCE_PORT" TARGET_PORT="$PORT" "$PY" - <<'PY'
import json, os, time
from redis import Redis
source = Redis(host='127.0.0.1', port=int(os.environ['SOURCE_FALKORDB_PORT']))
target = Redis(host='127.0.0.1', port=int(os.environ['TARGET_PORT']))
for _ in range(60):
    try:
        target.execute_command('GRAPH.LIST')
        break
    except Exception:
        time.sleep(.5)
else:
    raise SystemExit('Isolated native FalkorDB did not start')
for name in ['repo_falkordb_py','repo_graphrag_sdk','repo_falkordb_code_graph','repo_mcp_python_sdk']:
    data = source.dump(name)  # Redis serialization: read only on the source instance.
    if data is None:
        raise SystemExit(f'Missing source graph {name}')
    target.restore(name, 0, data)
print(json.dumps({'mode':'DISPOSABLE_NATIVE_DATABASE_COPY','target_port':target.connection_pool.connection_kwargs['port'],
                  'copied_graphs':4,'source_mutation':False}))
PY
export FALKORDB_HOST=127.0.0.1 FALKORDB_PORT="$PORT"
cd "$ROOT"
"$PY" -m pytest backend/tests -v > "$OUT/backend-full.log" 2>&1
tail -4 "$OUT/backend-full.log"

CHRONOSGRAPH_DISPOSABLE_BENCHMARK=1 EVIDENCE_DIR="$OUT" "$PY" scripts/benchmark-navigation.py > "$OUT/navigation-benchmark.log"
