#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
  echo "Usage: $0 RUN_TAG RELEASE_MANIFEST KEY_FILE CAPTION_STORE [NUM_SHARDS]" >&2
  exit 2
fi

RUN_TAG="$1"
RELEASE_MANIFEST="$2"
KEY_FILE="$3"
CAPTION_STORE="$4"
NUM_SHARDS="${5:-1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "NUM_SHARDS must be positive" >&2
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
SUMMARY="${RUN_DIR}/summary.json"
if [[ "${NUM_SHARDS}" == "1" ]]; then
  OUTPUT_ARGS="--output ${RUN_DIR}/shards/captions_shard_0.jsonl"
else
  OUTPUT_ARGS="--output-pattern ${RUN_DIR}/shards/captions_shard_{index}.jsonl --num-shards ${NUM_SHARDS}"
fi
COMMAND=".venv/bin/python scripts/build_caption_qa_pairs.py --release-manifest ${RELEASE_MANIFEST} --key-file ${KEY_FILE} --caption-store ${CAPTION_STORE} ${OUTPUT_ARGS} --summary ${SUMMARY}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/shards"
DATA_HASH="$(sha256sum "${RELEASE_MANIFEST}" "${KEY_FILE}" "${CAPTION_STORE}" | sort -k2 | sha256sum | awk '{print $1}')"
EXPECTED_JSON="$(for INDEX in $(seq 0 $((NUM_SHARDS - 1))); do printf '%s\n' "${RUN_DIR}/shards/captions_shard_${INDEX}.jsonl"; done | jq -R . | jq -s --arg summary "${SUMMARY}" '. + [$summary]')"
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
  --argjson expected "${EXPECTED_JSON}" \
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
    expected_artifacts: $expected
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
