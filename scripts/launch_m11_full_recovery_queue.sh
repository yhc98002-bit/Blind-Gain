#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/m11_generalization_recovery_v2.json"
RUNTIME_AUDIT="reports/m11_runtime_audit_v2.json"
RUNTIME_FREEZE="reports/m11_runtime_freeze_v2.txt"
cd "${ROOT}"

CRITICAL_FILES=(
  "${CONFIG}"
  scripts/launch_m11_full_recovery_queue.sh
  scripts/run_m11_full_recovery_queue.py
  scripts/run_m11_generalization_queue.py
  scripts/launch_nonqwen_fliptrack_eval.sh
  scripts/launch_nonqwen_blind_sample.sh
  scripts/eval_nonqwen_fliptrack.py
  scripts/eval_nonqwen_blind_sample.py
  src/eval/nonqwen_adapters.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "critical M11 recovery code or config differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical M11 recovery file: ${FILE}" >&2
    exit 2
  }
done
if [[ ! -s "${RUNTIME_AUDIT}" || ! -s "${RUNTIME_FREEZE}" ]] || ! jq -e \
  '(.status == "pass") and (.schema_version == "blind-gains.m11-runtime-audit.v2") and (.checks | type == "object" and all(. == true))' \
  "${RUNTIME_AUDIT}" >/dev/null; then
  echo "M11 isolated runtime audit is absent or non-pass" >&2
  exit 2
fi
if [[ "$(jq -r '.freeze_sha256' "${RUNTIME_AUDIT}")" != "$(sha256sum "${RUNTIME_FREEZE}" | awk '{print $1}')" ]]; then
  echo "M11 runtime freeze hash does not match its machine audit" >&2
  exit 2
fi
PYTHONPATH=. .venv/bin/python scripts/run_m11_full_recovery_queue.py \
  --config "${CONFIG}" --preflight-only >/dev/null

while IFS= read -r ACTIVE_MANIFEST; do
  if jq -e '(.job_type | startswith("m11_generalization")) and (.status == "running")' \
    "${ACTIVE_MANIFEST}" >/dev/null 2>&1; then
    echo "active M11 queue already exists: ${ACTIVE_MANIFEST}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -type f -name run_manifest.json | sort)

MACHINE="$(jq -r '.outputs.machine' "${CONFIG}")"
MARKDOWN="$(jq -r '.outputs.markdown' "${CONFIG}")"
if [[ -e "${MACHINE}" || -e "${MARKDOWN}" ]]; then
  echo "refusing M11 recovery because final outputs already exist" >&2
  exit 73
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_generalization_full_recovery_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
CONFIG_SNAPSHOT="${RUN_DIR}/config.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
cp "${CONFIG}" "${CONFIG_SNAPSHOT}"
CONFIG_HASH="$(sha256sum "${CONFIG_SNAPSHOT}" | awk '{print $1}')"
RUNTIME_AUDIT_HASH="$(sha256sum "${RUNTIME_AUDIT}" | awk '{print $1}')"
RUNTIME_FREEZE_HASH="$(sha256sum "${RUNTIME_FREEZE}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m11_full_recovery_queue.py --config '${CONFIG_SNAPSHOT}' --run-dir '${RUN_DIR}'"

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
    job_type: "m11_generalization_full_recovery_queue",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "Login-only watchdog validates six pinned smoke cells and waits for all four M2 step-100 evaluation markers before launching independent TP1 full cells on an29.",
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
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "M11 full recovery queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
