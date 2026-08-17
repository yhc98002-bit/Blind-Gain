#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 SMOKE_RUN_DIR AUDIT_JSON" >&2
  exit 2
fi

SMOKE_RUN="$1"
AUDIT_JSON="$2"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
if [[ ! "${SMOKE_RUN}" =~ ^experiments/runs/pilot_reward_smoke_[A-Za-z0-9._-]+$ ]]; then
  echo "Invalid pilot reward smoke run directory" >&2
  exit 2
fi
for path in "${SMOKE_RUN}/run_manifest.json" "${AUDIT_JSON}"; do
  if [[ ! -s "${path}" ]]; then
    echo "Pilot smoke cleanup prerequisite is absent: ${path}" >&2
    exit 2
  fi
done

CHECKSUM="${SMOKE_RUN}/checkpoint_retention_expired.sha256"
PREDELETE="${SMOKE_RUN}/checkpoint_predelete_record.json"
DELETION="${SMOKE_RUN}/checkpoint_deletion_record.json"
for path in "${CHECKSUM}" "${PREDELETE}" "${DELETION}"; do
  if [[ -e "${path}" ]]; then
    echo "Refusing to overwrite pilot smoke cleanup artifact: ${path}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_reward_smoke_checkpoint_cleanup_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="env PYTHONPATH=. .venv/bin/python scripts/cleanup_pilot_reward_smoke_checkpoint.py --run-manifest ${SMOKE_RUN}/run_manifest.json --audit ${AUDIT_JSON} --checksum-output ${CHECKSUM} --predelete-record ${PREDELETE} --deletion-record ${DELETION}"
DATA_HASH="$(sha256sum "${SMOKE_RUN}/run_manifest.json" "${AUDIT_JSON}" | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg smoke_manifest "${SMOKE_RUN}/run_manifest.json" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg checksum "${CHECKSUM}" \
  --arg predelete "${PREDELETE}" \
  --arg deletion "${DELETION}" \
  --arg log "${LOG}" \
  '{
    run_id: $run_id,
    job_type: "l3_pilot_reward_smoke_checkpoint_cleanup",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only hash verification and deletion of a retention-expired smoke checkpoint on shared storage.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $smoke_manifest,
    data_manifest_hash: $data_hash,
    seed: 1,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$checksum, $predelete, $deletion],
    stdout_stderr_log: $log,
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
