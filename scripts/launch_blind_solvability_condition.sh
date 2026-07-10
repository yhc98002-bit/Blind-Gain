#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 NODE GPU CONDITION MODEL_PATH RUN_TAG" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
CONDITION="$3"
MODEL_PATH="$4"
RUN_TAG="$5"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
CAPTION_RUN="experiments/runs/geometry3k_qwen25vl3b_captionstore384_20260710T005300Z"

if [[ ! "${GPU}" =~ ^[0-7]$ || ! "${CONDITION}" =~ ^(real|gray|noise|none|caption)$ ]]; then
  echo "Invalid GPU or condition" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="blind_solvability_${RUN_TAG}_${CONDITION}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_ROOT="${BLIND_GAINS_CACHE_ROOT:-/dev/shm/blind-gains}"
CACHE_DIR="${CACHE_ROOT}/${RUN_ID}/condition_cache"
CAPTION_ARGS=""
DATA_FILES=("${MANIFEST}" "${FORMAT_PROMPT}")
if [[ "${CONDITION}" == "caption" ]]; then
  CAPTION_ARGS="--caption-shards ${CAPTION_RUN}/shards/store_shard_0.jsonl ${CAPTION_RUN}/shards/store_shard_1.jsonl ${CAPTION_RUN}/shards/store_shard_2.jsonl"
  DATA_FILES+=("${CAPTION_RUN}/shards/store_shard_0.jsonl" "${CAPTION_RUN}/shards/store_shard_1.jsonl" "${CAPTION_RUN}/shards/store_shard_2.jsonl")
fi
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 .venv/bin/python scripts/run_blind_solvability.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} --format-prompt ${FORMAT_PROMPT} --condition ${CONDITION} --output ${OUTPUT} --cache-dir ${CACHE_DIR} ${CAPTION_ARGS} --splits train test --batch-size 8 --max-tokens 512 --group-size 5 --sample-count 16 --sample-temperature 1.0 --seed 20260710"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${DATA_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg model "${MODEL_PATH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg cache_dir "${CACHE_DIR}" \
  '{
    run_id: $run_id,
    job_type: "p2_2_geometry3k_blind_solvability",
    node: $node,
    gpu_allocation: [$gpu],
    condition: $condition,
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "Geometry3K train+test; fixed 3B caption store for caption condition",
    data_manifest_hash: $data_hash,
    model_revision: $model,
    inference_engine: "vllm==0.7.3",
    group_size: 5,
    sample_count: 16,
    sample_temperature: 1.0,
    local_condition_cache: $cache_dir,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
