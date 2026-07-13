#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <an12|an29> <pilot-resume-training-run-dir>" >&2
  exit 2
fi
NODE="$1"
TRAINING_RUN="$2"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
MANIFEST_IN="${TRAINING_RUN}/run_manifest.json"

[[ -f "${MANIFEST_IN}" ]] || { echo "resume parent manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${MANIFEST_IN}")" == "l13_mechanical_pilot_arm" ]] || { echo "not a pilot parent" >&2; exit 2; }
[[ "$(jq -r '.arm' "${MANIFEST_IN}")" == "a3_caption" ]] || { echo "not the A3 arm" >&2; exit 2; }
[[ "$(jq -r '.resumed_from_global_step' "${MANIFEST_IN}")" == "20" ]] || { echo "parent is not a step-20 resume" >&2; exit 2; }
[[ "$(jq -r '.node' "${MANIFEST_IN}")" == "${NODE}" ]] || { echo "node mismatch" >&2; exit 2; }
[[ "$(jq -r '.status' "${MANIFEST_IN}")" == "running" ]] || { echo "resume parent is not running" >&2; exit 2; }

PARENT_RUN_ID="$(jq -er '.run_id' "${MANIFEST_IN}")"
RUN_LABEL="$(jq -er '.arm_run_name' "${MANIFEST_IN}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${MANIFEST_IN}")"
[[ "${RUN_ROOT}" == "${ROOT}/checkpoints/pilot/mech_a3_caption_resume20" ]] || { echo "unapproved resume checkpoint root" >&2; exit 2; }
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}"
STEP60_MARKER="${ROOT}/${TRAINING_RUN}/step60_fliptrack_complete.json"
CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_pilot_resume_checkpoints import resume_code_bundle_hash; print(resume_code_bundle_hash())')"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_resume_checkpoint_watch_${RUN_LABEL}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_resume_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${MANIFEST_IN} --node ${NODE} --run-label ${RUN_LABEL} --step60-evaluation-marker ${STEP60_MARKER} --expected-code-hash ${CODE_HASH}"

jq -n \
  --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CODE_HASH}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${MANIFEST_IN}")" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg root "${RUN_ROOT}" \
  --arg archive "${ARCHIVE_ROOT}" --arg marker "${STEP60_MARKER}" \
  --arg final_index "${RUN_ROOT}/global_step_100/actor/huggingface/model.safetensors.index.json" \
  --arg final_raw "${RUN_ROOT}/global_step_100/actor/RAW_STATE_RELOCATED.json" \
  '{
    schema_version: "blind-gains.run-manifest.v1", run_id: $run_id,
    job_type: "pilot_resume_checkpoint_retention_watch", parent_training_run: $parent,
    node: "login", compute_node: $node, gpu_ids: [], gpu_allocation: [],
    tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only login watcher handles immutable resumed checkpoints; it never signals GPU jobs.",
    git_hash: $git_hash, config_hash: $config_hash, data_manifest_hash: $data_hash,
    seed: 1, command: $command, start_time_utc: $started, end_time_utc: null,
    status: "running", run_root: $root, archive_root: $archive,
    raw_retention: "latest raw state only", resume_schedule: [40,60,80,100],
    step60_evaluation_marker: $marker, expected_artifacts: [$final_index, $final_raw], deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "resume watcher exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
