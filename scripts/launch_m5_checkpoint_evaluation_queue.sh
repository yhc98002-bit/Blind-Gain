#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 SOURCE_RUN [STEPS_CSV]" >&2
  exit 2
fi

SOURCE_RUN="$1"
STEPS="${2:-200,300,400}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
R19_MANIFEST="experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
cd "${ROOT}"

[[ "${STEPS}" =~ ^(150|200|300|400)(,(150|200|300|400))*$ ]] || {
  echo "invalid M5 evaluation step list" >&2; exit 2;
}
for path in "${SOURCE_RUN}/run_manifest.json" "${R19_MANIFEST}" \
  scripts/run_m5_checkpoint_evaluation_queue.py scripts/launch_m5_checkpoint_evaluation_queue.sh \
  scripts/launch_m5_geo3k_checkpoint_eval.sh scripts/launch_m5_fliptrack_checkpoint_eval.sh \
  scripts/launch_m5_step_evaluation_watch.sh scripts/finalize_m5_step_evaluation.py \
  scripts/watch_m5_step_evaluation.py docs/registered_extensions_v1.md; do
  [[ -s "${path}" ]] || { echo "M5 evaluation queue input absent: ${path}" >&2; exit 2; }
done
for path in scripts/run_m5_checkpoint_evaluation_queue.py scripts/launch_m5_checkpoint_evaluation_queue.sh \
  scripts/launch_m5_geo3k_checkpoint_eval.sh scripts/launch_m5_fliptrack_checkpoint_eval.sh \
  scripts/launch_m5_step_evaluation_watch.sh scripts/finalize_m5_step_evaluation.py \
  scripts/watch_m5_step_evaluation.py docs/registered_extensions_v1.md; do
  git ls-files --error-unmatch "${path}" >/dev/null 2>&1 || {
    echo "M5 evaluation queue contract file is untracked: ${path}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- scripts/run_m5_checkpoint_evaluation_queue.py \
  scripts/launch_m5_checkpoint_evaluation_queue.sh scripts/launch_m5_geo3k_checkpoint_eval.sh \
  scripts/launch_m5_fliptrack_checkpoint_eval.sh scripts/launch_m5_step_evaluation_watch.sh \
  scripts/finalize_m5_step_evaluation.py scripts/watch_m5_step_evaluation.py \
  docs/registered_extensions_v1.md || {
  echo "M5 evaluation queue contract differs from HEAD" >&2; exit 3;
}

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_checkpoint_evaluation_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
STATE="${RUN_DIR}/queue_state.json"
COMMAND="PYTHONPATH=${ROOT} .venv/bin/python scripts/run_m5_checkpoint_evaluation_queue.py --run-dir ${RUN_DIR} --source-run ${SOURCE_RUN} --steps ${STEPS} --nodes an12,an29 --r19-manifest ${R19_MANIFEST} --poll-seconds 60 --stable-polls 2"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$({ sha256sum "${SOURCE_RUN}/run_manifest.json" "${R19_MANIFEST}" \
  docs/registered_extensions_v1.md scripts/run_m5_checkpoint_evaluation_queue.py; } \
  | sort -k2 | sha256sum | awk '{print $1}')"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" --arg source_run "${SOURCE_RUN}" --arg steps "${STEPS}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_checkpoint_evaluation_queue",
    node:"login",observed_nodes:["an12","an29"],gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,
    replica_count:0,placement_justification:"CPU-only scheduler waits for registered M5 merged checkpoints and two stable capacity polls, then launches single-node TP1 evaluation replicas without preemption.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$source_run,data_manifest_hash:$data_hash,
    source_training_run:$source_run,registered_steps:($steps|split(",")|map(tonumber)),command:$command,
    start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$state],performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' \
  > "${RUN_MANIFEST}"

nohup setsid --wait "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py \
  "${RUN_MANIFEST}" "${LOG}" >/dev/null 2>&1 </dev/null &
echo "$!" > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
