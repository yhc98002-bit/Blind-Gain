#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 7 || $# -gt 11 ]]; then
  echo "Usage: $0 NODE GPU CONDITION MODEL_PATH MANIFEST SPLIT RUN_TAG [CAPTION_RUN|-] [BATCH_SIZE] [MAX_MODEL_LEN] [RESUME_FROM|-]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
CONDITION="$3"
MODEL_PATH="$4"
MANIFEST="$5"
SPLIT="$6"
RUN_TAG="$7"
CAPTION_RUN="${8:--}"
BATCH_SIZE="${9:-4}"
MAX_MODEL_LEN="${10:-8192}"
RESUME_FROM="${11:--}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"

if [[ ! "${GPU}" =~ ^[0-7]$ || ! "${CONDITION}" =~ ^(real|gray|noise|none|caption)$ ]]; then
  echo "Invalid GPU or condition" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ || ! "${SPLIT}" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "Invalid run tag or split" >&2
  exit 2
fi
if [[ ! "${BATCH_SIZE}" =~ ^[1-9][0-9]*$ || ! "${MAX_MODEL_LEN}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BATCH_SIZE and MAX_MODEL_LEN must be positive" >&2
  exit 2
fi

cd "${ROOT}"
if [[ ! -s "${MANIFEST}" || ! -s "${FORMAT_PROMPT}" ]]; then
  echo "Manifest or format prompt is missing" >&2
  exit 2
fi

CAPTION_ARGS=""
DATA_FILES=("${MANIFEST}" "${FORMAT_PROMPT}")
if [[ "${CONDITION}" == "caption" ]]; then
  if [[ "${CAPTION_RUN}" == "-" || ! -d "${CAPTION_RUN}/shards" ]]; then
    echo "Caption condition requires a completed caption run directory" >&2
    exit 2
  fi
  mapfile -t CAPTION_FILES < <(find "${CAPTION_RUN}/shards" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)
  if [[ "${#CAPTION_FILES[@]}" -eq 0 ]]; then
    echo "Caption run has no completed store shards" >&2
    exit 2
  fi
  printf -v CAPTION_ARGS ' %q' "${CAPTION_FILES[@]}"
  CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"
  DATA_FILES+=("${CAPTION_FILES[@]}")
fi

RESUME_ARGS=""
if [[ "${RESUME_FROM}" != "-" ]]; then
  if [[ ! -s "${RESUME_FROM}" ]]; then
    echo "Resume source is missing or empty: ${RESUME_FROM}" >&2
    exit 2
  fi
  RESUME_MANIFEST="$(dirname "${RESUME_FROM}")/run_manifest.json"
  if [[ ! -s "${RESUME_MANIFEST}" ]]; then
    echo "Resume source run manifest is missing: ${RESUME_MANIFEST}" >&2
    exit 2
  fi
  if ! jq -e \
    --arg condition "${CONDITION}" \
    --arg model "${MODEL_PATH}" \
    --arg manifest "${MANIFEST}" \
    --arg split "${SPLIT}" \
    --argjson batch_size "${BATCH_SIZE}" \
    --argjson max_model_len "${MAX_MODEL_LEN}" \
    '(.condition == $condition) and
     (.model_revision == $model) and
     (.data_manifest == $manifest) and
     (.split == $split) and
     (.batch_size == $batch_size) and
     (.max_model_len == $max_model_len) and
     (.group_size == 5) and
     (.sample_count == 16) and
     (.sample_temperature == 1)' "${RESUME_MANIFEST}" >/dev/null; then
    echo "Resume source run contract does not match the requested run" >&2
    exit 2
  fi
  printf -v RESUME_ARGS ' --resume-from %q' "${RESUME_FROM}"
  DATA_FILES+=("${RESUME_FROM}" "${RESUME_MANIFEST}")
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
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 .venv/bin/python scripts/run_blind_solvability.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} --format-prompt ${FORMAT_PROMPT} --condition ${CONDITION} --output ${OUTPUT} --cache-dir ${CACHE_DIR} ${CAPTION_ARGS}${RESUME_ARGS} --splits ${SPLIT} --batch-size ${BATCH_SIZE} --max-tokens 512 --max-model-len ${MAX_MODEL_LEN} --group-size 5 --sample-count 16 --sample-temperature 1.0 --seed 20260710"

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
  --arg manifest "${MANIFEST}" \
  --arg split "${SPLIT}" \
  --arg model "${MODEL_PATH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg cache_dir "${CACHE_DIR}" \
  --arg resume_from "${RESUME_FROM}" \
  --argjson batch_size "${BATCH_SIZE}" \
  --argjson max_model_len "${MAX_MODEL_LEN}" \
  '{
    run_id: $run_id,
    job_type: "p2_2_manifest_blind_solvability",
    node: $node,
    gpu_allocation: [$gpu],
    condition: $condition,
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $manifest,
    data_manifest_hash: $data_hash,
    split: $split,
    model_revision: $model,
    inference_engine: "vllm==0.7.3",
    group_size: 5,
    sample_count: 16,
    sample_temperature: 1.0,
    batch_size: $batch_size,
    max_model_len: $max_model_len,
    local_condition_cache: $cache_dir,
    resume_from: (if $resume_from == "-" then null else $resume_from end),
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
