#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <a1_real|a2_gray|a2b_noimage|a3_caption> <an12|an29> <gpu0,gpu1,gpu2,gpu3>" >&2
  exit 2
fi

ARM="$1"
NODE="$2"
GPU_LIST="$3"
if [[ "${NODE}" != "an12" && "${NODE}" != "an29" ]]; then
  echo "pilot arm must run wholly on an12 or an29" >&2
  exit 2
fi
if [[ ! "${GPU_LIST}" =~ ^[0-7](,[0-7]){3}$ ]]; then
  echo "pilot arm requires exactly four comma-separated GPU indices" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
if [[ "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -ne 4 ]]; then
  echo "pilot arm GPU indices must be unique" >&2
  exit 2
fi

case "${ARM}" in
  a1_real)
    CONFIG_REL="configs/train/mech_a1_real_3b_geo3k.yaml"
    ARM_RUN_NAME="mech_a1_real"
    IMAGE_CONDITION="real"
    ;;
  a2_gray)
    CONFIG_REL="configs/train/mech_a2_gray_3b_geo3k.yaml"
    ARM_RUN_NAME="mech_a2_gray"
    IMAGE_CONDITION="gray"
    ;;
  a2b_noimage)
    CONFIG_REL="configs/train/mech_a2b_noimage_3b_geo3k.yaml"
    ARM_RUN_NAME="mech_a2b_noimage"
    IMAGE_CONDITION="none"
    ;;
  a3_caption)
    CONFIG_REL="configs/train/mech_a3_caption_3b_geo3k.yaml"
    ARM_RUN_NAME="mech_a3_caption"
    IMAGE_CONDITION="caption"
    ;;
  *)
    echo "unknown pilot arm: ${ARM}" >&2
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_CONFIG="${ROOT}/${CONFIG_REL}"
EASYR1_DIR="${ROOT}/artifacts/repos/EasyR1"
PREREG="reports/preregistration_pilot_v1.md"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
AUTHORIZATION="reports/pilot_launch_authorization_${ARM}_${STAMP}.json"

# This is the first executable gate. A blocked L3/L4/L5/L12 state exits before
# any run directory, checkpoint namespace, SSH process, or GPU allocation exists.
PYTHONPATH=. .venv/bin/python scripts/check_pilot_launch_authorization.py \
  --root . \
  --arm "${ARM}" \
  --output "${AUTHORIZATION}"

if ! git ls-files --error-unmatch "${PREREG}" >/dev/null 2>&1; then
  echo "final preregistration exists locally but is not merged in Git" >&2
  exit 2
fi
if ! git diff --quiet HEAD -- "${PREREG}"; then
  echo "final preregistration differs from the merged Git version" >&2
  exit 2
fi
if ! git diff --quiet HEAD -- \
  "${CONFIG_REL}" \
  scripts/launch_mech_pilot_arm.sh \
  scripts/check_pilot_launch_authorization.py \
  scripts/watch_anchor_checkpoints.py \
  scripts/watch_pilot_checkpoints.py \
  scripts/launch_pilot_checkpoint_watch.sh \
  src/rewards/pilot_reward.py \
  src/ops/easyr1_checkpoint_guard.py \
  docs/easyr1_storage_guard_patch.diff; then
  echo "critical pilot launch code/config differs from HEAD" >&2
  exit 2
fi

CHECKPOINT_PATH="${ROOT}/checkpoints/pilot/${ARM_RUN_NAME}"
if [[ -e "${CHECKPOINT_PATH}" ]]; then
  echo "pilot checkpoint namespace appeared after authorization: ${CHECKPOINT_PATH}" >&2
  exit 73
fi
for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  if [[ ! "${USED_MIB}" =~ ^[0-9]+$ || "${USED_MIB}" -ge 1024 ]]; then
    echo "refusing pilot arm: ${NODE} GPU ${GPU} has ${USED_MIB:-unknown} MiB allocated" >&2
    exit 75
  fi
done
SHM_FREE_KIB="$(ssh "${NODE}" "df -Pk /dev/shm | awk 'NR==2 {print \$4}'")"
if [[ ! "${SHM_FREE_KIB}" =~ ^[0-9]+$ || "${SHM_FREE_KIB}" -lt $((40 * 1024 * 1024)) ]]; then
  echo "refusing pilot arm: ${NODE} /dev/shm has less than 40 GiB free" >&2
  exit 75
fi
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*${ARM_RUN_NAME}'"; then
  echo "refusing duplicate ${ARM_RUN_NAME} process on ${NODE}" >&2
  exit 73
