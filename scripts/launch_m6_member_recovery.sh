#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <m6-collective-preflight-run-dir>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
PREFLIGHT="$(realpath -m "$1")"
CP_MANIFEST="experiments/runs/mini_a5_cp_plumbing_smoke_an29_20260722T041049Z/run_manifest.json"
FAILED_MEMBER_MANIFEST="experiments/runs/mini_a5_member_plumbing_smoke_an29_20260722T041726Z/run_manifest.json"
[[ "${PREFLIGHT}" == "${ROOT}"/experiments/runs/m6_collective_preflight_an29_*/run_manifest.json ]] || {
  PREFLIGHT="${PREFLIGHT%/}/run_manifest.json"
}
for PATH_REQUIRED in "${PREFLIGHT}" "${CP_MANIFEST}" "${FAILED_MEMBER_MANIFEST}"; do
  [[ -s "${PATH_REQUIRED}" ]] || { echo "M6 recovery input absent: ${PATH_REQUIRED}" >&2; exit 2; }
done
CRITICAL=(
  scripts/run_m6_member_recovery.py
  scripts/launch_m6_member_recovery.sh
  scripts/probe_single_node_collectives.py
  scripts/launch_m6_collective_preflight.sh
  scripts/launch_mini_a5_plumbing_smoke.sh
  scripts/audit_mini_a5_plumbing_smoke.py
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked M6 recovery-critical file: ${FILE}" >&2
    exit 2
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "M6 recovery code differs from HEAD" >&2; exit 2; }
if pgrep -af '[r]un_m6_member_recovery.py'; then
  echo "refusing duplicate M6 member recovery" >&2
  exit 73
fi
[[ ! -e reports/mini_a5_plumbing_smoke_audit_v1.json && ! -e reports/mini_a5_plumbing_smoke_audit_v1.md ]] || {
  echo "refusing to overwrite existing Mini-A5 smoke audit" >&2
  exit 73
}

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m6_member_smoke_recovery_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/recovery_state.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m6_member_recovery.py --run-dir ${RUN_DIR} --cp-manifest ${CP_MANIFEST} --failed-member-manifest ${FAILED_MEMBER_MANIFEST} --preflight-manifest ${PREFLIGHT} --node an29 --poll-seconds 30 --stable-polls 4"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$({ sha256sum "${CP_MANIFEST}" "${FAILED_MEMBER_MANIFEST}" "${PREFLIGHT}"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg preflight "${PREFLIGHT}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m6_registered_smoke_member_recovery_v1",status:"running",node:"login",
    target_node:"an29",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    child_gpu_count:8,child_tensor_parallel_width:1,child_replica_count:8,
    placement_justification:"GPU-inert recovery controller requires a fresh two-round collective preflight and a 90-second quiet window before retrying only the failed eight-GPU member smoke on an29.",
    git_hash:$git_hash,config_path:"scripts/run_m6_member_recovery.py",config_hash:$config_hash,
    data_manifest:$preflight,data_manifest_hash:$data_hash,seed:20260716,command:$command,
    start_time_utc:$start,end_time_utc:null,exit_code:null,stdout_stderr_log:$log,
    expected_artifacts:[$state,"reports/mini_a5_plumbing_smoke_audit_v1.json","reports/mini_a5_plumbing_smoke_audit_v1.md"],
    main_optimizer_steps_authorized:0,performance_values_opened:false,
    scientific_gate_decision:null,
    deviations:["The original CP smoke is reused unchanged. Only the member smoke is retried after the original run failed before its optimizer step with Gloo connectFullMesh."]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "M6 member recovery controller exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
