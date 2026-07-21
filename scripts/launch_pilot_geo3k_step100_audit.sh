#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 EVALUATION_RUN_DIR" >&2
  exit 2
fi

EVALUATION_RUN="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_MANIFEST="${EVALUATION_RUN}/run_manifest.json"
if [[ ! -s "${SOURCE_MANIFEST}" ]]; then
  echo "evaluation manifest is absent: ${SOURCE_MANIFEST}" >&2
  exit 2
fi
if ! jq -e \
  '(.job_type == "m2_pilot_geo3k_step100_eval" or
    .job_type == "m3_pilot_geo3k_checkpoint_eval") and
   (.status == "complete") and (.exit_code == 0) and (.artifacts_exist == true)' \
  "${SOURCE_MANIFEST}" >/dev/null; then
  echo "evaluation run is not structurally complete" >&2
  exit 3
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SOURCE_RUN_ID="$(jq -r '.run_id' "${SOURCE_MANIFEST}")"
SOURCE_JOB_TYPE="$(jq -r '.job_type' "${SOURCE_MANIFEST}")"
if [[ "${SOURCE_JOB_TYPE}" == "m3_pilot_geo3k_checkpoint_eval" ]]; then
  AUDIT_JOB_TYPE="m3_pilot_geo3k_checkpoint_audit"
  RUN_ID="pilot_followup_geo3k_audit_${SOURCE_RUN_ID}_${STAMP}"
else
  AUDIT_JOB_TYPE="m2_pilot_geo3k_step100_audit"
  RUN_ID="pilot_geo3k_step100_audit_${SOURCE_RUN_ID}_${STAMP}"
fi
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
OUTPUT="${RUN_DIR}/audit.json"
COMMAND="PYTHONPATH=${ROOT}:${ROOT}/artifacts/repos/EasyR1 .venv/bin/python scripts/audit_pilot_geo3k_step100_eval.py --run-dir ${EVALUATION_RUN} --output ${OUTPUT}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg job_type "${AUDIT_JOB_TYPE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "$(sha256sum "${SOURCE_MANIFEST}" "$(jq -r '.expected_artifacts[0]' "${SOURCE_MANIFEST}")" | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg source_run "${EVALUATION_RUN}" \
  --arg source_manifest_sha256 "$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg log "${LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: $job_type,
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only row-identity, provenance, strict-accounting, and full score-recomputation audit; no GPU is allocated.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: $data_hash,
    source_evaluation_run: $source_run,
    source_evaluation_manifest_sha256: $source_manifest_sha256,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output],
    deviations: [],
    scientific_gate_decision: null
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
