#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 QUEUE_RUN_DIR" >&2
  exit 2
fi

QUEUE_RUN_DIR="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUEUE_STATE="${QUEUE_RUN_DIR}/queue_state.json"
QUEUE_MANIFEST="${QUEUE_RUN_DIR}/run_manifest.json"
for REQUIRED in "${QUEUE_STATE}" "${QUEUE_MANIFEST}"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing R20 queue artifact: ${REQUIRED}" >&2
    exit 2
  fi
done
if [[ -e "${ROOT}/reports/fliptrack_r20_confirmatory.json" || -e "${ROOT}/reports/fliptrack_r20_confirmatory.md" ]]; then
  echo "R20 confirmatory output already exists" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="fliptrack_r20_finalize_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
STATE="${RUN_DIR}/finalizer_state.json"
LOG="${RUN_DIR}/logs/login.log"
LAUNCHER_LOG="${RUN_DIR}/logs/launcher.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
CONFIG_PATH="$(jq -r .config "${ROOT}/${QUEUE_STATE}")"
CONFIG_HASH="$(jq -r .config_sha256 "${ROOT}/${QUEUE_STATE}")"
COMMAND="PYTHONUNBUFFERED=1 .venv/bin/python scripts/finalize_fliptrack_r20_queue.py --queue-state ${QUEUE_STATE} --state ${STATE} --poll-seconds 60"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG_PATH}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg queue_run "${QUEUE_RUN_DIR}" \
  --arg queue_state "${QUEUE_STATE}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg state "${STATE}" \
  '{
    run_id: $run_id,
    job_type: "fliptrack_r20_confirmatory_finalizer",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only R20 finalization and report assembly on the login node.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    data_manifest: $config_path,
    data_manifest_hash: $config_hash,
    source_queue_run: $queue_run,
    source_queue_state: $queue_state,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [
      $state,
      "reports/fliptrack_r20_confirmatory.json",
      "reports/fliptrack_r20_confirmatory.md"
    ]
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
  echo "R20 finalizer failed its startup liveness check; inspect ${LAUNCHER_LOG}" >&2
  exit 1
fi
printf '%s\n' "${RUN_DIR}"
