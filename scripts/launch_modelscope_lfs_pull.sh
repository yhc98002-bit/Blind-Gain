#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 REPO_DIR INCLUDE_GLOB RUN_TAG" >&2
  exit 2
fi

REPO_DIR="$1"
INCLUDE_GLOB="$2"
RUN_TAG="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"
EXPECTED_BYTES="${BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES:?set BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES to the LFS pull's conservative byte budget}"

if [[ ! -d "${ROOT}/${REPO_DIR}/.git" ]]; then
  echo "Not a git repository: ${REPO_DIR}" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="modelscope_lfs_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
REVISION="$(git -C "${ROOT}/${REPO_DIR}" rev-parse HEAD)"
SOURCE_URL="$(git -C "${ROOT}/${REPO_DIR}" remote get-url origin)"
COMMAND="env http_proxy=${PROXY_URL} https_proxy=${PROXY_URL} git -C ${REPO_DIR} lfs pull --include=${INCLUDE_GLOB} --exclude="

"${ROOT}/.venv/bin/python" "${ROOT}/scripts/storage_guard.py" \
  --tier S \
  --path "${ROOT}/${REPO_DIR}" \
  --operation modelscope_lfs_pull \
  --required-bytes "${EXPECTED_BYTES}" \
  --log "${ROOT}/logs/storage_guard.jsonl"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg source_url "${SOURCE_URL}" \
  --arg revision "${REVISION}" \
  --arg include_glob "${INCLUDE_GLOB}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg repo_dir "${REPO_DIR}" \
  --argjson expected_bytes "${EXPECTED_BYTES}" \
  '{
    run_id: $run_id,
    job_type: "external_dataset_acquisition",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: ($source_url + "@" + $revision + " include=" + $include_glob),
    data_manifest_hash: $revision,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$repo_dir],
    expected_download_bytes: $expected_bytes
  }' > "${MANIFEST}"

tmux new-session -d -s "${RUN_ID}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
echo "${RUN_DIR}"
echo "tmux_session=${RUN_ID} log=${LOG}"
