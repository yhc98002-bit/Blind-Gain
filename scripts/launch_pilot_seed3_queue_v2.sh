#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
if [[ $# -ne 2 ]]; then
  echo "usage: $0 <sealed-seed2-lifecycle-manifest> <m6-smoke-queue-manifest>" >&2
  exit 2
fi
SEED2="$(realpath -m "$1")"
M6="$(realpath -m "$2")"
for manifest in "${SEED2}" "${M6}"; do
  case "${manifest}" in
    "${ROOT}"/experiments/runs/*/run_manifest.json) ;;
    *) echo "queue dependency must be under experiments/runs" >&2; exit 2 ;;
  esac
done
M5="experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z/run_manifest.json"
REGISTRATION="docs/registered_pilot_seed23_v1.md"
for path in "${SEED2}" "${M6}" "${M5}" "${REGISTRATION}"; do
  [[ -s "${path}" ]] || { echo "seed-3 queue input is absent: ${path}" >&2; exit 2; }
done
jq -e '((.job_type == "pilot_followup_evaluation_lifecycle") or
        (.job_type == "pilot_followup_evaluation_recovery_lifecycle")) and
       (.pilot_seed == 2) and (.performance_values_opened == false)' "${SEED2}" >/dev/null
jq -e '((.job_type == "m6_registered_smoke_priority_queue_v2") or
        (.job_type == "m6_registered_smoke_priority_queue_v3") or
        (.job_type == "m6_registered_smoke_member_recovery_v1")) and
       (.main_optimizer_steps_authorized == 0)' "${M6}" >/dev/null
jq -e '(.job_type == "m5_anchor_longhorizon_400") and
       (.target_global_step == 400) and (.status == "running" or .status == "complete")' "${M5}" >/dev/null

CHECKPOINTS=(
  checkpoints/pilot/mech_a1_real_seed3
  checkpoints/pilot/mech_a2_gray_seed3
  checkpoints/pilot/mech_a2b_noimage_seed3
  checkpoints/pilot/mech_a3_caption_seed3
)
for checkpoint in "${CHECKPOINTS[@]}"; do
  [[ ! -e "${checkpoint}" ]] || { echo "seed-3 checkpoint namespace already exists: ${checkpoint}" >&2; exit 73; }
done
if pgrep -af '[r]un_pilot_seed3_queue_v2.py'; then
  echo "refusing duplicate seed-3 capacity queue" >&2
  exit 73
fi

CRITICAL_FILES=(
  scripts/run_pilot_seed3_queue_v2.py
  scripts/launch_pilot_seed3_queue_v2.sh
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
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "seed-3 queue contract differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked seed-3 critical file: ${FILE}" >&2
    exit 2
  }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed3_queue_v4_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_seed3_queue_v2.py --run-dir ${RUN_DIR} --seed2-manifest ${SEED2} --m6-manifest ${M6} --m5-manifest ${M5} --poll-seconds 60 --stable-polls 2"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$({ sha256sum "${CRITICAL_FILES[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$({ sha256sum "${SEED2}" "${M6}" "${M5}" data/geo3k_pilot_filtered.jsonl data/geo3k_pilot_filtered_ids.json; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg seed2 "${SEED2}" \
  --arg m6 "${M6}" --arg m5 "${M5}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m3_seed3_training_capacity_queue_v4",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    child_gpu_count: 4,
    child_tensor_parallel_width: 1,
    child_replica_count: 4,
    placement_justification: "GPU-inert login scheduler waits for the sealed seed-2 lifecycle and registered M6 smoke audit, then launches at most one four-GPU synchronous pilot trainer per node and immediately attaches retention watchers.",
    git_hash: $git_hash,
    config_path: "docs/registered_pilot_seed23_v1.md",
    config_hash: $config_hash,
    data_manifest: "data/geo3k_pilot_filtered.jsonl",
    data_manifest_hash: $data_hash,
    seed: 3,
    command: $command,
    seed2_dependency: $seed2,
    m6_smoke_dependency: $m6,
    m5_dependency: $m5,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: ["Supersedes failed dependency queues. Registered seed-3 configs and launch order are unchanged; the accepted M6 dependency may be the explicit member-smoke recovery artifact."]
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "seed-3 capacity queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
