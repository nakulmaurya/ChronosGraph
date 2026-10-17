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
API_PID= UI_PID=
cleanup(){
  [[ -z "$UI_PID" ]] || kill -TERM -- "-$UI_PID" 2>/dev/null || true
  [[ -z "$API_PID" ]] || kill -TERM -- "-$API_PID" 2>/dev/null || true
  [[ -z "$UI_PID" ]] || wait "$UI_PID" 2>/dev/null || true
  [[ -z "$API_PID" ]] || wait "$API_PID" 2>/dev/null || true
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
TENANT_GRAPH=$("$PY" - <<'PY'
import subprocess,tempfile,uuid
from pathlib import Path
from app.ingestion.ingest_repo import ingest_repo
name='repo_test_'+uuid.uuid4().hex
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'change-planning-example';root.mkdir()
    subprocess.run(['git','init','--quiet',str(root)],check=True)
    files={'README.md':'# Mixed-language workspace fixture\n','web/app.ts':'export const demo = 1;\n','src/pkg/__init__.py':'','src/pkg/a.py':'def helper():\n    return 1\n',
           'src/pkg/b.py':'from pkg.a import helper\ndef run():\n    return helper()\n',
           'tests/test_helper.py':'from pkg.b import run\ndef test_helper():\n    assert run() == 1\n'}
    for path,text in files.items():
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Local Test Author','-c','user.email=fixture@example.invalid','commit','--quiet','-m','Change planner fixture'],check=True)
    ingest_repo(str(root),name)
print(name)
PY
)
export TENANT_GRAPH
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
API_URL=http://127.0.0.1:8005/api/v1 EVIDENCE_DIR="$OUT/ui" node tests/change-planning-smoke.mjs > "$OUT/ui.log" 2>&1
API_URL=http://127.0.0.1:8005/api/v1 EVIDENCE_DIR="$OUT/recovery" node tests/ui-recovery-smoke.mjs > "$OUT/recovery.log" 2>&1
API_URL=http://127.0.0.1:8005/api/v1 EVIDENCE_DIR="$OUT/setup" node tests/agent-setup-smoke.mjs > "$OUT/setup.log" 2>&1
API_URL=http://127.0.0.1:8005/api/v1 EVIDENCE_DIR="$OUT/bulk" node tests/bulk-workspace-smoke.mjs > "$OUT/bulk-ui.log" 2>&1
"$PY" - <<'PY'
import os
from app.db.client import db_manager
names=db_manager.list_tenant_graphs()
assert not any(n.startswith(('sandbox_','tmp_')) for n in names),names
rows=db_manager.get_graph(os.environ['TENANT_GRAPH']).ro_query("MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.source_text").result_set
assert rows==[['def helper():\n    return 1\n']],rows
print('Native postconditions: no sandbox graphs, saved source unchanged; owned DB/API/UI cleaned on exit.')
PY
cat "$OUT/ui.log"
