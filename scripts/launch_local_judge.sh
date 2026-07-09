#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an12}"
GPU="${2:-4}"
PORT="${3:-18080}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_PATH="${ROOT}/artifacts/models/Qwen/Qwen2.5-7B-Instruct"
MODEL_HASH="1e8d53b21b997eb18436573d3f5cc961fbaf00cd583131f6a89a05617e24c72c"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="local_judge_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="${ROOT}/experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
SERVED_NAME="qwen25-7b-judge"
COMMAND="python -m vllm.entrypoints.openai.api_server --model ${MODEL_PATH} --served-model-name ${SERVED_NAME} --host 0.0.0.0 --port ${PORT} --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.85 --trust-remote-code"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
GIT_HASH="$(git -C "${ROOT}" rev-parse HEAD)"
CONFIG_HASH="$(printf '%s\n' "${COMMAND}" | sha256sum | awk '{print $1}')"
cat > "${MANIFEST}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_2_local_openai_judge_service",
  "node": "${NODE}",
  "gpu_allocation": "${GPU}",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": null,
  "data_manifest_hash": null,
  "model_path": "${MODEL_PATH}",
  "model_revision": "ModelScope master",
  "model_tree_sha256": "${MODEL_HASH}",
  "served_model_name": "${SERVED_NAME}",
  "endpoint": "http://${NODE}:${PORT}/v1",
  "command": "${COMMAND}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ready_time_utc": null,
  "end_time_utc": null,
  "status": "starting",
  "stdout_stderr_log": "${LOG}"
}
JSON

ssh "${NODE}" "cd '${ROOT}' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} ${COMMAND} > '${LOG}' 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
printf 'endpoint=http://%s:%s/v1 pid_file=%s log=%s\n' "${NODE}" "${PORT}" "${PID_FILE}" "${LOG}"
