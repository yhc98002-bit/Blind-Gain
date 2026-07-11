#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 NODE" >&2
  exit 2
fi

NODE="$1"
if [[ "${NODE}" != "an12" ]]; then
  echo "The registered anchor resume placement is an12 only" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT}/scripts/lib/run_paths.sh"
SOURCE_RUN_ID="anchor_a0_recipe_3b_geo3k_20260709T224852Z"
SOURCE_RUN="experiments/runs/${SOURCE_RUN_ID}"
CHECKPOINT_ROOT="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${SOURCE_RUN_ID}"
RESUME_CHECKPOINT="${CHECKPOINT_ROOT}/global_step_80"
RESTORE_MARKER="${RESUME_CHECKPOINT}/actor/RAW_STATE_RESTORED_FOR_RESUME.json"
CONFIG_PATH="${ROOT}/configs/train/anchor_a0_recipe_3b_geo3k.yaml"
GPU_LIST="0,1,2,3"
LOCK_PATH="/tmp/blind_gains_${NODE}_anchor_a0_recipe.lock"

cd "${ROOT}"
if [[ "$(jq -r .status "${SOURCE_RUN}/run_manifest.json")" != "fail" ]]; then
  echo "Source anchor attempt is not finalized fail" >&2
  exit 2
fi
if ! jq -e '.status == "restored_for_optimizer_resume"' "${RESTORE_MARKER}" >/dev/null; then
  echo "Step-80 raw restore marker is absent or invalid" >&2
  exit 2
fi
if [[ "$(find "${RESUME_CHECKPOINT}/actor" -maxdepth 1 -type f \( -name 'model_world_size_4_rank_*.pt' -o -name 'optim_world_size_4_rank_*.pt' \) | wc -l)" -ne 8 ]]; then
  echo "Step-80 resume checkpoint does not contain all eight raw shards" >&2
  exit 2
fi
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*anchor_a0_recipe_3b_geo3k.yaml'"; then
  echo "Refusing duplicate anchor process on ${NODE}" >&2
  exit 73
fi
if ssh "${NODE}" "pgrep -af '[r]un_blind_solvability_v2.py|[V]LMEvalKit/run.py'"; then
  echo "Refusing anchor resume while project VLM evaluators consume an12 host memory" >&2
  exit 74
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="anchor_a0_recipe_3b_geo3k_resume80_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
RAY_TMP_DIR="$(short_ray_tmp_dir "${USER}:${NODE}:${RUN_ID}")"
COMMAND="PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} python -u -m verl.trainer.main config=${CONFIG_PATH} trainer.save_checkpoint_path=${CHECKPOINT_ROOT} trainer.experiment_name=${SOURCE_RUN_ID} trainer.load_checkpoint_path=${RESUME_CHECKPOINT} trainer.find_last_checkpoint=false"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
BASE_CONFIG_HASH="$(sha256sum "${CONFIG_PATH}" | awk '{print $1}')"
CONFIG_HASH="$({
  cat "${CONFIG_PATH}"
  printf '\ntrainer.save_checkpoint_path=%s\n' "${CHECKPOINT_ROOT}"
  printf 'trainer.experiment_name=%s\n' "${SOURCE_RUN_ID}"
  printf 'trainer.load_checkpoint_path=%s\n' "${RESUME_CHECKPOINT}"
  printf 'trainer.find_last_checkpoint=false\n'
} | sha256sum | awk '{print $1}')"
DATA_HASH="$(jq -r .data_manifest_hash "${SOURCE_RUN}/run_manifest.json")"
RESUME_ARTIFACT_HASH="$({
  sha256sum "${SOURCE_RUN}/run_manifest.json"
  sha256sum "${RESTORE_MARKER}"
  sha256sum "/tmp/blindgain_checkpoint_archive/${SOURCE_RUN_ID}/global_step_80/actor/raw_training_state.source.sha256"
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG_PATH}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg base_config_hash "${BASE_CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg resume_artifact_hash "${RESUME_ARTIFACT_HASH}" \
  --arg source_run "${SOURCE_RUN}" \
  --arg checkpoint "${RESUME_CHECKPOINT}" \
  --arg restore_marker "${RESTORE_MARKER}" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg ray_tmp "${RAY_TMP_DIR}" \
  --arg log "${LOG_PATH}" \
  --arg expected "${CHECKPOINT_ROOT}/global_step_100/actor" \
  '{
    run_id: $run_id,
    job_type: "p1_1_anchor_a0_recipe_3b_geo3k_resume80",
    node: "an12",
    gpu_allocation: "0,1,2,3",
    gpu_ids: [0,1,2,3],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "One synchronous native-reward EasyR1/GRPO FSDP continuation wholly on an12; project VLM evaluators are excluded from the host-memory window.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    base_config_hash: $base_config_hash,
    seed: 1,
    data_manifest: "hiyouga/geometry3k@train|hiyouga/geometry3k@test",
    data_manifest_hash: $data_hash,
    resume_artifact_hash: $resume_artifact_hash,
    source_attempt: $source_run,
    resume_checkpoint: $checkpoint,
    restore_marker: $restore_marker,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    ray_tmp_dir: $ray_tmp,
    stdout_stderr_log: $log,
    expected_artifacts: [$expected],
    deviations: [
      "Resume from the last checksum-verified native checkpoint after a Ray host-memory kill; optimizer, RNG, scheduler, and dataloader states are restored from step 80.",
      "Only load-path and checkpoint-discovery overrides are added; the anchor config and native r1v reward binding are unchanged."
    ]
  }' > "${MANIFEST_PATH}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP_DIR}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK_PATH}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST_PATH}' '${ROOT}/${LOG_PATH}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_PATH}')"

sleep 20
REMOTE_PID="$(cat "${PID_PATH}")"
if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "Anchor resume exited during startup; inspect ${LOG_PATH}" >&2
  exit 1
fi
printf '%s\n' "${RUN_DIR}"
