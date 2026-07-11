#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 9 ]]; then
  echo "Usage: $0 NODE GPU_LIST MODEL_DOWNLOAD_RUN MODEL_PATH MODEL_ID REVISION R19_IMAGES R20_IMAGES RUN_TAG" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="$2"
MODEL_DOWNLOAD_RUN="$3"
MODEL_PATH="$4"
MODEL_ID="$5"
REVISION="$6"
R19_IMAGES="$7"
R20_IMAGES="$8"
RUN_TAG="$9"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX_NEW_TOKENS=384
BATCH_SIZE=16
TP_WIDTH=4
EXPECTED_OUTPUT_BYTES=200000000

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
DOWNLOAD_MANIFEST="${MODEL_DOWNLOAD_RUN}/run_manifest.json"
CHECKOUT_MANIFEST="${MODEL_DOWNLOAD_RUN}/model_checkout.json"
if [[ ! -s "${DOWNLOAD_MANIFEST}" || ! -s "${CHECKOUT_MANIFEST}" ]]; then
  echo "Completed model download manifests are required" >&2
  exit 2
fi
if ! jq -e \
  --arg node "${NODE}" \
  --arg path "${MODEL_PATH}" \
  '(.status == "complete") and (.node == $node) and (.local_path == $path)' \
  "${DOWNLOAD_MANIFEST}" >/dev/null; then
  echo "Model download run is not complete on the selected serving node" >&2
  exit 2
fi
if ! jq -e \
  --arg path "${MODEL_PATH}" \
  '(.status == "pass") and (.local_path == $path) and (.memory_filesystem == true)' \
  "${CHECKOUT_MANIFEST}" >/dev/null; then
  echo "Ephemeral model checkout hash manifest is invalid" >&2
  exit 2
fi
for path in "${R19_IMAGES}" "${R20_IMAGES}"; do
  if [[ ! -d "${path}" ]]; then
    echo "Image root is absent: ${path}" >&2
    exit 2
  fi
done
if ! ssh "${NODE}" "test -d '${MODEL_PATH}'"; then
  echo "Ephemeral model checkout is absent on ${NODE}" >&2
  exit 2
fi
for gpu in "${GPU_IDS[@]}"; do
  if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${gpu}' --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
    echo "Selected GPU ${gpu} is occupied; choose an actually free four-GPU window" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="strong_caption_store_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
PARTIAL="${RUN_DIR}/captions.jsonl.partial"
OUTPUT="${RUN_DIR}/captions.jsonl"
R19_HASH="$(find -L "${R19_IMAGES}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
R20_HASH="$(find -L "${R20_IMAGES}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
DATA_HASH="$(printf 'r19=%s\nr20=%s\n' "${R19_HASH}" "${R20_HASH}" | sha256sum | awk '{print $1}')"
CHECKOUT_HASH="$(sha256sum "${CHECKOUT_MANIFEST}" | awk '{print $1}')"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${RUN_DIR} --operation l9_strong_caption_store --required-bytes ${EXPECTED_OUTPUT_BYTES} && env TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU_LIST} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/caption_image_store_vllm.py --model-path ${MODEL_PATH} --caption-model-id ${MODEL_ID} --caption-model-revision ${REVISION} --input-dir ${R19_IMAGES} --input-dir ${R20_IMAGES} --output ${PARTIAL} --run-manifest ${MANIFEST} --tensor-parallel-size ${TP_WIDTH} --batch-size ${BATCH_SIZE} --max-new-tokens ${MAX_NEW_TOKENS} && mv ${PARTIAL} ${OUTPUT}"
GPU_IDS_JSON="$(printf '%s\n' "${GPU_IDS[@]}" | jq -sc 'map(tonumber)')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg r19_images "${R19_IMAGES}" \
  --arg r20_images "${R20_IMAGES}" \
  --arg r19_hash "${R19_HASH}" \
  --arg r20_hash "${R20_HASH}" \
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
  '{
    run_id: $run_id,
    job_type: "l9_strong_caption_store_generation",
    node: $node,
    gpu_allocation: ($gpu_ids | map(tostring) | join(",")),
    gpu_ids: $gpu_ids,
    tensor_parallel_width: $tp_width,
    replica_count: 1,
    placement_justification: "Qwen2.5-VL-72B cannot fit on one A800 at BF16; one TP4 replica serves R19 and R20 on a single node without cross-node disaggregation.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: [$r19_images, $r20_images],
    data_manifest_hash: $data_hash,
    input_hashes: {r19: $r19_hash, r20: $r20_hash},
    model_path: $model_path,
    model_id: $model_id,
    model_revision: $revision,
    model_download_run: $download_run,
    model_checkout_manifest_sha256: $checkout_hash,
    max_new_tokens: $max_tokens,
    batch_size: $batch_size,
    decoding: {temperature: 0, top_p: 1, n: 1, seed: 0},
    caption_prompt_contract: "question_blind_v1",
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup setsid '${ROOT}/.venv/bin/python' scripts/run_manifest_job.py '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
