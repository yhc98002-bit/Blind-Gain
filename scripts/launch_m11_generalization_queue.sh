#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/m11_generalization_v1.json"
RUNTIME_AUDIT="reports/m11_runtime_audit_v1.json"
RUNTIME_FREEZE="reports/m11_runtime_freeze_v1.txt"
cd "${ROOT}"
if [[ ! -s "${CONFIG}" ]]; then
  echo "M11 queue config is absent" >&2
  exit 2
fi
if ! git diff --quiet HEAD -- \
  "${CONFIG}" \
  scripts/launch_m11_generalization_queue.sh \
  scripts/run_m11_generalization_queue.py \
  scripts/launch_nonqwen_fliptrack_eval.sh \
  scripts/launch_nonqwen_blind_sample.sh \
  scripts/eval_nonqwen_fliptrack.py \
  scripts/eval_nonqwen_blind_sample.py \
  src/eval/nonqwen_adapters.py; then
  echo "critical M11 queue code or config differs from HEAD" >&2
  exit 2
fi
if [[ ! -s "${RUNTIME_AUDIT}" || ! -s "${RUNTIME_FREEZE}" ]] || ! jq -e \
  '(.status == "pass") and (.checks | type == "object" and all(. == true))' \
  "${RUNTIME_AUDIT}" >/dev/null; then
  echo "M11 isolated runtime audit is absent or non-pass" >&2
  exit 2
fi
if [[ "$(jq -r '.freeze_sha256' "${RUNTIME_AUDIT}")" != "$(sha256sum "${RUNTIME_FREEZE}" | awk '{print $1}')" ]]; then
  echo "M11 runtime freeze hash does not match its machine audit" >&2
  exit 2
fi
while IFS= read -r ACTIVE_MANIFEST; do
  if jq -e '(.job_type == "m11_generalization_queue") and (.status == "running")' \
    "${ACTIVE_MANIFEST}" >/dev/null; then
    echo "active M11 queue already exists: ${ACTIVE_MANIFEST}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -type f -name run_manifest.json | sort)
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
RUNTIME_AUDIT_HASH="$(sha256sum "${RUNTIME_AUDIT}" | awk '{print $1}')"
RUNTIME_FREEZE_HASH="$(sha256sum "${RUNTIME_FREEZE}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m11_generalization_queue.py --config '${CONFIG_SNAPSHOT}' --run-dir '${RUN_DIR}'"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg config "${CONFIG_SNAPSHOT}" \
  --arg runtime_audit "${RUNTIME_AUDIT}" --arg runtime_audit_hash "${RUNTIME_AUDIT_HASH}" \
  --arg runtime_freeze "${RUNTIME_FREEZE}" --arg runtime_freeze_hash "${RUNTIME_FREEZE_HASH}" \
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
    placement_justification: "Login-only scheduler launches child TP1 jobs only after a GPU is below the registered memory/utilization ceilings for two consecutive polls.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    runtime_audit: $runtime_audit,
    runtime_audit_sha256: $runtime_audit_hash,
    runtime_freeze: $runtime_freeze,
    runtime_freeze_sha256: $runtime_freeze_hash,
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
