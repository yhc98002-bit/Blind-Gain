#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <base-config.json>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
BASE_CONFIG="$(realpath -m "$1")"
case "${BASE_CONFIG}" in
  "${ROOT}"/configs/eval/*.json) ;;
  *) echo "base config must be under configs/eval" >&2; exit 2 ;;
esac
[[ -f "${BASE_CONFIG}" ]] || { echo "base config absent" >&2; exit 2; }

CRITICAL_FILES=(
  scripts/run_pilot_step100_eval_queue.py
  scripts/launch_pilot_step100_eval_queue.sh
  scripts/launch_fliptrack_eval_shards.sh
  scripts/launch_pilot_step_evaluation_watch.sh
  scripts/watch_pilot_step_evaluation.py
  scripts/finalize_pilot_step_evaluation.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "pilot step-100 queue code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${FILE}" >&2
    exit 2
  }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARM="$(jq -er .arm "${BASE_CONFIG}")"
NODE="$(jq -er .node "${BASE_CONFIG}")"
RUN_ID="pilot_step100_eval_queue_${ARM}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${RUN_DIR}/config.json"
STATE="${RUN_DIR}/state.json"
EVAL_RUN="experiments/runs/pilot_fliptrack_${ARM}_seed1_step100_real_${NODE}_${STAMP}"
AGGREGATE_TAG="m2_${ARM}_step100_${STAMP,,}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq \
  --arg evaluation_run "${EVAL_RUN}" \
  --arg aggregate_tag "${AGGREGATE_TAG}" \
  --arg state_path "${STATE}" \
  '. + {
    evaluation_run: $evaluation_run,
    aggregate_tag: $aggregate_tag,
    state_path: $state_path
  }' "${BASE_CONFIG}" > "${CONFIG}"

PYTHONPATH=. .venv/bin/python -c \
  'import json,sys; from pathlib import Path; from scripts.run_pilot_step100_eval_queue import validate_config; validate_config(json.loads(Path(sys.argv[1]).read_text()), Path.cwd())' \
  "${CONFIG}"

MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_step100_eval_queue.py --config '${CONFIG}'"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
GPU_IDS="$(jq -c .gpu_ids "${CONFIG}")"
MARKER="$(jq -er .marker "${CONFIG}")"
R19_HASH="$(jq -er .r19_manifest_sha256 "${CONFIG}")"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" \
  --arg config "${CONFIG}" --arg state "${STATE}" --arg marker "${MARKER}" \
  --arg evaluation "${EVAL_RUN}" --arg log "${LOG}" --arg node "${NODE}" \
  --arg r19_hash "${R19_HASH}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson target_gpu_ids "${GPU_IDS}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_step100_evaluation_queue",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    target_node: $node,
    target_gpu_ids: $target_gpu_ids,
    child_tensor_parallel_width: 1,
    child_replica_count: 4,
    placement_justification: "CPU-only queue observes pinned retention and capacity state; the child uses four independent TP1 replicas on one permanent node and sends no process signals.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $config,
    data_manifest_hash: $r19_hash,
    seed: 0,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state, $marker, ($evaluation + "/run_manifest.json")],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "pilot step-100 evaluation queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
