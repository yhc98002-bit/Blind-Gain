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

# --- registration gates: the amendment and the split registration must be
# --- tracked and byte-clean at HEAD before any optimizer step.
REGISTRATIONS=(
  docs/registered_m7_amendment_v1.md
  docs/registered_m7_heldout_split_v2.md
  docs/registered_extensions_v1.md
)
CRITICAL=("${REGISTRATIONS[@]}" "${CONFIG}" scripts/launch_m7_virl_arm.sh scripts/build_m7_heldout_split_v2.py scripts/build_m7_configs.py)
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
  data/virl39k_m7_split_manifest_v2.json >/dev/null || {
  echo "corpus hashes do not match the registered image-disjoint split" >&2; exit 3; }

CHECKPOINT_PATH="$(python3 -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_checkpoint_path"])' "${CONFIG}")"
[[ ! -e "${CHECKPOINT_PATH}" ]] || { echo "refusing to overwrite M7 checkpoints: ${CHECKPOINT_PATH}" >&2; exit 73; }

# --- one synchronous RL trainer per node
if ssh "${NODE}" "pgrep -f 'verl.trainer.main' >/dev/null"; then
  echo "refusing to colocate a second RL trainer on ${NODE}" >&2
  exit 75
fi
IFS=',' read -r -a GPU_ARRAY <<< "${GPU_IDS}"
for GPU in "${GPU_ARRAY[@]}"; do
  if [[ -n "$(ssh "${NODE}" "nvidia-smi -i ${GPU} --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
    echo "GPU ${NODE}:${GPU} is occupied" >&2
    exit 75
  fi
done

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
cp "${CONFIG}" "${EFFECTIVE}"

COMMAND="cd ${ROOT} && CUDA_VISIBLE_DEVICES=${GPU_IDS} PYTHONHASHSEED=${SEED} TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home PYTHONPATH=${ROOT}/artifacts/repos/EasyR1 .venv/bin/python -u -m verl.trainer.main config=${ROOT}/${EFFECTIVE}"
jq -n \
  --arg run_id "${RUN_ID}" --arg git "$(git rev-parse HEAD)" --arg arm "${ARM}" \
  --argjson seed "${SEED}" --arg node "${NODE}" --arg config "${CONFIG}" \
  --arg config_sha "${CONFIG_SHA}" --arg train "${TRAIN_FILE}" --arg train_sha "${TRAIN_SHA}" \
  --arg val "${VAL_FILE}" --arg val_sha "${VAL_SHA}" --arg ckpt "${CHECKPOINT_PATH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --argjson gpus "$(printf '%s' "[${GPU_IDS}]")" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m7_virl_stratified_arm",registration:"docs/registered_m7_amendment_v1.md",
    split_registration:"docs/registered_m7_heldout_split_v2.md",
    arm:$arm,seed:$seed,node:$node,gpu_ids:$gpus,
    tensor_parallel_width:1,replica_count:4,
    placement_justification:"One synchronous RL trainer per node on four disjoint GPUs; matched to the registered Geometry3K pilot recipe with only the corpus changed.",
    git_hash:$git,config_path:$config,config_hash:$config_sha,
    data_manifest:$train,data_manifest_hash:$train_sha,
    heldout_manifest:$val,heldout_manifest_hash:$val_sha,
    checkpoint_path:$ckpt,command:$command,
    start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,performance_values_opened:false,
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

ssh "${NODE}" "cd ${ROOT} && (nohup bash -lc '${COMMAND}' > ${ROOT}/${LOG} 2>&1 & echo \$! > ${ROOT}/${RUN_DIR}/pids/${NODE}.pid)"
sleep 5
printf '%s\n' "${RUN_DIR}"
