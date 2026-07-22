#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <base-config.json> <r19-queue-run>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
BASE_CONFIG="$(realpath -m "$1")"
R19_QUEUE_RUN="$(realpath -m "$2")"
case "${BASE_CONFIG}" in
  "${ROOT}"/configs/eval/*.json) ;;
  *) echo "base config must be under configs/eval" >&2; exit 2 ;;
esac
case "${R19_QUEUE_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "R19 queue run must be under experiments/runs" >&2; exit 2 ;;
esac
[[ -f "${BASE_CONFIG}" && -f "${R19_QUEUE_RUN}/run_manifest.json" ]] || {
  echo "base config or R19 queue manifest absent" >&2
  exit 2
}

CRITICAL_FILES=(
  scripts/run_pilot_geo3k_step100_queue.py
  scripts/launch_pilot_followup_geo3k_queue.sh
  scripts/launch_pilot_geo3k_step100_eval.sh
  scripts/run_pilot_geo3k_step100_eval.py
  scripts/launch_pilot_geo3k_step100_audit.sh
  scripts/audit_pilot_geo3k_step100_eval.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "pilot follow-up Geometry3K queue code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${FILE}" >&2
    exit 2
  }
done

SCHEMA="$(jq -er .schema_version "${BASE_CONFIG}")"
[[ "${SCHEMA}" == "blind-gains.pilot-followup-geo3k-queue.v1" ]] || {
  echo "base config is not a follow-up Geometry3K queue" >&2
  exit 2
}
ARM="$(jq -er .arm "${BASE_CONFIG}")"
SEED="$(jq -er .seed "${BASE_CONFIG}")"
GLOBAL_STEP="$(jq -er .global_step "${BASE_CONFIG}")"
NODE="$(jq -er .node "${BASE_CONFIG}")"
GPU="$(jq -er .gpu_id "${BASE_CONFIG}")"
TRAINING_RUN="$(jq -er .training_run "${BASE_CONFIG}")"
COMPLETION_MARKER="${TRAINING_RUN}/step${GLOBAL_STEP}_geo3k_complete.json"
jq -e \
  --arg arm "${ARM}" \
  --argjson seed "${SEED}" --argjson global_step "${GLOBAL_STEP}" \
  '(.job_type == "pilot_followup_r19_evaluation_queue") and
   (.arm == $arm) and (.pilot_seed == $seed) and (.global_step == $global_step)' \
  "${R19_QUEUE_RUN}/run_manifest.json" >/dev/null || {
    echo "R19 queue identity does not match the Geometry3K endpoint" >&2
    exit 2
  }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_followup_geo3k_queue_${ARM}_seed${SEED}_step${GLOBAL_STEP}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${RUN_DIR}/config.json"
STATE="${RUN_DIR}/state.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq \
  --arg r19_queue_run "${R19_QUEUE_RUN#"${ROOT}/"}" \
  --arg state_path "${STATE}" \
  --arg completion_marker "${COMPLETION_MARKER}" \
  '. + {
    r19_queue_run: $r19_queue_run,
    state_path: $state_path,
    completion_marker: $completion_marker
  }' \
  "${BASE_CONFIG}" > "${CONFIG}"

PYTHONPATH=. .venv/bin/python -c \
  'import json,sys; from pathlib import Path; from scripts.run_pilot_geo3k_step100_queue import validate_config; validate_config(json.loads(Path(sys.argv[1]).read_text()), Path.cwd())' \
  "${CONFIG}"

MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_geo3k_step100_queue.py --config '${CONFIG}'"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
R19_MARKER="$(jq -er .r19_marker "${CONFIG}")"
COMPLETION_MARKER="$(jq -er .completion_marker "${CONFIG}")"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" \
  --arg config "${CONFIG}" --arg state "${STATE}" \
  --arg r19_marker "${R19_MARKER}" --arg completion_marker "${COMPLETION_MARKER}" \
  --arg r19_queue "${R19_QUEUE_RUN#"${ROOT}/"}" --arg log "${LOG}" \
  --arg arm "${ARM}" \
  --arg node "${NODE}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson gpu "${GPU}" --argjson pilot_seed "${SEED}" \
  --argjson global_step "${GLOBAL_STEP}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_followup_geo3k_evaluation_queue",
    arm: $arm,
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    target_node: $node,
    target_gpu_ids: [$gpu],
    child_tensor_parallel_width: 1,
    child_replica_count: 1,
    pilot_seed: $pilot_seed,
    global_step: $global_step,
    placement_justification: "CPU-only queue waits for the exact R19 marker and one free evaluation GPU; its TP1 child emits a 601-row locked evaluation followed by a CPU-only recomputation audit.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $config,
    data_manifest_hash: $config_hash,
    seed: 0,
    command: $command,
    source_r19_queue: $r19_queue,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    source_r19_marker: $r19_marker,
    expected_artifacts: [$state, $completion_marker],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "pilot follow-up Geometry3K queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
