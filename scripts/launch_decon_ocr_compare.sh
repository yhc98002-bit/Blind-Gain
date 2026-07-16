#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 7 ]]; then
  echo "Usage: $0 NODE BASELINE TRAIN_RECORDS EVAL_RECORDS OCR_RUN_DIR RUN_TAG [DATA_LABEL]" >&2
  exit 2
fi

NODE="$1"
BASELINE="$2"
TRAIN_RECORDS="$3"
EVAL_RECORDS="$4"
OCR_RUN_DIR="$5"
RUN_TAG="$6"
DATA_LABEL="${7:-embedding comparison plus complete RapidOCR shards}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag: ${RUN_TAG}" >&2
  exit 2
fi
for REQUIRED in "${BASELINE}" "${TRAIN_RECORDS}" "${EVAL_RECORDS}" "${OCR_RUN_DIR}/run_manifest.json"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing OCR comparison input: ${REQUIRED}" >&2
    exit 2
  fi
done
mapfile -t OCR_SHARDS < <(find "${ROOT}/${OCR_RUN_DIR}/shards" -maxdepth 1 -type f -name 'shard_*.jsonl' | sort)
if [[ ${#OCR_SHARDS[@]} -eq 0 ]]; then
  echo "No OCR shards found under ${OCR_RUN_DIR}/shards" >&2
  exit 2
fi
if [[ "$(jq -r '.status' "${ROOT}/${OCR_RUN_DIR}/run_manifest.json")" != "complete" ]]; then
  echo "OCR extraction run is not complete: ${OCR_RUN_DIR}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_ocr_compare_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
OUTPUT="${RUN_DIR}/comparison_v4.json"
SHARD_ARGS="$(printf ' %q' "${OCR_SHARDS[@]#${ROOT}/}")"
COMMAND=".venv/bin/python scripts/compare_decon_ocr.py --baseline ${BASELINE} --train-records ${TRAIN_RECORDS} --eval-records ${EVAL_RECORDS} --ocr-shards${SHARD_ARGS} --output ${OUTPUT}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$({ sha256sum "${BASELINE}" "${TRAIN_RECORDS}" "${EVAL_RECORDS}"; sha256sum "${OCR_SHARDS[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg data_label "${DATA_LABEL}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg ocr_run "${OCR_RUN_DIR}" \
  --argjson shard_count "${#OCR_SHARDS[@]}" \
  '{
    run_id: $run_id,
    job_type: "l5_decon_ocr_comparison",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only deterministic OCR-signal merge; no GPU allocation or tensor parallelism is used.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_label,
    data_manifest_hash: $data_hash,
    ocr_extraction_run: $ocr_run,
    ocr_shard_count: $shard_count,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
