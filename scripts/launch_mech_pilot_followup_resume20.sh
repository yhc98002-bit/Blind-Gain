#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: $0 <2|3> <a1_real|a2_gray|a2b_noimage|a3_caption> <an12|an29> <gpu0,gpu1,gpu2,gpu3> <failed-source-run-dir>" >&2
  exit 2
fi

SEED="$1"
ARM="$2"
NODE="$3"
GPU_LIST="$4"
SOURCE_RUN="$(realpath -m "$5")"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
[[ "${SEED}" == "2" || "${SEED}" == "3" ]] || { echo "follow-up seed must be 2 or 3" >&2; exit 2; }
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }
[[ "${GPU_LIST}" =~ ^[0-7](,[0-7]){3}$ ]] || { echo "exactly four GPU indices are required" >&2; exit 2; }
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
[[ "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -eq 4 ]] || { echo "GPU indices must be unique" >&2; exit 2; }
case "${SOURCE_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "source run must be under experiments/runs" >&2; exit 2 ;;
esac

case "${ARM}" in
  a1_real) IMAGE_CONDITION="real" ;;
  a2_gray) IMAGE_CONDITION="gray" ;;
  a2b_noimage) IMAGE_CONDITION="none" ;;
  a3_caption) IMAGE_CONDITION="caption" ;;
  *) echo "unsupported arm" >&2; exit 2 ;;
esac

SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
SOURCE_STEP=20
BASE_NAME="mech_${ARM}_seed${SEED}"
ARM_RUN_NAME="${BASE_NAME}_resume20"
SOURCE_CHECKPOINT_ROOT="${ROOT}/checkpoints/pilot/${BASE_NAME}"
SOURCE_CHECKPOINT="${SOURCE_CHECKPOINT_ROOT}/global_step_${SOURCE_STEP}"
SOURCE_ACTOR="${SOURCE_CHECKPOINT}/actor"
SAVE_ROOT="${ROOT}/checkpoints/pilot/${ARM_RUN_NAME}"
REGISTRATION="docs/registered_pilot_seed23_v1.md"

[[ -f "${SOURCE_MANIFEST}" ]] || { echo "source manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${SOURCE_MANIFEST}")" == "m3_mechanical_pilot_arm" ]] || { echo "source is not an M3 pilot run" >&2; exit 2; }
[[ "$(jq -r '.status' "${SOURCE_MANIFEST}")" == "fail" ]] || { echo "source run must be finalized fail" >&2; exit 2; }
[[ "$(jq -r '.arm' "${SOURCE_MANIFEST}")" == "${ARM}" ]] || { echo "source arm mismatch" >&2; exit 2; }
[[ "$(jq -r '.image_condition' "${SOURCE_MANIFEST}")" == "${IMAGE_CONDITION}" ]] || { echo "source image condition mismatch" >&2; exit 2; }
[[ "$(jq -r '.seed' "${SOURCE_MANIFEST}")" == "${SEED}" ]] || { echo "source seed mismatch" >&2; exit 2; }
[[ "$(realpath -m "$(jq -er '.checkpoint_path' "${SOURCE_MANIFEST}")")" == "${SOURCE_CHECKPOINT_ROOT}" ]] || { echo "source checkpoint namespace mismatch" >&2; exit 2; }
[[ ! -e "${SAVE_ROOT}" ]] || { echo "resume checkpoint namespace already exists" >&2; exit 73; }

RAW_RELOCATED="${SOURCE_ACTOR}/RAW_STATE_RELOCATED.json"
RAW_RESTORED="${SOURCE_ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json"
if [[ -f "${RAW_RELOCATED}" ]]; then
  [[ -f "${RAW_RESTORED}" ]] || { echo "relocated raw state has not been restored" >&2; exit 2; }
  [[ "$(jq -r '.status' "${RAW_RESTORED}")" == "restored_for_optimizer_resume" ]] || { echo "invalid raw restore marker" >&2; exit 2; }
