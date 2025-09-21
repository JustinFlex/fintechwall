#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

if [ -f "${SCRIPT_DIR}/env.example" ] && [ ! -f "${BACKEND_DIR}/.env" ]; then
  echo "Warning: ${BACKEND_DIR}/.env not found. Copy deployment/uv/env.example to backend/.env" >&2
fi

cd "${BACKEND_DIR}"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
