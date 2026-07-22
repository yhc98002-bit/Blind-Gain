#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <an12|an29> <completed-training-run-dir> <failed-watcher-run-dir>" >&2
  exit 2
fi
NODE="$1"
TRAINING_RUN="$2"
FAILED_WATCHER_RUN="$3"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
FAILED_WATCHER_MANIFEST="${FAILED_WATCHER_RUN}/run_manifest.json"
[[ -s "${TRAINING_MANIFEST}" && -s "${FAILED_WATCHER_MANIFEST}" ]] || { echo "recovery input manifest absent" >&2; exit 2; }

CRITICAL=(
  scripts/watch_pilot_completed_parent_checkpoints.py
  scripts/launch_pilot_completed_checkpoint_recovery.sh
  scripts/watch_pilot_checkpoints.py
  scripts/watch_anchor_checkpoints.py
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked recovery file: ${FILE}" >&2; exit 3; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "completed-parent recovery code differs from HEAD" >&2; exit 3; }
PYTHONPATH=. .venv/bin/python - "${TRAINING_MANIFEST}" "${FAILED_WATCHER_MANIFEST}" <<'PY'
import sys
from pathlib import Path
from scripts.watch_pilot_completed_parent_checkpoints import read_json, validate_recovery_inputs
errors = validate_recovery_inputs(read_json(Path(sys.argv[1])), read_json(Path(sys.argv[2])))
if errors:
    raise SystemExit(f"invalid completed-parent recovery inputs: {errors}")
PY
[[ "$(jq -r '.node' "${TRAINING_MANIFEST}")" == "${NODE}" ]] || { echo "recovery node differs from parent placement" >&2; exit 3; }
RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_MANIFEST}")"
PARENT_RUN_ID="$(jq -er '.run_id' "${TRAINING_MANIFEST}")"
RUN_LABEL="$(jq -er '.arm_run_name' "${TRAINING_MANIFEST}")"
[[ "${RUN_ROOT}" == "${ROOT}/checkpoints/pilot/"* ]] || { echo "checkpoint root outside pilot namespace" >&2; exit 3; }
[[ -s "${RUN_ROOT}/global_step_20/actor/RAW_STATE_RELOCATED.json" ]] || { echo "step-20 raw relocation marker absent" >&2; exit 3; }
[[ -s "${RUN_ROOT}/global_step_20/actor/MERGED_CHECKPOINT_RELOCATED.json" ]] || { echo "step-20 merged relocation marker absent" >&2; exit 3; }
for STEP in 40 60 80 100; do
  COUNT="$(find "${RUN_ROOT}/global_step_${STEP}/actor" -maxdepth 1 -type f \( -name 'model_world_size_4_rank_*.pt' -o -name 'optim_world_size_4_rank_*.pt' \) | wc -l)"
  [[ "${COUNT}" -eq 8 ]] || { echo "step-${STEP} does not have eight raw shards" >&2; exit 3; }
done
if pgrep -af '[w]atch_pilot_completed_parent_checkpoints.py.*mech_a1_real_seed2'; then
  echo "A1 completed-parent recovery already active" >&2; exit 73
fi

ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}"
STEP60_MARKER="${ROOT}/${TRAINING_RUN}/step60_fliptrack_complete.json"
STEP60_GEO3K_MARKER="${ROOT}/${TRAINING_RUN}/step60_geo3k_complete.json"
EXPECTED_CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_pilot_completed_parent_checkpoints import recovery_code_bundle_hash; print(recovery_code_bundle_hash())')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_completed_checkpoint_recovery_${RUN_LABEL}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_completed_parent_checkpoints.py --run-root '${RUN_ROOT}' --archive-root '${ARCHIVE_ROOT}' --run-manifest '${TRAINING_MANIFEST}' --failed-watcher-manifest '${FAILED_WATCHER_MANIFEST}' --node '${NODE}' --run-label '${RUN_LABEL}' --step60-evaluation-marker '${STEP60_MARKER}' --step60-geo3k-marker '${STEP60_GEO3K_MARKER}' --expected-code-hash '${EXPECTED_CODE_HASH}'"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg failed "${FAILED_WATCHER_RUN}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${EXPECTED_CODE_HASH}" \
  --arg data_hash "$({ sha256sum "${TRAINING_MANIFEST}" "${FAILED_WATCHER_MANIFEST}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg compute_node "${NODE}" \
  --arg run_root "${RUN_ROOT}" --arg archive_root "${ARCHIVE_ROOT}" --arg marker "${STEP60_MARKER}" \
  --arg geo3k_marker "${STEP60_GEO3K_MARKER}" \
  --argjson seed "$(jq -er '.seed' "${TRAINING_MANIFEST}")" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"pilot_completed_parent_checkpoint_recovery",
    parent_training_run:$parent,prior_failed_watcher:$failed,node:"login",compute_node:$compute_node,
    gpu_ids:[],gpu_allocation:[],tensor_parallel_width:0,replica_count:0,
    placement_policy_version:"pi-2026-07-11",placement_justification:"CPU/login orchestrator resumes only checkpoint merge and retention after the completed A1 parent watcher failed; no optimizer work is performed.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$parent,data_manifest_hash:$data_hash,seed:$seed,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    run_root:$run_root,archive_root:$archive_root,recovery_steps:[40,60,80,100],
    raw_retention:"latest raw state only",step60_evaluation_marker:$marker,
    step60_geo3k_marker:$geo3k_marker,
    expected_artifacts:[($run_root+"/global_step_100/actor/huggingface/model.safetensors.index.json"),($run_root+"/global_step_100/actor/RAW_STATE_RELOCATED.json")],
    performance_values_opened:false,scientific_gate_decision:null,deviations:["Checkpoint-lifecycle recovery after the original watcher failed before step 40; the completed optimizer trajectory is unchanged."]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || { echo "completed-parent recovery exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