fi

RUN_ID="${ARM_RUN_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG_SNAPSHOT="${ROOT}/${RUN_DIR}/effective_config.yaml"
PREREG_SNAPSHOT="${ROOT}/${RUN_DIR}/preregistration_pilot_v1.md"
EASYR1_PATCH="${ROOT}/${RUN_DIR}/easyr1_worktree.patch"
EASYR1_LOGGER="${ROOT}/${RUN_DIR}/easyr1_logger.py"
EASYR1_TRAINER="${ROOT}/${RUN_DIR}/easyr1_ray_trainer.py"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1, 1, 12)}')"
RAY_TMP_DIR="/dev/shm/bg-ray-${RAY_DIGEST}"
LOCK="/tmp/blind_gains_${NODE}_${ARM_RUN_NAME}.lock"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
install -m 0444 "${SOURCE_CONFIG}" "${CONFIG_SNAPSHOT}"
install -m 0444 "${PREREG}" "${PREREG_SNAPSHOT}"
git -C "${EASYR1_DIR}" diff --binary --no-ext-diff > "${EASYR1_PATCH}"
chmod 0444 "${EASYR1_PATCH}"
install -m 0444 "${EASYR1_DIR}/verl/utils/logger/logger.py" "${EASYR1_LOGGER}"
install -m 0444 "${EASYR1_DIR}/verl/trainer/ray_trainer.py" "${EASYR1_TRAINER}"
if ! grep -q "Preserving existing EasyR1 file logger artifact during resume" "${EASYR1_LOGGER}"; then
  echo "EasyR1 resume-safe logger patch is absent" >&2
  exit 2
fi
if ! grep -q "wait_for_easyr1_checkpoint_storage" "${EASYR1_TRAINER}"; then
  echo "EasyR1 checkpoint storage guard patch is absent" >&2
  exit 2
fi

PLACEMENT_JSON="$(PYTHONPATH=. .venv/bin/python scripts/resolve_easyr1_rollout_placement.py --config "${CONFIG_SNAPSHOT}" --gpu-list "${GPU_LIST}" --require-tp 1)"
TP_WIDTH="$(jq -er '.tensor_parallel_width' <<< "${PLACEMENT_JSON}")"
REPLICA_COUNT="$(jq -er '.replica_count' <<< "${PLACEMENT_JSON}")"
CONFIG_CONDITION="$(.venv/bin/python -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["data"]["image_condition"])' "${CONFIG_SNAPSHOT}")"
if [[ "${CONFIG_CONDITION}" != "${IMAGE_CONDITION}" ]]; then
  echo "selected config image condition does not match arm" >&2
  exit 2
fi

CAPTION_MODEL=""
CAPTION_PROMPT_SHA256=""
CAPTION_STORE_SHA256=""
CAPTION_STORE_FILES_SHA256=""
if [[ "${ARM}" == "a3_caption" ]]; then
  A3_AUDIT="experiments/runs/a3_caption_path_audit_login_20260711T110048Z/audit.json"
  CAPTION_MODEL="$(jq -er '.caption_store_metadata.caption_model_path' "${A3_AUDIT}")"
  CAPTION_PROMPT_SHA256="$(jq -er '.caption_store_metadata.caption_prompt_sha256' "${A3_AUDIT}")"
  CAPTION_STORE_SHA256="$(jq -er '.caption_store_metadata.caption_store_sha256' "${A3_AUDIT}")"
  CAPTION_STORE_FILES_SHA256="$(jq -S '.caption_store_file_sha256' "${A3_AUDIT}" | sha256sum | awk '{print $1}')"
fi

