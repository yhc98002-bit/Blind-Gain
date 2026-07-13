#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 9 ]]; then
  echo "usage: $0 <an12|an29> <gpu> <internvl3|gemma3> <model-path> <real|none|caption> <run-tag> [num-shards] [shard-index] [limit|-]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
BACKEND="$3"
MODEL_PATH="$4"
CONDITION="$5"
RUN_TAG="$6"
NUM_SHARDS="${7:-1}"
SHARD_INDEX="${8:-0}"
LIMIT="${9:--}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_PYTHON_REL="${BLIND_GAINS_NONQWEN_PYTHON:-.venv/bin/python}"
DATA_MANIFEST="data/virl39k_blind_sample_4096.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
CAPTION_RUN="experiments/runs/virl39k_sample4096_qwen25vl3b_captionstore384_20260710T094300Z"
MAX_NEW_TOKENS=2048

if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "invalid node or GPU" >&2
  exit 2
fi
if [[ ! "${BACKEND}" =~ ^(internvl3|gemma3)$ ]]; then
  echo "backend must be internvl3 or gemma3" >&2
  exit 2
fi
if [[ ! "${CONDITION}" =~ ^(real|none|caption)$ ]]; then
  echo "condition must be real, none, or caption" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "run tag contains unsafe characters" >&2
  exit 2
fi
if [[ ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ || ! "${SHARD_INDEX}" =~ ^[0-9]+$ ]] || (( SHARD_INDEX >= NUM_SHARDS )); then
  echo "invalid shard selection" >&2
  exit 2
fi
if [[ "${LIMIT}" != "-" && ! "${LIMIT}" =~ ^[1-9][0-9]*$ ]]; then
  echo "limit must be positive or -" >&2
  exit 2
fi
if [[ ! "${MODEL_PATH}" =~ ^/dev/shm/blind-gains/models/[A-Za-z0-9._-]+$ ]]; then
  echo "model must be an ephemeral node-local checkout" >&2
  exit 2
fi
if [[ ! "${RUNTIME_PYTHON_REL}" =~ ^\.venv(-m11)?/bin/python$ ]]; then
  echo "non-Qwen runtime must be a registered project virtual environment" >&2
  exit 2
fi

cd "${ROOT}"
RUNTIME_PYTHON="${ROOT}/${RUNTIME_PYTHON_REL}"
if [[ ! -x "${RUNTIME_PYTHON}" ]] || ! ssh "${NODE}" "test -x '${RUNTIME_PYTHON}'"; then
  echo "non-Qwen runtime is absent on ${NODE}: ${RUNTIME_PYTHON}" >&2
  exit 2
fi
if [[ ! -s "${DATA_MANIFEST}" || ! -s "${FORMAT_PROMPT}" ]]; then
  echo "frozen ViRL sample or format prompt is absent" >&2
  exit 2
fi
if ! ssh "${NODE}" "test -d '${MODEL_PATH}'"; then
  echo "model checkout is absent on ${NODE}: ${MODEL_PATH}" >&2
  exit 2
fi

CAPTION_ARGS=""
CAPTION_HASH="-"
DATA_FILES=("${DATA_MANIFEST}" "${FORMAT_PROMPT}")
if [[ "${CONDITION}" == "caption" ]]; then
  CAPTION_MANIFEST="${CAPTION_RUN}/run_manifest.json"
  if [[ ! -s "${CAPTION_MANIFEST}" ]] || ! jq -e \
    '(.status == "complete") and (.job_type == "caption_image_store_generation") and (.expected_shards > 0)' \
    "${CAPTION_MANIFEST}" >/dev/null; then
    echo "caption condition requires the completed frozen 3B store" >&2
    exit 2
  fi
  mapfile -t CAPTION_FILES < <(find "${CAPTION_RUN}/shards" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)
  if [[ "${#CAPTION_FILES[@]}" -ne "$(jq -r '.expected_shards' "${CAPTION_MANIFEST}")" ]]; then
    echo "fixed caption store has incomplete shards" >&2
    exit 2
  fi
  printf -v CAPTION_ARGS ' %q' "${CAPTION_FILES[@]}"
  CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"
  CAPTION_HASH="$(sha256sum "${CAPTION_FILES[@]}" | sha256sum | awk '{print $1}')"
  DATA_FILES+=("${CAPTION_MANIFEST}" "${CAPTION_FILES[@]}")
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_${RUN_TAG}_${BACKEND}_${CONDITION}_s${SHARD_INDEX}of${NUM_SHARDS}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
METRICS="${RUN_DIR}/metrics.json"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
LIMIT_ARGS=""
if [[ "${LIMIT}" != "-" ]]; then
  LIMIT_ARGS="--limit ${LIMIT}"
