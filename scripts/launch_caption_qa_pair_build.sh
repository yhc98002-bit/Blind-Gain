#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 RUN_TAG RELEASE_MANIFEST KEY_FILE CAPTION_STORE" >&2
  exit 2
fi

RUN_TAG="$1"
RELEASE_MANIFEST="$2"
KEY_FILE="$3"
CAPTION_STORE="$4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
for REQUIRED in "${RELEASE_MANIFEST}" "${KEY_FILE}" "${CAPTION_STORE}"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing caption-QA pair input: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="caption_qa_pair_build_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/shards/captions_shard_0.jsonl"
SUMMARY="${RUN_DIR}/summary.json"
COMMAND=".venv/bin/python scripts/build_caption_qa_pairs.py --release-manifest ${RELEASE_MANIFEST} --key-file ${KEY_FILE} --caption-store ${CAPTION_STORE} --output ${OUTPUT} --summary ${SUMMARY}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/shards"
DATA_HASH="$(sha256sum "${RELEASE_MANIFEST}" "${KEY_FILE}" "${CAPTION_STORE}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg release_manifest "${RELEASE_MANIFEST}" \
  --arg key_file "${KEY_FILE}" \
  --arg caption_store "${CAPTION_STORE}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg summary "${SUMMARY}" \
  '{
    run_id: $run_id,
    job_type: "p1_8_caption_qa_pair_adapter",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $release_manifest,
    data_manifest_hash: $data_hash,
    private_key_file: $key_file,
    caption_store: $caption_store,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $summary]
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
