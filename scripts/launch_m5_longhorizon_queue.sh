#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_longhorizon_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m5_longhorizon_queue.py --run-dir ${RUN_DIR} --poll-seconds 60"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum scripts/run_m5_longhorizon_queue.py scripts/launch_m5_anchor_longhorizon.sh configs/train/m5_anchor_longhorizon_400.yaml docs/registered_extensions_v1.md; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg state "${RUN_DIR}/queue_state.json" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_longhorizon_capacity_queue",
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"Login-only non-preemptive queue launches M5 on the first stable single-node four-GPU placement after restore integrity passes.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:"reports/m5_restore_resume_integrity.json",data_manifest_hash:null,
    seed:1,command:$command,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" >/dev/null 2>&1 </dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
