#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 NODE [CUDA_VISIBLE_DEVICES]" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="${2:-0,1}"
ROOT="$(pwd)"
RUN_ID="easyr1_geo3k_smoke_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG_PATH="${ROOT}/configs/train/easyr1_qwen25vl3b_geo3k_smoke.yaml"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' checkpoints/stage0_repro/easyr1_geo3k_smoke && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1':\${PYTHONPATH:-} python -m verl.trainer.main config='${CONFIG_PATH}' > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"

echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
