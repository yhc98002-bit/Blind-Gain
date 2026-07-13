#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 9 || $# -gt 11 ]]; then
  echo "usage: $0 <an12|an29> <gpu> <internvl3|gemma3> <model-path> <r19|r20> <manifest> <real|none|caption> <caption-input|-> <run-tag> [max-new-tokens] [limit|-]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
BACKEND="$3"
MODEL_PATH="$4"
DATASET_ID="$5"
DATA_MANIFEST="$6"
CONDITION="$7"
CAPTION_INPUT="$8"
RUN_TAG="$9"
MAX_NEW_TOKENS="${10:-384}"
LIMIT="${11:--}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${NODE}" =~ ^(an12|an29)$ ]]; then
  echo "node must be an12 or an29" >&2
  exit 2
fi
if [[ ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "gpu must be one index from 0 through 7" >&2
  exit 2
fi
if [[ ! "${BACKEND}" =~ ^(internvl3|gemma3)$ ]]; then
  echo "backend must be internvl3 or gemma3" >&2
  exit 2
fi
if [[ ! "${DATASET_ID}" =~ ^(r19|r20)$ ]]; then
  echo "dataset id must be r19 or r20" >&2
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
if [[ ! "${MAX_NEW_TOKENS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "max-new-tokens must be positive" >&2
  exit 2
fi
if [[ "${LIMIT}" != "-" && ! "${LIMIT}" =~ ^[1-9][0-9]*$ ]]; then
  echo "limit must be positive or -" >&2
  exit 2
fi

cd "${ROOT}"
if [[ ! -s "${DATA_MANIFEST}" ]]; then
  echo "nonempty FlipTrack manifest is required" >&2
  exit 2
fi
if [[ "${CONDITION}" == "caption" ]]; then
  if [[ "${CAPTION_INPUT}" == "-" || ! -s "${CAPTION_INPUT}" ]]; then
    echo "caption condition requires a nonempty fixed caption input" >&2
    exit 2
  fi
elif [[ "${CAPTION_INPUT}" != "-" ]]; then
  echo "caption input is only valid for caption condition" >&2
  exit 2
fi
if [[ ! "${MODEL_PATH}" =~ ^/dev/shm/blind-gains/models/[A-Za-z0-9._-]+$ ]]; then
  echo "model must be an ephemeral node-local checkout" >&2
  exit 2
fi
if ! ssh "${NODE}" "test -d '${MODEL_PATH}'"; then
  echo "model checkout is absent on ${NODE}: ${MODEL_PATH}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_${RUN_TAG}_${BACKEND}_${CONDITION}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/predictions.jsonl"
METRICS="${RUN_DIR}/metrics.json"
MANIFEST="${RUN_DIR}/run_manifest.json"
if [[ -e "${RUN_DIR}" ]]; then
  echo "refusing to overwrite immutable non-Qwen run: ${RUN_DIR}" >&2
  exit 73
fi

DATA_HASH="$(sha256sum "${DATA_MANIFEST}" | awk '{print $1}')"
CAPTION_HASH="-"
CAPTION_ARGS=""
if [[ "${CAPTION_INPUT}" != "-" ]]; then
  CAPTION_HASH="$(sha256sum "${CAPTION_INPUT}" | awk '{print $1}')"
  CAPTION_ARGS="--caption-input '${CAPTION_INPUT}'"
fi
CONFIG_HASH="$(printf 'backend=%s\nmodel=%s\ndataset=%s\ncondition=%s\nmax_new_tokens=%s\ncaption_hash=%s\nlimit=%s\n' "${BACKEND}" "${MODEL_PATH}" "${DATASET_ID}" "${CONDITION}" "${MAX_NEW_TOKENS}" "${CAPTION_HASH}" "${LIMIT}" | sha256sum | awk '{print $1}')"
LIMIT_ARGS=""
if [[ "${LIMIT}" != "-" ]]; then
  LIMIT_ARGS="--limit ${LIMIT}"
fi
COMMAND="env CUDA_VISIBLE_DEVICES=${GPU} TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/eval_nonqwen_fliptrack.py --backend '${BACKEND}' --model-path '${MODEL_PATH}' --dataset-id '${DATASET_ID}' --manifest '${DATA_MANIFEST}' --condition '${CONDITION}' ${CAPTION_ARGS} --output '${OUTPUT}' --metrics-output '${METRICS}' --max-new-tokens ${MAX_NEW_TOKENS} ${LIMIT_ARGS}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --argjson gpu "${GPU}" \
  --arg backend "${BACKEND}" \
  --arg model_path "${MODEL_PATH}" \
  --arg data_manifest "${DATA_MANIFEST}" \
  --arg dataset_id "${DATASET_ID}" \
  --arg data_hash "${DATA_HASH}" \
  --arg caption_input "${CAPTION_INPUT}" \
  --arg caption_hash "${CAPTION_HASH}" \
  --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg output "${OUTPUT}" \
  --arg metrics "${METRICS}" \
  --argjson max_new_tokens "${MAX_NEW_TOKENS}" \
  --arg limit "${LIMIT}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_nonqwen_fliptrack_evaluation",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "One model replica runs TP1 on one GPU of one node; no serving or inference state crosses nodes.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    dataset_id: $dataset_id,
    caption_input: (if $caption_input == "-" then null else $caption_input end),
    caption_input_hash: (if $caption_hash == "-" then null else $caption_hash end),
    model_backend: $backend,
    model_path: $model_path,
    model_revision: "ModelScope master; per-file stage manifest pinned in M11 V3",
    condition: $condition,
    max_new_tokens: $max_new_tokens,
    limit: (if $limit == "-" then null else ($limit | tonumber) end),
    decoding: {temperature: 0.0, top_p: 1.0, n: 1},
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output, $metrics],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
