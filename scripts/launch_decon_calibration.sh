#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 NODE GPU RECORDS RUN_TAG" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
RECORDS="$3"
RUN_TAG="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${GPU}" =~ ^[0-7]$ || ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid GPU or run tag" >&2
  exit 2
fi
if [[ ! -f "${ROOT}/${RECORDS}" ]]; then
  echo "Missing calibration records: ${RECORDS}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_calibration_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/calibration.json"
TRANSFORMS="${RUN_DIR}/transforms"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} .venv/bin/python scripts/calibrate_decon.py --records ${RECORDS} --output ${OUTPUT} --transform-dir ${TRANSFORMS} --dino-model facebook/dinov2-small --text-model artifacts/models/BAAI/bge-small-en-v1.5 --sample-size 64 --seed 20260710"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "${RECORDS}" \
  --arg data_hash "$(sha256sum "${RECORDS}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg transforms "${TRANSFORMS}" \
  '{
    run_id: $run_id,
    job_type: "p1_10_decon_calibration",
    node: $node,
    gpu_allocation: [$gpu],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    model_revision: "facebook/dinov2-small plus BAAI/bge-small-en-v1.5",
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $transforms]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