fi
[[ "$(find "${SOURCE_ACTOR}" -maxdepth 1 -type f \( -name 'model_world_size_4_rank_*.pt' -o -name 'optim_world_size_4_rank_*.pt' \) | wc -l)" -eq 8 ]] || { echo "step-20 raw state is incomplete" >&2; exit 2; }
[[ "$(find "${SOURCE_ACTOR}" -maxdepth 1 -type f -name 'extra_state_world_size_4_rank_*.pt' | wc -l)" -eq 4 ]] || { echo "step-20 extra state is incomplete" >&2; exit 2; }
[[ -f "${SOURCE_CHECKPOINT}/dataloader.pt" ]] || { echo "step-20 dataloader state absent" >&2; exit 2; }

for FILE in "${REGISTRATION}" scripts/prepare_pilot_resume_config.py scripts/audit_easyr1_resume_checkpoint.py \
  scripts/probe_ray_tempdir.py scripts/launch_mech_pilot_followup_resume20.sh \
  scripts/watch_pilot_resume_checkpoints.py scripts/launch_pilot_resume_checkpoint_watch.sh \
  scripts/watch_anchor_checkpoints.py src/rewards/pilot_reward.py src/ops/easyr1_checkpoint_guard.py; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked resume-critical file: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${REGISTRATION}" scripts/prepare_pilot_resume_config.py \
  scripts/audit_easyr1_resume_checkpoint.py scripts/probe_ray_tempdir.py \
  scripts/launch_mech_pilot_followup_resume20.sh scripts/watch_pilot_resume_checkpoints.py \
  scripts/launch_pilot_resume_checkpoint_watch.sh scripts/watch_anchor_checkpoints.py \
  src/rewards/pilot_reward.py src/ops/easyr1_checkpoint_guard.py || {
  echo "resume registration/code differs from HEAD" >&2; exit 2;
}
[[ "$(sha256sum "${REGISTRATION}" | awk '{print $1}')" == "$(jq -er '.registration_sha256' "${SOURCE_MANIFEST}")" ]] || { echo "source registration hash mismatch" >&2; exit 2; }

if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"; then
  echo "another project EasyR1 trainer is active on ${NODE}" >&2; exit 74
