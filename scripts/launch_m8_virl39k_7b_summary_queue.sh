#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 BASE_CONFIG_JSON" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
BASE_CONFIG="$(realpath -m "$1")"
case "${BASE_CONFIG}" in
  "${ROOT}"/configs/eval/*.json) ;;
  *) echo "base config must be under configs/eval" >&2; exit 2 ;;
esac
[[ -s "${BASE_CONFIG}" ]] || { echo "base config is absent" >&2; exit 2; }

CRITICAL_FILES=(
  scripts/run_m8_virl39k_7b_summary_queue.py
  scripts/launch_m8_virl39k_7b_summary_queue.sh
  scripts/launch_virl39k_7b_blind_v1_summary.sh
  scripts/summarize_blind_solvability_virl39k_v1.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "M8 queue code differs from HEAD" >&2
  exit 2
}
for file in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${file}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${file}" >&2
    exit 2
  }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m8_virl39k_7b_summary_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${RUN_DIR}/config.json"
STATE="${RUN_DIR}/state.json"
LOG="${RUN_DIR}/logs/login.log"
MANIFEST="${RUN_DIR}/run_manifest.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq --arg state_path "${STATE}" '. + {state_path: $state_path}' "${BASE_CONFIG}" > "${CONFIG}"
PYTHONPATH=. .venv/bin/python -c \
  'import json,sys; from pathlib import Path; from scripts.run_m8_virl39k_7b_summary_queue import validate_config; validate_config(json.loads(Path(sys.argv[1]).read_text()), Path.cwd())' \
  "${CONFIG}"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_m8_virl39k_7b_summary_queue.py --config ${CONFIG}"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(sha256sum "${CONFIG}" | awk '{print $1}')" \
  --arg data_hash "$(sha256sum "${CONFIG}" "${BASE_CONFIG}" | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg config "${CONFIG}" \
  --arg state "${STATE}" \
  --arg log "${LOG}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id, job_type: "m8_virl39k_7b_summary_queue",
    node: "login", gpu_allocation: [], gpu_ids: [],
    tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only fail-closed watcher for five exact M8 runs and their deterministic summary audit; it sends no process signals.",
    git_hash: $git_hash, config_hash: $config_hash,
    data_manifest: $config, data_manifest_hash: $data_hash,
    command: $command, start_time_utc: $started, end_time_utc: null,
    status: "running", stdout_stderr_log: $log,
    expected_artifacts: [$state],
    performance_values_inspected: false,
    scientific_gate_decision: null, deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "M8 summary queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
