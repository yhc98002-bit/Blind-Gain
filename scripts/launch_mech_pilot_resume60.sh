#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <a1_real|a2_gray> <an12|an21|an29> <gpu0,gpu1,gpu2,gpu3> <failed-source-run-dir>" >&2
  exit 2
fi

ARM="$1"
NODE="$2"
GPU_LIST="$3"
SOURCE_RUN_INPUT="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_RUN="$(realpath -m "${SOURCE_RUN_INPUT}")"
case "${SOURCE_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "source run must be under experiments/runs" >&2; exit 2 ;;
esac
SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
PREREG="reports/preregistration_pilot_v1.md"
SOURCE_STEP=60
MIN_MEM_AVAILABLE_KIB=$((650 * 1024 * 1024))

case "${ARM}" in
  a1_real)
    BASE_NAME="mech_a1_real"
    IMAGE_CONDITION="real"
    ;;
  a2_gray)
    BASE_NAME="mech_a2_gray"
    IMAGE_CONDITION="gray"
    ;;
  *) echo "step-60 recovery only supports a1_real or a2_gray" >&2; exit 2 ;;
esac
ARM_RUN_NAME="${BASE_NAME}_resume60"
SAVE_ROOT="${ROOT}/checkpoints/pilot/${ARM_RUN_NAME}"

