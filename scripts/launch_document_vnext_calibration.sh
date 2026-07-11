#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/data/fliptrack_document_vnext_calibration_v1.json"
OUTPUT="data/fliptrack_document_vnext_calibration_manifest.jsonl"
METADATA="data/fliptrack_document_vnext_calibration.json"
SOURCE_DIR="data/fliptrack_document_vnext_calibration_source"
CONTACTS="reports/contact_sheets/fliptrack_document_vnext_calibration"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="document_vnext_calibration_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python -m src.fliptrack.build_document_vnext --config ${CONFIG} --out-dir ${SOURCE_DIR} --manifest ${OUTPUT} --contact-sheet-dir ${CONTACTS} --metadata ${METADATA}"

cd "${ROOT}"
"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/data" \
  --operation document_vnext_calibration_generation \
  --required-bytes 2147483648 \
  --log "${ROOT}/logs/storage_guard.jsonl"
mkdir -p "${RUN_DIR}/logs"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
DATA_HASH="$({ sha256sum "${CONFIG}" src/fliptrack/build_document_vnext.py src/fliptrack/build_v02.py src/fliptrack/schema.py src/eval/fliptrack_metrics.py; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${CONFIG}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg metadata "${METADATA}" \
  --arg contacts "${CONTACTS}" \
  '{
    run_id: $run_id,
    job_type: "l11_document_vnext_one_shot_generation",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: $config,
    data_manifest_hash: $data_hash,
    seed: 20261101,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $metadata, $contacts],
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
