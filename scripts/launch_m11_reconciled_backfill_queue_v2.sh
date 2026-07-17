#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/m11_generalization_reconciled_backfill_v2.json"
cd "${ROOT}"

CRITICAL_FILES=(
  "${CONFIG}"
  scripts/launch_m11_reconciled_backfill_queue_v2.sh
  scripts/run_m11_reconciled_backfill_queue.py
  scripts/run_m11_generalization_queue.py
  scripts/launch_nonqwen_fliptrack_eval.sh
  scripts/launch_nonqwen_blind_sample.sh
  scripts/eval_nonqwen_fliptrack.py
  scripts/eval_nonqwen_blind_sample.py
  src/eval/conditioned_inputs.py
  src/eval/nonqwen_adapters.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "critical M11 V2 reconciliation code or config differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical M11 V2 reconciliation file: ${FILE}" >&2
    exit 2
  }
done

PYTHONPATH=. .venv/bin/python scripts/run_m11_reconciled_backfill_queue.py \
  --config "${CONFIG}" --preflight-only >/dev/null

while IFS= read -r ACTIVE_MANIFEST; do
  if jq -e '(.job_type == "m11_generalization_reconciled_backfill_queue_v2") and (.status == "running")' \
    "${ACTIVE_MANIFEST}" >/dev/null 2>&1; then
    echo "active M11 V2 reconciliation queue already exists: ${ACTIVE_MANIFEST}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -type f -name run_manifest.json | sort)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_reconciled_backfill_v2_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
CONFIG_SNAPSHOT="${RUN_DIR}/config.json"
.venv/bin/python scripts/storage_guard.py --tier S --path "${RUN_DIR}" \
  --operation m11_reconciliation_v2 --required-bytes 100000000
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
cp "${CONFIG}" "${CONFIG_SNAPSHOT}"
CONFIG_HASH="$(sha256sum "${CONFIG_SNAPSHOT}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m11_reconciled_backfill_queue.py --config '${CONFIG_SNAPSHOT}' --run-dir '${RUN_DIR}'"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg config "${CONFIG_SNAPSHOT}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_generalization_reconciled_backfill_queue_v2",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "Login-only V2 watcher reconciles all 18 immutable cells, including the repaired InternVL real-image run, without reading performance values or launching GPU work.",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: $config,
    data_manifest_hash: $config_hash,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: [],
    supersedes_failed_queue: "experiments/runs/m11_reconciled_backfill_login_20260716T172041Z"
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "M11 V2 reconciliation queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
