#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 {cp|member} NODE [CUDA_VISIBLE_DEVICES]" >&2
  exit 2
fi

MODE="$1"
NODE="$2"
GPU_LIST="${3:-0,1,2,3,4,5,6,7}"
case "${MODE}" in
  cp)
    SOURCE_CONFIG="configs/train/mini_a5_cp_3b_v1.yaml"
    EXPECTED_GROUP_MODE="joint"
    EXPECTED_REWARD_SUFFIX="src/rewards/cp_grpo_reward.py:compute_score"
    ;;
  member)
    SOURCE_CONFIG="configs/train/mini_a5_same_data_3b_v1.yaml"
    EXPECTED_GROUP_MODE="member"
    EXPECTED_REWARD_SUFFIX="src/rewards/cp_grpo_reward.py:compute_member_score"
    ;;
  *)
    echo "mode must be cp or member" >&2
    exit 2
    ;;
esac
if [[ ! "${GPU_LIST}" =~ ^[0-7](,[0-7]){7}$ ]]; then
  echo "Mini-A5 main arm requires eight comma-separated GPU indices" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
if [[ "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -ne 8 ]]; then
  echo "Mini-A5 main arm GPU indices must be unique" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
REGISTRATION_DOC="docs/registered_mini_a5_main_v1.md"
REGISTRATION_MARKER="reports/mini_a5_main_registration_marker_v1.json"
EASYR1_DIR="${ROOT}/artifacts/repos/EasyR1-mini-a5"
PINNED_EASYR1_REVISION="dd71bbd252694f5f850213eec15795b6b88d9fea"
TRAIN_DATA="data/mini_a5_train_v1/train.parquet"
VAL_DATA="data/mini_a5_plumbing_val_v1.jsonl"
CHECKPOINT_PATH="$(${ROOT}/.venv/bin/python - "${SOURCE_CONFIG}" <<'PY'
import sys, yaml
print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["trainer"]["save_checkpoint_path"])
PY
)"

for path in "${REGISTRATION_DOC}" "${REGISTRATION_MARKER}" "${SOURCE_CONFIG}" "${TRAIN_DATA}" "${VAL_DATA}"; do
  [[ -s "${path}" ]] || { echo "required registered input is absent: ${path}" >&2; exit 2; }
done
[[ -d "${EASYR1_DIR}/.git" || -f "${EASYR1_DIR}/.git" ]] || {
  echo "prepared isolated EasyR1 mini-A5 worktree is absent: ${EASYR1_DIR}" >&2
  exit 2
}
[[ ! -e "${CHECKPOINT_PATH}" ]] || {
  echo "refusing to overwrite Mini-A5 main checkpoint: ${CHECKPOINT_PATH}" >&2
  exit 2
}
git diff --quiet -- \
  "${REGISTRATION_DOC}" \
  "${REGISTRATION_MARKER}" \
  "${SOURCE_CONFIG}" \
  "${TRAIN_DATA}" \
  docs/easyr1_mini_a5_pair_grouping_patch.diff \
  src/train/cp_grouping.py \
  src/rewards/cp_grpo_reward.py \
  scripts/launch_mini_a5_main.sh

REGISTRATION_COMMIT="$(jq -er '.registration_commit' "${REGISTRATION_MARKER}")"
git cat-file -e "${REGISTRATION_COMMIT}^{commit}"
git merge-base --is-ancestor "${REGISTRATION_COMMIT}" HEAD
jq -e \
  --arg mode "${MODE}" \
  --arg doc_sha "$(sha256sum "${REGISTRATION_DOC}" | awk '{print $1}')" \
  --arg config_sha "$(sha256sum "${SOURCE_CONFIG}" | awk '{print $1}')" \
  --arg corpus_sha "$(sha256sum "${TRAIN_DATA}" | awk '{print $1}')" \
  --arg launcher_sha "$(sha256sum scripts/launch_mini_a5_main.sh | awk '{print $1}')" \
  '(.status == "registered")
   and (.registration_document_sha256 == $doc_sha)
   and (.main_config_sha256[$mode] == $config_sha)
   and (.train_corpus_sha256 == $corpus_sha)
   and (.launcher_sha256 == $launcher_sha)
   and (.main_optimizer_steps_authorized_per_arm == 120)' \
  "${REGISTRATION_MARKER}" >/dev/null

[[ "$(git -C "${EASYR1_DIR}" rev-parse HEAD)" == "${PINNED_EASYR1_REVISION}" ]] || {
  echo "isolated EasyR1 worktree revision drift" >&2
  exit 2
}
EASYR1_DIFF_SHA="$({ git -C "${EASYR1_DIR}" diff --binary --no-ext-diff; } | sha256sum | awk '{print $1}')"
[[ "${EASYR1_DIFF_SHA}" == "$(jq -er '.easyr1_worktree_diff_sha256' "${REGISTRATION_MARKER}")" ]] || {
  echo "isolated EasyR1 worktree patch inventory drift" >&2
  exit 2
}

for GPU in "${GPUS[@]}"; do
  USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
  if [[ ! "${USED_MIB}" =~ ^[0-9]+$ || "${USED_MIB}" -ge 1024 ]]; then
    echo "refusing Mini-A5 main arm: ${NODE} GPU ${GPU} has ${USED_MIB:-unknown} MiB allocated" >&2
    exit 75
  fi
done
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main'"; then
  echo "refusing Mini-A5 main arm: another synchronous trainer is active on ${NODE}" >&2
  exit 73
