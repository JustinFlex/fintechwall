#!/usr/bin/env bash
# Probe /health/ready and /data/latest to validate external open-data feeds.

set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
JQ_BIN="${JQ_BIN:-jq}"

if ! command -v "${JQ_BIN}" >/dev/null 2>&1; then
  echo "[probe] jq is required but not found (set JQ_BIN to override)." >&2
  exit 90
fi

echo "[probe] Checking backend readiness at ${API_BASE}/health/ready" >&2
if ! curl -fsS "${API_BASE}/health/ready" >/dev/null; then
  echo "[probe] /health/ready failed" >&2
  exit 2
fi

payload_file="$(mktemp)"
trap 'rm -f "${payload_file}"' EXIT

echo "[probe] Fetching ${API_BASE}/data/latest" >&2
if ! curl -fsS "${API_BASE}/data/latest" -o "${payload_file}"; then
  echo "[probe] /data/latest fetch failed" >&2
  exit 3
fi

data_mode=$("${JQ_BIN}" -r '.data_mode // .metadata.data_mode // ""' "${payload_file}")
if [ "${data_mode}" != "open" ]; then
  echo "[probe] Expected data_mode=open but got '${data_mode}'" >&2
  exit 4
fi

check_field() {
  local path=$1
  if ! "${JQ_BIN}" -e "${path}" "${payload_file}" >/dev/null; then
    echo "[probe] Missing expected field: ${path}" >&2
    return 1
  fi
}

check_field '.indices."SPX.GI".last'
check_field '.rates."UST10Y.GBM".timestamp'
check_field '.rates."SOFR.IR".last'
check_field '.calendar.events[0].source'

echo "[probe] Snapshot looks healthy (Stooq/FRED/ForexFactory reachable)." >&2
