#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "Usage: $0 DATASET_ID LOCAL_DIR LICENSE REDISTRIBUTION EXPECTED_BYTES RUN_TAG" >&2
  exit 2
fi

DATASET_ID="$1"
LOCAL_DIR="$2"
LICENSE="$3"
REDISTRIBUTION="$4"
EXPECTED_BYTES="$5"
RUN_TAG="$6"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_URL="https://www.modelscope.cn/datasets/${DATASET_ID}.git"

if [[ ! "${EXPECTED_BYTES}" =~ ^[1-9][0-9]*$ ]]; then
  echo "EXPECTED_BYTES must be positive" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag" >&2
  exit 2
fi
cd "${ROOT}"
if [[ -e "${LOCAL_DIR}" ]]; then
  echo "Refusing to overwrite dataset checkout: ${LOCAL_DIR}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="modelscope_dataset_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
INVENTORY="${RUN_DIR}/dataset_inventory.json"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${LOCAL_DIR} --operation modelscope_dataset_clone --required-bytes ${EXPECTED_BYTES} && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy git clone --depth 1 ${SOURCE_URL} ${LOCAL_DIR} && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy git -C ${LOCAL_DIR} lfs pull && git -C ${LOCAL_DIR} lfs fsck && .venv/bin/python scripts/inventory_dataset_checkout.py --checkout ${LOCAL_DIR} --dataset-id ${DATASET_ID} --source-url ${SOURCE_URL} --license ${LICENSE} --redistribution ${REDISTRIBUTION} --output ${INVENTORY}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg dataset_id "${DATASET_ID}" \
  --arg source_url "${SOURCE_URL}" \
  --arg local_dir "${LOCAL_DIR}" \
  --arg license "${LICENSE}" \
  --arg redistribution "${REDISTRIBUTION}" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg inventory "${INVENTORY}" \
  --argjson expected_bytes "${EXPECTED_BYTES}" \
  '{
    run_id: $run_id,
    job_type: "modelscope_dataset_clone",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: null,
    data_manifest_hash: null,
    dataset_id: $dataset_id,
    source: "ModelScope direct domestic route",
    source_url: $source_url,
    requested_revision: "HEAD",
    license: $license,
    redistribution: $redistribution,
    local_path: $local_dir,
    storage_tier: "S",
    expected_download_bytes: $expected_bytes,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$local_dir, $inventory],
    deviations: []
  }' > "${MANIFEST}"

nohup "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
