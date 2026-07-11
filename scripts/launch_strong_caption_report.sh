#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 8 ]]; then
  echo "Usage: $0 R19_BASELINE R20_BASELINE R19_STRONG R20_STRONG DOWNLOAD_MANIFEST CHECKOUT_MANIFEST CAPTION_MANIFEST DELETION_RECORD" >&2
  exit 2
fi

R19_BASELINE="$1"
R20_BASELINE="$2"
R19_STRONG="$3"
R20_STRONG="$4"
DOWNLOAD_MANIFEST="$5"
CHECKOUT_MANIFEST="$6"
CAPTION_MANIFEST="$7"
DELETION_RECORD="$8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT="reports/strong_caption_stress.md"
MACHINE="reports/strong_caption_stress.json"

cd "${ROOT}"
INPUTS=(
  "${R19_BASELINE}"
  "${R20_BASELINE}"
  "${R19_STRONG}"
  "${R20_STRONG}"
  "${DOWNLOAD_MANIFEST}"
  "${CHECKOUT_MANIFEST}"
  "${CAPTION_MANIFEST}"
  "${DELETION_RECORD}"
)
for path in "${INPUTS[@]}"; do
  if [[ ! -s "${path}" ]]; then
    echo "Strong-caption report input is absent: ${path}" >&2
    exit 2
  fi
done
if [[ -e "${REPORT}" || -e "${MACHINE}" ]]; then
  echo "Refusing to overwrite strong-caption reports" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="strong_caption_report_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/build_strong_caption_stress_report.py --r19-baseline ${R19_BASELINE} --r20-baseline ${R20_BASELINE} --r19-strong ${R19_STRONG} --r20-strong ${R20_STRONG} --download-manifest ${DOWNLOAD_MANIFEST} --checkout-manifest ${CHECKOUT_MANIFEST} --caption-manifest ${CAPTION_MANIFEST} --deletion-record ${DELETION_RECORD} --output ${REPORT} --machine-output ${MACHINE}"
DATA_HASH="$(sha256sum "${INPUTS[@]}" | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg data_manifest "${CAPTION_MANIFEST}" \
  --arg command "${COMMAND}" \
  --arg report "${REPORT}" \
  --arg machine "${MACHINE}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    run_id: $run_id,
    job_type: "l9_strong_caption_report",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only deterministic aggregation after TP4 captioning, TP1 QA, and ephemeral-weight deletion.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
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
