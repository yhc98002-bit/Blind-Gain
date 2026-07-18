#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 8 ]]; then
  echo "Usage: $0 NODE GPU_LIST MODEL_DOWNLOAD_RUN MODEL_PATH MODEL_ID REVISION CALIBRATION_MANIFEST RUN_TAG" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="$2"
MODEL_DOWNLOAD_RUN="$3"
MODEL_PATH="$4"
MODEL_ID="$5"
REVISION="$6"
CALIBRATION_MANIFEST="$7"
RUN_TAG="$8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LEGEND_IMAGES="data/fliptrack_chart_v08_calibration_v1/legend_target/images"
POINT_IMAGES="data/fliptrack_chart_v08_calibration_v1/point_value/images"
EXPECTED_MANIFEST_SHA256="d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292"
MAX_NEW_TOKENS=384
BATCH_SIZE=16
TP_WIDTH=4
EXPECTED_OUTPUT_BYTES=50000000
MIN_HOST_AVAILABLE_BYTES=85899345920

if [[ ! "${NODE}" =~ ^(an12|an29)$ ]]; then
  echo "NODE must be an12 or an29" >&2
  exit 2
fi
if [[ ! "${GPU_LIST}" =~ ^[0-7](,[0-7]){3}$ ]]; then
  echo "GPU_LIST must contain exactly four comma-separated GPU ids" >&2
  exit 2
fi
IFS=',' read -r -a GPU_IDS <<< "${GPU_LIST}"
if [[ "$(printf '%s\n' "${GPU_IDS[@]}" | sort -u | wc -l)" -ne 4 ]]; then
  echo "GPU_LIST contains duplicate ids" >&2
  exit 2
fi
if [[ ! "${MODEL_PATH}" =~ ^/dev/shm/blind-gains/[A-Za-z0-9._/-]+$ || "${MODEL_PATH}" == *".."* ]]; then
  echo "MODEL_PATH must be an ephemeral /dev/shm checkout" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi

cd "${ROOT}"
LOCK_PATH="/tmp/blind_gains_${NODE}_chart_v08_strong_caption_launch.lock"
exec 9>"${LOCK_PATH}"
if ! flock -n 9; then
  echo "Another chart-v08 strong-caption launch preflight is active for ${NODE}" >&2
  exit 3
fi
if [[ "$(sha256sum "${CALIBRATION_MANIFEST}" | awk '{print $1}')" != "${EXPECTED_MANIFEST_SHA256}" ]]; then
  echo "Chart-v08 calibration manifest hash mismatch" >&2
  exit 2
fi
if ! jq -s -e '
  (length == 100) and
  ([.[].pair_id] | unique | length == 100) and
  ([.[] | select(.template_id == "chart_v08_legend_target_flip")] | length == 50) and
  ([.[] | select(.template_id == "chart_v08_point_value_flip")] | length == 50) and
  ([.[].image_a_path, .[].image_b_path] | unique | length == 200)
' "${CALIBRATION_MANIFEST}" >/dev/null; then
  echo "Chart-v08 calibration manifest structure mismatch" >&2
  exit 2
fi
for path in "${LEGEND_IMAGES}" "${POINT_IMAGES}"; do
  if [[ ! -d "${path}" ]]; then
    echo "Chart-v08 image root is absent: ${path}" >&2
    exit 2
  fi
done
if [[ "$(find -L "${LEGEND_IMAGES}" "${POINT_IMAGES}" -type f -name '*.png' | wc -l)" -ne 200 ]]; then
  echo "Chart-v08 source image roots must contain exactly 200 PNG files" >&2
  exit 2
fi

DOWNLOAD_MANIFEST="${MODEL_DOWNLOAD_RUN}/run_manifest.json"
CHECKOUT_MANIFEST="${MODEL_DOWNLOAD_RUN}/model_checkout.json"
if ! jq -e --arg node "${NODE}" --arg path "${MODEL_PATH}" \
  '(.status == "complete") and (.node == $node) and (.local_path == $path)' \
  "${DOWNLOAD_MANIFEST}" >/dev/null; then
  echo "Model download run is not complete on the selected node" >&2
  exit 2
fi
if ! jq -e --arg path "${MODEL_PATH}" \
  '(.status == "pass") and (.local_path == $path) and (.memory_filesystem == true)' \
  "${CHECKOUT_MANIFEST}" >/dev/null; then
  echo "Ephemeral model checkout hash manifest is invalid" >&2
  exit 2
fi
if ! ssh "${NODE}" "test -d '${MODEL_PATH}'"; then
  echo "Ephemeral model checkout is absent on ${NODE}" >&2
  exit 2
