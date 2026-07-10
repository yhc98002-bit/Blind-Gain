#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 || $# -gt 9 ]]; then
  echo "Usage: $0 NODE SHARD_OFFSET NUM_SHARDS MODEL_PATH IMAGE_DIR RUN_DIR [GPU_LIST] [MAX_NEW_TOKENS] [RESUME_RUN|-]" >&2
  exit 2
fi

NODE="$1"
SHARD_OFFSET="$2"
NUM_SHARDS="$3"
MODEL_PATH="$4"
IMAGE_DIR="$5"
RUN_DIR="$6"
GPU_LIST="${7:-0 1 2 3 4 5 6 7}"
MAX_NEW_TOKENS="${8:-384}"
RESUME_RUN="${9:--}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

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

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards"
LAUNCH_LOCK="${RUN_DIR}/.launch_lock"
if ! mkdir "${LAUNCH_LOCK}" 2>/dev/null; then
  echo "Another launcher owns the caption-store run directory: ${RUN_DIR}" >&2
  exit 2
fi
cleanup_launch_lock() {
  rm -f "${LAUNCH_LOCK}/owner"
  rmdir "${LAUNCH_LOCK}" 2>/dev/null || true
}
trap cleanup_launch_lock EXIT
printf 'pid=%s\nstarted_utc=%s\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${LAUNCH_LOCK}/owner"
if [[ -e "${RUN_DIR}/run_manifest.json" ]]; then
  echo "Caption-store run directory is already initialized: ${RUN_DIR}" >&2
  exit 2
fi
GIT_HASH="$(git rev-parse HEAD)"
if ! find -L "${IMAGE_DIR}" -type f -print -quit | grep -q .; then
  echo "IMAGE_DIR contains no readable image files" >&2
  exit 2
fi
IMAGE_HASH="$(find -L "${IMAGE_DIR}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
RESUME_SOURCE_HASH=""
if [[ "${RESUME_RUN}" != "-" ]]; then
  RESUME_MANIFEST="${RESUME_RUN}/run_manifest.json"
  if [[ ! -s "${RESUME_MANIFEST}" ]] || ! jq -e \
    --arg model "${MODEL_PATH}" \
    --arg image_dir "${IMAGE_DIR}" \
    --argjson shards "${NUM_SHARDS}" \
    --argjson max_tokens "${MAX_NEW_TOKENS}" \
    '(.status == "fail") and
     (.job_type == "caption_image_store_generation") and
     (.model_path == $model) and
     (.data_manifest == $image_dir) and
     (.expected_shards == $shards) and
     (.max_new_tokens == $max_tokens)' "${RESUME_MANIFEST}" >/dev/null; then
    echo "Caption resume run contract does not match or is not failed" >&2
    exit 2
  fi
  mapfile -t RESUME_FILES < <(find "${RESUME_RUN}/shards" -maxdepth 1 -type f \( -name 'store_shard_*.jsonl' -o -name 'store_shard_*.jsonl.partial' \) -size +0c | sort)
  if [[ "${#RESUME_FILES[@]}" -gt 0 ]]; then
    RESUME_SOURCE_HASH="$(sha256sum "${RESUME_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
  fi
fi
CONFIG_HASH="$(printf 'model=%s\nimage_hash=%s\nmax_new_tokens=%s\nprompt=question_blind_v1\nresume_source_hash=%s\n' "${MODEL_PATH}" "${IMAGE_HASH}" "${MAX_NEW_TOKENS}" "${RESUME_SOURCE_HASH}" | sha256sum | awk '{print $1}')"
cat > "${RUN_DIR}/run_manifest.json" <<JSON
{
  "job_type": "caption_image_store_generation",
  "node": "${NODE}",
  "gpu_allocation": "${GPU_LIST}",
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${IMAGE_DIR}",
  "data_manifest_hash": "${IMAGE_HASH}",
  "model_path": "${MODEL_PATH}",
  "max_new_tokens": ${MAX_NEW_TOKENS},
  "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
  "command": "scripts/launch_caption_store_shards.sh ${NODE} ${SHARD_OFFSET} ${NUM_SHARDS} ${MODEL_PATH} ${IMAGE_DIR} ${RUN_DIR} '${GPU_LIST}' ${MAX_NEW_TOKENS} ${RESUME_RUN}",
  "resume_from_run": $(if [[ "${RESUME_RUN}" == "-" ]]; then printf 'null'; else printf '"%s"' "${RESUME_RUN}"; fi),
  "resume_source_hash": $(if [[ -z "${RESUME_SOURCE_HASH}" ]]; then printf 'null'; else printf '"%s"' "${RESUME_SOURCE_HASH}"; fi),
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_shards": ${NUM_SHARDS}
}
JSON

LAUNCHED=0
for GPU in ${GPU_LIST}; do
  SHARD_INDEX=$((SHARD_OFFSET + GPU))
  if [[ "${SHARD_INDEX}" -lt 0 || "${SHARD_INDEX}" -ge "${NUM_SHARDS}" ]]; then
    continue
  fi
  LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}_store_shard${SHARD_INDEX}.log"
  PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}_store_shard${SHARD_INDEX}.pid"
  OUT_PATH="${RUN_DIR}/shards/store_shard_${SHARD_INDEX}.jsonl"
  PARTIAL_PATH="${OUT_PATH}.partial"
  RESUME_ARG=""
  if [[ "${RESUME_RUN}" != "-" ]]; then
    RESUME_PATH="${RESUME_RUN}/shards/store_shard_${SHARD_INDEX}.jsonl"
    if [[ ! -s "${RESUME_PATH}" ]]; then
      RESUME_PATH="${RESUME_PATH}.partial"
    fi
    if [[ -s "${RESUME_PATH}" ]]; then
      printf -v RESUME_ARG ' --resume-from %q' "${RESUME_PATH}"
    fi
  fi
  if [[ -s "${OUT_PATH}" ]]; then
    echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} skip=output_exists"
    continue
  fi
  ssh "${NODE}" "cd '${ROOT}' && (nohup /bin/bash -lc \"env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES=${GPU} '${ROOT}/.venv/bin/python' scripts/caption_image_store.py --model-path '${MODEL_PATH}' --input-dir '${IMAGE_DIR}' --output '${PARTIAL_PATH}' --num-shards ${NUM_SHARDS} --shard-index ${SHARD_INDEX} --max-new-tokens ${MAX_NEW_TOKENS}${RESUME_ARG} && mv '${PARTIAL_PATH}' '${OUT_PATH}'\" > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
  echo "${NODE} gpu=${GPU} shard=${SHARD_INDEX} pid_file=${PID_PATH} log=${LOG_PATH}"
  LAUNCHED=$((LAUNCHED + 1))
done

if [[ "${LAUNCHED}" -eq 0 ]]; then
  echo "No caption-store workers launched; check SHARD_OFFSET, NUM_SHARDS, and GPU_LIST" >&2
  python scripts/finalize_sharded_run.py "${RUN_DIR}/run_manifest.json" --wait --timeout-seconds 0 || true
  exit 2
fi

scripts/launch_remote_sharded_finalizer.sh "${NODE}" "${RUN_DIR}"
