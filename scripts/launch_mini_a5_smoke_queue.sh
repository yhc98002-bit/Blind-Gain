#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

SEED2="experiments/runs/pilot_seed2_queue_login_20260716T164718Z/run_manifest.json"
M11="experiments/runs/m11_reconciled_backfill_login_20260716T172041Z/run_manifest.json"
M5="experiments/runs/m5_anchor_longhorizon_400_an12_20260716T173030Z/run_manifest.json"
REGISTRATION="reports/mini_a5_smoke_registration_marker_v1.json"
for path in "${SEED2}" "${M11}" "${M5}" "${REGISTRATION}"; do
  [[ -s "${path}" ]] || { echo "Mini-A5 queue input is absent: ${path}" >&2; exit 2; }
done
jq -e '(.status == "registered") and (.main_optimizer_steps_authorized == 0)' "${REGISTRATION}" >/dev/null
if pgrep -af '[r]un_mini_a5_smoke_queue.py'; then
  echo "refusing duplicate Mini-A5 smoke queue" >&2
  exit 73
fi
if [[ -e reports/mini_a5_plumbing_smoke_audit_v1.json || -e reports/mini_a5_plumbing_smoke_audit_v1.md ]]; then
  echo "refusing to overwrite Mini-A5 smoke audit outputs" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_smoke_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_mini_a5_smoke_queue.py --run-dir ${RUN_DIR} --seed2-manifest ${SEED2} --m11-manifest ${M11} --m5-manifest ${M5} --poll-seconds 60 --stable-polls 2"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${REGISTRATION}" "${SEED2}" "${M11}" "${M5}"
  sha256sum scripts/run_mini_a5_smoke_queue.py scripts/launch_mini_a5_plumbing_smoke.sh scripts/audit_mini_a5_plumbing_smoke.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg state "${RUN_DIR}/queue_state.json" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_registered_smoke_priority_queue",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "GPU-inert login queue; each child smoke independently enforces one-node eight-GPU TP1 placement.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "seed-2 + M11 + M5 structural dependency manifests and Mini-A5 smoke registration",
    data_manifest_hash: $data_hash,
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
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")"
printf '%s\n' "${RUN_DIR}"
