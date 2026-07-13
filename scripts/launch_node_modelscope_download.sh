#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <an12|an29> <model-id> <declared-bytes> <destination-name>" >&2
  exit 2
fi

NODE="$1"
MODEL_ID="$2"
DECLARED_BYTES="$3"
DESTINATION_NAME="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${NODE}" =~ ^(an12|an29)$ ]]; then
  echo "download node must be an12 or an29" >&2
  exit 2
fi
if [[ ! "${DECLARED_BYTES}" =~ ^[1-9][0-9]*$ ]]; then
  echo "declared bytes must be positive" >&2
  exit 2
fi
if [[ ! "${DESTINATION_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "destination name contains unsafe characters" >&2
  exit 2
fi

cd "${ROOT}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_modelscope_${DESTINATION_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
ARTIFACT_MANIFEST="${RUN_DIR}/artifact_manifest.tsv"
DESTINATION="/dev/shm/blind-gains/models/${DESTINATION_NAME}"
PARTIAL="${DESTINATION}.partial"
CONFIG_HASH="$(printf 'model=%s\nbytes=%s\ndestination=%s\nsource=modelscope\n' "${MODEL_ID}" "${DECLARED_BYTES}" "${DESTINATION}" | sha256sum | awk '{print $1}')"

if ssh "${NODE}" "test -e '${DESTINATION}'"; then
  echo "refusing to overwrite node-local model: ${NODE}:${DESTINATION}" >&2
  exit 73
fi
FREE_BYTES="$(ssh "${NODE}" "df -PB1 /dev/shm | awk 'NR==2 {print \$4}'")"
if [[ ! "${FREE_BYTES}" =~ ^[0-9]+$ ]] || (( FREE_BYTES - DECLARED_BYTES < 40 * 1024 * 1024 * 1024 )); then
  echo "storage_guard: node-local download would leave less than 40 GiB free" >&2
  exit 75
fi

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY MODELSCOPE_CACHE=/dev/shm/blind-gains/modelscope-cache .venv/bin/modelscope download --model ${MODEL_ID} --local_dir ${PARTIAL} && mv ${PARTIAL} ${DESTINATION} && find ${DESTINATION} -type f -print0 | sort -z | xargs -0 sha256sum > ${ROOT}/${ARTIFACT_MANIFEST}"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg model_id "${MODEL_ID}" \
  --arg destination "${DESTINATION}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg artifact_manifest "${ARTIFACT_MANIFEST}" \
  --argjson declared_bytes "${DECLARED_BYTES}" \
  --argjson free_before "${FREE_BYTES}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_modelscope_node_local_download",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: null,
    replica_count: 0,
    placement_justification: "CPU/network-only ModelScope-first download to re-derivable node-local memory storage; no GPU is allocated.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: null,
    model_id: $model_id,
    model_revision: "master",
    source: ("https://modelscope.cn/models/" + $model_id),
    destination: $destination,
    declared_bytes: $declared_bytes,
    free_bytes_before: $free_before,
    scratch_floor_bytes: 42949672960,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$artifact_manifest],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
