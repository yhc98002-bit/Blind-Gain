#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <an12|an29> <pilot-training-run-dir>" >&2
  exit 2
fi

NODE="$1"
TRAINING_RUN="$2"
if [[ "${NODE}" != "an12" && "${NODE}" != "an29" ]]; then
  echo "pilot checkpoint watcher requires one compute node" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
if [[ ! -f "${TRAINING_MANIFEST}" ]]; then
  echo "pilot training manifest is absent: ${TRAINING_MANIFEST}" >&2
  exit 2
fi
PARENT_JOB_TYPE="$(jq -r '.job_type' "${TRAINING_MANIFEST}")"
if [[ "${PARENT_JOB_TYPE}" != "l13_mechanical_pilot_arm" && "${PARENT_JOB_TYPE}" != "m3_mechanical_pilot_arm" ]]; then
  echo "checkpoint watcher refuses a non-pilot parent manifest" >&2
  exit 2
fi
if [[ "$(jq -r '.node' "${TRAINING_MANIFEST}")" != "${NODE}" ]]; then
  echo "checkpoint watcher node differs from parent training placement" >&2
  exit 2
fi
if [[ "$(jq -r '.status' "${TRAINING_MANIFEST}")" != "running" ]]; then
  echo "checkpoint watcher requires a running pilot parent" >&2
  exit 2
fi

PARENT_RUN_ID="$(jq -er '.run_id' "${TRAINING_MANIFEST}")"
RUN_LABEL="$(jq -er '.arm_run_name' "${TRAINING_MANIFEST}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_MANIFEST}")"
EXPECTED_PREFIX="${ROOT}/checkpoints/pilot/"
if [[ "${RUN_ROOT}" != "${EXPECTED_PREFIX}"* ]]; then
  echo "pilot checkpoint root is outside the approved shared namespace" >&2
  exit 2
fi
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}"
STEP60_MARKER="${ROOT}/${TRAINING_RUN}/step60_fliptrack_complete.json"
EXPECTED_CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_pilot_checkpoints import pilot_code_bundle_hash; print(pilot_code_bundle_hash())')"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_checkpoint_watch_${RUN_LABEL}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SESSION="${RUN_ID}"
mkdir -p "${RUN_DIR}/logs"
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "pilot checkpoint watcher session already exists: ${SESSION}" >&2
  exit 73
fi

COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${TRAINING_MANIFEST} --node ${NODE} --run-label ${RUN_LABEL} --step60-evaluation-marker ${STEP60_MARKER} --expected-code-hash ${EXPECTED_CODE_HASH}"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg parent_run "${TRAINING_RUN}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${EXPECTED_CODE_HASH}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${TRAINING_MANIFEST}")" \
  --arg command "${COMMAND}" \
  --arg run_root "${RUN_ROOT}" \
  --arg archive_root "${ARCHIVE_ROOT}" \
  --arg step60_marker "${STEP60_MARKER}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson seed "$(jq -er '.seed' "${TRAINING_MANIFEST}")" \
  --arg final_index "${RUN_ROOT}/global_step_100/actor/huggingface/model.safetensors.index.json" \
  --arg final_raw_marker "${RUN_ROOT}/global_step_100/actor/RAW_STATE_RELOCATED.json" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_checkpoint_retention_watch",
    parent_training_run: $parent_run,
    node: "login",
    compute_node: $node,
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only login-node watcher orchestrates merge and retention for one single-node pilot; model scoring remains a separate compute-node job.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $parent_run,
    data_manifest_hash: $data_hash,
    seed: $seed,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    run_root: $run_root,
    archive_root: $archive_root,
    raw_retention: "latest raw state only",
    merged_retention: {
      intermediate_steps: [20, 40, 60, 80],
      final_shared_step: 100,
      step60_requires_evaluation_marker: $step60_marker
    },
    expected_artifacts: [$final_index, $final_raw_marker],
    deviations: []
  }' > "${MANIFEST}"

tmux new-session -d -s "${SESSION}" \
  ".venv/bin/python scripts/run_manifest_job.py '${MANIFEST}' '${LOG}'"
printf '%s\n' "${RUN_DIR}"
