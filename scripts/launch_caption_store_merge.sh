#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 RUN_TAG RELEASE_MANIFEST SHARD [SHARD ...]" >&2
  exit 2
fi

RUN_TAG="$1"
RELEASE_MANIFEST="$2"
shift 2
SHARDS=("$@")
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
for REQUIRED in "${RELEASE_MANIFEST}" "${SHARDS[@]}"; do
  if [[ ! -f "${ROOT}/${REQUIRED}" ]]; then
    echo "Missing caption merge input: ${REQUIRED}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="caption_store_merge_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/captions.jsonl"
SUMMARY="${RUN_DIR}/summary.json"

printf -v QUOTED_RELEASE '%q' "${RELEASE_MANIFEST}"
printf -v QUOTED_OUTPUT '%q' "${OUTPUT}"
printf -v QUOTED_SUMMARY '%q' "${SUMMARY}"
QUOTED_SHARDS=""
for SHARD in "${SHARDS[@]}"; do
  printf -v QUOTED_SHARD '%q' "${SHARD}"
  QUOTED_SHARDS+=" ${QUOTED_SHARD}"
done
COMMAND=".venv/bin/python scripts/merge_caption_stores.py --release-manifest ${QUOTED_RELEASE} --shards${QUOTED_SHARDS} --output ${QUOTED_OUTPUT} --summary ${QUOTED_SUMMARY}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$(sha256sum "${RELEASE_MANIFEST}" "${SHARDS[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
SHARDS_JSON="$(printf '%s\n' "${SHARDS[@]}" | jq -R . | jq -s .)"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg release_manifest "${RELEASE_MANIFEST}" \
  --argjson input_shards "${SHARDS_JSON}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg summary "${SUMMARY}" \
  '{
    run_id: $run_id,
    job_type: "p1_8_caption_store_exact_release_merge",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $release_manifest,
    data_manifest_hash: $data_hash,
    input_shards: $input_shards,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $summary]
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
