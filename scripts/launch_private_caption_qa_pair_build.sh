#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 RUN_TAG PRIVATE_MANIFEST CAPTION_STORE [NUM_SHARDS]" >&2
  exit 2
fi

RUN_TAG="$1"
PRIVATE_MANIFEST="$2"
CAPTION_STORE="$3"
NUM_SHARDS="${4:-1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi
if [[ ! "${NUM_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "NUM_SHARDS must be positive" >&2
  exit 2
fi
for path in "${PRIVATE_MANIFEST}" "${CAPTION_STORE}"; do
  if [[ ! -s "${ROOT}/${path}" ]]; then
    echo "Private caption-QA input is absent: ${path}" >&2
    exit 2
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="private_caption_qa_pair_build_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SUMMARY="${RUN_DIR}/summary.json"
OUTPUT_PATTERN="${RUN_DIR}/shards/captions_shard_{index}.jsonl"
COMMAND=".venv/bin/python scripts/build_private_caption_qa_pairs.py --private-manifest ${PRIVATE_MANIFEST} --caption-store ${CAPTION_STORE} --output-pattern '${OUTPUT_PATTERN}' --num-shards ${NUM_SHARDS} --summary ${SUMMARY}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/shards"
DATA_HASH="$(sha256sum "${PRIVATE_MANIFEST}" "${CAPTION_STORE}" | sort -k2 | sha256sum | awk '{print $1}')"
EXPECTED_JSON="$(for index in $(seq 0 $((NUM_SHARDS - 1))); do printf '%s\n' "${RUN_DIR}/shards/captions_shard_${index}.jsonl"; done | jq -R . | jq -s --arg summary "${SUMMARY}" '. + [$summary]')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg private_manifest "${PRIVATE_MANIFEST}" \
  --arg caption_store "${CAPTION_STORE}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson expected "${EXPECTED_JSON}" \
  '{
    run_id: $run_id,
    job_type: "l11_private_caption_qa_pair_adapter",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only strict hash join for an internal one-shot calibration batch; no model serving or GPU allocation.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $private_manifest,
    data_manifest_hash: $data_hash,
    caption_store: $caption_store,
    scope: "internal-calibration-only",
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: $expected,
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
