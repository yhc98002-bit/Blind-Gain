#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <seed3-a2-training-run> <seed3-a2-watcher-run> <m5-step200-source-run> <m5-step200-handoff-run>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
A2_TRAINING="${1%/}"
A2_WATCHER="${2%/}"
M5_SOURCE="${3%/}"
M5_HANDOFF="${4%/}"

for REQUIRED in \
  "${A2_TRAINING}/run_manifest.json" \
  "${A2_WATCHER}/run_manifest.json" \
  "${M5_SOURCE}/run_manifest.json" \
  "${M5_HANDOFF}/run_manifest.json" \
  "${M5_HANDOFF}/handoff_result.json"; do
  [[ -s "${REQUIRED}" ]] || { echo "M5 lifecycle input is absent: ${REQUIRED}" >&2; exit 2; }
done

if pgrep -af '[r]un_m5_after_seed3_a2_queue.py'; then
  echo "refusing a duplicate active M5-after-A2 lifecycle queue" >&2
  exit 73
fi

mapfile -t CONTRACT_PATHS < <(
  PYTHONPATH=. .venv/bin/python -c \
    'from scripts.run_m5_after_seed3_a2_queue import CONTRACT_PATHS; print("\n".join(CONTRACT_PATHS))'
)
[[ "${#CONTRACT_PATHS[@]}" -gt 0 ]] || { echo "empty M5 queue contract" >&2; exit 3; }
for FILE in "${CONTRACT_PATHS[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked M5 lifecycle contract: ${FILE}" >&2
    exit 3
  }
done
git diff --quiet HEAD -- "${CONTRACT_PATHS[@]}" || {
  echo "M5 lifecycle contract differs from HEAD" >&2
  exit 3
}
CONTRACT_HASH="$(PYTHONPATH=. .venv/bin/python -c \
  'from scripts.run_m5_after_seed3_a2_queue import contract_hash; print(contract_hash())')"

PYTHONPATH=. .venv/bin/python - "${A2_TRAINING}" "${A2_WATCHER}" "${M5_SOURCE}" "${M5_HANDOFF}" <<'PY'
import sys
from scripts.run_m5_after_seed3_a2_queue import validate_a2_identity, validate_initial_m5

validate_a2_identity(sys.argv[1], sys.argv[2])
validate_initial_m5(sys.argv[3], sys.argv[4])
PY

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_after_seed3_a2_lifecycle_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m5_after_seed3_a2_queue.py --run-dir ${RUN_DIR} --a2-training-run ${A2_TRAINING} --a2-watcher-run ${A2_WATCHER} --initial-m5-run ${M5_SOURCE} --handoff-run ${M5_HANDOFF} --expected-contract-hash ${CONTRACT_HASH} --node an12 --gpu-ids 0,1,2,3 --poll-seconds 60"
CONFIG_HASH="${CONTRACT_HASH}"
DATA_HASH="$({
  sha256sum \
    "${A2_TRAINING}/run_manifest.json" \
    "${A2_WATCHER}/run_manifest.json" \
    "${M5_SOURCE}/run_manifest.json" \
    "${M5_HANDOFF}/run_manifest.json" \
    "${M5_HANDOFF}/handoff_result.json"
} | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" \
  --arg a2_training "${A2_TRAINING}" --arg a2_watcher "${A2_WATCHER}" \
  --arg m5_source "${M5_SOURCE}" --arg m5_handoff "${M5_HANDOFF}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m5_after_seed3_a2_lifecycle_queue",node:"login",gpu_allocation:[],gpu_ids:[],
    tensor_parallel_width:0,replica_count:0,child_node:"an12",child_gpu_ids:[0,1,2,3],
    child_tensor_parallel_width:2,child_replica_count:2,
    placement_justification:"GPU-inert login scheduler waits for the exact seed-3 A2 trainer and retention watcher to release an12, then serializes hash-verified M5 segments on an12 GPUs 0-3. It never launches or signals another pilot arm.",
    git_hash:$git_hash,config_path:"scripts/run_m5_after_seed3_a2_queue.py",config_hash:$config_hash,
    data_manifest:$a2_training,data_manifest_hash:$data_hash,seed:1,command:$command,
    a2_training_run:$a2_training,a2_watcher_run:$a2_watcher,
    initial_m5_run:$m5_source,m5_handoff_run:$m5_handoff,
    start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,
    deviations:["M5 is operationally segmented at verified 50-step boundaries to contain the measured Ray worker-memory ramp; the registered terminal remains step 400.","TP2 is retained only for exact continuity with the launched anchor checkpoint."]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
sleep 3
ps -p "$(cat "${RUN_DIR}/pids/login.pid")" -o pid= >/dev/null || {
  echo "M5 lifecycle queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
