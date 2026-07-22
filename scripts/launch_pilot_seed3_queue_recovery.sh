#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <failed-seed3-queue-run-dir> <adopted-training-run-dir>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
FAILED_QUEUE="${1%/}"
TRAINING_RUN="${2%/}"
FAILED_MANIFEST="${FAILED_QUEUE}/run_manifest.json"
FAILED_LOG="${FAILED_QUEUE}/logs/login.log"
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
WATCHER_POINTER="${TRAINING_RUN}/checkpoint_watcher_run.txt"
for PATH_REQUIRED in "${FAILED_MANIFEST}" "${FAILED_LOG}" "${TRAINING_MANIFEST}" "${WATCHER_POINTER}"; do
  [[ -s "${PATH_REQUIRED}" ]] || { echo "seed-3 recovery input absent: ${PATH_REQUIRED}" >&2; exit 2; }
done
jq -e '(.job_type == "m3_seed3_training_capacity_queue_v4") and (.status == "fail") and (.exit_code != 0)' "${FAILED_MANIFEST}" >/dev/null
grep -F 'checkpoint watcher failed to launch (73): pilot checkpoint watcher session already exists' "${FAILED_LOG}" >/dev/null
jq -e '(.job_type == "m3_mechanical_pilot_arm") and (.seed == 3) and
       (.arm == "a1_real") and (.status == "running" or .status == "complete") and
       (.node == "an29") and (.gpu_ids == [0,1,2,3])' "${TRAINING_MANIFEST}" >/dev/null
WATCHER_RUN="$(cat "${WATCHER_POINTER}")"
[[ "${WATCHER_RUN}" == experiments/runs/pilot_checkpoint_watch_* ]] || {
  echo "seed-3 recovery watcher pointer is invalid" >&2
  exit 2
}
jq -e --arg parent "${TRAINING_RUN}" \
  '(.job_type == "pilot_checkpoint_retention_watch") and
   (.parent_training_run == $parent) and (.compute_node == "an29") and
   (.status == "running" or .status == "complete")' "${WATCHER_RUN}/run_manifest.json" >/dev/null

SEED2="$(jq -er '.seed2_dependency' "${FAILED_MANIFEST}")"
M6="$(jq -er '.m6_smoke_dependency' "${FAILED_MANIFEST}")"
M5="$(jq -er '.m5_dependency' "${FAILED_MANIFEST}")"
for PATH_REQUIRED in "${SEED2}" "${M6}" "${M5}"; do
  [[ -s "${PATH_REQUIRED}" ]] || { echo "seed-3 recovery dependency absent: ${PATH_REQUIRED}" >&2; exit 2; }
done
for CHECKPOINT in \
  checkpoints/pilot/mech_a2_gray_seed3 \
  checkpoints/pilot/mech_a2b_noimage_seed3 \
  checkpoints/pilot/mech_a3_caption_seed3; do
  [[ ! -e "${CHECKPOINT}" ]] || { echo "pending seed-3 checkpoint namespace already exists: ${CHECKPOINT}" >&2; exit 73; }
done
if pgrep -af '[r]un_pilot_seed3_queue_v2.py'; then
  echo "refusing duplicate active seed-3 scheduler" >&2
  exit 73
fi

CRITICAL=(
  scripts/run_pilot_seed3_queue_v2.py
  scripts/launch_pilot_seed3_queue_recovery.sh
  scripts/launch_mech_pilot_followup_arm.sh
  scripts/check_pilot_followup_launch_authorization.py
  scripts/launch_pilot_checkpoint_watch.sh
  scripts/watch_pilot_checkpoints.py
  scripts/watch_anchor_checkpoints.py
  docs/registered_pilot_seed23_v1.md
  configs/train/mech_a1_real_seed3_3b_geo3k.yaml
  configs/train/mech_a2_gray_seed3_3b_geo3k.yaml
  configs/train/mech_a2b_noimage_seed3_3b_geo3k.yaml
  configs/train/mech_a3_caption_seed3_3b_geo3k.yaml
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked seed-3 recovery file: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "seed-3 recovery contract differs from HEAD" >&2; exit 2; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed3_queue_v5_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_seed3_queue_v2.py --run-dir ${RUN_DIR} --seed2-manifest ${SEED2} --m6-manifest ${M6} --m5-manifest ${M5} --poll-seconds 60 --stable-polls 2 --adopted-arm a1_real --adopted-training-run ${TRAINING_RUN} --adopted-watcher-run ${WATCHER_RUN}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$({ sha256sum "${SEED2}" "${M6}" "${M5}" "${FAILED_MANIFEST}" "${TRAINING_MANIFEST}" "${WATCHER_RUN}/run_manifest.json"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg seed2 "${SEED2}" \
  --arg m6 "${M6}" --arg m5 "${M5}" --arg failed "${FAILED_MANIFEST}" \
  --arg training "${TRAINING_RUN}" --arg watcher "${WATCHER_RUN}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m3_seed3_training_capacity_queue_v5",node:"login",gpu_allocation:[],gpu_ids:[],
    tensor_parallel_width:0,replica_count:0,child_gpu_count:4,child_tensor_parallel_width:1,child_replica_count:4,
    placement_justification:"GPU-inert recovery scheduler adopts the already-running A1 seed-3 trainer and its identity-checked watcher, then continues the registered one-trainer-per-node sequence without restarting A1.",
    git_hash:$git_hash,config_path:"docs/registered_pilot_seed23_v1.md",config_hash:$config_hash,
    data_manifest:"data/geo3k_pilot_filtered.jsonl",data_manifest_hash:$data_hash,seed:3,
    command:$command,seed2_dependency:$seed2,m6_smoke_dependency:$m6,m5_dependency:$m5,
    failed_queue_dependency:$failed,adopted_training_run:$training,adopted_watcher_run:$watcher,
    start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,
    deviations:["The v4 scheduler launched A1 and its built-in watcher successfully, then failed closed after attempting a duplicate watcher. This v5 scheduler adopts those exact running artifacts; no optimizer trajectory is restarted or reconstructed."]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "seed-3 recovery scheduler exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
