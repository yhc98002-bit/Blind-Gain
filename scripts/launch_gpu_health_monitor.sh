#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <pilot-run-dir> [pilot-run-dir ...]" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
git diff --quiet HEAD -- scripts/monitor_gpu_health.py scripts/launch_gpu_health_monitor.sh || { echo "monitor code differs from HEAD" >&2; exit 2; }

RUNS='[]'
for RUN_DIR_INPUT in "$@"; do
  RUN_DIR="$(realpath -m "${RUN_DIR_INPUT}")"
  [[ "${RUN_DIR}" == "${ROOT}/experiments/runs/"* ]] || { echo "run outside immutable registry" >&2; exit 2; }
  MANIFEST="${RUN_DIR}/run_manifest.json"
  [[ -f "${MANIFEST}" ]] || { echo "manifest absent: ${MANIFEST}" >&2; exit 2; }
  [[ "$(jq -r '.job_type' "${MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "not a pilot run" >&2; exit 2; }
  ENTRY="$(jq -n --arg run_dir "${RUN_DIR#"${ROOT}/"}" --arg run_id "$(jq -er '.run_id' "${MANIFEST}")" '{run_dir:$run_dir,run_id:$run_id}')"
  RUNS="$(jq -c --argjson item "${ENTRY}" '. + [$item]' <<< "${RUNS}")"
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="gpu_health_24x60m_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${RUN_DIR}/config.json"
SAMPLES="${RUN_DIR}/samples.jsonl"
SUMMARY_JSON="${RUN_DIR}/summary.json"
SUMMARY_MD="${RUN_DIR}/summary.md"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --argjson runs "${RUNS}" --arg samples "${SAMPLES}" --arg summary_json "${SUMMARY_JSON}" --arg summary_md "${SUMMARY_MD}" '{schema_version:"blind-gains.gpu-health-monitor-config.v1",duration_seconds:3600,interval_seconds:30,nodes:["an12","an21","an29"],runs:$runs,samples_jsonl:$samples,summary_json:$summary_json,summary_markdown:$summary_md}' > "${CONFIG}"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/monitor_gpu_health.py --config '${CONFIG}'"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" --arg config "${CONFIG}" --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg samples "${SAMPLES}" --arg summary_json "${SUMMARY_JSON}" --arg summary_md "${SUMMARY_MD}" --arg log "${LOG}" '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"gpu_health_monitor",node:"login",observed_nodes:["an12","an21","an29"],gpu_ids:[],gpu_allocation:[],tensor_parallel_width:0,replica_count:0,placement_justification:"Read-only login-node sampler observes all 24 GPUs, host memory, and reported compute processes over SSH; it never sends process signals.",git_hash:$git_hash,config_path:$config,config_hash:$config_hash,data_manifest_hash:$config_hash,seed:null,command:$command,start_time_utc:$started,end_time_utc:null,status:"running",stdout_stderr_log:$log,expected_artifacts:[$samples,$summary_json,$summary_md],duration_seconds:3600,interval_seconds:30,scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 3
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "monitor exited during startup" >&2; exit 1; }
printf '%s\nsummary=%s\n' "${RUN_DIR}" "${SUMMARY_MD}"
