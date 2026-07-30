#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <a1_real|a2_gray|a2b_noimage|a3_caption> <seed:1|2> <an12|an29> <gpu-ids csv>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
ARM="$1"
SEED="$2"
NODE="$3"
GPU_IDS="$4"
LABEL="m7_virl_${ARM}_seed${SEED}"
CONFIG="configs/train/${LABEL}_3b.yaml"

[[ "${ARM}" =~ ^(a1_real|a2_gray|a2b_noimage|a3_caption)$ ]] || { echo "unknown M7 arm" >&2; exit 2; }
[[ "${SEED}" =~ ^[12]$ ]] || { echo "M7 registers exactly two seeds" >&2; exit 2; }
[[ "${NODE}" =~ ^(an12|an29)$ ]] || { echo "unknown node" >&2; exit 2; }
[[ "${GPU_IDS}" =~ ^[0-7](,[0-7])*$ ]] || { echo "invalid gpu ids" >&2; exit 2; }
# the config fixes n_gpus_per_node; a mismatched list silently mis-shards
GPU_COUNT="$(printf '%s' "${GPU_IDS}" | tr ',' '\n' | sort -u | grep -c .)"
CFG_GPUS="$(grep -E '^[[:space:]]+n_gpus_per_node:' "${CONFIG}" | awk '{print $2}')"
[[ "${GPU_COUNT}" == "${CFG_GPUS}" ]] || {
  echo "gpu count ${GPU_COUNT} != config n_gpus_per_node ${CFG_GPUS}" >&2; exit 2; }

# --- registration gates: the amendment and the split registration must be
# --- tracked and byte-clean at HEAD before any optimizer step.
REGISTRATIONS=(
  docs/registered_m7_amendment_v1.md
  docs/registered_m7_heldout_split_v2.md
  docs/registered_extensions_v1.md
  docs/registered_m7_single_image_v2.md
  # the seed-scope / checkpoint-format amendment is in force for arms 2-4 and
  # its 1(b) requires the deviation be recorded in each run manifest below, so
  # it must be tracked and byte-clean at HEAD like every other M7 registration
  docs/registered_m7_seed_scope_v1.md
)
CRITICAL=("${REGISTRATIONS[@]}" "${CONFIG}" scripts/launch_m7_virl_arm.sh scripts/build_m7_heldout_split_v2.py scripts/build_m7_configs.py scripts/m7_gpu_occupancy_guard.py)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked M7 contract: ${FILE}" >&2; exit 3; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "M7 contract differs from HEAD" >&2; exit 3; }

# --- frozen input identity
CONFIG_SHA="$(sha256sum "${CONFIG}" | awk '{print $1}')"
jq -e --arg cfg "${CONFIG}" --arg sha "${CONFIG_SHA}" \
  '[.configs[] | select(.config == $cfg and .config_sha256 == $sha)] | length == 1' \
  reports/m7_arm_configs_v1.json >/dev/null || {
  echo "config hash is not the registered generated artifact" >&2; exit 3; }

TRAIN_FILE="$(python3 -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["data"]["train_files"])' "${CONFIG}")"
VAL_FILE="$(python3 -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["data"]["val_files"])' "${CONFIG}")"
TRAIN_SHA="$(sha256sum "${TRAIN_FILE}" | awk '{print $1}')"
VAL_SHA="$(sha256sum "${VAL_FILE}" | awk '{print $1}')"
jq -e --arg t "${TRAIN_SHA}" --arg v "${VAL_SHA}" \
  '(.train_sha256 == $t) and (.heldout_sha256 == $v) and (.image_integrity.shared_images == 0)' \
  data/virl39k_m7_split_manifest_v3.json >/dev/null || {
  echo "corpus hashes do not match the registered image-disjoint split" >&2; exit 3; }

CHECKPOINT_PATH="$(python3 -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_checkpoint_path"])' "${CONFIG}")"
[[ ! -e "${CHECKPOINT_PATH}" ]] || { echo "refusing to overwrite M7 checkpoints: ${CHECKPOINT_PATH}" >&2; exit 73; }

# --- colocation guard: GPU scope, not node scope.
# This narrowing implements the placement policy CLAUDE.md states verbatim:
#   "Single-node placement for every job unless it genuinely requires >8 GPUs.
#    Never split one training or serving job across an12/an29.
#    Colocating disjoint-GPU jobs on one node is normal; the researcher's own
#    processes are normal neighbors, never anomalies."
# NODE CO-TENANCY IS THEREFORE EXPLICITLY NORMAL and is not a refusal
# condition. The predecessor guard refused whenever ANY verl trainer ran on the
# target node, which capped M7 at one arm per node and idled 10 GPUs; refusal
# is now conditioned on GPU-set OVERLAP alone.
# The helper derives occupancy from actual state -- nvidia-smi compute-apps
# plus each live trainer's own run manifest / effective config -- never from a
# process-name regex alone, keeps the bracketed-pattern self-match protection
# (a defect that bit this project before), and fails closed: indeterminate
# occupancy exits 75 exactly like a real overlap.
if ! python3 "${ROOT}/scripts/m7_gpu_occupancy_guard.py" \
    --node "${NODE}" --gpus "${GPU_IDS}"; then
  echo "refusing to launch ${LABEL} on ${NODE}:${GPU_IDS}: GPU-scope guard denied" >&2
  exit 75
fi

