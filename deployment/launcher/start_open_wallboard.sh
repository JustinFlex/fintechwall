#!/usr/bin/env bash
# One-click launcher for the open-data wallboard (backend + frontend).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend/src"
ENV_TEMPLATE="${PROJECT_ROOT}/config/defaults/backend.env"
ENV_FILE="${BACKEND_DIR}/.env"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"
URL="http://localhost:4173/rolling-screen.html"

mkdir -p "${LOG_DIR}"

require_bin() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[launcher] Missing dependency: $1" >&2
    exit 1
  fi
}

require_bin python3
require_bin uv

if [ ! -f "${ENV_FILE}" ]; then
  echo "[launcher] Creating backend/.env from defaults"
  cp "${ENV_TEMPLATE}" "${ENV_FILE}"
fi

python3 - <<'PY' "${ENV_FILE}"
from pathlib import Path
import re, sys
path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
if re.search(r'^DATA_MODE=', text, flags=re.MULTILINE):
    text = re.sub(r'^DATA_MODE=.*$', 'DATA_MODE=open', text, flags=re.MULTILINE)
else:
    if not text.endswith('\n'):
        text += '\n'
    text += 'DATA_MODE=open\n'
path.write_text(text, encoding='utf-8')
PY

if [ ! -d "${BACKEND_DIR}/.venv" ]; then
  echo "[launcher] Installing backend dependencies via uv sync (first run)"
  (cd "${BACKEND_DIR}" && uv sync)
fi

start_backend() {
  echo "[launcher] Starting backend (logs: ${BACKEND_LOG})"
  (
    cd "${BACKEND_DIR}"
    DATA_MODE=open uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
  ) >>"${BACKEND_LOG}" 2>&1 &
  BACKEND_PID=$!
}

start_frontend() {
  echo "[launcher] Starting frontend (logs: ${FRONTEND_LOG})"
  (
    cd "${FRONTEND_DIR}"
    python3 -m http.server 4173
  ) >>"${FRONTEND_LOG}" 2>&1 &
  FRONTEND_PID=$!
}

cleanup() {
  echo "[launcher] Shutting down..."
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

start_backend
sleep 2
start_frontend
sleep 2

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
elif command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe start "${URL}" >/dev/null 2>&1 || true
fi

echo "[launcher] Wallboard is running. Open ${URL} in your browser."
wait
