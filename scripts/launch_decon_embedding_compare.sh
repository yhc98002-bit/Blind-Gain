#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 8 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE GPU BASELINE TRAIN_RECORDS EVAL_RECORDS IMAGE_EMBEDDINGS TEXT_EMBEDDINGS RUN_TAG [DATA_LABEL]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
BASELINE="$3"
TRAIN_RECORDS="$4"
EVAL_RECORDS="$5"
IMAGE_EMBEDDINGS="$6"
TEXT_EMBEDDINGS="$7"
RUN_TAG="$8"
DATA_LABEL="${9:-hash/text baseline plus DINOv2 and BGE embeddings}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${GPU}" =~ ^[0-7]$ || ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid GPU or run tag" >&2
  exit 2
fi
for REQUIRED in "${BASELINE}" "${TRAIN_RECORDS}" "${EVAL_RECORDS}" "${IMAGE_EMBEDDINGS}" "${TEXT_EMBEDDINGS}"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing comparison input: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_embedding_compare_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/comparison_v2.json"
COMMAND="CUDA_VISIBLE_DEVICES=${GPU} .venv/bin/python scripts/compare_decon_embeddings.py --baseline ${BASELINE} --train-records ${TRAIN_RECORDS} --eval-records ${EVAL_RECORDS} --image-embeddings ${IMAGE_EMBEDDINGS} --text-embeddings ${TEXT_EMBEDDINGS} --output ${OUTPUT}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${BASELINE}" "${TRAIN_RECORDS}" "${EVAL_RECORDS}" "${IMAGE_EMBEDDINGS}" "${TEXT_EMBEDDINGS}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg data_label "${DATA_LABEL}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  '{
    run_id: $run_id,
    job_type: "p1_10_decon_embedding_comparison",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "Single-GPU batched cosine comparison; no model serving or tensor parallelism is used.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_label,
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
