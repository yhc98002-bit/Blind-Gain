#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "usage: $0 <retired-v5-queue> <a1-training> <a1-watcher> <a2-training> <a2-watcher> <m5-lifecycle>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
RETIRED_QUEUE="${1%/}"
A1_TRAINING="${2%/}"
A1_WATCHER="${3%/}"
A2_TRAINING="${4%/}"
A2_WATCHER="${5%/}"
M5_LIFECYCLE="${6%/}"

for REQUIRED in \
  "${RETIRED_QUEUE}/run_manifest.json" \
  "${RETIRED_QUEUE}/queue_state.json" \
  "${A1_TRAINING}/run_manifest.json" \
  "${A1_WATCHER}/run_manifest.json" \
  "${A2_TRAINING}/run_manifest.json" \
  "${A2_WATCHER}/run_manifest.json" \
  "${M5_LIFECYCLE}/run_manifest.json"; do
  [[ -s "${REQUIRED}" ]] || { echo "seed-3 remaining-queue input absent: ${REQUIRED}" >&2; exit 2; }
done

jq -e '(.job_type=="m3_seed3_training_capacity_queue_v5") and
       (.status=="fail") and (.exit_code==-15)' \
  "${RETIRED_QUEUE}/run_manifest.json" >/dev/null || {
  echo "retired v5 queue identity is invalid" >&2
  exit 3
}
jq -e --arg a1 "${A1_TRAINING}" --arg a1w "${A1_WATCHER}" \
       --arg a2 "${A2_TRAINING}" --arg a2w "${A2_WATCHER}" '
  (.arms.a1_real.training_run==$a1) and (.arms.a1_real.watcher_run==$a1w) and
  (.arms.a2_gray.training_run==$a2) and (.arms.a2_gray.watcher_run==$a2w) and
  (.arms.a2b_noimage.status=="pending") and (.arms.a3_caption.status=="pending")
' "${RETIRED_QUEUE}/queue_state.json" >/dev/null || {
  echo "retired v5 child identities are invalid" >&2
  exit 3
}
jq -e '(.job_type=="m5_after_seed3_a2_lifecycle_queue") and
       (.status=="running" or .status=="complete") and
       (.child_node=="an12") and (.child_gpu_ids==[0,1,2,3])' \
  "${M5_LIFECYCLE}/run_manifest.json" >/dev/null || {
  echo "M5 lifecycle dependency identity is invalid" >&2
  exit 3
}

PYTHONPATH=. .venv/bin/python - \
  "${A1_TRAINING}" "${A1_WATCHER}" "${A2_TRAINING}" "${A2_WATCHER}" <<'PY'
import sys
from scripts.run_pilot_seed3_queue_v2 import validate_adopted_record

validate_adopted_record("a1_real", sys.argv[1], sys.argv[2])
validate_adopted_record("a2_gray", sys.argv[3], sys.argv[4])
PY

for CHECKPOINT in \
  checkpoints/pilot/mech_a2b_noimage_seed3 \
  checkpoints/pilot/mech_a3_caption_seed3; do
  [[ ! -e "${CHECKPOINT}" ]] || {
    echo "pending seed-3 checkpoint namespace already exists: ${CHECKPOINT}" >&2
    exit 73
  }
done
if pgrep -af '[r]un_pilot_seed3_queue_v2.py'; then
  echo "refusing a duplicate active seed-3 scheduler" >&2
  exit 73
fi

CRITICAL=(
  scripts/run_pilot_seed3_queue_v2.py
  scripts/launch_pilot_seed3_remaining_an29.sh
  scripts/launch_mech_pilot_followup_arm.sh
  scripts/check_pilot_followup_launch_authorization.py
  scripts/launch_pilot_checkpoint_watch.sh
  scripts/watch_pilot_checkpoints.py
  scripts/watch_anchor_checkpoints.py
  docs/registered_pilot_seed23_v1.md
  configs/train/mech_a2b_noimage_seed3_3b_geo3k.yaml
  configs/train/mech_a3_caption_seed3_3b_geo3k.yaml
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked seed-3 remaining-queue contract: ${FILE}" >&2
    exit 3
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "seed-3 remaining-queue contract differs from HEAD" >&2
  exit 3
}

SEED2_MANIFEST="$(jq -er '.seed2_dependency' "${RETIRED_QUEUE}/run_manifest.json")"
M6_MANIFEST="$(jq -er '.m6_smoke_dependency' "${RETIRED_QUEUE}/run_manifest.json")"
for REQUIRED in "${SEED2_MANIFEST}" "${M6_MANIFEST}"; do
  [[ -s "${REQUIRED}" ]] || { echo "seed-3 dependency absent: ${REQUIRED}" >&2; exit 3; }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed3_remaining_an29_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
M5_MANIFEST="${M5_LIFECYCLE}/run_manifest.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_seed3_queue_v2.py --run-dir ${RUN_DIR} --seed2-manifest ${SEED2_MANIFEST} --m6-manifest ${M6_MANIFEST} --m5-manifest ${M5_MANIFEST} --poll-seconds 60 --stable-polls 2 --adopted-arm a1_real --adopted-training-run ${A1_TRAINING} --adopted-watcher-run ${A1_WATCHER} --additional-adopted-record a2_gray,${A2_TRAINING},${A2_WATCHER} --launch-nodes an29"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum \
    "${RETIRED_QUEUE}/run_manifest.json" \
    "${RETIRED_QUEUE}/queue_state.json" \
    "${A1_TRAINING}/run_manifest.json" \
    "${A1_WATCHER}/run_manifest.json" \
    "${A2_TRAINING}/run_manifest.json" \
    "${A2_WATCHER}/run_manifest.json" \
    "${M5_MANIFEST}" "${SEED2_MANIFEST}" "${M6_MANIFEST}"
} | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg seed2 "${SEED2_MANIFEST}" \
  --arg m6 "${M6_MANIFEST}" --arg m5 "${M5_MANIFEST}" \
  --arg retired "${RETIRED_QUEUE}" --arg a1 "${A1_TRAINING}" \
  --arg a1w "${A1_WATCHER}" --arg a2 "${A2_TRAINING}" --arg a2w "${A2_WATCHER}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m3_seed3_remaining_an29_queue_v1",node:"login",gpu_allocation:[],gpu_ids:[],
    tensor_parallel_width:0,replica_count:0,child_node:"an29",child_gpu_ids:[0,1,2,3],
    child_tensor_parallel_width:1,child_replica_count:4,
    placement_justification:"GPU-inert scheduler adopts the exact active A1/A2 runs but can launch pending A2b then A3 only on an29 GPUs 0-3. an12 remains exclusively reserved for the independent M5 lifecycle.",
    git_hash:$git_hash,config_path:"scripts/run_pilot_seed3_queue_v2.py",config_hash:$config_hash,
    data_manifest:"data/geo3k_pilot_filtered.jsonl",data_manifest_hash:$data_hash,seed:3,
    command:$command,seed2_dependency:$seed2,m6_smoke_dependency:$m6,m5_dependency:$m5,
    retired_queue_dependency:$retired,adopted_training_runs:[$a1,$a2],
    adopted_watcher_runs:[$a1w,$a2w],launch_nodes:["an29"],
    start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,
    deviations:["The superseded v5 scheduler was intentionally retired after launching A2. This queue adopts both exact live children and restricts all future launches to an29 so it cannot race the M5 an12 lifecycle."]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
sleep 3
ps -p "$(cat "${RUN_DIR}/pids/login.pid")" -o pid= >/dev/null || {
  echo "seed-3 remaining queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
