#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 NODE [CUDA_VISIBLE_DEVICES]" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="${2:-1,5,6,7}"
if [[ ! "${GPU_LIST}" =~ ^[0-7](,[0-7]){3}$ ]]; then
  echo "Pilot reward smoke requires exactly four comma-separated GPU indices" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
if [[ "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -ne 4 ]]; then
  echo "Pilot reward smoke GPU indices must be unique" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_CONFIG_PATH="${ROOT}/configs/train/mech_a1_real_3b_geo3k.yaml"
DATA_PATH="data/geo3k_pilot_filtered.jsonl"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_reward_smoke_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG_PATH="${ROOT}/${RUN_DIR}/effective_config.yaml"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"
SHADOW_PATH="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
CHECKPOINT_PATH="${ROOT}/checkpoints/smoke/${RUN_ID}"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1, 1, 12)}')"
RAY_TMP_DIR="/dev/shm/bg-ray-${RAY_DIGEST}"
LOCK_PATH="/tmp/blind_gains_${NODE}_pilot_reward_smoke.lock"

for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  if [[ ! "${USED_MIB}" =~ ^[0-9]+$ || "${USED_MIB}" -ge 1024 ]]; then
    echo "Refusing pilot reward smoke: ${NODE} GPU ${GPU} has ${USED_MIB:-unknown} MiB allocated" >&2
    exit 75
  fi
done
SHM_FREE_KIB="$(ssh "${NODE}" "df -Pk /dev/shm | awk 'NR==2 {print \$4}'")"
if [[ ! "${SHM_FREE_KIB}" =~ ^[0-9]+$ || "${SHM_FREE_KIB}" -lt $((40 * 1024 * 1024)) ]]; then
  echo "Refusing pilot reward smoke: ${NODE} /dev/shm has less than 40 GiB free" >&2
  exit 75
fi
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*pilot_reward_smoke_'"; then
  echo "Refusing duplicate pilot reward smoke on ${NODE}" >&2
  exit 73
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
install -m 0444 "${SOURCE_CONFIG_PATH}" "${CONFIG_PATH}"
PLACEMENT_JSON="$("${ROOT}/.venv/bin/python" "${ROOT}/scripts/resolve_easyr1_rollout_placement.py" --config "${CONFIG_PATH}" --gpu-list "${GPU_LIST}" --require-tp 1)"
TP_WIDTH="$(jq -er '.tensor_parallel_width' <<< "${PLACEMENT_JSON}")"
REPLICA_COUNT="$(jq -er '.replica_count' <<< "${PLACEMENT_JSON}")"
COMMAND="python -u -m verl.trainer.main config=${CONFIG_PATH} trainer.max_steps=5 trainer.val_before_train=false trainer.val_freq=-1 trainer.save_freq=-1 trainer.save_checkpoint_path=${CHECKPOINT_PATH} trainer.experiment_name=${RUN_ID} trainer.find_last_checkpoint=false"
BASE_CONFIG_HASH="$(sha256sum "${CONFIG_PATH}" | awk '{print $1}')"
CONFIG_HASH="$({ cat "${CONFIG_PATH}"; printf '\n%s\n' "trainer.max_steps=5" "trainer.val_before_train=false" "trainer.val_freq=-1" "trainer.save_freq=-1" "trainer.save_checkpoint_path=${CHECKPOINT_PATH}" "trainer.experiment_name=${RUN_ID}" "trainer.find_last_checkpoint=false"; } | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${DATA_PATH}" | awk '{print $1}')"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu_allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG_PATH}" \
  --arg source_config_path "${SOURCE_CONFIG_PATH}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg base_config_hash "${BASE_CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} ${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg shadow_path "${RUN_DIR}/reward_shadow.jsonl" \
  --arg log_path "${LOG_PATH}" \
  --arg ray_tmp_dir "${RAY_TMP_DIR}" \
  --arg checkpoint_path "${CHECKPOINT_PATH}" \
  --argjson tensor_parallel_width "${TP_WIDTH}" \
  --argjson replica_count "${REPLICA_COUNT}" \
  '{
    run_id: $run_id,
    job_type: "l3_pilot_reward_plumbing_smoke",
    node: $node,
    gpu_allocation: $gpu_allocation,
    gpu_ids: $gpu_ids,
    tensor_parallel_width: $tensor_parallel_width,
    replica_count: $replica_count,
    placement_justification: "One synchronous EasyR1/GRPO smoke is colocated on four GPUs of one node; four independent TP1 rollout replicas serve request shards while training and rollout remain colocated.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: $config_path,
    source_config_path: $source_config_path,
    config_hash: $config_hash,
    base_config_hash: $base_config_hash,
    data_manifest: "data/geo3k_pilot_filtered.jsonl",
    data_manifest_hash: $data_hash,
    model_revision: "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
    seed: 1,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$shadow_path],
    stdout_stderr_log: $log_path,
    ray_tmp_dir: $ray_tmp_dir,
    checkpoint_path: $checkpoint_path,
    deviations: [
      "Five-step plumbing smoke disables scheduled validation and checkpoint saves; EasyR1 may still perform an unconditional final save in the isolated smoke checkpoint namespace. All rollout, group, reward, optimizer, and image-condition settings remain the A1 pilot settings."
    ]
  }' > "${MANIFEST_PATH}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP_DIR}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK_PATH}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW_PATH}' HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST_PATH}' '${ROOT}/${LOG_PATH}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_PATH}')"

sleep 20
REMOTE_PID="$(cat "${PID_PATH}")"
if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "Pilot reward smoke exited during startup; log follows:" >&2
  sed -n '1,240p' "${LOG_PATH}" >&2 || true
  exit 1
fi

printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_pilot_reward_smoke.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
