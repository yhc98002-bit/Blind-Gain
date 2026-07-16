#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <an12|an29> <m5-training-run-dir>" >&2
  exit 2
fi
NODE="$1"
TRAINING_RUN="$2"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
[[ "$(jq -r '.job_type // ""' "${TRAINING_MANIFEST}")" == "m5_anchor_longhorizon_400" ]] || {
  echo "M5 watcher refuses a non-M5 parent" >&2; exit 2;
}
[[ "$(jq -r '.status // ""' "${TRAINING_MANIFEST}")" == "running" ]] || {
  echo "M5 watcher requires a running parent" >&2; exit 2;
}
[[ "$(jq -r '.node' "${TRAINING_MANIFEST}")" == "${NODE}" ]] || {
  echo "M5 watcher node differs from training node" >&2; exit 2;
}

PARENT_ID="$(jq -er '.run_id' "${TRAINING_MANIFEST}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_MANIFEST}")"
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_ID}"
CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_m5_checkpoints import m5_code_bundle_hash; print(m5_code_bundle_hash())')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_checkpoint_watch_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_m5_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${TRAINING_MANIFEST} --node ${NODE} --run-label m5_anchor_longhorizon_400 --expected-code-hash ${CODE_HASH}"
mkdir -p "${RUN_DIR}/logs"
jq -n --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CODE_HASH}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${TRAINING_MANIFEST}")" \
  --arg command "${COMMAND}" --arg root "${RUN_ROOT}" --arg archive "${ARCHIVE_ROOT}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_checkpoint_retention_watch",
    parent_training_run:$parent,node:"login",compute_node:$node,gpu_ids:[],gpu_allocation:[],
    tensor_parallel_width:0,replica_count:0,placement_justification:"CPU-only login watcher merges checkpoints and enforces latest-raw retention; evaluation is a separate queue.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$parent,data_manifest_hash:$data_hash,
    seed:1,command:$command,start_time_utc:$start,end_time_utc:null,status:"running",
    run_root:$root,archive_root:$archive,raw_retention:"latest raw state only",
    checkpoint_schedule:[150,200,250,300,350,400],stdout_stderr_log:$log,
    expected_artifacts:[($root+"/global_step_400/actor/huggingface/model.safetensors.index.json"),($root+"/global_step_400/actor/RAW_STATE_RELOCATED.json")],
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
tmux new-session -d -s "${RUN_ID}" ".venv/bin/python scripts/run_manifest_job.py '${MANIFEST}' '${LOG}'"
printf '%s\n' "${RUN_DIR}"
