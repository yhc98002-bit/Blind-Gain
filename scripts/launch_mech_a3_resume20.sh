#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <failed-a3-run-dir>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_RUN="$1"
SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
NODE="an29"
GPU_LIST="4,5,6,7"
ARM="a3_caption"
ARM_RUN_NAME="mech_a3_caption_resume20"
SOURCE_STEP=20
SOURCE_CHECKPOINT="${ROOT}/checkpoints/pilot/mech_a3_caption/global_step_${SOURCE_STEP}"
SOURCE_ACTOR="${SOURCE_CHECKPOINT}/actor"
RESTORE_MARKER="${SOURCE_ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json"
SAVE_ROOT="${ROOT}/checkpoints/pilot/${ARM_RUN_NAME}"
PREREG="reports/preregistration_pilot_v1.md"

[[ -f "${SOURCE_MANIFEST}" ]] || { echo "source manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${SOURCE_MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "source is not a pilot run" >&2; exit 2; }
[[ "$(jq -r '.arm' "${SOURCE_MANIFEST}")" == "${ARM}" ]] || { echo "source is not A3" >&2; exit 2; }
[[ "$(jq -r '.node' "${SOURCE_MANIFEST}")" == "${NODE}" ]] || { echo "source node mismatch" >&2; exit 2; }
[[ "$(jq -r '.status' "${SOURCE_MANIFEST}")" == "fail" ]] || { echo "source run must be finalized fail" >&2; exit 2; }
[[ -f "${RESTORE_MARKER}" ]] || { echo "step-20 raw state has not been restored" >&2; exit 2; }
[[ "$(jq -r '.status' "${RESTORE_MARKER}")" == "restored_for_optimizer_resume" ]] || { echo "invalid raw restore marker" >&2; exit 2; }
[[ "$(find "${SOURCE_ACTOR}" -maxdepth 1 -type f \( -name 'model_world_size_4_rank_*.pt' -o -name 'optim_world_size_4_rank_*.pt' \) | wc -l)" -eq 8 ]] || { echo "step-20 raw state is incomplete" >&2; exit 2; }
[[ -f "${SOURCE_CHECKPOINT}/dataloader.pt" ]] || { echo "step-20 dataloader state absent" >&2; exit 2; }
[[ "$(find "${SOURCE_ACTOR}" -maxdepth 1 -name 'extra_state_world_size_4_rank_*.pt' | wc -l)" -eq 4 ]] || { echo "step-20 extra state incomplete" >&2; exit 2; }
[[ ! -e "${SAVE_ROOT}" ]] || { echo "resume checkpoint namespace already exists" >&2; exit 73; }

git ls-files --error-unmatch "${PREREG}" >/dev/null 2>&1 || { echo "preregistration is not tracked" >&2; exit 2; }
git diff --quiet HEAD -- "${PREREG}" || { echo "preregistration differs from HEAD" >&2; exit 2; }
git diff --quiet HEAD -- \
  scripts/prepare_pilot_resume_config.py scripts/probe_ray_tempdir.py \
  scripts/launch_mech_a3_resume20.sh scripts/watch_pilot_resume_checkpoints.py \
  scripts/launch_pilot_resume_checkpoint_watch.sh scripts/watch_anchor_checkpoints.py \
  src/rewards/pilot_reward.py src/ops/easyr1_checkpoint_guard.py || {
    echo "resume-critical code differs from HEAD" >&2
    exit 2
  }

if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*mech_a3_caption'"; then
  echo "an A3 trainer is already active on ${NODE}" >&2
  exit 73
fi
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  [[ "${USED_MIB}" =~ ^[0-9]+$ && "${USED_MIB}" -lt 1024 ]] || { echo "${NODE} GPU ${GPU} still has ${USED_MIB:-unknown} MiB allocated" >&2; exit 75; }
done
SHM_FREE_KIB="$(ssh "${NODE}" "df -Pk /dev/shm | awk 'NR==2 {print \$4}'")"
[[ "${SHM_FREE_KIB}" =~ ^[0-9]+$ && "${SHM_FREE_KIB}" -ge $((40 * 1024 * 1024)) ]] || { echo "less than 40 GiB free in ${NODE}:/dev/shm" >&2; exit 75; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${ARM_RUN_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${ROOT}/${RUN_DIR}/effective_config.yaml"
CONFIG_AUDIT="${ROOT}/${RUN_DIR}/resume_config_audit.json"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
RAY_ROOT="/dev/shm/bg-ray-${RAY_DIGEST}"
JOB_TMP="${RAY_ROOT}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_mech_a3_caption.lock"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

PYTHONPATH=. .venv/bin/python scripts/prepare_pilot_resume_config.py \
  --source "${SOURCE_RUN}/effective_config.yaml" --output "${CONFIG}" \
  --audit "${CONFIG_AUDIT}" --experiment-name "${ARM_RUN_NAME}" \
  --save-checkpoint-path "${SAVE_ROOT}" --load-checkpoint-path "${SOURCE_CHECKPOINT}" \
  --expected-step "${SOURCE_STEP}"
chmod 0444 "${CONFIG}" "${CONFIG_AUDIT}"
install -m 0444 "${PREREG}" "${RUN_DIR}/preregistration_pilot_v1.md"
git -C artifacts/repos/EasyR1 diff --binary --no-ext-diff > "${RUN_DIR}/easyr1_worktree.patch"
chmod 0444 "${RUN_DIR}/easyr1_worktree.patch"
install -m 0444 artifacts/repos/EasyR1/verl/utils/logger/logger.py "${RUN_DIR}/easyr1_logger.py"
install -m 0444 artifacts/repos/EasyR1/verl/trainer/ray_trainer.py "${RUN_DIR}/easyr1_ray_trainer.py"
jq -c 'select((.step // -1) <= 20)' checkpoints/pilot/mech_a3_caption/experiment_log.jsonl > "${RUN_DIR}/source_log_prefix_through_step20.jsonl"
chmod 0444 "${RUN_DIR}/source_log_prefix_through_step20.jsonl"

TEMP_PROBE_ROOT="/dev/shm/bg-temp-probe-${RAY_DIGEST}"
TEMP_PROBE_OUTPUT="${ROOT}/${RUN_DIR}/ray_tempdir_probe.json"
ssh "${NODE}" "cd '${ROOT}' && source .venv/bin/activate && CUDA_VISIBLE_DEVICES='' TMPDIR='${TEMP_PROBE_ROOT}/tmp' TMP='${TEMP_PROBE_ROOT}/tmp' TEMP='${TEMP_PROBE_ROOT}/tmp' RAY_TMPDIR='${TEMP_PROBE_ROOT}' PYTHONPATH='${ROOT}' timeout --signal=TERM --kill-after=30 180 .venv/bin/python scripts/probe_ray_tempdir.py --expected-root '${TEMP_PROBE_ROOT}' --output '${TEMP_PROBE_OUTPUT}'"
ssh "${NODE}" "rm -rf '${TEMP_PROBE_ROOT}'"
[[ "$(jq -r '.status' "${TEMP_PROBE_OUTPUT}")" == "pass" ]] || { echo "Ray temp probe failed" >&2; exit 1; }
chmod 0444 "${TEMP_PROBE_OUTPUT}"

CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
CONFIG_AUDIT_HASH="$(sha256sum "${CONFIG_AUDIT}" | awk '{print $1}')"
SOURCE_MANIFEST_HASH="$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')"
RESTORE_HASH="$(sha256sum "${RESTORE_MARKER}" | awk '{print $1}')"
DATA_HASH="$(sha256sum data/geo3k_pilot_filtered.jsonl | awk '{print $1}')"
PREREG_HASH="$(sha256sum "${RUN_DIR}/preregistration_pilot_v1.md" | awk '{print $1}')"
COMMAND="python -u -m verl.trainer.main config=${CONFIG}"

jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${CONFIG}" --arg config_hash "${CONFIG_HASH}" --arg config_audit "${CONFIG_AUDIT}" \
  --arg config_audit_hash "${CONFIG_AUDIT_HASH}" --arg source_run "${SOURCE_RUN}" \
  --arg source_manifest_hash "${SOURCE_MANIFEST_HASH}" --arg source_checkpoint "${SOURCE_CHECKPOINT}" \
  --arg restore_marker "${RESTORE_MARKER}" --arg restore_hash "${RESTORE_HASH}" \
  --arg save_root "${SAVE_ROOT}" --arg data_hash "${DATA_HASH}" --arg prereg_hash "${PREREG_HASH}" \
  --arg command "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} ${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg shadow "${RUN_DIR}/reward_shadow.jsonl" \
  --arg ray_root "${RAY_ROOT}" --arg job_tmp "${JOB_TMP}" --arg temp_probe "${RUN_DIR}/ray_tempdir_probe.json" \
  --arg caption_model "$(jq -r '.caption_model' "${SOURCE_MANIFEST}")" \
  --arg caption_prompt "$(jq -r '.caption_prompt_sha256' "${SOURCE_MANIFEST}")" \
  --arg caption_store "$(jq -r '.caption_store_sha256' "${SOURCE_MANIFEST}")" \
  --arg caption_files "$(jq -r '.caption_store_files_sha256' "${SOURCE_MANIFEST}")" \
  '{
    schema_version: "blind-gains.run-manifest.v1", run_id: $run_id,
    job_type: "l13_mechanical_pilot_arm", arm: "a3_caption", arm_run_name: "mech_a3_caption_resume20",
    image_condition: "caption", node: $node, gpu_allocation: "4,5,6,7", gpu_ids: [4,5,6,7],
    tensor_parallel_width: 1, replica_count: 4, placement_policy_version: "pi-2026-07-11",
    placement_justification: "Single-node synchronous GRPO resume on an29 GPUs 4-7 with four TP1 rollout replicas; A2b remains isolated on GPUs 0-3.",
    git_hash: $git_hash, config_path: $config, config_hash: $config_hash,
    resume_config_audit: $config_audit, resume_config_audit_sha256: $config_audit_hash,
    data_manifest: "data/geo3k_pilot_filtered.jsonl", data_manifest_hash: $data_hash,
    model_revision: "Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3", seed: 1,
    preregistration_snapshot: ("experiments/runs/" + $run_id + "/preregistration_pilot_v1.md"), preregistration_sha256: $prereg_hash,
    recovery_of_run: $source_run, recovery_of_manifest_sha256: $source_manifest_hash,
    resumed_from_global_step: 20, load_checkpoint_path: $source_checkpoint,
    raw_restore_marker: $restore_marker, raw_restore_marker_sha256: $restore_hash,
    source_log_policy: "Only source metrics through global step 20 are retained in the resumed trajectory; failed uncheckpointed source steps 21-26 are excluded.",
    caption_model: $caption_model, caption_prompt_sha256: $caption_prompt,
    caption_store_sha256: $caption_store, caption_store_files_sha256: $caption_files,
    command: $command, start_time_utc: $started, end_time_utc: null, status: "running",
    checkpoint_path: $save_root, checkpoint_schedule: [40,60,80,100], validation_cadence: 10,
    raw_retention: "latest raw state only after verified merge", stdout_stderr_log: $log,
    ray_tmp_dir: $ray_root, runtime_tmp_dir: $job_tmp, ray_tempdir_probe: $temp_probe,
    pytorch_cuda_alloc_conf: "expandable_segments:True",
    expected_artifacts: [$shadow, ($save_root + "/experiment_log.jsonl"), ($save_root + "/checkpoint_tracker.json")],
    deviations: [{
      code: "resume_from_step20_after_compute_node_tmp_exhaustion",
      scientific_config_change: false,
      operational_changes: ["new immutable save namespace", "explicit step-20 load path", "TMPDIR/TMP/TEMP/RAY_TMPDIR under /dev/shm"],
      excluded_uncheckpointed_source_steps: [21,22,23,24,25,26]
    }]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || { echo "A3 resume exited during startup; inspect ${LOG}" >&2; exit 1; }
WATCHER_RUN="$(bash scripts/launch_pilot_resume_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
printf '%s\n' "${WATCHER_RUN}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\nwatcher=%s\npid_file=%s\nlog=%s\n' "${RUN_DIR}" "${WATCHER_RUN}" "${PID_FILE}" "${LOG}"
