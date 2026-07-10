#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNAPSHOT="${1:-${ROOT}/artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K/snapshots/812ec617dea4bc8a4e751663b88e4ebb7de4d00e}"
OUTPUT_ROOT="${2:-${ROOT}/data/virl39k}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="prepare_virl39k_${STAMP}"
RUN_DIR="${ROOT}/experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATS="${ROOT}/reports/virl39k_stats.json"
SHEET="${ROOT}/reports/contact_sheets/virl39k_16.png"
PARQUET="${SNAPSHOT}/39Krelease.parquet"
ZIP="${SNAPSHOT}/images.zip"
COMMAND="unzip -q -n ${ZIP} -d ${OUTPUT_ROOT} && python -m src.data.virl39k_loader --parquet ${PARQUET} --image-root ${OUTPUT_ROOT} --stats-output ${STATS} --contact-sheet ${SHEET}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
SOURCE_HASH="$( { sha256sum "${PARQUET}"; sha256sum "${ZIP}"; } | sha256sum | awk '{print $1}')"
cat > "${MANIFEST}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_9_prepare_virl39k",
  "node": "$(hostname)",
  "gpu_allocation": [],
  "git_hash": "$(git -C "${ROOT}" rev-parse HEAD)",
  "config_hash": "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')",
  "data_manifest": "TIGER-Lab/ViRL39K@812ec617dea4bc8a4e751663b88e4ebb7de4d00e",
  "data_manifest_hash": "${SOURCE_HASH}",
  "command": "${COMMAND}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_artifacts": ["${OUTPUT_ROOT}/images", "${STATS}", "${SHEET}"]
}
JSON

tmux new-session -d -s "${RUN_ID}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${MANIFEST}' '${LOG}'"
tmux list-panes -t "${RUN_ID}" -F '#{pane_pid}' > "${PID_FILE}"
echo "${RUN_DIR}"
echo "pid_file=${PID_FILE} log=${LOG}"
