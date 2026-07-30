#!/usr/bin/env bash
# Launch one C5 7B access-pair arm (ladder rung R4).
#
# Modeled on scripts/launch_m7_virl_arm.sh with three deliberate improvements:
#   1. The trainer is routed through scripts/run_manifest_job.py (like
#      scripts/launch_mech_pilot_arm.sh), so the manifest finalizes itself on
#      exit instead of staying "running" forever.
#   2. GPU-scope colocation checking reuses scripts/m7_gpu_occupancy_guard.py.
#   3. The TOCTOU window that killed M7 arm 4's first attempt is closed:
#      after the guard passes, a RESERVATION claim file is written per claimed
#      GPU under /dev/shm/blind-gains/gpu_claims on the node BEFORE anything
#      launches, the guard is re-run with --ignore-claim-run-id to confirm no
#      competitor moved in between the first pass and the claims, and the
#      guard treats fresh claims (age < 30 min or recorded pid alive) as
#      occupied.  This protects the minutes-long vLLM init during which the
#      trainer holds no GPU memory.  Claims are removed if the launch aborts
#      and expire by age/pid otherwise, so a crashed launcher cannot wedge the
#      node for longer than 30 minutes.  Fail-closed throughout.
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <a1_real|a2_gray> <an12|an29> <gpu-ids csv, e.g. 0,1,2,3>" >&2
  exit 2
fi

# jq lives in ~/.local/bin, which non-interactive shells do not put on PATH.
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
PY="${ROOT}/.venv/bin/python"
ARM="$1"
NODE="$2"
GPU_IDS="$3"
SEED=1
LABEL="c5_${ARM}_seed${SEED}_7b"
CONFIG="configs/train/${LABEL}.yaml"
INVENTORY="reports/c5_arm_configs_v1.json"

[[ "${ARM}" =~ ^(a1_real|a2_gray)$ ]] || {
  echo "unknown C5 arm: ${ARM} (C5 registers a1_real and a2_gray only; A2b/A3 are NOT run at 7B)" >&2; exit 2; }
[[ "${NODE}" =~ ^(an12|an29)$ ]] || { echo "unknown node" >&2; exit 2; }
[[ "${GPU_IDS}" =~ ^[0-7](,[0-7])*$ ]] || { echo "invalid gpu ids" >&2; exit 2; }
# the config fixes n_gpus_per_node; a mismatched list silently mis-shards
GPU_COUNT="$(printf '%s' "${GPU_IDS}" | tr ',' '\n' | sort -u | grep -c .)"
LISTED_COUNT="$(printf '%s' "${GPU_IDS}" | tr ',' '\n' | grep -c .)"
[[ "${GPU_COUNT}" == "${LISTED_COUNT}" ]] || { echo "duplicate gpu ids in ${GPU_IDS}" >&2; exit 2; }
CFG_GPUS="$(grep -E '^[[:space:]]+n_gpus_per_node:' "${CONFIG}" | awk '{print $2}')"
[[ "${GPU_COUNT}" == "${CFG_GPUS}" ]] || {
  echo "gpu count ${GPU_COUNT} != config n_gpus_per_node ${CFG_GPUS}" >&2; exit 2; }

# --- registration gates: fail-closed, merged-at-HEAD is sign-off (I9).
REGISTRATIONS=(
  docs/registered_c5_7b_access_pair_v1.md
  docs/registered_extensions_v1.md
)
CRITICAL=("${REGISTRATIONS[@]}" "${CONFIG}" "${INVENTORY}"
  scripts/launch_c5_7b_arm.sh scripts/build_c5_configs.py
  scripts/m7_gpu_occupancy_guard.py scripts/run_manifest_job.py
  scripts/finalize_run_manifest.py src/rewards/pilot_reward.py)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked C5 contract: ${FILE}" >&2; exit 3; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "C5 contract differs from HEAD" >&2; exit 3; }

