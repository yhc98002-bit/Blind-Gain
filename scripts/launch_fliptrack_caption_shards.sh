#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 7 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH MANIFEST RUN_DIR [GPU_LIST]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
MANIFEST="$5"
RUN_DIR="$6"
GPU_LIST="${7:-0 1 2 3 4 5 6 7}"
ROOT="$(pwd)"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards"

for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}_caption_shard${SHARD_INDEX}.log"
  PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}_caption_shard${SHARD_INDEX}.pid"
  OUT_PATH="${RUN_DIR}/shards/captions_shard_${SHARD_INDEX}.jsonl"

  if [[ -s "${OUT_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=output_exists"
    continue
  fi
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RUN_DIR}/shards' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=${GPU} python scripts/caption_fliptrack.py --model-path '${MODEL_PATH}' --manifest '${MANIFEST}' --output '${OUT_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
done
