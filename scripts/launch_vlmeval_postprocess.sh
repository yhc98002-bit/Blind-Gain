#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 INPUT_WORKBOOK SOURCE_RUN_DIR RUN_TAG [embedded|legacy-config]" >&2
  exit 2
fi

INPUT="$1"
SOURCE_RUN_DIR="$2"
RUN_TAG="$3"
CONTRACT_MODE="${4:-embedded}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ "${CONTRACT_MODE}" != "embedded" && "${CONTRACT_MODE}" != "legacy-config" ]]; then
  echo "Contract mode must be embedded or legacy-config" >&2
  exit 2
fi
for REQUIRED in "${INPUT}" "${SOURCE_RUN_DIR}/run_manifest.json"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing required input: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="vlmevalkit_postprocess_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
ROWS="${RUN_DIR}/rows.jsonl"
METRICS="${RUN_DIR}/metrics.json"
LEGACY_FLAG=""
if [[ "${CONTRACT_MODE}" == "legacy-config" ]]; then
  LEGACY_FLAG="--allow-legacy-config-contract"
fi
COMMAND="artifacts/envs/vlmevalkit/bin/python scripts/postprocess_vlmeval_predictions.py --input ${INPUT} --rows-output ${ROWS} --metrics-output ${METRICS} --run-manifest ${SOURCE_RUN_DIR}/run_manifest.json ${LEGACY_FLAG}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg input "${INPUT}" \
  --arg input_hash "$(sha256sum "${INPUT}" | awk '{print $1}')" \
  --arg source_run "${SOURCE_RUN_DIR}" \
  --arg contract_mode "${CONTRACT_MODE}" \
  --arg command "${COMMAND}" \
  --arg command_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg rows "${ROWS}" \
  --arg metrics "${METRICS}" \
  '{
    run_id: $run_id,
    job_type: "p1_2_vlmevalkit_unified_postprocess",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $command_hash,
    data_manifest: $input,
    data_manifest_hash: $input_hash,
    source_run: $source_run,
    prompt_contract_resolution: $contract_mode,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$rows, $metrics]
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