fi
EXPECTED_ROWS=$(( (4096 - SHARD_INDEX + NUM_SHARDS - 1) / NUM_SHARDS ))
if [[ "${LIMIT}" != "-" && "${LIMIT}" -lt "${EXPECTED_ROWS}" ]]; then
  EXPECTED_ROWS="${LIMIT}"
fi
COMMAND="env CUDA_VISIBLE_DEVICES=${GPU} TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONHASHSEED=0 PYTHONPATH=. '${RUNTIME_PYTHON}' scripts/eval_nonqwen_blind_sample.py --backend '${BACKEND}' --model-path '${MODEL_PATH}' --manifest '${DATA_MANIFEST}' --format-prompt '${FORMAT_PROMPT}' --condition '${CONDITION}' ${CAPTION_ARGS} --cache-dir '${CACHE_DIR}' --output '${OUTPUT}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --max-new-tokens ${MAX_NEW_TOKENS} ${LIMIT_ARGS} && PYTHONPATH=. '${RUNTIME_PYTHON}' scripts/aggregate_nonqwen_blind_sample.py --inputs '${OUTPUT}' --output '${METRICS}' --expected-rows ${EXPECTED_ROWS}"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${DATA_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
PROMPT_CONTRACT_JSON="$(PYTHONPATH=. .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"

if [[ -e "${RUN_DIR}" ]]; then
  echo "refusing to overwrite immutable non-Qwen blind run" >&2
  exit 73
fi
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --argjson gpu "${GPU}" \
  --arg backend "${BACKEND}" --arg model "${MODEL_PATH}" \
  --arg condition "${CONDITION}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg runtime_python "${RUNTIME_PYTHON}" \
  --arg data_manifest "${DATA_MANIFEST}" --arg caption_run "${CAPTION_RUN}" \
  --arg caption_hash "${CAPTION_HASH}" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg output "${OUTPUT}" --arg cache_dir "${CACHE_DIR}" \
  --arg metrics "${METRICS}" \
  --argjson num_shards "${NUM_SHARDS}" --argjson shard_index "${SHARD_INDEX}" \
  --arg limit "${LIMIT}" --argjson max_new_tokens "${MAX_NEW_TOKENS}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" \
  --arg prompt_hash "${PROMPT_CONTRACT_HASH}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_nonqwen_blind_sample_evaluation",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "One non-Qwen model runs TP1 on one GPU of one node; no inference state crosses nodes.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    runtime_python: $runtime_python,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    model_backend: $backend,
    model_path: $model,
    model_revision: "ModelScope master; per-file stage manifest pinned in M11 V3",
    condition: $condition,
    caption_source_run: (if $condition == "caption" then $caption_run else null end),
    caption_store_sha256: (if $caption_hash == "-" then null else $caption_hash end),
    num_shards: $num_shards,
    shard_index: $shard_index,
    limit: (if $limit == "-" then null else ($limit | tonumber) end),
    max_new_tokens: $max_new_tokens,
    prompt_contract: $prompt_contract,
    prompt_contract_sha256: $prompt_hash,
    decoding: {temperature: 0.0, top_p: 1.0, n: 1},
    local_condition_cache: $cache_dir,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output, $metrics],
    deviations: []
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