fi
HOST_AVAILABLE_KIB="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
if [[ ! "${HOST_AVAILABLE_KIB}" =~ ^[0-9]+$ ]]; then
  echo "Could not parse remote MemAvailable" >&2
  exit 75
fi
HOST_AVAILABLE_BYTES=$((HOST_AVAILABLE_KIB * 1024))
if [[ "${HOST_AVAILABLE_BYTES}" -lt "${MIN_HOST_AVAILABLE_BYTES}" ]]; then
  echo "Host available memory is below the 80-GiB launch floor" >&2
  exit 75
fi
for gpu in "${GPU_IDS[@]}"; do
  if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${gpu}' --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
    echo "Selected GPU ${gpu} is occupied" >&2
    exit 75
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="chart_v08_strong_caption_store_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
PARTIAL="${RUN_DIR}/captions.jsonl.partial"
OUTPUT="${RUN_DIR}/captions.jsonl"
LEGEND_HASH="$(find -L "${LEGEND_IMAGES}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
POINT_HASH="$(find -L "${POINT_IMAGES}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
DATA_HASH="$(printf 'manifest=%s\nlegend=%s\npoint=%s\n' "${EXPECTED_MANIFEST_SHA256}" "${LEGEND_HASH}" "${POINT_HASH}" | sha256sum | awk '{print $1}')"
CHECKOUT_HASH="$(sha256sum "${CHECKOUT_MANIFEST}" | awk '{print $1}')"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${RUN_DIR} --operation m12_chart_v08_strong_caption_store --required-bytes ${EXPECTED_OUTPUT_BYTES} && env TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU_LIST} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/caption_image_store_vllm.py --model-path ${MODEL_PATH} --caption-model-id ${MODEL_ID} --caption-model-revision ${REVISION} --input-dir ${LEGEND_IMAGES} --input-dir ${POINT_IMAGES} --output ${PARTIAL} --run-manifest ${MANIFEST} --tensor-parallel-size ${TP_WIDTH} --batch-size ${BATCH_SIZE} --max-new-tokens ${MAX_NEW_TOKENS} && mv ${PARTIAL} ${OUTPUT}"
GPU_IDS_JSON="$(printf '%s\n' "${GPU_IDS[@]}" | jq -sc 'map(tonumber)')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg calibration_manifest "${CALIBRATION_MANIFEST}" \
  --arg manifest_hash "${EXPECTED_MANIFEST_SHA256}" \
  --arg legend_images "${LEGEND_IMAGES}" \
  --arg point_images "${POINT_IMAGES}" \
  --arg legend_hash "${LEGEND_HASH}" \
  --arg point_hash "${POINT_HASH}" \
  --arg model_path "${MODEL_PATH}" \
  --arg model_id "${MODEL_ID}" \
  --arg revision "${REVISION}" \
  --arg download_run "${MODEL_DOWNLOAD_RUN}" \
  --arg checkout_hash "${CHECKOUT_HASH}" \
  --arg command "${COMMAND}" \
  --arg output "${OUTPUT}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson tp_width "${TP_WIDTH}" \
  --argjson max_tokens "${MAX_NEW_TOKENS}" \
  --argjson batch_size "${BATCH_SIZE}" \
  --argjson host_available "${HOST_AVAILABLE_BYTES}" \
  '{
    run_id: $run_id,
    job_type: "m12_chart_v08_strong_caption_store_generation",
    node: $node,
    gpu_allocation: ($gpu_ids | map(tostring) | join(",")),
    gpu_ids: $gpu_ids,
    tensor_parallel_width: $tp_width,
    replica_count: 1,
    placement_justification: "Qwen2.5-VL-72B requires TP4; the 200-image question-blind v08 caption store uses one single-node replica on the free an12 GPU 4-7 block.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $calibration_manifest,
    data_manifest_hash: $data_hash,
    input_hashes: {manifest: $manifest_hash, legend_target_images: $legend_hash, point_value_images: $point_hash},
    input_roots: {legend_target: $legend_images, point_value: $point_images},
    expected_pair_count: 100,
    expected_unique_image_count: 200,
    model_path: $model_path,
    model_id: $model_id,
    model_revision: $revision,
    model_download_run: $download_run,
    model_checkout_manifest_sha256: $checkout_hash,
    host_available_bytes_at_preflight: $host_available,
    max_new_tokens: $max_tokens,
    batch_size: $batch_size,
    decoding: {temperature: 0, top_p: 1, n: 1, seed: 0},
    caption_prompt_contract: "question_blind_v1",
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    performance_values_opened: false,
    expected_artifacts: [$output],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup setsid '${ROOT}/.venv/bin/python' scripts/run_manifest_job.py '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