COMMAND="python -u -m verl.trainer.main config=${CONFIG_SNAPSHOT}"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
AUTH_SHA256="$(sha256sum "${AUTHORIZATION}" | awk '{print $1}')"
PREREG_SHA256="$(sha256sum "${PREREG_SNAPSHOT}" | awk '{print $1}')"
CONFIG_SHA256="$(sha256sum "${CONFIG_SNAPSHOT}" | awk '{print $1}')"
DATA_SHA256="$(sha256sum data/geo3k_pilot_filtered.jsonl | awk '{print $1}')"
FILTER_SHA256="$(sha256sum data/geo3k_pilot_filtered_ids.json | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg arm "${ARM}" \
  --arg arm_run_name "${ARM_RUN_NAME}" \
  --arg condition "${IMAGE_CONDITION}" \
  --arg node "${NODE}" \
  --arg gpu_allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" \
  --argjson tp_width "${TP_WIDTH}" \
  --argjson replicas "${REPLICA_COUNT}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG_SNAPSHOT}" \
  --arg config_hash "${CONFIG_SHA256}" \
  --arg data_hash "${DATA_SHA256}" \
  --arg filter_hash "${FILTER_SHA256}" \
  --arg authorization "${AUTHORIZATION}" \
  --arg authorization_hash "${AUTH_SHA256}" \
  --arg preregistration "${PREREG_SNAPSHOT}" \
  --arg preregistration_hash "${PREREG_SHA256}" \
  --arg easyr1_revision "$(git -C "${EASYR1_DIR}" rev-parse HEAD)" \
  --arg easyr1_patch "${EASYR1_PATCH}" \
  --arg easyr1_patch_hash "$(sha256sum "${EASYR1_PATCH}" | awk '{print $1}')" \
  --arg logger "${EASYR1_LOGGER}" \
  --arg logger_hash "$(sha256sum "${EASYR1_LOGGER}" | awk '{print $1}')" \
  --arg trainer "${EASYR1_TRAINER}" \
  --arg trainer_hash "$(sha256sum "${EASYR1_TRAINER}" | awk '{print $1}')" \
  --arg command "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} ${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg checkpoint_path "${CHECKPOINT_PATH}" \
  --arg shadow "${RUN_DIR}/reward_shadow.jsonl" \
  --arg log "${LOG}" \
  --arg ray_tmp "${RAY_TMP_DIR}" \
  --arg caption_model "${CAPTION_MODEL}" \
  --arg caption_prompt_hash "${CAPTION_PROMPT_SHA256}" \
  --arg caption_store_hash "${CAPTION_STORE_SHA256}" \
  --arg caption_files_hash "${CAPTION_STORE_FILES_SHA256}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "l13_mechanical_pilot_arm",
    arm: $arm,
    arm_run_name: $arm_run_name,
    image_condition: $condition,
    node: $node,
    gpu_allocation: $gpu_allocation,
    gpu_ids: $gpu_ids,
    tensor_parallel_width: $tp_width,
    replica_count: $replicas,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "One synchronous EasyR1/GRPO arm is colocated on four GPUs of one node; four TP1 rollout replicas shard requests while rollout and FSDP training remain on that node.",
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    data_manifest: "data/geo3k_pilot_filtered.jsonl",
    data_manifest_hash: $data_hash,
    filtered_ids: "data/geo3k_pilot_filtered_ids.json",
    filtered_ids_sha256: $filter_hash,
    model_revision: "Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3",
    seed: 1,
    launch_authorization: $authorization,
    launch_authorization_sha256: $authorization_hash,
    preregistration_snapshot: $preregistration,
    preregistration_sha256: $preregistration_hash,
    easyr1_revision: $easyr1_revision,
    easyr1_worktree_patch: $easyr1_patch,
    easyr1_worktree_patch_sha256: $easyr1_patch_hash,
    easyr1_logger_snapshot: $logger,
    easyr1_logger_sha256: $logger_hash,
    easyr1_trainer_snapshot: $trainer,
    easyr1_trainer_sha256: $trainer_hash,
    caption_model: (if $caption_model == "" then null else $caption_model end),
    caption_prompt_sha256: (if $caption_prompt_hash == "" then null else $caption_prompt_hash end),
    caption_store_sha256: (if $caption_store_hash == "" then null else $caption_store_hash end),
    caption_store_files_sha256: (if $caption_files_hash == "" then null else $caption_files_hash end),
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    checkpoint_path: $checkpoint_path,
    checkpoint_schedule: [20, 40, 60, 80, 100],
    validation_cadence: 10,
    raw_retention: "latest raw state only after verified merge",
    stdout_stderr_log: $log,
    ray_tmp_dir: $ray_tmp,
    expected_artifacts: [$shadow, ($checkpoint_path + "/experiment_log.jsonl"), ($checkpoint_path + "/checkpoint_tracker.json")],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP_DIR}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"

sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "pilot arm exited during startup; inspect ${LOG}" >&2
  exit 1
fi
WATCHER_RUN="$(bash scripts/launch_pilot_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
printf '%s\n' "${WATCHER_RUN}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\n' "${RUN_DIR}"
printf 'watcher=%s\n' "${WATCHER_RUN}"
printf 'pid_file=%s\n' "${PID_FILE}"
printf 'log=%s\n' "${LOG}"
