#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <shared-model-dir> <model-revision> <an12|an29> <destination-name>" >&2
  exit 2
fi

SOURCE_INPUT="$1"
MODEL_REVISION="$2"
NODE="$3"
DESTINATION_NAME="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || {
  echo "stage node must be a permanent node: an12 or an29" >&2
  exit 2
}
[[ "${DESTINATION_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || {
  echo "destination name contains unsafe characters" >&2
  exit 2
}
[[ -n "${MODEL_REVISION}" ]] || { echo "model revision is required" >&2; exit 2; }

cd "${ROOT}"
SOURCE="$(realpath -e "${SOURCE_INPUT}")"
case "${SOURCE}" in
  "${ROOT}"/artifacts/models/*) ;;
  *) echo "source model must be under artifacts/models" >&2; exit 2 ;;
esac
[[ -f "${SOURCE}/config.json" ]] || { echo "source model config is absent" >&2; exit 2; }

CRITICAL_FILES=(
  scripts/launch_shared_model_stage.sh
  scripts/run_manifest_job.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "shared-model staging code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${FILE}" >&2
    exit 2
  }
done

DESTINATION="/dev/shm/blind-gains/models/${DESTINATION_NAME}"
PARTIAL="${DESTINATION}.partial"
# shellcheck disable=SC2029
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
RUN_ID="shared_model_stage_${DESTINATION_NAME}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
HASH_MANIFEST="${RUN_DIR}/source_manifest_relative.tsv"
COMPLETION="${RUN_DIR}/stage_complete.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

(cd "${SOURCE}" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "${HASH_MANIFEST}"
[[ -s "${HASH_MANIFEST}" ]] || { echo "source hash manifest is empty" >&2; exit 2; }
SOURCE_MANIFEST_HASH="$(sha256sum "${HASH_MANIFEST}" | awk '{print $1}')"
CONFIG_HASH="$(printf 'source_manifest=%s\nnode=%s\ndestination=%s\nrevision=%s\n' "${SOURCE_MANIFEST_HASH}" "${NODE}" "${DESTINATION}" "${MODEL_REVISION}" | sha256sum | awk '{print $1}')"
COMMAND="ssh ${NODE} \"mkdir -p '${PARTIAL}'\" && rsync -a --partial '${SOURCE}/' '${NODE}:${PARTIAL}/' && ssh ${NODE} \"cd '${PARTIAL}' && sha256sum -c -\" < '${HASH_MANIFEST}' && ssh ${NODE} \"mv '${PARTIAL}' '${DESTINATION}'\" && jq -n --arg destination '${DESTINATION}' --arg manifest_sha256 '${SOURCE_MANIFEST_HASH}' '{status:\"complete\", destination:\$destination, source_manifest_sha256:\$manifest_sha256}' > '${COMPLETION}'"

jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${SOURCE_MANIFEST_HASH}" --arg source "${SOURCE}" \
  --arg destination "${DESTINATION}" --arg revision "${MODEL_REVISION}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg hash_manifest "${HASH_MANIFEST}" \
  --arg completion "${COMPLETION}" --argjson source_bytes "${SOURCE_BYTES}" \
  --argjson free_before "${FREE_BYTES}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "shared_to_node_ephemeral_model_stage",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: null,
    replica_count: 0,
    placement_justification: "CPU/network-only staging creates one hash-verified node-local model copy; no GPU is allocated.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $hash_manifest,
    data_manifest_hash: $data_hash,
    source: $source,
    destination: $destination,
    model_revision: $revision,
    source_bytes: $source_bytes,
    free_bytes_before: $free_before,
    scratch_floor_bytes: 42949672960,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$hash_manifest, $completion],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
