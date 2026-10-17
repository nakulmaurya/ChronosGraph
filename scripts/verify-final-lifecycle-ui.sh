#!/usr/bin/env bash
# Owned, isolated DB/API/UI. Never tests POST previews against the running preview.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PYTHON_BIN:-"$ROOT/.venv/bin/python"}
OUT=${EVIDENCE_DIR:-"${TMPDIR:-/tmp}/chronos-change-planning-$$"}
mkdir -p "$OUT"
"$PY" - <<'PY'
import socket
for port in (3003,8005):
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: s.bind(('127.0.0.1',port))
        except OSError: raise SystemExit(f'Port {port} is in use; stop only its known owned test server before retrying')
PY
IMAGE=$(docker inspect --format '{{.Image}}' "${SOURCE_FALKORDB_CONTAINER:-chronosgraph-local-6142}")
ID=$(docker run --rm -d -p 127.0.0.1::6379 "$IMAGE")
API_PID= UI_PID= FIXTURE_PID=
cleanup(){
  [[ -z "$UI_PID" ]] || kill -TERM -- "-$UI_PID" 2>/dev/null || true
  [[ -z "$API_PID" ]] || kill -TERM -- "-$API_PID" 2>/dev/null || true
  [[ -z "$UI_PID" ]] || wait "$UI_PID" 2>/dev/null || true
  [[ -z "$API_PID" ]] || wait "$API_PID" 2>/dev/null || true
  [[ -z "$FIXTURE_PID" ]] || kill -TERM "$FIXTURE_PID" 2>/dev/null || true
  [[ -z "$FIXTURE_PID" ]] || wait "$FIXTURE_PID" 2>/dev/null || true
  docker stop "$ID" >/dev/null 2>&1 || true
}
trap cleanup EXIT
PORT=$(docker port "$ID" 6379/tcp | awk -F: '{print $NF}')
export PYTHONPATH="$ROOT/backend:$ROOT/backend/tests" FALKORDB_HOST=127.0.0.1 FALKORDB_PORT="$PORT"
export SOURCE_PORT=${SOURCE_FALKORDB_PORT:-6379}
"$PY" - <<'PY'
import os,time
from redis import Redis
source=Redis(host='127.0.0.1',port=int(os.environ['SOURCE_PORT']))
target=Redis(host='127.0.0.1',port=int(os.environ['FALKORDB_PORT']))
for _ in range(60):
    try: target.ping(); break
    except Exception: time.sleep(.5)
else: raise SystemExit('Isolated DB unavailable')
for name in ('repo_falkordb_py','repo_graphrag_sdk','repo_falkordb_code_graph','repo_mcp_python_sdk'):
    data=source.dump(name)
    if data is None: raise SystemExit('Missing seed source graph')
    target.restore(name,0,data)
PY
"$PY" "$ROOT/scripts/serve-hero-ui-fixture.py" "$OUT/fixture.json" > "$OUT/fixture.log" 2>&1 & FIXTURE_PID=$!
for i in $(seq 1 360); do [[ ! -f "$OUT/fixture.json" ]] || break; kill -0 "$FIXTURE_PID" 2>/dev/null || { cat "$OUT/fixture.log"; exit 1; }; sleep .5; done
[[ -f "$OUT/fixture.json" ]]
export HERO_FIXTURE="$OUT/fixture.json"
export CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION=1 CHRONOSGRAPH_UI_ORIGINS=http://127.0.0.1:3003
export CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS=$("$PY" -c 'import json,os;print(json.load(open(os.environ["HERO_FIXTURE"]))["allowed_root"])')
export CHRONOSGRAPH_EXECUTION_REPOSITORIES=$("$PY" -c 'import json,os;d=json.load(open(os.environ["HERO_FIXTURE"]));print(json.dumps({d["tenant"]:d["root"]}))')
setsid "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8005 > "$OUT/api.log" 2>&1 & API_PID=$!
"$PY" - <<'PY'
import time,urllib.request
for _ in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8005/health',timeout=2) as r: assert r.status==200
        break
    except Exception: time.sleep(.5)
else: raise SystemExit('Owned API failed to start')
PY
cd "$ROOT/frontend"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8005/api/v1 npm run build > "$OUT/build.log" 2>&1
setsid node node_modules/next/dist/bin/next start -p 3003 --hostname 127.0.0.1 > "$OUT/ui-server.log" 2>&1 & UI_PID=$!
"$PY" - <<'PY'
import time,urllib.request
for _ in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:3003',timeout=2) as r: assert r.status==200
        break
    except Exception: time.sleep(.5)
else: raise SystemExit('Owned UI failed to start')
PY
API_URL=http://127.0.0.1:8005/api/v1 EVIDENCE_DIR="$OUT/ui" node "tests/${FINAL01_BROWSER_SCRIPT:-final-lifecycle-smoke.mjs}" > "$OUT/ui.log" 2>&1
cat "$OUT/ui.log"
