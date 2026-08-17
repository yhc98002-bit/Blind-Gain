#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
M5_QUEUE="experiments/runs/m5_longhorizon_queue_login_20260716T164157Z/queue_state.json"
M5_INTEGRITY="experiments/runs/m5_integrity_queue_login_20260716T163532Z/queue_state.json"
[[ ! -e checkpoints/pilot/mech_a1_real_seed2 && ! -e checkpoints/pilot/mech_a2_gray_seed2 && ! -e checkpoints/pilot/mech_a2b_noimage_seed2 && ! -e checkpoints/pilot/mech_a3_caption_seed2 ]] || {
  echo "a seed-2 checkpoint namespace already exists" >&2; exit 73;
}
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed2_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_followup_queue.py --seed 2 --run-dir ${RUN_DIR} --m5-queue-state ${M5_QUEUE} --m5-integrity-state ${M5_INTEGRITY} --poll-seconds 60"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum docs/registered_pilot_seed23_v1.md configs/train/mech_*_seed2_3b_geo3k.yaml scripts/run_pilot_followup_queue.py scripts/launch_mech_pilot_followup_arm.sh; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg m5 "${M5_QUEUE}" --arg integrity "${M5_INTEGRITY}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg state "${RUN_DIR}/queue_state.json" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m3_seed2_training_capacity_queue",
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"Login-only non-preemptive scheduler waits for M5 placement, then runs at most one synchronous pilot trainer per node.",
    git_hash:$git_hash,config_path:"docs/registered_pilot_seed23_v1.md",config_hash:$config_hash,
    data_manifest:"data/geo3k_pilot_filtered.jsonl",data_manifest_hash:null,seed:2,command:$command,
    m5_priority_queue_state:$m5,m5_integrity_queue_state:$integrity,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" >/dev/null 2>&1 </dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
