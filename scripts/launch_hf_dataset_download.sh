#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 REPO_ID REVISION LOCAL_DIR RUN_TAG" >&2
  exit 2
fi

REPO_ID="$1"
REVISION="$2"
LOCAL_DIR="$3"
RUN_TAG="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"

if [[ ! "${REPO_ID}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "REPO_ID must have namespace/name form" >&2
  exit 2
fi
if [[ ! "${REVISION}" =~ ^[A-Fa-f0-9]{40}$ ]]; then
  echo "REVISION must be a 40-character commit hash" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="hf_dataset_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SESSION="${RUN_ID//-/_}"
COMMAND="env http_proxy=${PROXY_URL} https_proxy=${PROXY_URL} HF_HOME=${ROOT}/artifacts/hf_home HF_HUB_DISABLE_XET=1 .venv/bin/hf download ${REPO_ID} --repo-type dataset --revision ${REVISION} --local-dir ${LOCAL_DIR} --max-workers 2"

cd "${ROOT}"
if [[ -e "${LOCAL_DIR}" ]]; then
  echo "LOCAL_DIR already exists: ${LOCAL_DIR}" >&2
  exit 2
fi
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg source_url "https://huggingface.co/datasets/${REPO_ID}/tree/${REVISION}" \
  --arg revision "${REVISION}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg local_dir "${LOCAL_DIR}" \
  '{
    run_id: $run_id,
    job_type: "external_dataset_acquisition",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $source_url,
    data_manifest_hash: $revision,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$local_dir]
  }' > "${MANIFEST}"

tmux new-session -d -s "${SESSION}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
echo "${RUN_DIR}"
echo "tmux_session=${SESSION} log=${LOG}"
