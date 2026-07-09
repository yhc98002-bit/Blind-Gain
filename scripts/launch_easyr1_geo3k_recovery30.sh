#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 NODE [CUDA_VISIBLE_DEVICES]" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="${2:-0,1}"
ROOT="$(pwd)"
RUN_ID="easyr1_geo3k_recovery30_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG_PATH="${ROOT}/configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(sha256sum "${CONFIG_PATH}" | awk '{print $1}')"
DATA_HASH="$(printf 'hiyouga/geometry3k@train|hiyouga/geometry3k@test[:32]' | sha256sum | awk '{print $1}')"
START_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "${MANIFEST_PATH}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "grpo_recovery_anchor",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_path": "${CONFIG_PATH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "hiyouga/geometry3k@train|hiyouga/geometry3k@test[:32]",
  "data_manifest_hash": "${DATA_HASH}",
  "command": "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1 python -m verl.trainer.main config=${CONFIG_PATH}",
  "start_time_utc": "${START_TIME}",
  "expected_artifact": "checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor",
  "stdout_stderr_log": "${LOG_PATH}"
}
JSON

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' checkpoints/stage0_repro/easyr1_geo3k_recovery30 && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1':\${PYTHONPATH:-} python -m verl.trainer.main config='${CONFIG_PATH}' > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"

printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_easyr1_geo3k_recovery30_run.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
