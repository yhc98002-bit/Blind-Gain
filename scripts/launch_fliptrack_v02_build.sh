#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an29}"
N_PER_TEMPLATE="${2:-100}"
SEED="${3:-20260710}"
VARIANT="${4:-v02}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

RUN_ID="fliptrack_${VARIANT}_build_${NODE}_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
OUTPUT_DIR="data/fliptrack_${VARIANT}_source/renderable"
OUTPUT_MANIFEST="data/fliptrack_${VARIANT}_source_manifest.jsonl"
CONTACT_DIR="reports/contact_sheets/fliptrack_${VARIANT}"
COMMAND="python -m src.fliptrack.build_v02 --out-dir ${OUTPUT_DIR} --manifest ${OUTPUT_MANIFEST} --contact-sheet-dir ${CONTACT_DIR} --n-per-template ${N_PER_TEMPLATE} --seed ${SEED}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
START_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DIRTY=false
if [[ -n "$(git status --short)" ]]; then
  DIRTY=true
fi

cat > "${MANIFEST_PATH}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_6_fliptrack_v02_generation",
  "node": "${NODE}",
  "gpu_allocation": [],
  "git_hash": "${GIT_HASH}",
  "worktree_dirty": ${DIRTY},
  "config_hash": "${CONFIG_HASH}",
  "seed": ${SEED},
  "data_manifest_hash": null,
  "command": "${COMMAND}",
  "start_time_utc": "${START_TIME}",
  "end_time_utc": null,
  "status": "running",
  "expected_artifacts": ["${OUTPUT_MANIFEST}", "${CONTACT_DIR}"]
}
JSON

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' && source .venv/bin/activate && (nohup bash -lc 'set +e; PYTHONPATH=. ${COMMAND}; code=\$?; PYTHONPATH=. python scripts/finalize_run_manifest.py ${MANIFEST_PATH} \$code; exit \$code' > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"

printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_fliptrack_v02_build_run.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