# --- frozen input identity: the config must be the registered generated
# --- artifact, byte for byte.
CONFIG_SHA="$(sha256sum "${CONFIG}" | awk '{print $1}')"
jq -e --arg cfg "${CONFIG}" --arg sha "${CONFIG_SHA}" \
  '[.configs[] | select(.config == $cfg and .config_sha256 == $sha)] | length == 1' \
  "${INVENTORY}" >/dev/null || {
  echo "config hash is not the registered generated artifact" >&2; exit 3; }

# arm <-> image-condition binding, from the effective bytes, not the filename
CONFIG_CONDITION="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["data"]["image_condition"])' "${CONFIG}")"
case "${ARM}" in
  a1_real) WANT_CONDITION="real" ;;
  a2_gray) WANT_CONDITION="gray" ;;
esac
[[ "${CONFIG_CONDITION}" == "${WANT_CONDITION}" ]] || {
  echo "config image_condition ${CONFIG_CONDITION} does not match arm ${ARM}" >&2; exit 3; }

# --- corpus identity vs the registered inventory
TRAIN_FILE="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["data"]["train_files"])' "${CONFIG}")"
TRAIN_SHA="$(sha256sum "${TRAIN_FILE}" | awk '{print $1}')"
IDS_FILE="$(jq -er '.filtered_ids' "${INVENTORY}")"
IDS_SHA="$(sha256sum "${IDS_FILE}" | awk '{print $1}')"
jq -e --arg tf "${TRAIN_FILE}" --arg t "${TRAIN_SHA}" --arg i "${IDS_SHA}" \
  '(.train_file == $tf) and (.train_sha256 == $t) and (.filtered_ids_sha256 == $i)' \
  "${INVENTORY}" >/dev/null || {
  echo "corpus hashes do not match the registered inventory" >&2; exit 3; }

# --- 7B model identity vs the registered inventory.  The model directory has
# --- no upstream revision marker, so identity is the computed on-disk hash
# --- set from build_c5_configs.py.  Index + per-shard byte sizes are checked
# --- on every launch; full per-shard SHA256s (minutes over 16 GB) with
# --- C5_VERIFY_SHARD_HASHES=1.
MODEL_PATH="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["worker"]["actor"]["model"]["model_path"])' "${CONFIG}")"
INV_MODEL_REL="$(jq -er '.model.path' "${INVENTORY}")"
[[ "${MODEL_PATH}" == "${ROOT}/${INV_MODEL_REL}" ]] || {
  echo "config model_path ${MODEL_PATH} is not the registered ${INV_MODEL_REL}" >&2; exit 3; }
INDEX_SHA="$(sha256sum "${MODEL_PATH}/model.safetensors.index.json" | awk '{print $1}')"
jq -e --arg s "${INDEX_SHA}" '.model.index_sha256 == $s' "${INVENTORY}" >/dev/null || {
  echo "7B model index hash does not match the registered identity" >&2; exit 3; }
"${PY}" - "${INVENTORY}" "${MODEL_PATH}" "${C5_VERIFY_SHARD_HASHES:-0}" <<'PYCHECK'
import hashlib, json, sys
from pathlib import Path
inventory = json.loads(Path(sys.argv[1]).read_text())
model_dir = Path(sys.argv[2])
full = sys.argv[3] == "1"
for shard in inventory["model"]["shards"]:
    path = model_dir / shard["file"]
    if not path.is_file():
        sys.exit(f"registered shard missing on disk: {path}")
    if path.stat().st_size != shard["bytes"]:
        sys.exit(f"shard size drift: {path} is {path.stat().st_size}, registered {shard['bytes']}")
    if full:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 22), b""):
                digest.update(chunk)
        if digest.hexdigest() != shard["sha256"]:
            sys.exit(f"shard hash drift: {path}")
print(f"model identity ok ({'full shard hashes' if full else 'index hash + shard sizes'})")
PYCHECK

