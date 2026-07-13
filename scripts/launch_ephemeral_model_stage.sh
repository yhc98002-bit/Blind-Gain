#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <completed-download-run-dir> <an12|an29> <destination-name>" >&2
  exit 2
fi

SOURCE_RUN="$1"
NODE="$2"
DESTINATION_NAME="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${NODE}" =~ ^(an12|an29)$ ]]; then
  echo "stage node must be an12 or an29" >&2
  exit 2
fi
if [[ ! "${DESTINATION_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "destination name contains unsafe characters" >&2
  exit 2
fi

cd "${ROOT}"
SOURCE_RUN="$(realpath "${SOURCE_RUN}")"
if [[ ! "${SOURCE_RUN}" =~ ^${ROOT}/experiments/runs/[^/]+$ ]]; then
  echo "source run must be an immutable experiments/runs directory" >&2
  exit 2
fi
SOURCE_RUN_MANIFEST="${SOURCE_RUN}/run_manifest.json"
SOURCE_HASH_MANIFEST="${SOURCE_RUN}/artifact_manifest.tsv"
if [[ ! -f "${SOURCE_RUN_MANIFEST}" || ! -f "${SOURCE_HASH_MANIFEST}" ]]; then
  echo "completed source run and artifact manifest are required" >&2
  exit 2
fi
if [[ "$(jq -r '.status' "${SOURCE_RUN_MANIFEST}")" != "complete" ]]; then
  echo "source download run is not complete" >&2
  exit 2
fi

SOURCE="$(jq -r '.destination' "${SOURCE_RUN_MANIFEST}")"
SOURCE="$(realpath "${SOURCE}")"
if [[ ! "${SOURCE}" =~ ^/tmp/blind-gains/models/[A-Za-z0-9._-]+$ || ! -d "${SOURCE}" ]]; then
  echo "source model must be a completed login-/tmp model directory" >&2
  exit 2
fi

DESTINATION="/dev/shm/blind-gains/models/${DESTINATION_NAME}"
PARTIAL="${DESTINATION}.partial"
if ssh "${NODE}" "test -e '${DESTINATION}' -o -e '${PARTIAL}'"; then
  echo "refusing to overwrite node-local model or partial: ${NODE}:${DESTINATION}" >&2
  exit 73
fi

SOURCE_BYTES="$(du -sb "${SOURCE}" | awk '{print $1}')"
FREE_BYTES="$(ssh "${NODE}" "df -PB1 /dev/shm | awk 'NR==2 {print \$4}'")"
if [[ ! "${FREE_BYTES}" =~ ^[0-9]+$ ]] || (( FREE_BYTES - SOURCE_BYTES < 40 * 1024 * 1024 * 1024 )); then
  echo "storage_guard: model stage would leave less than 40 GiB free" >&2
  exit 75
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_stage_${DESTINATION_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
RELATIVE_HASH_MANIFEST="${RUN_DIR}/source_manifest_relative.tsv"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

sed "s#  ${SOURCE}/#  #" "${SOURCE_HASH_MANIFEST}" > "${RELATIVE_HASH_MANIFEST}"
if grep -Fq "  ${SOURCE}/" "${RELATIVE_HASH_MANIFEST}"; then
  echo "failed to make source hash manifest relative" >&2
  exit 2
fi
SOURCE_MANIFEST_HASH="$(sha256sum "${RELATIVE_HASH_MANIFEST}" | awk '{print $1}')"
CONFIG_HASH="$(printf 'source_manifest=%s\nnode=%s\ndestination=%s\n' "${SOURCE_MANIFEST_HASH}" "${NODE}" "${DESTINATION}" | sha256sum | awk '{print $1}')"
COMMAND="ssh ${NODE} \"mkdir -p '${PARTIAL}'\" && rsync -a --partial '${SOURCE}/' '${NODE}:${PARTIAL}/' && ssh ${NODE} \"cd '${PARTIAL}' && sha256sum -c -\" < '${RELATIVE_HASH_MANIFEST}' && ssh ${NODE} \"mv '${PARTIAL}' '${DESTINATION}'\""

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_manifest_hash "${SOURCE_MANIFEST_HASH}" \
  --arg source_run "${SOURCE_RUN#${ROOT}/}" \
  --arg source "${SOURCE}" \
  --arg destination "${DESTINATION}" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg hash_manifest "${RELATIVE_HASH_MANIFEST}" \
  --argjson source_bytes "${SOURCE_BYTES}" \
  --argjson free_before "${FREE_BYTES}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_ephemeral_model_stage",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: null,
    replica_count: 0,
    placement_justification: "CPU/network-only staging into node-local /dev/shm; no GPU is allocated and later inference remains single-node.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: $data_manifest_hash,
    source_run: $source_run,
    source: $source,
    destination: $destination,
    source_bytes: $source_bytes,
    free_bytes_before: $free_before,
    scratch_floor_bytes: 42949672960,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$hash_manifest],
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
