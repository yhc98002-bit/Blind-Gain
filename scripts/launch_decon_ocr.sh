#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 || $# -gt 6 ]]; then
  echo "Usage: $0 NODE TRAIN_RECORDS EVAL_RECORDS NUM_SHARDS RUN_TAG [DATA_LABEL]" >&2
  exit 2
fi

NODE="$1"
TRAIN_RECORDS="$2"
EVAL_RECORDS="$3"
NUM_SHARDS="$4"
RUN_TAG="$5"
DATA_LABEL="${6:-Geometry3K train and full Layer-1 records}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ || ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid shard count or run tag" >&2
  exit 2
fi
for REQUIRED in "${TRAIN_RECORDS}" "${EVAL_RECORDS}" ".venv-ocr/bin/python"; do
  if [[ ! -e "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing required path: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_ocr_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
mkdir -p "${ROOT}/${RUN_DIR}/logs" "${ROOT}/${RUN_DIR}/pids" "${ROOT}/${RUN_DIR}/shards"

COMMAND="set -euo pipefail; pids=(); for shard in \$(seq 0 $((NUM_SHARDS - 1))); do PYTHONPATH=. OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv-ocr/bin/python scripts/extract_decon_ocr.py --inputs ${TRAIN_RECORDS} ${EVAL_RECORDS} --output ${RUN_DIR}/shards/shard_\${shard}.jsonl --num-shards ${NUM_SHARDS} --shard-index \${shard} & pids+=(\$!); done; for pid in \${pids[@]}; do wait \${pid}; done"
DATA_HASH="$(sha256sum "${ROOT}/${TRAIN_RECORDS}" "${ROOT}/${EVAL_RECORDS}" | sort -k2 | sha256sum | awk '{print $1}')"
EXPECTED="$(seq 0 $((NUM_SHARDS - 1)) | jq -R --arg run_dir "${RUN_DIR}" '$run_dir + "/shards/shard_" + . + ".jsonl"' | jq -s .)"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git -C "${ROOT}" rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg data_label "${DATA_LABEL}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson expected "${EXPECTED}" \
  --argjson num_shards "${NUM_SHARDS}" \
  '{
    run_id: $run_id,
    job_type: "p1_10_decon_ocr_extraction",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only sharded RapidOCR extraction; no GPU allocation or tensor parallelism is used.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_label,
    data_manifest_hash: $data_hash,
    model_revision: "rapidocr_onnxruntime==1.4.4 bundled PP-OCR models",
    num_shards: $num_shards,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: $expected
  }' > "${ROOT}/${MANIFEST}"

if [[ "${NODE}" == "login" ]]; then
  cd "${ROOT}"
  command -v tmux >/dev/null 2>&1 || {
    echo "tmux is required for login-node detached execution" >&2
    exit 2
  }
  tmux new-session -d -s "${RUN_ID}" \
    "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
  tmux list-panes -t "${RUN_ID}" -F '#{pane_pid}' > "${ROOT}/${PID_FILE}"
else
  ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
fi
printf '%s\n' "${RUN_DIR}"
