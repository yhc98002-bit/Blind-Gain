#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 R20_QUEUE_RUN_DIR" >&2
  exit 2
fi

R20_QUEUE_RUN_DIR="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/l10_layer1_queue_v1.json"
UPSTREAM_STATE="${R20_QUEUE_RUN_DIR}/queue_state.json"
if [[ ! -f "${ROOT}/${UPSTREAM_STATE}" ]]; then
  echo "Missing R20 queue state: ${UPSTREAM_STATE}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="l10_layer1_queue_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
STATE="${RUN_DIR}/queue_state.json"
LOG="${RUN_DIR}/logs/login.log"
LAUNCHER_LOG="${RUN_DIR}/logs/launcher.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
COMMAND="PYTHONUNBUFFERED=1 .venv/bin/python scripts/run_l10_layer1_queue.py --config ${CONFIG} --upstream-state ${UPSTREAM_STATE} --state ${STATE}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${CONFIG}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg upstream "${UPSTREAM_STATE}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg state "${STATE}" \
  '{
    run_id: $run_id,
    job_type: "l10_layer1_base_evaluation_queue",
    node: "login orchestrating an12",
    gpu_allocation: "an12:4,5,6,7 after R20 release",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: $config,
    data_manifest_hash: $config_hash,
    upstream_state: $upstream,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$state]
  }' > "${MANIFEST}"

nohup setsid --wait "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py \
  "${MANIFEST}" "${LOG}" >"${LAUNCHER_LOG}" 2>&1 </dev/null &
LAUNCH_PID="$!"
echo "${LAUNCH_PID}" > "${PID_FILE}"
sleep 1
if ! kill -0 "${LAUNCH_PID}" 2>/dev/null; then
  if [[ "$(jq -r .status "${MANIFEST}")" == "running" ]]; then
    "${ROOT}/.venv/bin/python" scripts/finalize_run_manifest.py "${MANIFEST}" 1
  fi
  echo "L10 queue failed its startup liveness check; inspect ${LAUNCHER_LOG}" >&2
  exit 1
fi
printf '%s\n' "${RUN_DIR}"