CHECKPOINT_PATH="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_checkpoint_path"])' "${CONFIG}")"
[[ ! -e "${CHECKPOINT_PATH}" ]] || { echo "refusing to overwrite C5 checkpoints: ${CHECKPOINT_PATH}" >&2; exit 73; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${LABEL}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"

# --- colocation guard, pass 1: GPU scope, not node scope.  Node co-tenancy
# --- is explicitly normal per the CLAUDE.md placement policy; refusal is
# --- conditioned on GPU-set overlap alone, and indeterminate occupancy
# --- refuses (exit 75).
if ! "${PY}" "${ROOT}/scripts/m7_gpu_occupancy_guard.py" \
    --node "${NODE}" --gpus "${GPU_IDS}"; then
  echo "refusing to launch ${LABEL} on ${NODE}:${GPU_IDS}: GPU-scope guard denied" >&2
  exit 75
fi

# --- RESERVATION claims (TOCTOU close): write one claim per GPU on the node
# --- BEFORE launching, so a competing launcher's guard sees these GPUs as
# --- occupied during the minutes-long vLLM init in which the trainer holds no
# --- GPU memory.  Claims are also archived in the run directory.  If this
# --- launcher aborts before the runner is confirmed alive, the trap removes
# --- them; otherwise they carry the runner pid and expire with it.
CLAIMS_NODE_DIR="/dev/shm/blind-gains/gpu_claims"
CLAIMS_LOCAL_DIR="${RUN_DIR}/gpu_claims"
mkdir -p "${CLAIMS_LOCAL_DIR}"
NODE_CLAIM_PATHS=()
IFS=',' read -r -a GPU_ARR <<< "${GPU_IDS}"
write_claims() {
  local pid_json="$1"
  local gpu
  for gpu in "${GPU_ARR[@]}"; do
    jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" \
      --argjson gpu "${gpu}" --argjson pid "${pid_json}" \
      --arg created "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{schema_version:"blind-gains.gpu-claim.v1",run_id:$run_id,node:$node,
        gpu:$gpu,pid:$pid,created_utc:$created,
        purpose:"c5_7b_access_arm",
        registration:"docs/registered_c5_7b_access_pair_v1.md"}' \
      > "${CLAIMS_LOCAL_DIR}/${NODE}_gpu${gpu}.claim"
  done
  ssh "${NODE}" "mkdir -p '${CLAIMS_NODE_DIR}' && cp '${ROOT}/${CLAIMS_LOCAL_DIR}/'*.claim '${CLAIMS_NODE_DIR}/'"
}
CLAIMS_PLACED=0
LAUNCHED=0
CLAIM_ABORT_STATE="clean"
cleanup_claims() {
  # Remove claims only on a CLEAN abort (nothing was started).  If the launch
  # reached the runner and its state is indeterminate, the claims are left to
  # protect a possibly-live startup and expire on their own in 30 minutes.
  if [[ "${CLAIM_ABORT_STATE}" != "clean" ]]; then
    echo "leaving GPU claims in place for expiry: launch state is ${CLAIM_ABORT_STATE}" >&2
    return
  fi
  if [[ "${CLAIMS_PLACED}" == 1 && "${LAUNCHED}" != 1 ]]; then
    local args=()
    local gpu
    for gpu in "${GPU_ARR[@]}"; do
      args+=("'${CLAIMS_NODE_DIR}/${NODE}_gpu${gpu}.claim'")
    done
    ssh "${NODE}" "rm -f ${args[*]}" || \
      echo "WARNING: could not remove GPU claims on ${NODE}; they expire in 30 min" >&2
  fi
}
trap cleanup_claims EXIT
write_claims null
NODE_CLAIM_PATHS=()
for GPU in "${GPU_ARR[@]}"; do
  NODE_CLAIM_PATHS+=("${CLAIMS_NODE_DIR}/${NODE}_gpu${GPU}.claim")
done
CLAIMS_PLACED=1

# --- colocation guard, pass 2: re-check with our own claims excluded.  This
# --- catches a competitor that claimed or occupied the same GPUs between
# --- pass 1 and our claim placement; if it refuses, the trap removes our
# --- claims and nothing has launched.
if ! "${PY}" "${ROOT}/scripts/m7_gpu_occupancy_guard.py" \
    --node "${NODE}" --gpus "${GPU_IDS}" --ignore-claim-run-id "${RUN_ID}"; then
  echo "refusing to launch ${LABEL}: a competitor moved in during claim placement" >&2
  exit 75
fi

# --- storage floor: ~85 GB of model-only checkpoints plus logs
FREE_BYTES="$(df --output=avail -B1 "${ROOT}" | tail -1)"
if (( FREE_BYTES < 150000000000 )); then
  echo "shared storage below the C5 launch floor: ${FREE_BYTES} bytes" >&2
  exit 76
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
EFFECTIVE="${RUN_DIR}/effective_config.yaml"
install -m 0444 "${CONFIG}" "${EFFECTIVE}"

# --- deviation provenance, DERIVED from the effective config against the 3B
# --- pilot template, never hardcoded per arm.  The registration sanctions
# --- exactly two mechanics deviations; anything else that differs here is a
# --- bug this derivation makes visible in the manifest.
PILOT_TEMPLATE="configs/train/mech_a1_real_3b_geo3k.yaml"
GPU_MEM_UTIL="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["worker"]["rollout"]["gpu_memory_utilization"])' "${EFFECTIVE}")"
PILOT_GMU="$("${PY}" -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))["worker"]["rollout"]["gpu_memory_utilization"])' "${PILOT_TEMPLATE}")"
SAVE_MODEL_ONLY="$("${PY}" -c 'import yaml,sys; print(str(bool(yaml.safe_load(open(sys.argv[1]))["trainer"].get("save_model_only", False))).lower())' "${EFFECTIVE}")"
SAVE_FREQ="$("${PY}" -c 'import yaml,sys; print(int(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_freq"]))' "${EFFECTIVE}")"
DEVIATIONS='[]'
if [[ "${GPU_MEM_UTIL}" != "${PILOT_GMU}" ]]; then
  DEVIATIONS="$(jq -c --argjson got "${GPU_MEM_UTIL}" --argjson pilot "${PILOT_GMU}" \
    '. + [{field:"worker.rollout.gpu_memory_utilization",value:$got,pilot_value:$pilot,
      kind:"mechanics",
      registration:"docs/registered_c5_7b_access_pair_v1.md",section:"Mechanics deviations (1)",
      sanctioned_in:"scripts/build_c5_configs.py:SANCTIONED_DEVIATIONS",
      effect:"vLLM serving memory reservation only; no estimand is touched. 7B at the inherited 0.6 projects to 75-78 GB against the measured 3B peak of 63.58/79.33 GB; 0.45 projects to ~65 GB."}]' \
    <<< "${DEVIATIONS}")"
