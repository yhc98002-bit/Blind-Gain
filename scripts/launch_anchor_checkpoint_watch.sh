#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANCHOR_RUN="anchor_a0_recipe_3b_geo3k_20260709T224852Z"
RUN_ROOT="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${ANCHOR_RUN}"
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${ANCHOR_RUN}"
ANCHOR_MANIFEST="${ROOT}/experiments/runs/${ANCHOR_RUN}/run_manifest.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="anchor_checkpoint_retention_watch_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"

cd "${ROOT}"
if tmux has-session -t anchor_checkpoint_retention_watch 2>/dev/null; then
  echo "anchor checkpoint retention watcher already exists" >&2
  exit 2
fi
mkdir -p "${RUN_DIR}/logs"
CONFIG_HASH="$(.venv/bin/python -c 'from scripts.watch_anchor_checkpoints import code_bundle_hash; print(code_bundle_hash())')"
COMMAND=".venv/bin/python scripts/watch_anchor_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --anchor-manifest ${ANCHOR_MANIFEST} --node an12 --expected-code-hash ${CONFIG_HASH}"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg final_index "${RUN_ROOT}/global_step_100/actor/huggingface/model.safetensors.index.json" \
  --arg final_raw_marker "${RUN_ROOT}/global_step_100/actor/RAW_STATE_RELOCATED.json" \
  '{
    run_id: $run_id,
    job_type: "anchor_checkpoint_retention_watch",
    node: "login (orchestrates an12 merge)",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "anchor_a0_recipe_3b_geo3k_20260709T224852Z steps 80 and 100",
    data_manifest_hash: null,
    seed: 1,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$final_index, $final_raw_marker],
    deviations: []
  }' > "${MANIFEST}"
tmux new-session -d -s anchor_checkpoint_retention_watch \
  ".venv/bin/python scripts/run_manifest_job.py '${MANIFEST}' '${LOG}'"
printf '%s\n' "${RUN_DIR}"
