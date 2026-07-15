#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: $0 <evaluation-run> <training-run> <global-step> <marker> <aggregate-tag>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
EVALUATION_RUN="$(realpath -m "$1")"
TRAINING_RUN="$(realpath -m "$2")"
GLOBAL_STEP="$3"
MARKER="$(realpath -m "$4")"
AGGREGATE_TAG="$5"

for PATH_VALUE in "${EVALUATION_RUN}" "${TRAINING_RUN}"; do
  case "${PATH_VALUE}" in
    "${ROOT}"/experiments/runs/*) ;;
    *) echo "evaluation and training runs must be under experiments/runs" >&2; exit 2 ;;
  esac
done
[[ "${GLOBAL_STEP}" == "60" || "${GLOBAL_STEP}" == "100" ]] || { echo "global step must be 60 or 100" >&2; exit 2; }
[[ "${AGGREGATE_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || { echo "invalid aggregate tag" >&2; exit 2; }
[[ -f "${EVALUATION_RUN}/run_manifest.json" && -f "${TRAINING_RUN}/run_manifest.json" ]] || { echo "source manifest absent" >&2; exit 2; }
EXPECTED_MARKER="${TRAINING_RUN}/step${GLOBAL_STEP}_fliptrack_complete.json"
[[ "${MARKER}" == "${EXPECTED_MARKER}" ]] || { echo "marker path is not bound to the training run and step" >&2; exit 2; }
[[ ! -e "${MARKER}" ]] || { echo "marker already exists" >&2; exit 73; }

while IFS= read -r ACTIVE_MANIFEST; do
  [[ "$(jq -r '.job_type // ""' "${ACTIVE_MANIFEST}" 2>/dev/null)" == "pilot_step_evaluation_finalize_watch" ]] || continue
  [[ "$(jq -r '.status // ""' "${ACTIVE_MANIFEST}" 2>/dev/null)" == "running" ]] || continue
  [[ "$(realpath -m "$(jq -r '.expected_artifacts[1] // ""' "${ACTIVE_MANIFEST}")")" == "${MARKER}" ]] || continue
  ACTIVE_PID_FILE="$(dirname "${ACTIVE_MANIFEST}")/pids/login.pid"
  if [[ -f "${ACTIVE_PID_FILE}" ]] && kill -0 "$(cat "${ACTIVE_PID_FILE}")" 2>/dev/null; then
    echo "active finalization watcher already owns marker: ${MARKER}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -print)

CRITICAL_FILES=(
  scripts/watch_pilot_step_evaluation.py
  scripts/launch_pilot_step_evaluation_watch.sh
  scripts/finalize_pilot_step_evaluation.py
  scripts/launch_fliptrack_aggregate.sh
  scripts/aggregate_fliptrack_eval.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || { echo "pilot evaluation watcher code differs from HEAD" >&2; exit 2; }
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked critical file: ${FILE}" >&2; exit 2; }
done

CHECKPOINT_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_RUN}/run_manifest.json")"
CHECKPOINT="${CHECKPOINT_ROOT}/global_step_${GLOBAL_STEP}/actor/huggingface"
ARM="$(jq -er '.arm' "${TRAINING_RUN}/run_manifest.json")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_step_eval_finalize_watch_${ARM}_step${GLOBAL_STEP}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
STATE="${RUN_DIR}/state.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_step_evaluation.py --evaluation-run '${EVALUATION_RUN#"${ROOT}/"}' --training-run '${TRAINING_RUN#"${ROOT}/"}' --checkpoint-path '${CHECKPOINT}' --global-step ${GLOBAL_STEP} --aggregate-tag '${AGGREGATE_TAG}' --marker '${MARKER#"${ROOT}/"}' --state '${STATE}'"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CONFIG_HASH}" \
  --arg command "${COMMAND}" --arg evaluation "${EVALUATION_RUN#"${ROOT}/"}" \
  --arg training "${TRAINING_RUN#"${ROOT}/"}" --arg checkpoint "${CHECKPOINT}" \
  --arg marker "${MARKER#"${ROOT}/"}" --arg state "${STATE}" --arg log "${LOG}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --argjson global_step "${GLOBAL_STEP}" \
  '{
    schema_version: "blind-gains.run-manifest.v1", run_id: $run_id,
    job_type: "pilot_step_evaluation_finalize_watch", node: "login",
    gpu_ids: [], gpu_allocation: [], tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only login watcher waits for a pinned evaluation, aggregates it, and writes a fail-closed checkpoint marker; it sends no process signals.",
    git_hash: $git_hash, config_hash: $config_hash, data_manifest: ($evaluation + "/run_manifest.json"),
    data_manifest_hash: $config_hash, seed: 0, command: $command,
    source_evaluation_run: $evaluation, source_training_run: $training,
    checkpoint_path: $checkpoint, global_step: $global_step,
    start_time_utc: $started, end_time_utc: null, status: "running",
    stdout_stderr_log: $log, expected_artifacts: [$state, $marker],
    scientific_gate_decision: null, deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "pilot evaluation watcher exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
