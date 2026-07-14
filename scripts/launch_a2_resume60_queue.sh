#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <a1-resume-run> <a2b-run> <a3-run> <failed-a2-source-run>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
A1="$1"; A2B="$2"; A3="$3"; A2_SOURCE="$4"
for FILE in scripts/watch_a2_resume60_release.py scripts/launch_a2_resume60_queue.sh scripts/launch_mech_pilot_resume60.sh scripts/launch_m2_completion_watchdog.sh; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "queue-critical file is not tracked: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- scripts/watch_a2_resume60_release.py scripts/launch_a2_resume60_queue.sh scripts/launch_mech_pilot_resume60.sh scripts/launch_m2_completion_watchdog.sh || { echo "queue-critical code differs from HEAD" >&2; exit 2; }

for SPEC in "a1_real:${A1}" "a2b_noimage:${A2B}" "a3_caption:${A3}" "a2_gray:${A2_SOURCE}"; do
  ARM="${SPEC%%:*}"; DIR="${SPEC#*:}"; MANIFEST="${DIR}/run_manifest.json"
  [[ -f "${MANIFEST}" ]] || { echo "manifest absent: ${MANIFEST}" >&2; exit 2; }
  [[ "$(jq -r '.job_type' "${MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "not a pilot run: ${DIR}" >&2; exit 2; }
  [[ "$(jq -r '.arm' "${MANIFEST}")" == "${ARM}" ]] || { echo "arm mismatch: ${DIR}" >&2; exit 2; }
done
[[ "$(jq -r '.resumed_from_global_step' "${A1}/run_manifest.json")" == "60" ]] || { echo "A1 is not the step-60 recovery run" >&2; exit 2; }
[[ "$(jq -r '.status' "${A2_SOURCE}/run_manifest.json")" == "fail" ]] || { echo "A2 source is not finalized fail" >&2; exit 2; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="a2_resume60_release_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${RUN_DIR}/config.json"
STATE="${RUN_DIR}/state.json"
TERMINAL="${RUN_DIR}/terminal.json"
LAUNCH_LOG="${RUN_DIR}/launch_attempts.jsonl"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg a1 "${A1}/run_manifest.json" --arg a2b "${A2B}/run_manifest.json" --arg a3 "${A3}/run_manifest.json" \
  --arg a1_run "${A1}" --arg a2b_run "${A2B}" --arg a3_run "${A3}" --arg source "${A2_SOURCE}" \
  --arg state "${STATE}" --arg terminal "${TERMINAL}" --arg launch_log "${LAUNCH_LOG}" \
  '{schema_version:"blind-gains.a2-resume60-release-queue.v1",poll_interval_seconds:120,
    upstream_manifests:{a1_real:$a1,a2b_noimage:$a2b,a3_caption:$a3},
    a1_resume_run:$a1_run,a2b_run:$a2b_run,a3_run:$a3_run,a2_failed_source_run:$source,
    state_path:$state,terminal_path:$terminal,launch_log:$launch_log}' > "${CONFIG}"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_a2_resume60_release.py --config '${CONFIG}'"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" --arg config "${CONFIG}" \
  --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg terminal "${TERMINAL}" --arg launch_log "${LAUNCH_LOG}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"a2_resume60_release_queue",
    node:"login",gpu_ids:[],gpu_allocation:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only lifecycle watcher launches A2 only after one complete node release; it reads no scientific metrics.",
    git_hash:$git_hash,config_path:$config,config_hash:$config_hash,data_manifest_hash:$config_hash,seed:1,
    command:$command,start_time_utc:$started,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state,$terminal,$launch_log],scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "A2 release queue exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
