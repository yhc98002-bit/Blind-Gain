#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 SPEC CHECKOUT OUTPUT RUN_TAG EXPECTED_BYTES" >&2
  exit 2
fi

SPEC="$1"
CHECKOUT="$2"
OUTPUT="$3"
RUN_TAG="$4"
EXPECTED_BYTES="$5"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi
if [[ ! -f "${SPEC}" || ! -d "${CHECKOUT}" ]]; then
  echo "SPEC or CHECKOUT is missing" >&2
  exit 2
fi
if [[ -e "${OUTPUT}" ]]; then
  echo "refusing to overwrite output: ${OUTPUT}" >&2
  exit 2
fi

"${ROOT}/.venv/bin/python" "${ROOT}/scripts/storage_guard.py" \
  --tier S \
  --path "${ROOT}/${CHECKOUT}" \
  --operation hf_dataset_file_repair \
  --required-bytes "${EXPECTED_BYTES}" \
  --log "${ROOT}/logs/storage_guard.jsonl"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="hf_file_repair_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SESSION="${RUN_ID//-/_}"
COMMAND="env http_proxy=${PROXY_URL} https_proxy=${PROXY_URL} ALL_PROXY=${PROXY_URL} .venv/bin/python scripts/repair_hf_dataset_files.py --spec ${SPEC} --checkout ${CHECKOUT} --output ${OUTPUT}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(sha256sum "${SPEC}" | awk '{print $1}')" \
  --arg data_manifest "${SPEC}" \
  --arg data_manifest_hash "$(sha256sum "${SPEC}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg checkout "${CHECKOUT}" \
  --argjson expected_bytes "${EXPECTED_BYTES}" \
  '{
    run_id: $run_id,
    job_type: "hf_dataset_file_repair",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_manifest_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $checkout],
    expected_download_bytes: $expected_bytes,
    deviations: ["ModelScope was attempted first; four bad mirror OIDs are repaired from the hash-matching official Hugging Face snapshot."]
  }' > "${MANIFEST}"

tmux new-session -d -s "${SESSION}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
echo "${RUN_DIR}"
echo "tmux_session=${SESSION} log=${LOG}"
