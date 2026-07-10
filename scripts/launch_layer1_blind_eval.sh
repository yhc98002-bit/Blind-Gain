#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 NODE GPU CONFIG RUN_TAG" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
CONFIG="$3"
RUN_TAG="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "GPU must be an index from 0 through 7" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ ! -f "${ROOT}/${CONFIG}" ]]; then
  echo "Missing config: ${CONFIG}" >&2
  exit 2
fi

INPUT_TSV="$(jq -r '.input_tsv' "${ROOT}/${CONFIG}")"
MODEL_PATH="$(jq -r '.model_path' "${ROOT}/${CONFIG}")"
SEED="$(jq -r '.seed' "${ROOT}/${CONFIG}")"
if [[ ! -f "${ROOT}/${INPUT_TSV}" || ! -d "${ROOT}/${MODEL_PATH}" ]]; then
  echo "Blind evaluation input or model path is missing" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="layer1_blind_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/predictions.jsonl"
METRICS="${RUN_DIR}/metrics.json"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} artifacts/envs/vlmevalkit/bin/python scripts/eval_layer1_blind.py --config ${CONFIG} --output ${OUTPUT} --metrics-output ${METRICS}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG}" \
  --arg config_hash "$(sha256sum "${CONFIG}" | awk '{print $1}')" \
  --arg data_manifest "${INPUT_TSV}" \
  --arg data_hash "$(sha256sum "${INPUT_TSV}" | awk '{print $1}')" \
  --arg model_path "${MODEL_PATH}" \
  --arg seed "${SEED}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg metrics "${METRICS}" \
  '{
    run_id: $run_id,
    job_type: "p1_2_layer1_image_removed_evaluation",
    node: $node,
    gpu_allocation: [$gpu],
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    model_path: $model_path,
    seed: ($seed | tonumber),
    image_protocol: "remove image message, image token, and image tensor; retain question text and options verbatim",
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $metrics]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