fi
if [[ "${SAVE_MODEL_ONLY}" == "true" ]]; then
  DEVIATIONS="$(jq -c --argjson freq "${SAVE_FREQ}" \
    '. + [{field:"trainer.save_model_only",value:true,
      kind:"mechanics",
      registration:"docs/registered_c5_7b_access_pair_v1.md",section:"Mechanics deviations (2)",
      sanctioned_in:"scripts/build_c5_configs.py:SANCTIONED_DEVIATIONS",
      save_freq_unchanged:$freq,
      effect:"Checkpoints hold HF weights only (~17 GB/save, ~85 GB/arm) instead of full FSDP state (~600 GB/arm). save_freq is unchanged, so the registered checkpoint CADENCE holds and only the on-disk FORMAT differs; the cost is that this arm cannot be resumed mid-run. Applied to BOTH arms, so no arm-to-arm asymmetry."}]' \
    <<< "${DEVIATIONS}")"
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
BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=25000000000 \
BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' \
BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' \
BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 \
BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' \
BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 \
HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' \
TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}'"

# Recorded verbatim in the run manifest; scripts/run_manifest_job.py executes
# exactly this string and finalizes the manifest when it exits.
COMMAND="env ${ENV_VARS} ${ROOT}/.venv/bin/python -u -m verl.trainer.main config=${ROOT}/${EFFECTIVE}"
CLAIMS_JSON="$(printf '%s\n' "${NODE_CLAIM_PATHS[@]}" | jq -Rsc 'split("\n") | map(select(length > 0))')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git "$(git rev-parse HEAD)" --arg arm "${ARM}" \
  --argjson seed "${SEED}" --arg node "${NODE}" --arg condition "${CONFIG_CONDITION}" \
  --arg config "${CONFIG}" --arg config_sha "${CONFIG_SHA}" \
  --arg train "${TRAIN_FILE}" --arg train_sha "${TRAIN_SHA}" \
  --arg ids "${IDS_FILE}" --arg ids_sha "${IDS_SHA}" \
  --arg model_path "${MODEL_PATH}" --arg model_index_sha "${INDEX_SHA}" \
  --arg ckpt "${CHECKPOINT_PATH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg shadow "${SHADOW}" \
  --argjson gpus "$(printf '%s' "[${GPU_IDS}]")" \
  --argjson claims "${CLAIMS_JSON}" \
  --argjson deviations "${DEVIATIONS}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"c5_7b_access_arm",
    registration:"docs/registered_c5_7b_access_pair_v1.md",
    amends:"docs/registered_extensions_v1.md Extension 4",
    arm:$arm,seed:$seed,image_condition:$condition,node:$node,gpu_ids:$gpus,
    tensor_parallel_width:1,replica_count:4,
    placement_policy_version:"pi-2026-07-11",
    placement_justification:"One synchronous RL trainer on four disjoint GPUs of a single node; the registered Geometry3K pilot recipe with only the model scaled to 7B. TP1 with four independent replicas per the pi-2026-07-11 addendum and the registered_extensions_v1.md Global Contract (TP at or below 7B is 1). Co-tenancy with other GPU-disjoint jobs on the same node is normal per the CLAUDE.md placement policy and is enforced at GPU scope by scripts/m7_gpu_occupancy_guard.py, including reservation-claim occupancy.",
    git_hash:$git,config_path:$config,config_hash:$config_sha,
    data_manifest:$train,data_manifest_hash:$train_sha,
    filtered_ids:$ids,filtered_ids_sha256:$ids_sha,
    model_path:$model_path,
    model_revision:null,
    model_identity:"on-disk hash set registered in reports/c5_arm_configs_v1.json (no upstream revision marker on disk); index sha256 recorded here",
    model_index_sha256:$model_index_sha,
    gpu_claims:$claims,claim_fresh_seconds:1800,
    checkpoint_path:$ckpt,command:$command,
    start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,performance_values_opened:false,
    expected_artifacts:[$shadow, ($ckpt + "/experiment_log.jsonl"), ($ckpt + "/checkpoint_tracker.json")],
    scientific_gate_decision:null,deviations:$deviations}' > "${MANIFEST}"

