#!/usr/bin/env bash
# Each mutating proposal suite gets a fresh owned DB/API/UI/fixture.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${EVIDENCE_DIR:-"${TMPDIR:-/tmp}/chronos-benchmark-ui-$$"}
export FRONTEND_URL=http://127.0.0.1:3003 TEST_API_URL=http://127.0.0.1:8005/api/v1
export BACKEND_PYTHON=${PYTHON_BIN:-"$ROOT/.venv/bin/python"}
export CHROMIUM_PATH=${CHROMIUM_PATH:-/usr/bin/chromium}
EVIDENCE_DIR="$OUT/proposal-review" FINAL01_BROWSER_SCRIPT=proposal-review-smoke.mjs bash "$ROOT/scripts/verify-final-lifecycle-ui.sh"
EVIDENCE_DIR="$OUT/lifecycle" FINAL01_BROWSER_SCRIPT=benchmark-release-smoke.mjs bash "$ROOT/scripts/verify-final-lifecycle-ui.sh"
EVIDENCE_DIR="$OUT/change-planning" bash "$ROOT/scripts/verify-change-planning-ui.sh"
