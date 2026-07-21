#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 7 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH MANIFEST RUN_DIR MAX_NEW_TOKENS [GPU_LIST] [IMAGE_MODE]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
MANIFEST="$5"
RUN_DIR="$6"
MAX_NEW_TOKENS="$7"
GPU_LIST="${8:-0 1 2 3 4 5 6 7}"
IMAGE_MODE="${9:-real}"
EVAL_SEED="${BLIND_GAINS_EVAL_SEED:-0}"
PILOT_SOURCE_RUN_INPUT="${BLIND_GAINS_PILOT_SOURCE_RUN:-}"
PILOT_GLOBAL_STEP="${BLIND_GAINS_PILOT_GLOBAL_STEP:-}"
M5_SOURCE_RUN_INPUT="${BLIND_GAINS_M5_SOURCE_RUN:-}"
M5_GLOBAL_STEP="${BLIND_GAINS_M5_GLOBAL_STEP:-}"
ROOT="$(pwd)"
R19_MANIFEST_SHA256="e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2"

if [[ ! "${SHARD_OFFSET}" =~ ^-?[0-9]+$ || ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "SHARD_OFFSET must be an integer and NUM_SHARDS must be positive" >&2
  exit 2
fi
if [[ ! "${GPU_LIST}" =~ ^[0-7](\ [0-7])*$ ]]; then
  echo "GPU_LIST must be a space-separated list of GPU indices 0-7" >&2
  exit 2
fi
if [[ ! "${MAX_NEW_TOKENS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "MAX_NEW_TOKENS must be positive" >&2
  exit 2
fi
if [[ ! "${EVAL_SEED}" =~ ^-?[0-9]+$ ]]; then
  echo "BLIND_GAINS_EVAL_SEED must be an integer" >&2
  exit 2
fi
[[ ! -e "${RUN_DIR}" ]] || { echo "Refusing to overwrite evaluation run directory: ${RUN_DIR}" >&2; exit 73; }

PROMPT_CONTRACT_JSON="$(PYTHONPATH=. .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_ID="$(jq -r '.contract_id' <<< "${PROMPT_CONTRACT_JSON}")"
PROMPT_CONTRACT_SHA256="$(PYTHONPATH=. .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
SOURCE_RUN_JSON=null
GLOBAL_STEP_JSON=null
EVALUATION_SCOPE_JSON=null
SOURCE_MANIFEST_SHA256_JSON=null
CHECKPOINT_INDEX_SHA256_JSON=null
SOURCE_MANIFEST_PATH=""
SOURCE_TRAINING_JOB_TYPE_JSON=null
SOURCE_TRAINING_SEED_JSON=null
if [[ -n "${PILOT_SOURCE_RUN_INPUT}" && -n "${M5_SOURCE_RUN_INPUT}" ]]; then
  echo "Pilot and M5 checkpoint bindings are mutually exclusive" >&2
  exit 2
fi
if [[ -n "${PILOT_SOURCE_RUN_INPUT}" || -n "${PILOT_GLOBAL_STEP}" ]]; then
  [[ -n "${PILOT_SOURCE_RUN_INPUT}" && -n "${PILOT_GLOBAL_STEP}" ]] || { echo "Pilot source run and global step must be supplied together" >&2; exit 2; }
  [[ "${PILOT_GLOBAL_STEP}" == "60" || "${PILOT_GLOBAL_STEP}" == "100" ]] || { echo "Pilot global step must be 60 or 100" >&2; exit 2; }
  [[ "${IMAGE_MODE}" == "real" && "${MAX_NEW_TOKENS}" == "32" ]] || { echo "Pilot FlipTrack endpoints require real images and 32 output tokens" >&2; exit 2; }
  PILOT_SOURCE_RUN="$(realpath -m "${PILOT_SOURCE_RUN_INPUT}")"
  case "${PILOT_SOURCE_RUN}" in
    "${ROOT}"/experiments/runs/*) ;;
    *) echo "Pilot source run must be under experiments/runs" >&2; exit 2 ;;
  esac
  PILOT_MANIFEST="${PILOT_SOURCE_RUN}/run_manifest.json"
  [[ -f "${PILOT_MANIFEST}" ]] || { echo "Pilot source manifest absent" >&2; exit 2; }
  PILOT_JOB_TYPE="$(jq -r '.job_type' "${PILOT_MANIFEST}")"
  case "${PILOT_JOB_TYPE}" in
    l13_mechanical_pilot_arm)
      EVALUATION_SCOPE_JSON='"registered M2 pilot FlipTrack checkpoint endpoint"'
      ;;
    m3_mechanical_pilot_arm)
      PILOT_SEED="$(jq -r '.seed' "${PILOT_MANIFEST}")"
      [[ "${PILOT_SEED}" == "2" || "${PILOT_SEED}" == "3" ]] || { echo "M3 pilot source seed must be 2 or 3" >&2; exit 2; }
      EVALUATION_SCOPE_JSON='"registered M3 pilot FlipTrack checkpoint endpoint"'
      SOURCE_TRAINING_SEED_JSON="${PILOT_SEED}"
      ;;
    *)
      echo "Pilot source must be an L13 seed-1 or M3 follow-up arm" >&2
      exit 2
      ;;
  esac
  [[ "$(jq -r '.status' "${PILOT_MANIFEST}")" == "complete" ]] || { echo "Pilot source run must be complete" >&2; exit 2; }
  DIRECT_MODEL="$(realpath -m "$(jq -er '.checkpoint_path' "${PILOT_MANIFEST}")/global_step_${PILOT_GLOBAL_STEP}/actor/huggingface")"
  EXPECTED_MODELS=("${DIRECT_MODEL}")
  if [[ "$(jq -r '.resumed_from_global_step // -1' "${PILOT_MANIFEST}")" == "${PILOT_GLOBAL_STEP}" ]]; then
    RESUME_SOURCE_MODEL="$(realpath -m "$(jq -er '.load_checkpoint_path' "${PILOT_MANIFEST}")/actor/huggingface")"
    EXPECTED_MODELS+=("${RESUME_SOURCE_MODEL}")
  fi
  RESOLVED_MODEL="$(realpath -m "${MODEL_PATH}")"
  printf '%s\n' "${EXPECTED_MODELS[@]}" | grep -Fxq "${RESOLVED_MODEL}" || { echo "Pilot checkpoint path does not match the registered source run and step" >&2; exit 2; }
  [[ -f "${RESOLVED_MODEL}/model.safetensors.index.json" ]] || { echo "Pilot merged checkpoint index absent" >&2; exit 2; }
  PILOT_SOURCE_REL="${PILOT_SOURCE_RUN#"${ROOT}/"}"
  SOURCE_RUN_JSON="$(jq -Rn --arg value "${PILOT_SOURCE_REL}" '$value')"
  SOURCE_TRAINING_JOB_TYPE_JSON="$(jq -Rn --arg value "${PILOT_JOB_TYPE}" '$value')"
  GLOBAL_STEP_JSON="${PILOT_GLOBAL_STEP}"
  SOURCE_MANIFEST_SHA256_JSON="$(jq -Rn --arg value "$(sha256sum "${PILOT_MANIFEST}" | awk '{print $1}')" '$value')"
  CHECKPOINT_INDEX_SHA256_JSON="$(jq -Rn --arg value "$(sha256sum "${RESOLVED_MODEL}/model.safetensors.index.json" | awk '{print $1}')" '$value')"
  SOURCE_MANIFEST_PATH="${PILOT_MANIFEST}"
fi
if [[ -n "${M5_SOURCE_RUN_INPUT}" || -n "${M5_GLOBAL_STEP}" ]]; then
  for contract in docs/registered_extensions_v1.md reports/registered_extensions_authorization_v4.json \
    reports/m5_host_memory_incident_v1.json scripts/launch_fliptrack_eval_shards.sh \
    scripts/launch_m5_fliptrack_checkpoint_eval.sh; do
    git ls-files --error-unmatch "${contract}" >/dev/null 2>&1 || {
      echo "M5 FlipTrack contract file is untracked: ${contract}" >&2; exit 3;
    }
  done
  git diff --quiet HEAD -- docs/registered_extensions_v1.md \
    reports/registered_extensions_authorization_v4.json reports/m5_host_memory_incident_v1.json \
    scripts/launch_fliptrack_eval_shards.sh scripts/launch_m5_fliptrack_checkpoint_eval.sh || {
    echo "M5 FlipTrack contract differs from HEAD" >&2; exit 3;
  }
  [[ -n "${M5_SOURCE_RUN_INPUT}" && -n "${M5_GLOBAL_STEP}" ]] || { echo "M5 source run and global step must be supplied together" >&2; exit 2; }
  [[ "${M5_GLOBAL_STEP}" =~ ^(150|200|300|400)$ ]] || { echo "M5 global step must be 150, 200, 300, or 400" >&2; exit 2; }
  [[ "${MAX_NEW_TOKENS}" == "32" ]] || { echo "M5 FlipTrack endpoints require 32 output tokens" >&2; exit 2; }
  if [[ "${M5_GLOBAL_STEP}" == "400" ]]; then
    [[ "${IMAGE_MODE}" =~ ^(real|gray|noise)$ ]] || { echo "M5 step 400 permits real, gray, or noise R19 evaluation" >&2; exit 2; }
  else
    [[ "${IMAGE_MODE}" == "real" ]] || { echo "M5 descriptive checkpoints require real-image R19 evaluation" >&2; exit 2; }
  fi
  M5_SOURCE_RUN="$(realpath -m "${M5_SOURCE_RUN_INPUT}")"
  case "${M5_SOURCE_RUN}" in
    "${ROOT}"/experiments/runs/*) ;;
    *) echo "M5 source run must be under experiments/runs" >&2; exit 2 ;;
  esac
  M5_MANIFEST="${M5_SOURCE_RUN}/run_manifest.json"
  [[ -f "${M5_MANIFEST}" ]] || { echo "M5 source manifest absent" >&2; exit 2; }
  [[ "$(jq -r '.job_type' "${M5_MANIFEST}")" == "m5_anchor_longhorizon_400" ]] || { echo "M5 source job type is invalid" >&2; exit 2; }
  [[ "$(jq -r '.target_global_step' "${M5_MANIFEST}")" == "400" && "$(jq -r '.terminal_no_extension' "${M5_MANIFEST}")" == "true" ]] || {
    echo "M5 source does not bind the fixed terminal contract" >&2; exit 2;
  }
  if [[ "${M5_GLOBAL_STEP}" == "150" ]]; then
    INCIDENT="reports/m5_host_memory_incident_v1.json"
    [[ -s "${INCIDENT}" ]] || { echo "M5 step-150 incident record absent" >&2; exit 2; }
    [[ "$(realpath -m "$(jq -r '.failed_run' "${INCIDENT}")")" == "${M5_SOURCE_RUN}" ]] || { echo "M5 step-150 source is not the incident-bound parent" >&2; exit 2; }
    jq -e '(.status=="fail") and (.exit_code==1)' "${M5_MANIFEST}" >/dev/null || { echo "M5 step-150 parent failure state is invalid" >&2; exit 2; }
    jq -e '(.status=="recoverable_blocked") and (.last_verified_checkpoint.step==150) and (.checks.step150_merge_complete==true)' "${INCIDENT}" >/dev/null || { echo "M5 incident does not certify step 150" >&2; exit 2; }
  else
    jq -e --argjson step "${M5_GLOBAL_STEP}" '(.status=="running" or .status=="complete") and (.registered_evaluation_steps | index($step) != null)' "${M5_MANIFEST}" >/dev/null || {
      echo "M5 source does not authorize this registered evaluation step" >&2; exit 2;
    }
  fi
  RESOLVED_MODEL="$(realpath -m "${MODEL_PATH}")"
  EXPECTED_MODEL="$(realpath -m "$(jq -er '.checkpoint_path' "${M5_MANIFEST}")/global_step_${M5_GLOBAL_STEP}/actor/huggingface")"
  [[ "${RESOLVED_MODEL}" == "${EXPECTED_MODEL}" ]] || { echo "M5 checkpoint path does not match the source run and step" >&2; exit 2; }
  [[ -f "${RESOLVED_MODEL}/model.safetensors.index.json" ]] || { echo "M5 merged checkpoint index absent" >&2; exit 2; }
  PYTHONPATH=. .venv/bin/python - "${RESOLVED_MODEL}" <<'PY'
import sys
from pathlib import Path
from scripts.watch_anchor_checkpoints import merged_checkpoint_complete

if not merged_checkpoint_complete(Path(sys.argv[1])):
    raise SystemExit("M5 merged checkpoint is incomplete")
PY
  M5_SOURCE_REL="${M5_SOURCE_RUN#"${ROOT}/"}"
  SOURCE_RUN_JSON="$(jq -Rn --arg value "${M5_SOURCE_REL}" '$value')"
  GLOBAL_STEP_JSON="${M5_GLOBAL_STEP}"
  EVALUATION_SCOPE_JSON='"registered M5 long-horizon FlipTrack checkpoint endpoint"'
  SOURCE_MANIFEST_SHA256_JSON="$(jq -Rn --arg value "$(sha256sum "${M5_MANIFEST}" | awk '{print $1}')" '$value')"
  CHECKPOINT_INDEX_SHA256_JSON="$(jq -Rn --arg value "$(sha256sum "${RESOLVED_MODEL}/model.safetensors.index.json" | awk '{print $1}')" '$value')"
  SOURCE_MANIFEST_PATH="${M5_MANIFEST}"
fi

GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf 'model=%s\nmanifest=%s\nmode=%s\nmax_new_tokens=%s\nseed=%s\nsource=%s\nstep=%s\n' "${MODEL_PATH}" "${MANIFEST}" "${IMAGE_MODE}" "${MAX_NEW_TOKENS}" "${EVAL_SEED}" "${SOURCE_RUN_JSON}" "${GLOBAL_STEP_JSON}" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${MANIFEST}" | awk '{print $1}')"
if [[ "${GLOBAL_STEP_JSON}" != "null" && "${DATA_HASH}" != "${R19_MANIFEST_SHA256}" ]]; then
  echo "Registered checkpoint evaluation manifest is not the locked R19 manifest" >&2
  exit 2
fi

read -r -a GPU_IDS <<< "${GPU_LIST}"
ACTIVE_GPU_IDS=()
for POSITION in "${!GPU_IDS[@]}"; do
  SHARD_INDEX=$((SHARD_OFFSET + POSITION))
  if [[ "${SHARD_INDEX}" -ge 0 && "${SHARD_INDEX}" -lt "${NUM_SHARDS}" ]]; then
    ACTIVE_GPU_IDS+=("${GPU_IDS[${POSITION}]}")
  fi
done
if [[ "${#ACTIVE_GPU_IDS[@]}" -eq 0 ]]; then
  echo "No evaluation workers launched; check SHARD_OFFSET, NUM_SHARDS, and GPU_LIST" >&2
  exit 2
fi
if [[ "$(printf '%s\n' "${ACTIVE_GPU_IDS[@]}" | sort -u | wc -l)" -ne "${#ACTIVE_GPU_IDS[@]}" ]]; then
  echo "GPU_LIST maps multiple evaluation shards to the same GPU" >&2
  exit 2
fi

# Serialize launch preflights and fail closed if a neighboring process acquired a
# target GPU after an outer scheduler's capacity poll.
LOCK_PATH="/tmp/blind_gains_${NODE}_fliptrack_eval_launch.lock"
exec 9>"${LOCK_PATH}"
if ! flock -n 9; then
  echo "Another FlipTrack evaluation launch preflight is active on ${NODE}" >&2
  exit 75
fi
for GPU in "${ACTIVE_GPU_IDS[@]}"; do
  # shellcheck disable=SC2029
  if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
    echo "FlipTrack evaluation GPU ${GPU} on ${NODE} is occupied" >&2
    exit 75
  fi
done
if [[ "${EVALUATION_SCOPE_JSON}" == '"registered M5 long-horizon FlipTrack checkpoint endpoint"' ]]; then
  MEM_AVAILABLE_KIB="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
  [[ "${MEM_AVAILABLE_KIB}" =~ ^[0-9]+$ && "${MEM_AVAILABLE_KIB}" -ge 471859200 ]] || {
    echo "M5 FlipTrack evaluation requires at least 450 GiB host MemAvailable" >&2; exit 76;
  }
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards" "${RUN_DIR}/metrics"
SOURCE_MANIFEST_SNAPSHOT_JSON=null
if [[ -n "${SOURCE_MANIFEST_PATH}" ]]; then
  SOURCE_MANIFEST_SNAPSHOT="${RUN_DIR}/source_training_manifest_snapshot.json"
  install -m 0444 "${SOURCE_MANIFEST_PATH}" "${SOURCE_MANIFEST_SNAPSHOT}"
  SOURCE_MANIFEST_SNAPSHOT_JSON="$(jq -Rn --arg value "${SOURCE_MANIFEST_SNAPSHOT}" '$value')"
  SOURCE_MANIFEST_SHA256_JSON="$(jq -Rn --arg value "$(sha256sum "${SOURCE_MANIFEST_SNAPSHOT}" | awk '{print $1}')" '$value')"
fi
GPU_IDS_JSON="$(printf '%s\n' "${GPU_IDS[@]}" | jq -sc 'map(tonumber)')"
REPLICA_COUNT="$(wc -w <<< "${GPU_LIST}" | tr -d ' ')"
cat > "${RUN_DIR}/run_manifest.json" <<JSON
{
  "run_id": "$(basename "${RUN_DIR}")",
  "job_type": "fliptrack_v02_image_evaluation",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "gpu_ids": ${GPU_IDS_JSON},
  "tensor_parallel_width": 1,
  "replica_count": ${REPLICA_COUNT},
  "placement_justification": "Independent TP1 replicas evaluate disjoint FlipTrack shards on one node, with shards assigned by replica ordinal; the model is at or below 7B.",
  "placement_policy_version": "pi-2026-07-11",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${MANIFEST}",
  "data_manifest_hash": "${DATA_HASH}",
  "model_path": "${MODEL_PATH}",
  "model_revision": "${MODEL_PATH}",
  "image_mode": "${IMAGE_MODE}",
  "seed": ${EVAL_SEED},
  "noise_seed": ${EVAL_SEED},
  "max_new_tokens": ${MAX_NEW_TOKENS},
  "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
  "prompt_contract": ${PROMPT_CONTRACT_JSON},
  "prompt_contract_id": "${PROMPT_CONTRACT_ID}",
  "prompt_contract_sha256": "${PROMPT_CONTRACT_SHA256}",
  "source_training_run": ${SOURCE_RUN_JSON},
  "source_training_job_type": ${SOURCE_TRAINING_JOB_TYPE_JSON},
  "source_training_seed": ${SOURCE_TRAINING_SEED_JSON},
  "source_training_manifest_snapshot": ${SOURCE_MANIFEST_SNAPSHOT_JSON},
  "source_training_manifest_sha256": ${SOURCE_MANIFEST_SHA256_JSON},
  "global_step": ${GLOBAL_STEP_JSON},
  "checkpoint_index_sha256": ${CHECKPOINT_INDEX_SHA256_JSON},
  "evaluation_scope": ${EVALUATION_SCOPE_JSON},
  "command": "scripts/launch_fliptrack_eval_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${MANIFEST} ${RUN_DIR} ${MAX_NEW_TOKENS} '${GPU_LIST}' ${IMAGE_MODE}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS},
  "expected_artifacts": ["${RUN_DIR}/shards", "${RUN_DIR}/metrics"],
  "performance_values_opened": false,
  "scientific_gate_decision": null
}
JSON

LAUNCHED=0
for POSITION in "${!GPU_IDS[@]}"; do
  GPU="${GPU_IDS[${POSITION}]}"
  SHARD_INDEX=$((SHARD_OFFSET + POSITION))
  if [[ "${SHARD_INDEX}" -lt 0 || "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}_shard${SHARD_INDEX}.log"
  PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}_shard${SHARD_INDEX}.pid"
  OUT_PATH="${RUN_DIR}/shards/shard_${SHARD_INDEX}.jsonl"
  METRICS_PATH="${RUN_DIR}/metrics/shard_${SHARD_INDEX}.json"

  if [[ -s "${METRICS_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=metrics_exists"
    continue
  fi
  # shellcheck disable=SC2029
  ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RUN_DIR}/shards' '${RUN_DIR}/metrics' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 PYTHONHASHSEED=${EVAL_SEED} TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} python scripts/eval_qwen_vl_fliptrack.py --model-path '${MODEL_PATH}' --manifest '${MANIFEST}' --output '${OUT_PATH}' --metrics-output '${METRICS_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --image-mode '${IMAGE_MODE}' --image-cache-dir '${RUN_DIR}/${IMAGE_MODE}_image_cache' --seed ${EVAL_SEED} --noise-seed ${EVAL_SEED} --max-new-tokens ${MAX_NEW_TOKENS} > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
  LAUNCHED=$((LAUNCHED + 1))
done

if [[ "${LAUNCHED}" -eq 0 ]]; then
  echo "No evaluation workers launched; check SHARD_OFFSET, NUM_SHARDS, and GPU_LIST" >&2
  python scripts/finalize_run_manifest.py "${RUN_DIR}/run_manifest.json" 2
  exit 2
fi

scripts/launch_remote_sharded_finalizer.sh "${NODE}" "${RUN_DIR}"