fi
for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  [[ "${USED_MIB}" =~ ^[0-9]+$ && "${USED_MIB}" -lt 1024 ]] || { echo "${NODE} GPU ${GPU} is occupied" >&2; exit 75; }
done
sleep 20
for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  [[ "${USED_MIB}" =~ ^[0-9]+$ && "${USED_MIB}" -lt 1024 ]] || { echo "${NODE} GPU ${GPU} did not remain free" >&2; exit 75; }
done
SHM_FREE_KIB="$(ssh "${NODE}" "df -Pk /dev/shm | awk 'NR==2 {print \$4}'")"
[[ "${SHM_FREE_KIB}" =~ ^[0-9]+$ && "${SHM_FREE_KIB}" -ge $((40 * 1024 * 1024)) ]] || { echo "less than 40 GiB free in ${NODE}:/dev/shm" >&2; exit 75; }
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"
[[ "${MEM_AVAILABLE_KIB}" -ge 681574400 ]] || { echo "pilot recovery needs 650 GiB host memory" >&2; exit 76; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${ARM_RUN_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${ROOT}/${RUN_DIR}/effective_config.yaml"
CONFIG_AUDIT="${ROOT}/${RUN_DIR}/resume_config_audit.json"
CHECKPOINT_AUDIT="${ROOT}/${RUN_DIR}/source_checkpoint_audit.json"
CHECKPOINT_SHA="${ROOT}/${RUN_DIR}/source_checkpoint.sha256"
REGISTRATION_SNAPSHOT="${ROOT}/${RUN_DIR}/registered_pilot_seed23_v1.md"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
RAY_ROOT="/dev/shm/bg-ray-${RAY_DIGEST}"
JOB_TMP="${RAY_ROOT}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_${ARM_RUN_NAME}.lock"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

PYTHONPATH=. .venv/bin/python scripts/audit_easyr1_resume_checkpoint.py \
  --checkpoint-dir "${SOURCE_CHECKPOINT}" --expected-step 20 --expected-world-size 4 \
  --output-json "${CHECKPOINT_AUDIT}" --output-sha256 "${CHECKPOINT_SHA}"
PYTHONPATH=. .venv/bin/python scripts/prepare_pilot_resume_config.py \
  --source "${SOURCE_RUN}/effective_config.yaml" --output "${CONFIG}" --audit "${CONFIG_AUDIT}" \
  --experiment-name "${ARM_RUN_NAME}" --save-checkpoint-path "${SAVE_ROOT}" \
  --load-checkpoint-path "${SOURCE_CHECKPOINT}" --expected-step 20 \
  --expected-image-condition "${IMAGE_CONDITION}"
install -m 0444 "${REGISTRATION}" "${REGISTRATION_SNAPSHOT}"
git -C artifacts/repos/EasyR1 diff --binary --no-ext-diff > "${RUN_DIR}/easyr1_worktree.patch"
install -m 0444 artifacts/repos/EasyR1/verl/utils/logger/logger.py "${RUN_DIR}/easyr1_logger.py"
install -m 0444 artifacts/repos/EasyR1/verl/trainer/ray_trainer.py "${RUN_DIR}/easyr1_ray_trainer.py"
jq -c 'select((.step // -1) <= 20)' "${SOURCE_CHECKPOINT_ROOT}/experiment_log.jsonl" > "${RUN_DIR}/source_log_prefix_through_step20.jsonl"
jq -sc '[.[] | select((.step // -1) > 20) | .step] | unique | sort' "${SOURCE_CHECKPOINT_ROOT}/experiment_log.jsonl" > "${RUN_DIR}/excluded_uncheckpointed_source_steps.json"
chmod 0444 "${CONFIG}" "${CONFIG_AUDIT}" "${CHECKPOINT_AUDIT}" "${CHECKPOINT_SHA}" \
  "${RUN_DIR}/easyr1_worktree.patch" "${RUN_DIR}/easyr1_logger.py" "${RUN_DIR}/easyr1_ray_trainer.py" \
  "${RUN_DIR}/source_log_prefix_through_step20.jsonl" "${RUN_DIR}/excluded_uncheckpointed_source_steps.json"

TEMP_PROBE_ROOT="/dev/shm/bg-temp-probe-${RAY_DIGEST}"
TEMP_PROBE_OUTPUT="${ROOT}/${RUN_DIR}/ray_tempdir_probe.json"
ssh "${NODE}" "cd '${ROOT}' && source .venv/bin/activate && CUDA_VISIBLE_DEVICES='' TMPDIR='${TEMP_PROBE_ROOT}/tmp' TMP='${TEMP_PROBE_ROOT}/tmp' TEMP='${TEMP_PROBE_ROOT}/tmp' RAY_TMPDIR='${TEMP_PROBE_ROOT}' PYTHONPATH='${ROOT}' timeout --signal=TERM --kill-after=30 180 .venv/bin/python scripts/probe_ray_tempdir.py --expected-root '${TEMP_PROBE_ROOT}' --output '${TEMP_PROBE_OUTPUT}'"
ssh "${NODE}" "rm -rf '${TEMP_PROBE_ROOT}'"
[[ "$(jq -r '.status' "${TEMP_PROBE_OUTPUT}")" == "pass" ]] || { echo "Ray temp probe failed" >&2; exit 1; }
chmod 0444 "${TEMP_PROBE_OUTPUT}"

GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
EXCLUDED_STEPS="$(cat "${RUN_DIR}/excluded_uncheckpointed_source_steps.json")"
COMMAND="python -u -m verl.trainer.main config=${CONFIG}"
jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg allocation "${GPU_LIST}" --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg arm "${ARM}" --arg base "${BASE_NAME}" --arg run_name "${ARM_RUN_NAME}" --arg condition "${IMAGE_CONDITION}" --argjson seed "${SEED}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config "${CONFIG}" --arg config_hash "$(sha256sum "${CONFIG}" | awk '{print $1}')" \
  --arg config_audit "${CONFIG_AUDIT}" --arg checkpoint_audit "${CHECKPOINT_AUDIT}" --arg checkpoint_sha "$(sha256sum "${CHECKPOINT_SHA}" | awk '{print $1}')" \
  --arg source_run "${SOURCE_RUN}" --arg source_hash "$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')" --arg source_checkpoint "${SOURCE_CHECKPOINT}" \
  --arg save_root "${SAVE_ROOT}" --arg registration "${REGISTRATION_SNAPSHOT}" --arg registration_hash "$(sha256sum "${REGISTRATION_SNAPSHOT}" | awk '{print $1}')" \
  --arg command "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} ${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg shadow "${RUN_DIR}/reward_shadow.jsonl" --arg ray_root "${RAY_ROOT}" --arg job_tmp "${JOB_TMP}" \
  --arg temp_probe "${RUN_DIR}/ray_tempdir_probe.json" --arg data_hash "$(jq -er '.data_manifest_hash' "${SOURCE_MANIFEST}")" \
  --arg model_revision "$(jq -er '.model_revision' "${SOURCE_MANIFEST}")" --argjson excluded "${EXCLUDED_STEPS}" --argjson mem "${MEM_AVAILABLE_KIB}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m3_mechanical_pilot_arm",
    arm:$arm,arm_run_name:$run_name,recovery_source_arm_run_name:$base,image_condition:$condition,
    node:$node,gpu_allocation:$allocation,gpu_ids:$gpu_ids,tensor_parallel_width:1,replica_count:4,
    placement_policy_version:"pi-2026-07-11",placement_justification:"Single-node synchronous GRPO recovery on four GPUs with four TP1 rollout replicas; one Blind Gains trainer per node.",
    git_hash:$git_hash,config_path:$config,config_hash:$config_hash,resume_config_audit:$config_audit,
    source_checkpoint_audit:$checkpoint_audit,source_checkpoint_checksum_manifest_sha256:$checkpoint_sha,
    data_manifest:"data/geo3k_pilot_filtered.jsonl",data_manifest_hash:$data_hash,model_revision:$model_revision,seed:$seed,
    registration_snapshot:$registration,registration_sha256:$registration_hash,preregistration_snapshot:$registration,
    recovery_of_run:$source_run,recovery_of_manifest_sha256:$source_hash,resumed_from_global_step:20,load_checkpoint_path:$source_checkpoint,
    source_log_policy:"Only source metrics through global step 20 are retained; all later uncheckpointed rows are excluded and recomputed.",
    command:$command,start_time_utc:$started,end_time_utc:null,status:"running",checkpoint_path:$save_root,
    checkpoint_schedule:[40,60,80,100],validation_cadence:10,raw_retention:"latest raw state only after verified merge",
    stdout_stderr_log:$log,ray_tmp_dir:$ray_root,runtime_tmp_dir:$job_tmp,ray_tempdir_probe:$temp_probe,
    host_memory_preflight:{minimum_mem_available_gib:650,observed_kib:$mem},
    expected_artifacts:[$shadow,($save_root+"/experiment_log.jsonl"),($save_root+"/checkpoint_tracker.json")],
    scientific_gate_decision:null,performance_values_opened:false,
    deviations:[{code:"operational_resume_from_hash_verified_step20",scientific_config_change:false,
      excluded_uncheckpointed_source_steps:$excluded,
      operational_changes:["new immutable checkpoint namespace","explicit step-20 optimizer/dataloader restore","all runtime temp routed to /dev/shm"]}]}' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=110000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' >/dev/null 2>&1 </dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || { echo "pilot recovery exited during startup; inspect ${LOG}" >&2; exit 1; }
WATCHER_RUN="$(bash scripts/launch_pilot_resume_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
printf '%s\n' "${WATCHER_RUN}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\nwatcher=%s\npid_file=%s\nlog=%s\n' "${RUN_DIR}" "${WATCHER_RUN}" "${PID_FILE}" "${LOG}"
