#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 7 || $# -gt 8 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH CAPTION_RUN_DIR QA_RUN_DIR [GPU_LIST] MAX_NEW_TOKENS" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
CAPTION_RUN_DIR="$5"
QA_RUN_DIR="$6"
GPU_LIST="${7:-0 1 2 3 4 5 6 7}"
MAX_NEW_TOKENS="${8:-32}"
ROOT="$(pwd)"

mkdir -p "${QA_RUN_DIR}/logs" "${QA_RUN_DIR}/pids" "${QA_RUN_DIR}/shards" "${QA_RUN_DIR}/metrics"

for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  INPUT_PATH="${CAPTION_RUN_DIR}/shards/captions_shard_${SHARD_INDEX}.jsonl"
  OUT_PATH="${QA_RUN_DIR}/shards/caption_qa_shard_${SHARD_INDEX}.jsonl"
  METRICS_PATH="${QA_RUN_DIR}/metrics/shard_${SHARD_INDEX}.json"
  LOG_PATH="${QA_RUN_DIR}/logs/${NODE}_gpu${GPU}_caption_qa_shard${SHARD_INDEX}.log"
  PID_PATH="${QA_RUN_DIR}/pids/${NODE}_gpu${GPU}_caption_qa_shard${SHARD_INDEX}.pid"

  if [[ ! -s "${INPUT_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=missing_caption_input"
    continue
  fi
  if [[ -s "${METRICS_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=metrics_exists"
    continue
  fi
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${QA_RUN_DIR}/logs' '${QA_RUN_DIR}/pids' '${QA_RUN_DIR}/shards' '${QA_RUN_DIR}/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=${GPU} python scripts/eval_caption_qa_fliptrack.py --model-path '${MODEL_PATH}' --input '${INPUT_PATH}' --output '${OUT_PATH}' --metrics-output '${METRICS_PATH}' --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
done
