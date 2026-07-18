#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
RESTORE_RUN="experiments/runs/m5_step150_raw_restore_login_20260718T015846Z"
A1_RUN="experiments/runs/mech_a1_real_seed2_an29_20260716T164827Z"
SEED_QUEUE_RUN="experiments/runs/pilot_seed2_queue_login_20260716T164718Z"
HOLD="${SEED_QUEUE_RUN}/m5_recovery_operational_hold.json"
for path in "${RESTORE_RUN}/run_manifest.json" "${A1_RUN}/run_manifest.json" "${HOLD}"; do
  [[ -f "${path}" ]] || { echo "M5 recovery queue input absent: ${path}" >&2; exit 2; }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_recovery_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m5_recovery_queue.py --run-dir '${RUN_DIR}' --restore-run '${RESTORE_RUN}' --a1-run '${A1_RUN}' --seed-queue-hold '${HOLD}' --node an29 --gpu-ids 2,5,6,7 --poll-seconds 120"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum scripts/run_m5_recovery_queue.py scripts/launch_m5_recovery_queue.sh scripts/launch_m5_anchor_recovery150.sh; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg data_hash "$({ sha256sum "${RESTORE_RUN}/run_manifest.json" "${A1_RUN}/run_manifest.json" "${HOLD}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg restore "${RESTORE_RUN}" --arg a1 "${A1_RUN}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_step150_recovery_capacity_queue",
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only watcher waits for the hash-verified restore, A1 release, two stable capacity polls, and 650-GiB host-memory admission before single-node M5 launch.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:($restore+"|"+$a1),data_manifest_hash:$data_hash,
    seed:1,command:$command,start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,expected_artifacts:[$state],performance_values_opened:false,
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
