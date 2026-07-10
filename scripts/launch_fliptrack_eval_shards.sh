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

if [[ ! "${SHARD_OFFSET}" =~ ^-?[0-9]+$ || ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "SHARD_OFFSET must be an integer and NUM_SHARDS must be positive" >&2
  exit 2
fi
if [[ ! "${GPU_LIST}" =~ ^[0-7](\ [0-7])*$ ]]; then
  echo "GPU_LIST must be a space-separated list of GPU indices 0-7" >&2
  exit 2
fi
if [[ ! "${MAX_NEW_TOKENS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "MAX_NEW_TOKENS must be positive" >&2
  exit 2
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards" "${RUN_DIR}/metrics"
GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf 'model=%s\nmanifest=%s\nmode=%s\nmax_new_tokens=%s\n' "${MODEL_PATH}" "${MANIFEST}" "${IMAGE_MODE}" "${MAX_NEW_TOKENS}" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${MANIFEST}" | awk '{print $1}')"
cat > "${RUN_DIR}/run_manifest.json" <<JSON
{
  "job_type": "fliptrack_v02_image_evaluation",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${MANIFEST}",
  "data_manifest_hash": "${DATA_HASH}",
  "model_path": "${MODEL_PATH}",
  "image_mode": "${IMAGE_MODE}",
  "max_new_tokens": ${MAX_NEW_TOKENS},
  "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
  "command": "scripts/launch_fliptrack_eval_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${MANIFEST} ${RUN_DIR} ${MAX_NEW_TOKENS}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS}
}
JSON

LAUNCHED=0
for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -lt 0 || "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
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
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RUN_DIR}/shards' '${RUN_DIR}/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} python scripts/eval_qwen_vl_fliptrack.py --model-path '${MODEL_PATH}' --manifest '${MANIFEST}' --output '${OUT_PATH}' --metrics-output '${METRICS_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --image-mode '${IMAGE_MODE}' --image-cache-dir '${RUN_DIR}/${IMAGE_MODE}_image_cache' --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
  LAUNCHED=$((LAUNCHED + 1))
done

if [[ "${LAUNCHED}" -eq 0 ]]; then
  echo "No evaluation workers launched; check SHARD_OFFSET, NUM_SHARDS, and GPU_LIST" >&2
  python scripts/finalize_run_manifest.py "${RUN_DIR}/run_manifest.json" 2
  exit 2
fi

scripts/launch_remote_sharded_finalizer.sh "${NODE}" "${RUN_DIR}"
