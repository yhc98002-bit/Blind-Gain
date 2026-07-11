#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 LEFT_RUN RIGHT_RUN LEFT_LABEL RIGHT_LABEL RUN_TAG" >&2
  exit 2
fi

LEFT_RUN="$1"
RIGHT_RUN="$2"
LEFT_LABEL="$3"
RIGHT_LABEL="$4"
RUN_TAG="$5"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
for LABEL in "${LEFT_LABEL}" "${RIGHT_LABEL}"; do
  if [[ ! "${LABEL}" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
    echo "Comparison labels must contain only letters, numbers, dot, underscore, or hyphen" >&2
    exit 2
  fi
done
for RUN in "${LEFT_RUN}" "${RIGHT_RUN}"; do
  if [[ ! -f "${ROOT}/${RUN}/run_manifest.json" ]]; then
    echo "Missing comparison run manifest: ${RUN}" >&2
    exit 2
  fi
  if [[ "$(jq -r .status "${ROOT}/${RUN}/run_manifest.json")" != "complete" ]]; then
    echo "Comparison source run is not complete: ${RUN}" >&2
    exit 2
  fi
done
mapfile -t INPUTS < <(find "${ROOT}/${LEFT_RUN}/shards" "${ROOT}/${RIGHT_RUN}/shards" -maxdepth 1 -type f -name '*.jsonl' | sort)
if [[ "${#INPUTS[@]}" -eq 0 ]]; then
  echo "Comparison source runs have no JSONL shards" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="fliptrack_compare_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/comparison.json"
LEFT_GLOB="${LEFT_RUN}/shards/*.jsonl"
RIGHT_GLOB="${RIGHT_RUN}/shards/*.jsonl"
COMMAND=".venv/bin/python scripts/compare_fliptrack_runs.py --left '${LEFT_GLOB}' --right '${RIGHT_GLOB}' --left-label ${LEFT_LABEL} --right-label ${RIGHT_LABEL} --output ${OUTPUT}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$({ sha256sum "${LEFT_RUN}/run_manifest.json" "${RIGHT_RUN}/run_manifest.json"; sha256sum "${INPUTS[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg left_run "${LEFT_RUN}" \
  --arg right_run "${RIGHT_RUN}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  '{
    run_id: $run_id,
    job_type: "fliptrack_paired_run_comparison",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only paired FlipTrack run comparison on the login node.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: [$left_run, $right_run],
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
