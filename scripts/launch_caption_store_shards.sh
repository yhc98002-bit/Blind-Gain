#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 8 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH IMAGE_DIR RUN_DIR [GPU_LIST] [MAX_NEW_TOKENS]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
IMAGE_DIR="$5"
RUN_DIR="$6"
GPU_LIST="${7:-0 1 2 3 4 5 6 7}"
MAX_NEW_TOKENS="${8:-384}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards"
GIT_HASH="$(git rev-parse HEAD)"
IMAGE_HASH="$(find "${IMAGE_DIR}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
CONFIG_HASH="$(printf 'model=%s\nimage_hash=%s\nmax_new_tokens=%s\nprompt=question_blind_v1\n' "${MODEL_PATH}" "${IMAGE_HASH}" "${MAX_NEW_TOKENS}" | sha256sum | awk '{print $1}')"
cat > "${RUN_DIR}/run_manifest.json" <<JSON
{
  "job_type": "caption_image_store_generation",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${IMAGE_DIR}",
  "data_manifest_hash": "${IMAGE_HASH}",
  "model_path": "${MODEL_PATH}",
  "max_new_tokens": ${MAX_NEW_TOKENS},
  "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
  "command": "scripts/launch_caption_store_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${IMAGE_DIR} ${RUN_DIR}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS}
}
JSON

for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}_store_shard${SHARD_INDEX}.log"
  PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}_store_shard${SHARD_INDEX}.pid"
  OUT_PATH="${RUN_DIR}/shards/store_shard_${SHARD_INDEX}.jsonl"
  if [[ -s "${OUT_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=output_exists"
    continue
  fi
  ssh "${NODE}" "cd '${ROOT}' && (nohup env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} '${ROOT}/.venv/bin/python' scripts/caption_image_store.py --model-path '${MODEL_PATH}' --input-dir '${IMAGE_DIR}' --output '${OUT_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
done

nohup "${ROOT}/.venv/bin/python" scripts/finalize_sharded_run.py "${RUN_DIR}/run_manifest.json" --wait \
  > "${RUN_DIR}/logs/finalizer.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/finalizer.pid"
