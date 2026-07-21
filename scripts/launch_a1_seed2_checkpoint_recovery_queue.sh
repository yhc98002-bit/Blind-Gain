#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
A3_RUN="experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z"
A1_RUN="experiments/runs/mech_a1_real_seed2_an29_20260716T164827Z"
FAILED_WATCHER="experiments/runs/pilot_checkpoint_watch_mech_a1_real_seed2_login_20260716T164920Z"
CRITICAL=(
  scripts/run_a1_seed2_checkpoint_recovery_queue.py
  scripts/launch_a1_seed2_checkpoint_recovery_queue.sh
  scripts/watch_pilot_completed_parent_checkpoints.py
  scripts/launch_pilot_completed_checkpoint_recovery.sh
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked A1 recovery queue file: ${FILE}" >&2; exit 3; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "A1 recovery queue code differs from HEAD" >&2; exit 3; }
for PATH_VALUE in "${A3_RUN}/run_manifest.json" "${A1_RUN}/run_manifest.json" "${FAILED_WATCHER}/run_manifest.json"; do
  [[ -s "${PATH_VALUE}" ]] || { echo "A1 recovery queue input absent: ${PATH_VALUE}" >&2; exit 2; }
done
if pgrep -af '[r]un_a1_seed2_checkpoint_recovery_queue.py'; then
  echo "A1 recovery queue already active" >&2; exit 73
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="a1_seed2_checkpoint_recovery_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_a1_seed2_checkpoint_recovery_queue.py --run-dir '${RUN_DIR}' --a3-run '${A3_RUN}' --a1-run '${A1_RUN}' --failed-watcher-run '${FAILED_WATCHER}' --poll-seconds 60"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg data_hash "$({ sha256sum "${A3_RUN}/run_manifest.json" "${A1_RUN}/run_manifest.json" "${FAILED_WATCHER}/run_manifest.json"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg state "${STATE}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"a1_seed2_checkpoint_recovery_queue",
    node:"login",gpu_ids:[],gpu_allocation:[],tensor_parallel_width:0,replica_count:0,
    placement_policy_version:"pi-2026-07-11",placement_justification:"GPU-inert queue waits for A3 step-100 checkpoint finalization and an29 trainer release before A1 checkpoint-only recovery.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:"A3 completion + A1 parent + failed watcher",data_manifest_hash:$data_hash,
    seed:2,command:$command,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || { echo "A1 recovery queue exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
