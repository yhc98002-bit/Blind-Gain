#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/m11_generalization_v1.json"
cd "${ROOT}"
if [[ ! -s "${CONFIG}" ]]; then
  echo "M11 queue config is absent" >&2
  exit 2
fi
MACHINE="$(jq -r '.outputs.machine' "${CONFIG}")"
MARKDOWN="$(jq -r '.outputs.markdown' "${CONFIG}")"
if [[ -e "${MACHINE}" || -e "${MARKDOWN}" ]]; then
  echo "refusing M11 queue because final outputs already exist" >&2
  exit 73
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_generalization_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/queue_state.json"
CONFIG_SNAPSHOT="${RUN_DIR}/config.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
cp "${CONFIG}" "${CONFIG_SNAPSHOT}"
CONFIG_HASH="$(sha256sum "${CONFIG_SNAPSHOT}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m11_generalization_queue.py --config '${CONFIG_SNAPSHOT}' --run-dir '${RUN_DIR}'"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg config "${CONFIG_SNAPSHOT}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg machine "${MACHINE}" \
  --arg markdown "${MARKDOWN}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_generalization_queue",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: null,
    replica_count: 0,
    placement_justification: "Login-only scheduler waits for M2 and launches child TP1 jobs on free GPUs of one configured node.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: $config_hash,
    config_path: $config,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state, $machine, $markdown],
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
