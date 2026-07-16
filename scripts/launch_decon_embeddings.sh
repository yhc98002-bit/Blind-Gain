#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 8 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE GPU KIND MODEL TRAIN_RECORDS EVAL_RECORDS BATCH_SIZE RUN_TAG [DATA_LABEL]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
KIND="$3"
MODEL="$4"
TRAIN_RECORDS="$5"
EVAL_RECORDS="$6"
BATCH_SIZE="$7"
RUN_TAG="$8"
DATA_LABEL="${9:-Geometry3K train and available Layer-1 records}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${GPU}" =~ ^[0-7]$ || ! "${KIND}" =~ ^(image|text)$ || ! "${BATCH_SIZE}" =~ ^[1-9][0-9]*$ ]]; then
  echo "Invalid GPU, embedding kind, or batch size" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag" >&2
  exit 2
fi
for REQUIRED in "${TRAIN_RECORDS}" "${EVAL_RECORDS}"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing record file: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/embeddings.npz"
METADATA="${RUN_DIR}/metadata.json"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} .venv/bin/python scripts/extract_decon_embeddings.py --kind ${KIND} --model ${MODEL} --inputs ${TRAIN_RECORDS} ${EVAL_RECORDS} --output ${OUTPUT} --metadata-output ${METADATA} --batch-size ${BATCH_SIZE}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${TRAIN_RECORDS}" "${EVAL_RECORDS}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg kind "${KIND}" \
  --arg model "${MODEL}" \
  --arg data_label "${DATA_LABEL}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg metadata "${METADATA}" \
  '{
    run_id: $run_id,
    job_type: "p1_10_decon_embedding_extraction",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "Single-GPU feature extraction; the encoder fits on one GPU and no tensor parallelism is required.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_label,
    data_manifest_hash: $data_hash,
    embedding_kind: $kind,
    model_revision: $model,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $metadata]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
