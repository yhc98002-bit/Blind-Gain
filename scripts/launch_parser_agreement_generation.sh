#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 8 ]]; then
  echo "Usage: $0 NODE GPU_LIST MODEL_PATH MANIFEST FORMAT_PROMPT RUN_DIR LIMIT MAX_NEW_TOKENS" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="$2"
MODEL_PATH="$3"
DATA_MANIFEST="$4"
FORMAT_PROMPT="$5"
RUN_DIR="$6"
LIMIT="$7"
MAX_NEW_TOKENS="$8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
read -ra GPUS <<< "${GPU_LIST}"
NUM_SHARDS="${#GPUS[@]}"
if [[ "${NUM_SHARDS}" -lt 1 || ! "${LIMIT}" =~ ^[3-9][0-9][0-9]+$ ]]; then
  echo "At least one GPU and LIMIT >= 300 are required" >&2
  exit 2
fi
for required in "${MODEL_PATH}" "${DATA_MANIFEST}" "${FORMAT_PROMPT}"; do
  if [[ ! -e "${ROOT}/${required}" ]]; then
    echo "Missing parser-agreement input: ${required}" >&2
    exit 2
  fi
done
if [[ -e "${ROOT}/${RUN_DIR}/run_manifest.json" ]]; then
  echo "Refusing to overwrite parser-agreement run" >&2
  exit 2
fi

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/shards"
COMMAND="scripts/launch_parser_agreement_generation.sh ${NODE} '${GPU_LIST}' ${MODEL_PATH} ${DATA_MANIFEST} ${FORMAT_PROMPT} ${RUN_DIR} ${LIMIT} ${MAX_NEW_TOKENS}"
jq -n \
  --arg node "${NODE}" \
  --arg gpu_list "${GPU_LIST}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "${DATA_MANIFEST}" \
  --arg data_hash "$(sha256sum "${DATA_MANIFEST}" "${FORMAT_PROMPT}" | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg model_path "${MODEL_PATH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson shards "${NUM_SHARDS}" \
  --argjson limit "${LIMIT}" \
  '{
    job_type: "parser_agreement_generation",
    node: $node,
    gpu_allocation: ($gpu_list | split(" ")),
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    model_revision: $model_path,
    command: $command,
    sample_limit: $limit,
    expected_shards: $shards,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running"
  }' > "${RUN_DIR}/run_manifest.json"

for index in "${!GPUS[@]}"; do
  gpu="${GPUS[$index]}"
  log="${RUN_DIR}/logs/${NODE}_gpu${gpu}_shard${index}.log"
  pid="${RUN_DIR}/pids/${NODE}_gpu${gpu}_shard${index}.pid"
  output="${RUN_DIR}/shards/shard_${index}.jsonl"
  ssh "${NODE}" "cd '${ROOT}' && (nohup env TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES='${gpu}' .venv/bin/python scripts/generate_parser_agreement.py --model-path '${MODEL_PATH}' --manifest '${DATA_MANIFEST}' --format-prompt '${FORMAT_PROMPT}' --output '${output}' --split test --limit '${LIMIT}' --num-shards '${NUM_SHARDS}' --shard-index '${index}' --max-new-tokens '${MAX_NEW_TOKENS}' > '${log}' 2>&1 < /dev/null & echo \$! > '${pid}')"
done

nohup .venv/bin/python scripts/finalize_sharded_run.py "${RUN_DIR}/run_manifest.json" --wait \
  > "${RUN_DIR}/logs/finalizer.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/finalizer.pid"
printf '%s\n' "${RUN_DIR}"
