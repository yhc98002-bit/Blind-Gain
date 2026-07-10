#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an12}"
GPU="${2:-4}"
RELEASE_DIR="${3:-data/fliptrack_v02}"
KEY_FILE="${4:-.private/fliptrack_v02_key.jsonl}"
OUTPUT="${5:-reports/artifact_gate_v02.json}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

RUN_ID="artifact_gate_v02_${NODE}_gpu${GPU}_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
COMMAND="python -m src.fliptrack.artifact_attackers --release-dir ${RELEASE_DIR} --key-file ${KEY_FILE} --output ${OUTPUT} --dinov2-model facebook/dinov2-small --batch-size 32 --old-input-jsonl data/fliptrack_v01_manifest.jsonl --n-splits 5 --n-bootstrap 1000 --seed 20260710"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$( { sha256sum "${RELEASE_DIR}/manifest.jsonl"; sha256sum "${KEY_FILE}"; } | sha256sum | awk '{print $1}')"
cat > "${MANIFEST_PATH}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_5_artifact_gate_v02",
  "node": "${NODE}",
  "gpu_allocation": "${GPU}",
  "git_hash": "$(git rev-parse HEAD)",
  "config_hash": "${CONFIG_HASH}",
  "seed": 20260710,
  "data_manifest": "${RELEASE_DIR}/manifest.jsonl + private key",
  "data_manifest_hash": "${DATA_HASH}",
  "model_revision": "facebook/dinov2-small (local cache)",
  "command": "${COMMAND}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_artifacts": ["${OUTPUT}"]
}
JSON

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' && source .venv/bin/activate && (nohup bash -lc 'set +e; env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} PYTHONPATH=. ${COMMAND}; code=\$?; PYTHONPATH=. python scripts/finalize_run_manifest.py ${MANIFEST_PATH} \$code; exit \$code' > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_artifact_gate_v02_run.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
