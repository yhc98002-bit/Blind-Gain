#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 6 && $# -ne 8 ]]; then
  echo "usage: $0 SOURCE_RUN GLOBAL_STEP CHECKPOINT GEO3K_RUN R19_RUN MARKER [GRAY_RUN NOISE_RUN]" >&2
  exit 2
fi

SOURCE_RUN="$1"
GLOBAL_STEP="$2"
CHECKPOINT="$3"
GEO3K_RUN="$4"
R19_RUN="$5"
MARKER="$6"
GRAY_RUN="${7:-}"
NOISE_RUN="${8:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ "${GLOBAL_STEP}" =~ ^(150|200|300|400)$ ]] || { echo "invalid M5 evaluation step" >&2; exit 2; }
if [[ "${GLOBAL_STEP}" == "400" ]]; then
  [[ -n "${GRAY_RUN}" && -n "${NOISE_RUN}" ]] || { echo "step 400 requires gray and noise runs" >&2; exit 2; }
else
  [[ -z "${GRAY_RUN}" && -z "${NOISE_RUN}" ]] || { echo "blind-floor runs are only valid at step 400" >&2; exit 2; }
fi

cd "${ROOT}"
for path in scripts/watch_m5_step_evaluation.py scripts/finalize_m5_step_evaluation.py \
  scripts/launch_m5_step_evaluation_watch.sh docs/registered_extensions_v1.md; do
  git ls-files --error-unmatch "${path}" >/dev/null 2>&1 || {
    echo "M5 evaluation watcher contract file is untracked: ${path}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- scripts/watch_m5_step_evaluation.py scripts/finalize_m5_step_evaluation.py \
  scripts/launch_m5_step_evaluation_watch.sh docs/registered_extensions_v1.md || {
  echo "M5 evaluation watcher contract differs from HEAD" >&2; exit 3;
}
for path in "${SOURCE_RUN}/run_manifest.json" "${CHECKPOINT}/model.safetensors.index.json" \
  "${GEO3K_RUN}/run_manifest.json" "${R19_RUN}/run_manifest.json"; do
  [[ -s "${path}" ]] || { echo "M5 watcher input absent: ${path}" >&2; exit 2; }
done
if [[ -n "${GRAY_RUN}" ]]; then
  [[ -s "${GRAY_RUN}/run_manifest.json" && -s "${NOISE_RUN}/run_manifest.json" ]] || {
    echo "M5 blind-floor watcher input absent" >&2; exit 2;
  }
fi
[[ ! -e "${MARKER}" ]] || { echo "refusing to overwrite M5 evaluation marker" >&2; exit 73; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_step${GLOBAL_STEP}_evaluation_watch_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/state.json"
TAG_BASE="m5_step${GLOBAL_STEP}_$(basename "${SOURCE_RUN}" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9_-')"
COMMAND="PYTHONPATH=${ROOT} .venv/bin/python scripts/watch_m5_step_evaluation.py --geo3k-run ${GEO3K_RUN} --r19-evaluation-run ${R19_RUN} --source-run ${SOURCE_RUN} --checkpoint-path ${CHECKPOINT} --global-step ${GLOBAL_STEP} --aggregate-tag ${TAG_BASE}_real --marker ${MARKER} --state ${STATE} --poll-seconds 60"
if [[ "${GLOBAL_STEP}" == "400" ]]; then
  COMMAND+=" --gray-evaluation-run ${GRAY_RUN} --gray-aggregate-tag ${TAG_BASE}_gray --noise-evaluation-run ${NOISE_RUN} --noise-aggregate-tag ${TAG_BASE}_noise"
fi
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$({ sha256sum "${SOURCE_RUN}/run_manifest.json" "${CHECKPOINT}/model.safetensors.index.json" \
  "${GEO3K_RUN}/run_manifest.json" "${R19_RUN}/run_manifest.json"; \
  if [[ -n "${GRAY_RUN}" ]]; then sha256sum "${GRAY_RUN}/run_manifest.json" "${NOISE_RUN}/run_manifest.json"; fi; } \
  | sort -k2 | sha256sum | awk '{print $1}')"
GPU_RUNS_JSON="$(printf '%s\n' "${GEO3K_RUN}" "${R19_RUN}" | jq -Rsc 'split("\n")[:-1]')"
if [[ -n "${GRAY_RUN}" ]]; then
  GPU_RUNS_JSON="$(printf '%s\n' "${GEO3K_RUN}" "${R19_RUN}" "${GRAY_RUN}" "${NOISE_RUN}" | jq -Rsc 'split("\n")[:-1]')"
fi
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" --arg source_run "${SOURCE_RUN}" --arg checkpoint "${CHECKPOINT}" \
  --arg marker "${MARKER}" --arg state "${STATE}" --arg command "${COMMAND}" --arg log "${LOG}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --argjson step "${GLOBAL_STEP}" \
  --argjson gpu_runs "${GPU_RUNS_JSON}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_step_evaluation_watch",
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only watcher waits for immutable M5 GPU evaluation artifacts, aggregates cached predictions, and emits a structural completion marker without opening performance values.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$source_run,data_manifest_hash:$data_hash,
    source_training_run:$source_run,checkpoint_path:$checkpoint,global_step:$step,gpu_evaluation_runs:$gpu_runs,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$marker,$state],performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' \
  > "${RUN_MANIFEST}"

nohup setsid --wait "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py \
  "${RUN_MANIFEST}" "${LOG}" >/dev/null 2>&1 </dev/null &
echo "$!" > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
