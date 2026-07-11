#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 NODE DOWNLOAD_RUN CAPTION_RUN RUN_TAG" >&2
  exit 2
fi

NODE="$1"
DOWNLOAD_RUN="$2"
CAPTION_RUN="$3"
RUN_TAG="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid node or run tag" >&2
  exit 2
fi
DOWNLOAD_MANIFEST="${DOWNLOAD_RUN}/run_manifest.json"
CHECKOUT_MANIFEST="${DOWNLOAD_RUN}/model_checkout.json"
CAPTION_MANIFEST="${CAPTION_RUN}/run_manifest.json"
CAPTION_STORE="${CAPTION_RUN}/captions.jsonl"
for path in "${DOWNLOAD_MANIFEST}" "${CHECKOUT_MANIFEST}" "${CAPTION_MANIFEST}" "${CAPTION_STORE}"; do
  if [[ ! -s "${ROOT}/${path}" ]]; then
    echo "Deletion prerequisite is absent: ${path}" >&2
    exit 2
  fi
done

cd "${ROOT}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="ephemeral_model_delete_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
PREDELETE="${RUN_DIR}/predelete_record.json"
DELETION="${RUN_DIR}/deletion_record.json"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/delete_ephemeral_model.py --node ${NODE} --download-manifest ${DOWNLOAD_MANIFEST} --checkout-manifest ${CHECKOUT_MANIFEST} --caption-manifest ${CAPTION_MANIFEST} --caption-store ${CAPTION_STORE} --predelete-record ${PREDELETE} --deletion-record ${DELETION}"
DATA_HASH="$(sha256sum "${DOWNLOAD_MANIFEST}" "${CHECKOUT_MANIFEST}" "${CAPTION_MANIFEST}" "${CAPTION_STORE}" | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg download_manifest "${DOWNLOAD_MANIFEST}" \
  --arg command "${COMMAND}" \
  --arg predelete "${PREDELETE}" \
  --arg deletion "${DELETION}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    run_id: $run_id,
    job_type: "l9_ephemeral_model_deletion",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only hash verification and deletion of retention-expired node-local model weights after caption-store commit.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $download_manifest,
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$predelete, $deletion],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup setsid '${ROOT}/.venv/bin/python' scripts/run_manifest_job.py '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
