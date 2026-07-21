#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

SEED2="experiments/runs/pilot_seed2_locked_eval_lifecycle_login_20260721T163341Z/run_manifest.json"
M11="experiments/runs/m11_reconciled_final_report_login_20260718T153539Z/run_manifest.json"
M5="experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z/run_manifest.json"
REGISTRATION="reports/mini_a5_smoke_registration_marker_v1.json"
for path in "${SEED2}" "${M11}" "${M5}" "${REGISTRATION}"; do
  [[ -s "${path}" ]] || { echo "Mini-A5 v2 queue input is absent: ${path}" >&2; exit 2; }
done
jq -e '(.job_type == "pilot_followup_evaluation_lifecycle") and
       (.pilot_seed == 2) and (.performance_values_opened == false)' "${SEED2}" >/dev/null
jq -e '(.job_type == "m11_reconciled_final_report") and
       (.status == "complete") and (.exit_code == 0) and (.artifacts_exist == true)' "${M11}" >/dev/null
jq -e '(.job_type == "m5_anchor_longhorizon_400") and
       (.target_global_step == 400) and (.status == "running" or .status == "complete")' "${M5}" >/dev/null
jq -e '(.status == "registered") and (.main_optimizer_steps_authorized == 0)' "${REGISTRATION}" >/dev/null

CRITICAL_FILES=(
  scripts/run_mini_a5_smoke_queue.py
  scripts/launch_mini_a5_smoke_queue_v2.sh
  scripts/launch_mini_a5_plumbing_smoke.sh
  scripts/audit_mini_a5_plumbing_smoke.py
  configs/train/mini_a5_cp_plumbing_smoke_v1.yaml
  configs/train/mini_a5_member_plumbing_smoke_v1.yaml
  docs/registered_mini_a5_smoke_v1.md
  reports/mini_a5_smoke_registration_marker_v1.json
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "Mini-A5 v2 smoke queue contract differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked Mini-A5 v2 critical file: ${FILE}" >&2
    exit 2
  }
done
if pgrep -af '[r]un_mini_a5_smoke_queue.py'; then
  echo "refusing duplicate Mini-A5 smoke queue" >&2
  exit 73
fi
if [[ -e reports/mini_a5_plumbing_smoke_audit_v1.json || -e reports/mini_a5_plumbing_smoke_audit_v1.md ]]; then
  echo "refusing to overwrite Mini-A5 smoke audit outputs" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_smoke_queue_v2_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_mini_a5_smoke_queue.py --run-dir ${RUN_DIR} --seed2-manifest ${SEED2} --m11-manifest ${M11} --m5-manifest ${M5} --poll-seconds 60 --stable-polls 2"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${REGISTRATION}" "${SEED2}" "${M11}" "${M5}"
  sha256sum "${CRITICAL_FILES[@]}"
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${RUN_DIR}/queue_state.json" \
  --arg seed2 "${SEED2}" --arg m11 "${M11}" --arg m5 "${M5}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_registered_smoke_priority_queue_v2",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    child_gpu_count: 8,
    child_tensor_parallel_width: 1,
    child_replica_count: 8,
    preferred_child_node: "an29",
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "GPU-inert login queue waits for the sealed seed-2 lifecycle and then requires one fully free permanent node; registered CP/member one-step smokes run sequentially with eight colocated TP1 workers, preferring an29.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "sealed seed-2 evaluation lifecycle + reconciled M11 + active M5 structural manifests and Mini-A5 smoke registration",
    data_manifest_hash: $data_hash,
    seed2_dependency: $seed2,
    m11_dependency: $m11,
    m5_dependency: $m5,
    seed: 20260716,
    command: $command,
    start_time_utc: $start_time,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [
      $state,
      "reports/mini_a5_plumbing_smoke_audit_v1.json",
      "reports/mini_a5_plumbing_smoke_audit_v1.md"
    ],
    performance_values_opened: false,
    main_optimizer_steps_authorized: 0,
    smoke_optimizer_steps_authorized_per_arm: 1,
    scientific_gate_decision: null,
    deviations: ["Supersedes the failed v1 queue dependency paths; the registered smoke commands, data, configs, and one-step authorization are unchanged."]
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || {
  echo "Mini-A5 v2 smoke queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
