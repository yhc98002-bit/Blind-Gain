#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="prepare_mmk12_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PARQUET_DIR="data/mmk12/data"
STATS="reports/mmk12_stats.json"
SHEET="reports/contact_sheets/mmk12_16.png"
REVISION="372a609268ea79b5e78d90ab173e02c37b486163"
COMMAND=".venv/bin/python -m src.data.mmk12_loader --parquet-dir ${PARQUET_DIR} --stats-output ${STATS} --contact-sheet ${SHEET}"

cd "${ROOT}"
if [[ ! -d "${PARQUET_DIR}" ]]; then
  echo "Missing MMK12 parquet directory: ${PARQUET_DIR}" >&2
  exit 2
fi
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$(sha256sum "${PARQUET_DIR}"/*.parquet | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "FanqingM/MMK12@${REVISION}" \
  --arg data_manifest_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg stats "${STATS}" \
  --arg sheet "${SHEET}" \
  '{
    run_id: $run_id,
    job_type: "p1_9_prepare_mmk12",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_manifest_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$stats, $sheet]
  }' > "${MANIFEST}"

tmux new-session -d -s "${RUN_ID}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
echo "${RUN_DIR}"
echo "tmux_session=${RUN_ID} log=${LOG}"