[[ "${NODE}" == "an12" || "${NODE}" == "an21" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }
[[ "${GPU_LIST}" =~ ^[0-7](,[0-7]){3}$ ]] || { echo "exactly four GPU indices are required" >&2; exit 2; }
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
[[ "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -eq 4 ]] || { echo "GPU indices must be unique" >&2; exit 2; }

[[ -f "${SOURCE_MANIFEST}" ]] || { echo "source manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${SOURCE_MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "source is not a pilot run" >&2; exit 2; }
[[ "$(jq -r '.arm' "${SOURCE_MANIFEST}")" == "${ARM}" ]] || { echo "source arm mismatch" >&2; exit 2; }
[[ "$(jq -r '.image_condition' "${SOURCE_MANIFEST}")" == "${IMAGE_CONDITION}" ]] || { echo "source image condition mismatch" >&2; exit 2; }
[[ "$(jq -r '.status' "${SOURCE_MANIFEST}")" == "fail" ]] || { echo "source run must be finalized fail" >&2; exit 2; }
SOURCE_CHECKPOINT_ROOT="$(jq -er '.checkpoint_path' "${SOURCE_MANIFEST}")"
[[ "$(realpath -m "${SOURCE_CHECKPOINT_ROOT}")" == "${ROOT}/checkpoints/pilot/${BASE_NAME}" ]] || { echo "source checkpoint namespace mismatch" >&2; exit 2; }
SOURCE_CHECKPOINT="${SOURCE_CHECKPOINT_ROOT}/global_step_${SOURCE_STEP}"
SOURCE_ACTOR="${SOURCE_CHECKPOINT}/actor"
SOURCE_CONFIG="$(jq -er '.config_path' "${SOURCE_MANIFEST}")"
[[ -f "${SOURCE_CONFIG}" ]] || { echo "source effective config absent" >&2; exit 2; }
[[ ! -e "${SAVE_ROOT}" ]] || { echo "resume checkpoint namespace already exists" >&2; exit 73; }

if [[ -f "${SOURCE_ACTOR}/RAW_STATE_RELOCATED.json" ]]; then
  [[ -f "${SOURCE_ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json" ]] || {
    echo "relocated source raw state has not been restored" >&2
    exit 2
  }
fi

git ls-files --error-unmatch "${PREREG}" >/dev/null 2>&1 || { echo "preregistration is not tracked" >&2; exit 2; }
git diff --quiet HEAD -- "${PREREG}" || { echo "preregistration differs from HEAD" >&2; exit 2; }
CRITICAL_FILES=(
  scripts/audit_easyr1_resume_checkpoint.py
  scripts/prepare_pilot_resume_config.py
  scripts/probe_ray_tempdir.py
  scripts/launch_mech_pilot_resume60.sh
  scripts/watch_pilot_resume60_checkpoints.py
  scripts/launch_pilot_resume60_checkpoint_watch.sh
  scripts/watch_anchor_checkpoints.py
  src/rewards/pilot_reward.py
  src/ops/easyr1_checkpoint_guard.py
)
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "resume-critical file is not tracked: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || { echo "resume-critical code differs from HEAD" >&2; exit 2; }

check_node_capacity() {
  if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main'"; then
    echo "a synchronous EasyR1 trainer is already active on ${NODE}" >&2
    return 75
  fi
  local gpu used_mib
  for gpu in "${GPUS[@]}"; do
    used_mib="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${gpu}'" | tr -d '[:space:]')"
    [[ "${used_mib}" =~ ^[0-9]+$ && "${used_mib}" -lt 1024 ]] || {
      echo "${NODE} GPU ${gpu} has ${used_mib:-unknown} MiB allocated" >&2
      return 75
    }
  done
  local mem_kib shm_kib
  mem_kib="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"
  [[ "${mem_kib}" =~ ^[0-9]+$ && "${mem_kib}" -ge "${MIN_MEM_AVAILABLE_KIB}" ]] || {
    echo "${NODE} MemAvailable ${mem_kib:-unknown} KiB is below the 650 GiB recovery floor" >&2
    return 75
  }
  shm_kib="$(ssh "${NODE}" "df -Pk /dev/shm | awk 'NR==2 {print \$4}'")"
  [[ "${shm_kib}" =~ ^[0-9]+$ && "${shm_kib}" -ge $((40 * 1024 * 1024)) ]] || {
    echo "${NODE} /dev/shm has less than 40 GiB free" >&2
    return 75
  }
}

check_node_capacity
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${ARM_RUN_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG="${ROOT}/${RUN_DIR}/effective_config.yaml"
CONFIG_AUDIT="${ROOT}/${RUN_DIR}/resume_config_audit.json"
CHECKPOINT_AUDIT="${ROOT}/${RUN_DIR}/resume_checkpoint_audit.json"
CHECKSUMS="${ROOT}/${RUN_DIR}/resume_checkpoint.sha256"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
RAY_ROOT="/dev/shm/bg-ray-${RAY_DIGEST}"
JOB_TMP="${RAY_ROOT}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_pilot_resume60.lock"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

PYTHONPATH=. .venv/bin/python scripts/audit_easyr1_resume_checkpoint.py \
  --checkpoint-dir "${SOURCE_CHECKPOINT}" --expected-step "${SOURCE_STEP}" \
  --expected-world-size 4 --output-json "${CHECKPOINT_AUDIT}" --output-sha256 "${CHECKSUMS}"
[[ "$(jq -r '.status' "${CHECKPOINT_AUDIT}")" == "pass" ]] || { echo "source checkpoint audit failed" >&2; exit 1; }

PYTHONPATH=. .venv/bin/python scripts/prepare_pilot_resume_config.py \
  --source "${SOURCE_CONFIG}" --output "${CONFIG}" --audit "${CONFIG_AUDIT}" \
  --experiment-name "${ARM_RUN_NAME}" --save-checkpoint-path "${SAVE_ROOT}" \
  --load-checkpoint-path "${SOURCE_CHECKPOINT}" --expected-step "${SOURCE_STEP}" \
  --expected-image-condition "${IMAGE_CONDITION}"
install -m 0444 "${PREREG}" "${RUN_DIR}/preregistration_pilot_v1.md"
git -C artifacts/repos/EasyR1 diff --binary --no-ext-diff > "${RUN_DIR}/easyr1_worktree.patch"
install -m 0444 artifacts/repos/EasyR1/verl/utils/logger/logger.py "${RUN_DIR}/easyr1_logger.py"
install -m 0444 artifacts/repos/EasyR1/verl/trainer/ray_trainer.py "${RUN_DIR}/easyr1_ray_trainer.py"
SOURCE_LOG="${SOURCE_CHECKPOINT_ROOT}/experiment_log.jsonl"
[[ -f "${SOURCE_LOG}" ]] || { echo "source experiment log absent" >&2; exit 2; }
jq -c 'select((.step // -1) <= 60)' "${SOURCE_LOG}" > "${RUN_DIR}/source_log_prefix_through_step60.jsonl"
EXCLUDED_STEPS="$(jq -s '[.[].step | select(. > 60)] | unique | sort' "${SOURCE_LOG}")"
chmod 0444 "${CONFIG}" "${CONFIG_AUDIT}" "${CHECKPOINT_AUDIT}" "${CHECKSUMS}" \
  "${RUN_DIR}/preregistration_pilot_v1.md" "${RUN_DIR}/easyr1_worktree.patch" \
  "${RUN_DIR}/easyr1_logger.py" "${RUN_DIR}/easyr1_ray_trainer.py" \
  "${RUN_DIR}/source_log_prefix_through_step60.jsonl"

TEMP_PROBE_ROOT="/dev/shm/bg-temp-probe-${RAY_DIGEST}"
TEMP_PROBE_OUTPUT="${ROOT}/${RUN_DIR}/ray_tempdir_probe.json"
ssh "${NODE}" "cd '${ROOT}' && source .venv/bin/activate && CUDA_VISIBLE_DEVICES='' TMPDIR='${TEMP_PROBE_ROOT}/tmp' TMP='${TEMP_PROBE_ROOT}/tmp' TEMP='${TEMP_PROBE_ROOT}/tmp' RAY_TMPDIR='${TEMP_PROBE_ROOT}' PYTHONPATH='${ROOT}' timeout --signal=TERM --kill-after=30 180 .venv/bin/python scripts/probe_ray_tempdir.py --expected-root '${TEMP_PROBE_ROOT}' --output '${TEMP_PROBE_OUTPUT}'"
ssh "${NODE}" "rm -rf '${TEMP_PROBE_ROOT}'"
[[ "$(jq -r '.status' "${TEMP_PROBE_OUTPUT}")" == "pass" ]] || { echo "Ray temp probe failed" >&2; exit 1; }
chmod 0444 "${TEMP_PROBE_OUTPUT}"
check_node_capacity
MEM_AVAILABLE_KIB_FINAL="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"

CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
DATA_HASH="$(sha256sum data/geo3k_pilot_filtered.jsonl | awk '{print $1}')"
[[ "${DATA_HASH}" == "$(jq -r '.data_manifest_hash' "${SOURCE_MANIFEST}")" ]] || { echo "filtered training data changed since source launch" >&2; exit 2; }
COMMAND="PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} python -u -m verl.trainer.main config=${CONFIG}"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"

jq -n \
  --arg run_id "${RUN_ID}" --arg arm "${ARM}" --arg arm_run_name "${ARM_RUN_NAME}" \
  --arg condition "${IMAGE_CONDITION}" --arg node "${NODE}" --arg gpu_allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${CONFIG}" --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg source_run "${SOURCE_RUN#"${ROOT}/"}" --arg source_manifest_hash "$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')" \
  --arg source_checkpoint "${SOURCE_CHECKPOINT}" --arg checkpoint_audit "${CHECKPOINT_AUDIT}" \
  --arg checkpoint_audit_hash "$(sha256sum "${CHECKPOINT_AUDIT}" | awk '{print $1}')" \
  --arg checksum_hash "$(sha256sum "${CHECKSUMS}" | awk '{print $1}')" --arg save_root "${SAVE_ROOT}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg shadow "${RUN_DIR}/reward_shadow.jsonl" --arg ray_root "${RAY_ROOT}" \
  --arg job_tmp "${JOB_TMP}" --arg temp_probe "${RUN_DIR}/ray_tempdir_probe.json" \
  --arg prereg_hash "$(sha256sum "${RUN_DIR}/preregistration_pilot_v1.md" | awk '{print $1}')" \
  --arg model_revision "$(jq -r '.model_revision' "${SOURCE_MANIFEST}")" \
  --argjson excluded_steps "${EXCLUDED_STEPS}" --argjson mem_initial "${MEM_AVAILABLE_KIB}" \
  --argjson mem_final "${MEM_AVAILABLE_KIB_FINAL}" \
  '{
    schema_version: "blind-gains.run-manifest.v1", run_id: $run_id,
    job_type: "l13_mechanical_pilot_arm", arm: $arm, arm_run_name: $arm_run_name,
    image_condition: $condition, node: $node, gpu_allocation: $gpu_allocation, gpu_ids: $gpu_ids,
    tensor_parallel_width: 1, replica_count: 4, placement_policy_version: "pi-2026-07-11",
    placement_justification: "Single-node synchronous GRPO recovery runs as the only pilot trainer on this node after the prior two-arm colocation exceeded Ray host-memory limits; four TP1 replicas use the registered four-GPU budget.",
    git_hash: $git_hash, config_path: $config, config_hash: $config_hash,
    data_manifest: "data/geo3k_pilot_filtered.jsonl", data_manifest_hash: $data_hash,
    model_revision: $model_revision, seed: 1,
    preregistration_snapshot: ("experiments/runs/" + $run_id + "/preregistration_pilot_v1.md"),
    preregistration_sha256: $prereg_hash, recovery_of_run: $source_run,
    recovery_of_manifest_sha256: $source_manifest_hash, resumed_from_global_step: 60,
    load_checkpoint_path: $source_checkpoint, raw_checkpoint_audit: $checkpoint_audit,
    raw_checkpoint_audit_sha256: $checkpoint_audit_hash,
    raw_checkpoint_checksum_manifest_sha256: $checksum_hash,
    source_log_policy: "Only source metrics through global step 60 are retained; later uncheckpointed source steps are excluded.",
    excluded_uncheckpointed_source_steps: $excluded_steps,
    command: $command, start_time_utc: $started, end_time_utc: null, status: "running",
    checkpoint_path: $save_root, checkpoint_schedule: [80,100], validation_cadence: 10,
    raw_retention: "latest raw state only after verified merge", stdout_stderr_log: $log,
    ray_tmp_dir: $ray_root, runtime_tmp_dir: $job_tmp, ray_tempdir_probe: $temp_probe,
    host_memory_preflight: {minimum_mem_available_gib: 650, initial_kib: $mem_initial, final_kib: $mem_final},
    pytorch_cuda_alloc_conf: "expandable_segments:True",
    expected_artifacts: [$shadow, ($save_root + "/experiment_log.jsonl"), ($save_root + "/checkpoint_tracker.json")],
    deviations: [{
      code: "resume_from_step60_after_ray_host_memory_pressure", scientific_config_change: false,
      operational_changes: ["new immutable save namespace", "explicit step-60 load path", "one pilot trainer per node", "650 GiB MemAvailable preflight"],
      excluded_uncheckpointed_source_steps: $excluded_steps
    }]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || { echo "pilot resume exited during startup; inspect ${LOG}" >&2; exit 1; }
WATCHER_RUN="$(bash scripts/launch_pilot_resume60_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
printf '%s\n' "${WATCHER_RUN}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\nwatcher=%s\npid_file=%s\nlog=%s\n' "${RUN_DIR}" "${WATCHER_RUN}" "${PID_FILE}" "${LOG}"