# --- manifest lifecycle: started THROUGH scripts/run_manifest_job.py, which
# --- reads payload["command"], waits for it, and calls finalize_manifest on
# --- exit -- the M7 arm-1 manifest stayed "running" forever because its
# --- launcher exec'd verl.trainer.main directly.  The recorded pid is the
# --- runner; the trainer's own argv still carries `-m verl.trainer.main
# --- config=...`, so the occupancy guard resolves it exactly as before.
CLAIM_ABORT_STATE="indeterminate: runner dispatch attempted"
ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_TMP_DIR}' '${JOB_TMP_DIR}' && (nohup setsid flock -n --no-fork '${LOCK}' '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > '${ROOT}/${RUN_DIR}/logs/runner.log' 2>&1 < /dev/null & echo \$! > '${ROOT}/${RUN_DIR}/pids/${NODE}.pid')"
sleep 25
REMOTE_PID="$(cat "${ROOT}/${RUN_DIR}/pids/${NODE}.pid" 2>/dev/null || true)"
if [[ -z "${REMOTE_PID}" ]] || ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "C5 arm exited during startup; inspect ${LOG}" >&2
  echo "GPU claims are left in place and expire in 30 min" >&2
  exit 1
fi
# refresh the claims with the live runner pid: from here on they stay
# occupied while the runner lives and expire by age once it exits.
write_claims "${REMOTE_PID}"
LAUNCHED=1
printf '%s\n' "${RUN_DIR}"
