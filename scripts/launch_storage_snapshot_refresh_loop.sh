#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
while IFS= read -r manifest; do
  if jq -e '(.job_type == "storage_snapshot_refresh_loop") and (.status == "running")' \
    "${manifest}" >/dev/null; then
    pid_file="$(dirname "${manifest}")/pids/login.pid"
    if [[ -s "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
      echo "active storage snapshot refresher exists: ${manifest}" >&2
      exit 73
    fi
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -type f -name run_manifest.json | sort)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="storage_snapshot_refresh_loop_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/state.json"
HISTORY="${RUN_DIR}/snapshots"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_storage_snapshot_refresh_loop.py --history-dir '${HISTORY}' --state '${STATE}' --initial-delay-seconds 7200 --interval-seconds 10800 --retry-seconds 600"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${HISTORY}"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(sha256sum scripts/run_storage_snapshot_refresh_loop.py | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg state "${STATE}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "storage_snapshot_refresh_loop",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "Login-node CPU quota measurement keeps the shared checkpoint snapshot fresh; no GPU is required.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: null,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [$state, "reports/storage_usage_snapshot.json"],
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
