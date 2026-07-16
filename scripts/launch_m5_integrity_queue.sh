#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 RESTORE_RUN_DIR" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESTORE_RUN="$1"
cd "${ROOT}"
[[ -f "${RESTORE_RUN}/run_manifest.json" ]] || {
  echo "restore run manifest is absent: ${RESTORE_RUN}" >&2
  exit 2
}
[[ ! -e reports/m5_restore_resume_integrity.json ]] || {
  echo "refusing to overwrite existing M5 integrity report" >&2
  exit 2
}

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_integrity_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=${ROOT} .venv/bin/python scripts/run_m5_integrity_queue.py --restore-run '${RESTORE_RUN}' --run-dir '${RUN_DIR}' --poll-seconds 60"
CONFIG_HASH="$({
  sha256sum configs/train/m5_anchor_resume_integrity_step101.yaml
  sha256sum configs/train/m5_anchor_longhorizon_400.yaml
  sha256sum reports/m5_restore_resume_plan_v1.md
} | sort -k2 | sha256sum | awk '{print $1}')"
RESTORE_HASH="$(sha256sum "${RESTORE_RUN}/run_manifest.json" | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg restore_run "${RESTORE_RUN}" \
  --arg restore_hash "${RESTORE_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${RUN_DIR}/queue_state.json" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m5_anchor_integrity_capacity_queue",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "Login-only queue observes an12/an29 and launches one single-node four-GPU integrity job after two stable free-capacity polls; it sends no process signals.",
    git_hash: $git_hash,
    config_path: "reports/m5_restore_resume_plan_v1.md",
    config_hash: $config_hash,
    data_manifest: ($restore_run + "/run_manifest.json"),
    data_manifest_hash: $restore_hash,
    seed: 1,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state, "reports/m5_restore_resume_integrity.json", "reports/m5_restore_resume_integrity.md"],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
