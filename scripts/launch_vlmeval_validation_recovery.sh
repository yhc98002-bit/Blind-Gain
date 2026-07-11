#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 CONFIG WORK_DIR SOURCE_RUN_DIR RUN_TAG" >&2
  exit 2
fi

CONFIG="$1"
WORK_DIR="$2"
SOURCE_RUN_DIR="$3"
RUN_TAG="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
for REQUIRED in "${CONFIG}" "${WORK_DIR}" "${SOURCE_RUN_DIR}/run_manifest.json"; do
  if [[ ! -e "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing required input: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="vlmevalkit_validation_recovery_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/validation.json"
SOURCE_MODE="$(jq -r '.mode // empty' "${SOURCE_RUN_DIR}/run_manifest.json")"
if [[ "${SOURCE_MODE}" == "infer" ]]; then
  SCORE_ARGS="--allow-missing-scores"
elif [[ "${SOURCE_MODE}" == "all" ]]; then
  SCORE_ARGS=""
else
  echo "Source run manifest has unsupported or missing mode: ${SOURCE_MODE}" >&2
  exit 2
fi
COMMAND=".venv/bin/python scripts/validate_vlmeval_run.py --config ${CONFIG} --work-dir ${WORK_DIR} --output ${OUTPUT} ${SCORE_ARGS}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
SOURCE_HASH="$(sha256sum "${SOURCE_RUN_DIR}/run_manifest.json" | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG}" \
  --arg config_hash "$(sha256sum "${CONFIG}" | awk '{print $1}')" \
  --arg source_run "${SOURCE_RUN_DIR}" \
  --arg source_hash "${SOURCE_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  '{
    run_id: $run_id,
    job_type: "p1_2_vlmevalkit_validation_recovery",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only validation recovery over an immutable VLMEvalKit inference directory.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    data_manifest: ($source_run + "/run_manifest.json"),
    data_manifest_hash: $source_hash,
    source_run: $source_run,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
