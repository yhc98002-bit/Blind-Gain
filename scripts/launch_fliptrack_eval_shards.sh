#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 7 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH MANIFEST RUN_DIR MAX_NEW_TOKENS [GPU_LIST] [IMAGE_MODE]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
MANIFEST="$5"
RUN_DIR="$6"
MAX_NEW_TOKENS="$7"
GPU_LIST="${8:-0 1 2 3 4 5 6 7}"
IMAGE_MODE="${9:-real}"
ROOT="$(pwd)"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards" "${RUN_DIR}/metrics"

for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}_shard${SHARD_INDEX}.log"
  PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}_shard${SHARD_INDEX}.pid"
  OUT_PATH="${RUN_DIR}/shards/shard_${SHARD_INDEX}.jsonl"
  METRICS_PATH="${RUN_DIR}/metrics/shard_${SHARD_INDEX}.json"

  if [[ -s "${METRICS_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=metrics_exists"
    continue
  fi
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RUN_DIR}/shards' '${RUN_DIR}/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=${GPU} python scripts/eval_qwen_vl_fliptrack.py --model-path '${MODEL_PATH}' --manifest '${MANIFEST}' --output '${OUT_PATH}' --metrics-output '${METRICS_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --image-mode '${IMAGE_MODE}' --image-cache-dir '${RUN_DIR}/${IMAGE_MODE}_image_cache' --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
done
