set -eu
BASE="$HOME/ChronosGraph-task-integration"
PY="$HOME/ChronosGraph-quality-batch1/.venv/bin/python"
cd "$BASE"
NAME="chronos-task-tests-$(date +%s)"
IMAGE=$(docker inspect --format '{{.Image}}' chronosgraph-review-c9e09cd)
ID=$(docker run --rm -d --name "$NAME" -p 127.0.0.1::6379 "$IMAGE")
trap 'docker stop "$ID" >/dev/null' EXIT
PORT=$(docker port "$ID" 6379/tcp | awk -F: '{print $NF}')
FALKORDB_PORT=6381 TARGET_PORT="$PORT" "$PY" - <<'PY'
import time,os
from redis import Redis
source=Redis(host='127.0.0.1',port=6381);target=Redis(host='127.0.0.1',port=int(os.environ['TARGET_PORT']))
for _ in range(60):
 try:target.execute_command('GRAPH.LIST');break
 except Exception:time.sleep(.5)
for name in ['repo_falkordb_py','repo_graphrag_sdk','repo_falkordb_code_graph','repo_mcp_python_sdk']:
 data=source.dump(name)
 assert data is not None,name
 target.restore(name,0,data)
print('DISPOSABLE_NATIVE_DATABASE_COPY source reads only; four corpora')
PY
FALKORDB_PORT="$PORT" PYTHONPATH="$BASE/backend:$BASE/backend/tests" CHRONOSGRAPH_DISPOSABLE_BENCHMARK=1 "$PY" -m pytest backend/tests -q --tb=short > /tmp/chronos-task-isolated-full-tests.log 2>&1
cat /tmp/chronos-task-isolated-full-tests.log
