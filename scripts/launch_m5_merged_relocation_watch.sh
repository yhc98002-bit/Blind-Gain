#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <m5-training-run-dir>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_RUN="$1"
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
[[ "$(jq -r '.job_type // ""' "${TRAINING_MANIFEST}")" == "m5_anchor_longhorizon_400" ]] || exit 2
PARENT_ID="$(jq -er '.run_id' "${TRAINING_MANIFEST}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_MANIFEST}")"
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_ID}"
MARKER_DIR="${ROOT}/${TRAINING_RUN}/evaluations"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_merged_relocation_watch_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_m5_merged_relocation.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-label m5_anchor_longhorizon_400 --evaluation-marker-dir ${MARKER_DIR}"
mkdir -p "${RUN_DIR}/logs" "${MARKER_DIR}"
jq -n --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg root "${RUN_ROOT}" --arg archive "${ARCHIVE_ROOT}" \
  --arg markers "${MARKER_DIR}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_merged_relocation_watch",
    parent_training_run:$parent,node:"login",gpu_ids:[],gpu_allocation:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only relocation queue waits for independent evaluation markers; relocation refusal cannot block evaluation.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$parent,data_manifest_hash:$config_hash,
    seed:1,command:$command,start_time_utc:$start,end_time_utc:null,status:"running",
    run_root:$root,archive_root:$archive,evaluation_marker_dir:$markers,stdout_stderr_log:$log,
    expected_artifacts:[($archive+"/global_step_350/actor/huggingface/merged_checkpoint.source.sha256")],
    retained_final_step:400,scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"
tmux new-session -d -s "${RUN_ID}" ".venv/bin/python scripts/run_manifest_job.py '${MANIFEST}' '${LOG}'"
printf '%s\n' "${RUN_DIR}"
