#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 METADATA METRIC_3B_REAL METRIC_7B_REAL METRIC_7B_CAPTION" >&2
  exit 2
fi

METADATA="$1"
METRIC_3B_REAL="$2"
METRIC_7B_REAL="$3"
METRIC_7B_CAPTION="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT="reports/document_v_next_calibration.md"
MACHINE="reports/document_v_next_calibration.json"

cd "${ROOT}"
for path in "${METADATA}" "${METRIC_3B_REAL}" "${METRIC_7B_REAL}" "${METRIC_7B_CAPTION}"; do
  if [[ ! -s "${path}" ]]; then
    echo "L11 report input is absent: ${path}" >&2
    exit 2
  fi
done
if [[ -e "${REPORT}" || -e "${MACHINE}" ]]; then
  echo "Refusing to overwrite L11 reports" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="document_vnext_report_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/build_document_vnext_report.py --metadata ${METADATA} --metric qwen25vl3b_real=${METRIC_3B_REAL} --metric qwen25vl7b_real=${METRIC_7B_REAL} --metric qwen25vl7b_caption=${METRIC_7B_CAPTION} --output ${REPORT} --machine-output ${MACHINE}"

mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$(sha256sum "${METADATA}" "${METRIC_3B_REAL}" "${METRIC_7B_REAL}" "${METRIC_7B_CAPTION}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg metadata "${METADATA}" \
  --arg command "${COMMAND}" \
  --arg report "${REPORT}" \
  --arg machine "${MACHINE}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    run_id: $run_id,
    job_type: "l11_document_vnext_report",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only deterministic aggregation of the three frozen L11 cells; no model serving or GPU allocation.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $metadata,
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$report, $machine],
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
