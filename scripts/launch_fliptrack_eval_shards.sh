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
PILOT_SOURCE_JSON=null
PILOT_STEP_JSON=null
PILOT_SCOPE_JSON=null
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
  [[ "$(jq -r '.job_type' "${PILOT_MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "Pilot source is not an L13 arm" >&2; exit 2; }
  [[ "$(jq -r '.status' "${PILOT_MANIFEST}")" == "complete" ]] || { echo "Pilot source run must be complete" >&2; exit 2; }
  EXPECTED_MODEL="$(realpath -m "$(jq -er '.checkpoint_path' "${PILOT_MANIFEST}")/global_step_${PILOT_GLOBAL_STEP}/actor/huggingface")"
  [[ "$(realpath -m "${MODEL_PATH}")" == "${EXPECTED_MODEL}" ]] || { echo "Pilot checkpoint path does not match the registered source run and step" >&2; exit 2; }
  [[ -f "${EXPECTED_MODEL}/model.safetensors.index.json" ]] || { echo "Pilot merged checkpoint index absent" >&2; exit 2; }
  PILOT_SOURCE_REL="${PILOT_SOURCE_RUN#"${ROOT}/"}"
  PILOT_SOURCE_JSON="$(jq -Rn --arg value "${PILOT_SOURCE_REL}" '$value')"
  PILOT_STEP_JSON="${PILOT_GLOBAL_STEP}"
  PILOT_SCOPE_JSON='"registered M2 pilot FlipTrack checkpoint endpoint"'
fi

GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf 'model=%s\nmanifest=%s\nmode=%s\nmax_new_tokens=%s\nseed=%s\n' "${MODEL_PATH}" "${MANIFEST}" "${IMAGE_MODE}" "${MAX_NEW_TOKENS}" "${EVAL_SEED}" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${MANIFEST}" | awk '{print $1}')"
if [[ "${PILOT_STEP_JSON}" != "null" && "${DATA_HASH}" != "${R19_MANIFEST_SHA256}" ]]; then
  echo "Pilot evaluation manifest is not the locked R19 manifest" >&2
  exit 2
fi
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards" "${RUN_DIR}/metrics"
GPU_IDS_JSON="$(printf '%s\n' ${GPU_LIST} | jq -sc 'map(tonumber)')"
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
  "source_training_run": ${PILOT_SOURCE_JSON},
  "global_step": ${PILOT_STEP_JSON},
  "evaluation_scope": ${PILOT_SCOPE_JSON},
  "command": "scripts/launch_fliptrack_eval_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${MANIFEST} ${RUN_DIR} ${MAX_NEW_TOKENS} '${GPU_LIST}' ${IMAGE_MODE}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS},
  "expected_artifacts": ["${RUN_DIR}/shards", "${RUN_DIR}/metrics"]
}
JSON

read -r -a GPU_IDS <<< "${GPU_LIST}"
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