fi

"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/checkpoints" \
  --operation "mini_a5_${MODE}_main_checkpoints" \
  --required-bytes 129000000000 \
  --log "${ROOT}/logs/storage_guard.jsonl"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_${MODE}_main_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
EFFECTIVE_CONFIG="${RUN_DIR}/effective_config.yaml"
EASYR1_SNAPSHOT="${RUN_DIR}/easyr1_worktree.patch"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
STORAGE_LOG="${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1, 1, 12)}')"
RAY_TMP="/dev/shm/bg-ray-${RAY_DIGEST}"
LOCK="/dev/shm/blind-gains/locks/mini_a5_main.lock"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
install -m 0444 "${SOURCE_CONFIG}" "${EFFECTIVE_CONFIG}"
git -C "${EASYR1_DIR}" diff --binary --no-ext-diff > "${EASYR1_SNAPSHOT}"
chmod 0444 "${EASYR1_SNAPSHOT}"

RESOLVED_MODE="$(${ROOT}/.venv/bin/python - "${EFFECTIVE_CONFIG}" <<'PY'
import sys, yaml
config = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
print(config["algorithm"]["pair_group_mode"])
PY
)"
RESOLVED_REWARD="$(${ROOT}/.venv/bin/python - "${EFFECTIVE_CONFIG}" <<'PY'
import sys, yaml
config = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
print(config["worker"]["reward"]["reward_function"])
PY
)"
RESOLVED_STEPS="$(${ROOT}/.venv/bin/python - "${EFFECTIVE_CONFIG}" <<'PY'
import sys, yaml
print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["trainer"]["max_steps"])
PY
)"
[[ "${RESOLVED_MODE}" == "${EXPECTED_GROUP_MODE}" ]] || { echo "group-mode mismatch" >&2; exit 2; }
[[ "${RESOLVED_REWARD}" == *"${EXPECTED_REWARD_SUFFIX}" ]] || { echo "reward callback mismatch" >&2; exit 2; }
[[ "${RESOLVED_STEPS}" == "120" ]] || { echo "max_steps mismatch: ${RESOLVED_STEPS}" >&2; exit 2; }

COMMAND="PYTHONPATH=${EASYR1_DIR}:${ROOT} python -u -m verl.trainer.main config=${ROOT}/${EFFECTIVE_CONFIG}"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
DATA_HASH="$({
  sha256sum "${TRAIN_DATA}" "${VAL_DATA}" data/mini_a5_fixed_subsets_v1_manifest.json
  sha256sum "${SOURCE_CONFIG}" docs/easyr1_mini_a5_pair_grouping_patch.diff src/train/cp_grouping.py src/rewards/cp_grpo_reward.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg mode "${MODE}" \
  --arg node "${NODE}" \
  --arg gpu_allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg registration_commit "${REGISTRATION_COMMIT}" \
  --arg registration_marker "${REGISTRATION_MARKER}" \
  --arg registration_marker_sha256 "$(sha256sum "${REGISTRATION_MARKER}" | awk '{print $1}')" \
  --arg config_path "${EFFECTIVE_CONFIG}" \
  --arg config_hash "$(sha256sum "${EFFECTIVE_CONFIG}" | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg checkpoint "${CHECKPOINT_PATH}" \
  --arg easyr1_diff "${EASYR1_SNAPSHOT}" \
  --arg easyr1_diff_sha "${EASYR1_DIFF_SHA}" \
  --arg storage_log "${STORAGE_LOG}" \
  --arg ray_tmp "${RAY_TMP}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_registered_main",
    main_mode: $mode,
    status: "running",
    node: $node,
    gpu_allocation: $gpu_allocation,
    gpu_ids: $gpu_ids,
    tensor_parallel_width: 1,
    replica_count: 8,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "One synchronous EasyR1/GRPO main arm occupies all eight GPUs of one fully free node at TP1; no cross-node disaggregation; no colocated trainer.",
    git_hash: $git_hash,
    registration_commit: $registration_commit,
    registration_marker: $registration_marker,
    registration_marker_sha256: $registration_marker_sha256,
    config_path: $config_path,
    config_hash: $config_hash,
    data_manifest: "data/mini_a5_train_v1/train.parquet",
    data_manifest_hash: $data_hash,
    model_revision: "ModelScope Qwen/Qwen2.5-VL-3B-Instruct master; tree 84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568",
    seed: 20260716,
    optimizer_steps_expected: 120,
    command: $command,
    start_time_utc: $start_time,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    checkpoint_path: $checkpoint,
    easyr1_revision: "dd71bbd252694f5f850213eec15795b6b88d9fea",
    easyr1_worktree_patch: $easyr1_diff,
    easyr1_worktree_patch_sha256: $easyr1_diff_sha,
    storage_guard_log: $storage_log,
    ray_tmp_dir: $ray_tmp,
    expected_artifacts: [
      $config_path,
      $easyr1_diff,
      ($checkpoint + "/global_step_120"),
      ($checkpoint + "/experiment_log.jsonl")
    ],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP}' /dev/shm/blind-gains/locks && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR='${RAY_TMP}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_CP_RUNTIME_AUDIT=1 BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=129000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_STORAGE_GUARD_LOG='${ROOT}/${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"

sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "Mini-A5 ${MODE} main arm exited during startup; inspect ${LOG}" >&2
  exit 1
fi
printf '%s\n' "${RUN_DIR}"
