#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 8 ]]; then
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

mkdir -p "${QA_RUN_DIR}/logs" "${QA_RUN_DIR}/pids" "${QA_RUN_DIR}/shards" "${QA_RUN_DIR}/metrics"
GIT_HASH="$(git rev-parse HEAD)"
CAPTION_HASH="$(find "${CAPTION_RUN_DIR}/shards" -type f -name 'captions_shard_*.jsonl' -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
CONFIG_HASH="$(printf 'model=%s\ncaption_hash=%s\nmax_new_tokens=%s\n' "${MODEL_PATH}" "${CAPTION_HASH}" "${MAX_NEW_TOKENS}" | sha256sum | awk '{print $1}')"
GPU_IDS_JSON="$(printf '%s\n' ${GPU_LIST} | jq -sc 'map(tonumber)')"
REPLICA_COUNT="$(wc -w <<< "${GPU_LIST}" | tr -d ' ')"
cat > "${QA_RUN_DIR}/run_manifest.json" <<JSON
{
  "run_id": "$(basename "${QA_RUN_DIR}")",
  "job_type": "fliptrack_v02_caption_only_qa",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "gpu_ids": ${GPU_IDS_JSON},
  "tensor_parallel_width": 1,
  "replica_count": ${REPLICA_COUNT},
  "placement_justification": "Independent TP1 replicas answer disjoint caption-only QA shards on one node; the model is at or below 7B.",
  "placement_policy_version": "pi-2026-07-11",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${CAPTION_RUN_DIR}/shards",
  "data_manifest_hash": "${CAPTION_HASH}",
  "model_path": "${MODEL_PATH}",
  "max_new_tokens": ${MAX_NEW_TOKENS},
  "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
  "command": "scripts/launch_caption_qa_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${CAPTION_RUN_DIR} ${QA_RUN_DIR} '${GPU_LIST}' ${MAX_NEW_TOKENS}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS},
  "expected_artifacts": ["${QA_RUN_DIR}/shards", "${QA_RUN_DIR}/metrics"]
}
JSON

LAUNCHED=0
for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -lt 0 || "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
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
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${QA_RUN_DIR}/logs' '${QA_RUN_DIR}/pids' '${QA_RUN_DIR}/shards' '${QA_RUN_DIR}/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} python scripts/eval_caption_qa_fliptrack.py --model-path '${MODEL_PATH}' --input '${INPUT_PATH}' --output '${OUT_PATH}' --metrics-output '${METRICS_PATH}' --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
  LAUNCHED=$((LAUNCHED + 1))
done

if [[ "${LAUNCHED}" -eq 0 ]]; then
  echo "No QA workers launched; check caption inputs and shard/GPU mapping" >&2
  python scripts/finalize_sharded_run.py "${QA_RUN_DIR}/run_manifest.json" --wait --timeout-seconds 0 || true
  exit 2
fi

scripts/launch_remote_sharded_finalizer.sh "${NODE}" "${QA_RUN_DIR}"