# --- storage floor before a run that writes ~6 raw saves
FREE_BYTES="$(df --output=avail -B1 "${ROOT}" | tail -1)"
if (( FREE_BYTES < 300000000000 )); then
  echo "shared storage below the M7 launch floor: ${FREE_BYTES} bytes" >&2
  exit 76
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${LABEL}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
EFFECTIVE="${RUN_DIR}/effective_config.yaml"
install -m 0444 "${CONFIG}" "${EFFECTIVE}"

# --- deviation provenance, DERIVED from the effective config, never hardcoded
# --- per arm. docs/registered_m7_seed_scope_v1.md 1(b) sanctions model-only
# --- checkpoints for the arms that carry them and requires the deviation be
# --- "Recorded in SANCTIONED_DEVIATIONS in scripts/build_m7_configs.py and in
# --- each run manifest": the first half is in build_m7_configs.py, this is the
# --- second. Arm 1 runs save_model_only: false and so records no deviation.
SAVE_MODEL_ONLY="$(python3 -c 'import yaml,sys; print(str(bool(yaml.safe_load(open(sys.argv[1]))["trainer"].get("save_model_only", False))).lower())' "${EFFECTIVE}")"
SAVE_FREQ="$(python3 -c 'import yaml,sys; print(int(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_freq"]))' "${EFFECTIVE}")"
if [[ "${SAVE_MODEL_ONLY}" == "true" ]]; then
  DEVIATIONS="$(jq -n --argjson freq "${SAVE_FREQ}" \
    '[{field:"trainer.save_model_only",value:true,
       registration:"docs/registered_m7_seed_scope_v1.md",section:"1(b)",
       sanctioned_in:"scripts/build_m7_configs.py:SANCTIONED_DEVIATIONS",
       save_freq_unchanged:$freq,
       effect:"Checkpoints hold HF weights only (~7.6 GB) instead of full FSDP state including optimizer shards (~38.5 GB). save_freq is unchanged, so the registered matched checkpoint CADENCE holds and only the on-disk FORMAT differs; the cost is that this arm cannot be resumed mid-run."}]')"
else
  DEVIATIONS='[]'
fi

SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1, 1, 12)}')"
RAY_TMP_DIR="/dev/shm/bg-ray-${RAY_DIGEST}"
JOB_TMP_DIR="${RAY_TMP_DIR}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_${LABEL}.lock"

ENV_VARS="PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 \
PYTHONHASHSEED=0 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' \
TMPDIR='${JOB_TMP_DIR}' TMP='${JOB_TMP_DIR}' TEMP='${JOB_TMP_DIR}' \
RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 \
CUDA_VISIBLE_DEVICES='${GPU_IDS}' EASYR1_ATTN_IMPLEMENTATION=sdpa \
BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' \
BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S \
BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000 \
BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' \
BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' \
BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 \
BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' \
BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 \
HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' \
TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}'"

# recorded verbatim in the run manifest so the provenance shows the exact
# environment the trainer ran under, not just the python invocation
COMMAND="env ${ENV_VARS} ${ROOT}/.venv/bin/python -u -m verl.trainer.main config=${ROOT}/${EFFECTIVE}"
jq -n \
  --arg run_id "${RUN_ID}" --arg git "$(git rev-parse HEAD)" --arg arm "${ARM}" \
  --argjson seed "${SEED}" --arg node "${NODE}" --arg config "${CONFIG}" \
  --arg config_sha "${CONFIG_SHA}" --arg train "${TRAIN_FILE}" --arg train_sha "${TRAIN_SHA}" \
  --arg val "${VAL_FILE}" --arg val_sha "${VAL_SHA}" --arg ckpt "${CHECKPOINT_PATH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --argjson gpus "$(printf '%s' "[${GPU_IDS}]")" \
  --argjson deviations "${DEVIATIONS}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m7_virl_stratified_arm",registration:"docs/registered_m7_amendment_v1.md",
    split_registration:"docs/registered_m7_heldout_split_v2.md",
    seed_scope_registration:"docs/registered_m7_seed_scope_v1.md",
    arm:$arm,seed:$seed,node:$node,gpu_ids:$gpus,
    tensor_parallel_width:1,replica_count:4,
    placement_justification:"One synchronous RL trainer on four disjoint GPUs of a single node; matched to the registered Geometry3K pilot recipe with only the corpus changed. Co-tenancy with other GPU-disjoint jobs on the same node is normal per the CLAUDE.md placement policy and is enforced at GPU scope by scripts/m7_gpu_occupancy_guard.py.",
    git_hash:$git,config_path:$config,config_hash:$config_sha,
    data_manifest:$train,data_manifest_hash:$train_sha,
    heldout_manifest:$val,heldout_manifest_hash:$val_sha,
    checkpoint_path:$ckpt,command:$command,
    start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,performance_values_opened:false,
    scientific_gate_decision:null,deviations:$deviations}' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP_DIR}' '${JOB_TMP_DIR}' && (nohup setsid flock -n --no-fork '${LOCK}' env ${ENV_VARS} '${ROOT}/.venv/bin/python' -u -m verl.trainer.main config='${ROOT}/${EFFECTIVE}' > '${ROOT}/${LOG}' 2>&1 < /dev/null & echo \$! > '${ROOT}/${RUN_DIR}/pids/${NODE}.pid')"
sleep 25
REMOTE_PID="$(cat "${ROOT}/${RUN_DIR}/pids/${NODE}.pid" 2>/dev/null || true)"
if [[ -z "${REMOTE_PID}" ]] || ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "M7 arm exited during startup; inspect ${LOG}" >&2
  exit 1
fi
printf '%s\n' "${RUN_DIR}"
