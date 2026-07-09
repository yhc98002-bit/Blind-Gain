#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 8 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH MANIFEST RUN_DIR GPU_LIST IMAGE_MODE [MAX_NEW_TOKENS]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
MANIFEST="$5"
RUN_DIR="$6"
GPU_LIST="$7"
IMAGE_MODE="$8"
MAX_NEW_TOKENS="${9:-32}"
ROOT="$(pwd)"
GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf 'model=%s\nmanifest=%s\nmode=%s\nmax_new_tokens=%s\n' "$MODEL_PATH" "$MANIFEST" "$IMAGE_MODE" "$MAX_NEW_TOKENS" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "$MANIFEST" | awk '{print $1}')"

mkdir -p "$RUN_DIR/logs" "$RUN_DIR/pids" "$RUN_DIR/shards" "$RUN_DIR/metrics"
cat > "$RUN_DIR/run_manifest.json" <<JSON
{
  "job_type": "fliptrack_v01_eval",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${MANIFEST}",
  "data_manifest_hash": "${DATA_HASH}",
  "image_mode": "${IMAGE_MODE}",
  "model_path": "${MODEL_PATH}",
  "command": "scripts/eval_qwen_vl_fliptrack.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} --num-shards ${NUM_SHARDS} --image-mode ${IMAGE_MODE}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "expected_artifact": "${RUN_DIR}/shards"
}
JSON

for gpu in ${GPU_LIST}; do
  shard_index=$((SHARD_OFFSET + gpu))
  out="${RUN_DIR}/shards/eval_${IMAGE_MODE}_shard_${shard_index}.jsonl"
  metrics="${RUN_DIR}/metrics/eval_${IMAGE_MODE}_shard_${shard_index}.json"
  log="${RUN_DIR}/logs/${NODE}_gpu${gpu}_${IMAGE_MODE}_shard${shard_index}.log"
  pid="${RUN_DIR}/pids/${NODE}_gpu${gpu}_${IMAGE_MODE}_shard${shard_index}.pid"
  ssh "$NODE" "cd '$ROOT' && mkdir -p '$RUN_DIR/logs' '$RUN_DIR/pids' '$RUN_DIR/shards' '$RUN_DIR/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES='$gpu' python scripts/eval_qwen_vl_fliptrack.py --model-path '$MODEL_PATH' --manifest '$MANIFEST' --output '$out' --metrics-output '$metrics' --num-shards '$NUM_SHARDS' --shard-index '$shard_index' --image-mode '$IMAGE_MODE' --image-cache-dir '$RUN_DIR/${IMAGE_MODE}_image_cache' --max-new-tokens '$MAX_NEW_TOKENS' > '$log' 2>&1 < /dev/null & echo \$! > '$pid')"
  echo "${NODE} gpu=${gpu} shard=${shard_index} log=${log}"
done
