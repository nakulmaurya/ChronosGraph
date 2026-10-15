#!/usr/bin/env bash
# Local trusted-user demo only. No public binding, cloud deployment or paid models.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_MODE=docker
INSTALL=1
VERIFY=0
while (($#)); do
  case "$1" in
    --db) DB_MODE="${2:?Use existing, native or docker}"; shift 2;;
    --no-install) INSTALL=0; shift;;
    --verify-only) VERIFY=1; shift;;
    --help) echo 'bash scripts/start-local.sh [--db docker|native|existing] [--no-install] [--verify-only]'; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
case "$DB_MODE" in docker|native|existing);; *) echo 'Invalid database mode' >&2; exit 2;; esac
command -v node >/dev/null
command -v npm >/dev/null
node -e 'if(Number(process.versions.node.split(".")[0])<24)process.exit(1)' || { echo 'Use Node.js 24+ (TypeScript test stripping)' >&2; exit 1; }
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
PY="$VENV_DIR/bin/python"
LOGS="$(mktemp -d "${TMPDIR:-/tmp}/chronosgraph-local.XXXXXX")"
CHILDREN=()
CONTAINER=""
cleanup() {
  for pid in "${CHILDREN[@]}"; do kill "$pid" 2>/dev/null || true; done
  if [[ -n "$CONTAINER" ]]; then docker stop "$CONTAINER" >/dev/null 2>&1 || true; fi
  echo "Local launcher stopped. Logs: $LOGS"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if ((INSTALL)); then
  if [[ ! -x "$PY" ]]; then python3 -m venv "$VENV_DIR"; fi
  "$PY" -m pip install -e "$ROOT/backend"
  if [[ "$DB_MODE" == native ]]; then "$PY" -m pip install falkordblite==0.10.0; fi
  (cd "$ROOT/frontend" && npm ci)
fi
[[ -x "$PY" ]] || { echo "Missing Python environment: $VENV_DIR" >&2; exit 1; }
[[ -d "$ROOT/frontend/node_modules" ]] || { echo 'Run without --no-install first' >&2; exit 1; }
export FALKORDB_HOST=127.0.0.1
export FALKORDB_PORT="${FALKORDB_PORT:-6379}"
if [[ "$DB_MODE" != existing ]]; then
  "$PY" - <<'PY'
import os,socket
s=socket.socket();s.settimeout(1)
if s.connect_ex(('127.0.0.1',int(os.environ['FALKORDB_PORT'])))==0:
    raise SystemExit('Database port is occupied. Explicitly use --db existing to reuse a trusted FalkorDB.')
s.close()
PY
  if [[ "$DB_MODE" == docker ]]; then
    command -v docker >/dev/null || { echo 'Docker unavailable; use --db native or --db existing' >&2; exit 1; }
    CONTAINER="chronosgraph-local-$$"
    docker run --detach --rm --name "$CONTAINER" --publish "127.0.0.1:$FALKORDB_PORT:6379" falkordb/falkordb:latest > "$LOGS/container.txt"
  else
    "$PY" "$ROOT/scripts/run-falkordblite.py" > "$LOGS/database.log" 2>&1 & CHILDREN+=("$!")
  fi
fi
"$PY" - <<'PY'
import os,time
from falkordb import FalkorDB
last=None
for _ in range(60):
    try:
        db=FalkorDB(host='127.0.0.1',port=int(os.environ['FALKORDB_PORT']))
        db.list_graphs()  # Reject plain Redis; require real GRAPH.LIST support.
        print('Native GRAPH.LIST verified');break
    except Exception as exc:
        last=type(exc).__name__;time.sleep(.5)
else: raise SystemExit('FalkorDB not ready; check database logs. Last error: '+str(last))
PY
(cd "$ROOT/backend" && "$PY" -m app.ingestion.seed_repos) | tee "$LOGS/seed.txt"
if ((VERIFY)); then
  (cd "$ROOT/backend" && "$PY" -m pytest -v) | tee "$LOGS/backend-pytest.txt"
  (cd "$ROOT/frontend" && npm test && npm run typecheck && NEXT_TELEMETRY_DISABLED=1 npm run build) | tee "$LOGS/frontend-checks.txt"
  echo "Verification completed; no web servers started. Evidence: $LOGS"
  exit 0
fi
# Refuse occupied web ports; do not stop user processes or silently choose a CORS-incompatible port.
"$PY" - <<'PY'
import socket
for port in (8000,3001):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port))==0:
            raise SystemExit(f'Port {port} is occupied; stop your own server or use --verify-only')
PY
(cd "$ROOT/backend" && exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) > "$LOGS/api.log" 2>&1 & CHILDREN+=("$!")
(cd "$ROOT/frontend" && exec node node_modules/next/dist/bin/next dev -p 3001 --hostname 127.0.0.1) > "$LOGS/frontend.log" 2>&1 & CHILDREN+=("$!")
echo "Open http://127.0.0.1:3001 after servers are ready. Logs: $LOGS"
echo 'Ctrl-C stops only processes/container owned by this launcher. Owned databases are ephemeral.'
wait -n "${CHILDREN[@]}"
