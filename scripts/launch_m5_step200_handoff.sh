#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_RUN="experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z"
SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z"
NODE="an12"
CRITICAL=(
  scripts/execute_m5_step200_handoff.py
  scripts/launch_m5_step200_handoff.sh
  scripts/relocate_rederivable_tree.py
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked M5 handoff contract: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "M5 handoff contract differs from HEAD" >&2; exit 2; }
[[ -s "${SOURCE_MANIFEST}" ]] || { echo "M5 runtime manifest is absent" >&2; exit 2; }
jq -e '(.job_type=="m5_anchor_longhorizon_400") and (.status=="running") and
       (.node=="an12") and (.resumed_from_global_step==150) and
       (.target_global_step==400) and (.performance_values_opened==false)' \
  "${SOURCE_MANIFEST}" >/dev/null
if pgrep -af '[e]xecute_m5_step200_handoff.py'; then
  echo "another M5 step-200 handoff is active" >&2
  exit 73
fi
WRAPPER_PID="$(cat "${SOURCE_RUN}/pids/${NODE}.pid")"
ssh "${NODE}" "ps -p '${WRAPPER_PID}' -o args= | grep -F 'scripts/run_manifest_job.py' >/dev/null" || {
  echo "registered M5 wrapper is not alive" >&2; exit 3;
}

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_step200_handoff_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
RESULT="${RUN_DIR}/handoff_result.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/execute_m5_step200_handoff.py --run-dir ${RUN_DIR} --source-run ${SOURCE_RUN} --archive-root ${ARCHIVE_ROOT} --node ${NODE} --slope-threshold 2.0 --available-threshold-gib 350 --wait-seconds 300"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg data_hash "$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg result "${RESULT}" --arg source "${SOURCE_RUN}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m5_step200_boundary_handoff",node:"login",compute_node:"an12",
    gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only fail-closed controller interrupts only the exact registered M5 trainer after complete step-200 raw, merged, evaluation, and SHA256 evidence meets mechanical host-memory thresholds.",
    git_hash:$git_hash,config_path:"scripts/execute_m5_step200_handoff.py",config_hash:$config_hash,
    data_manifest:($source+"/run_manifest.json"),data_manifest_hash:$data_hash,seed:1,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,source_training_run:$source,handoff_step:200,
    slope_threshold_gib_per_step:2.0,available_threshold_gib:350,
    expected_artifacts:[$result],performance_values_opened:false,
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || { echo "M5 handoff exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
