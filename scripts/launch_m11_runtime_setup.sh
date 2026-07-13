#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
for path in .venv-m11 reports/m11_runtime_freeze_v1.txt reports/m11_runtime_audit_v1.json; do
  if [[ -e "${path}" ]]; then
    echo "M11 runtime artifact already exists: ${path}" >&2
    exit 73
  fi
done
if ! git diff --quiet HEAD -- \
  configs/env/m11_runtime_requirements.txt \
  scripts/setup_m11_runtime.sh \
  scripts/verify_m11_runtime.py; then
  echo "M11 runtime setup inputs differ from HEAD" >&2
  exit 2
fi

.venv/bin/python scripts/storage_guard.py \
  --tier S --path .venv-m11 --operation m11_isolated_runtime \
  --required-bytes 20000000000
.venv/bin/python scripts/storage_guard.py \
  --tier T --path /tmp/blind-gains-m11-pip-cache \
  --operation m11_runtime_download_cache --required-bytes 20000000000

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_runtime_setup_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
CONFIG_HASH="$(sha256sum configs/env/m11_runtime_requirements.txt scripts/setup_m11_runtime.sh scripts/verify_m11_runtime.py | sha256sum | awk '{print $1}')"
COMMAND="bash scripts/setup_m11_runtime.sh"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_isolated_runtime_setup",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "A login-node network/CPU job builds an isolated inference environment; it does not allocate a GPU or modify the pilot environment.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: null,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: ["reports/m11_runtime_freeze_v1.txt", "reports/m11_runtime_audit_v1.json"],
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
