#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 NODE [CUDA_VISIBLE_DEVICES]" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="${2:-0,1,2,3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/lib/run_paths.sh"
cd "${ROOT}"
RUN_ID="anchor_a0_recipe_3b_geo3k_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
CONFIG_PATH="${ROOT}/configs/train/anchor_a0_recipe_3b_geo3k.yaml"
LOG_PATH="${RUN_DIR}/logs/${NODE}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
LOCK_PATH="/tmp/blind_gains_${NODE}_anchor_a0_recipe.lock"
RAY_TMP_DIR="$(short_ray_tmp_dir "${USER}:${NODE}:${RUN_ID}")"
CHECKPOINT_PATH="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${RUN_ID}"
COMMAND="python -u -m verl.trainer.main config=${CONFIG_PATH} trainer.save_checkpoint_path=${CHECKPOINT_PATH} trainer.experiment_name=${RUN_ID}"

if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*anchor_a0_recipe_3b_geo3k.yaml'"; then
  echo "Refusing duplicate anchor launch on ${NODE}: a matching EasyR1 process is active." >&2
  exit 73
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

GIT_HASH="$(git rev-parse HEAD)"
BASE_CONFIG_HASH="$(sha256sum "${CONFIG_PATH}" | awk '{print $1}')"
CONFIG_HASH="$( { cat "${CONFIG_PATH}"; printf '\ntrainer.save_checkpoint_path=%s\ntrainer.experiment_name=%s\n' "${CHECKPOINT_PATH}" "${RUN_ID}"; } | sha256sum | awk '{print $1}')"
DATA_HASH="$(printf 'hiyouga/geometry3k@train|hiyouga/geometry3k@test' | sha256sum | awk '{print $1}')"
START_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "${MANIFEST_PATH}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_1_anchor_a0_recipe_3b_geo3k",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_path": "${CONFIG_PATH}",
  "config_hash": "${CONFIG_HASH}",
  "base_config_hash": "${BASE_CONFIG_HASH}",
  "seed": 1,
  "data_manifest": "hiyouga/geometry3k@train|hiyouga/geometry3k@test",
  "data_manifest_hash": "${DATA_HASH}",
  "command": "PYTHONPATH=${ROOT}/artifacts/repos/EasyR1 ${COMMAND}",
  "start_time_utc": "${START_TIME}",
  "end_time_utc": null,
  "status": "running",
  "ray_tmp_dir": "${RAY_TMP_DIR}",
  "expected_artifact": "${CHECKPOINT_PATH}/global_step_100/actor",
  "stdout_stderr_log": "${LOG_PATH}"
}
JSON

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${CHECKPOINT_PATH}' '${RAY_TMP_DIR}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK_PATH}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1':\${PYTHONPATH:-} ${COMMAND} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"

sleep 20
REMOTE_PID="$(cat "${PID_PATH}")"
if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "Anchor process exited during startup; log follows:" >&2
  ssh "${NODE}" "sed -n '1,240p' '${ROOT}/${LOG_PATH}'" >&2 || true
  exit 1
fi

printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_anchor_a0_recipe_3b_geo3k_run.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
