#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 SOURCE_RUN_DIR RUN_TAG [sync|async]" >&2
  exit 2
fi

SOURCE_RUN="$1"
RUN_TAG="$2"
LAUNCH_MODE="${3:-sync}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ "${LAUNCH_MODE}" != "sync" && "${LAUNCH_MODE}" != "async" ]]; then
  echo "Launch mode must be sync or async" >&2
  exit 2
fi
if [[ ! -f "${ROOT}/${SOURCE_RUN}/run_manifest.json" ]]; then
  echo "Missing source run manifest: ${SOURCE_RUN}/run_manifest.json" >&2
  exit 2
fi
if [[ "$(jq -r .status "${ROOT}/${SOURCE_RUN}/run_manifest.json")" != "complete" ]]; then
  echo "Source run is not complete: ${SOURCE_RUN}" >&2
  exit 2
fi
mapfile -t INPUTS < <(find "${ROOT}/${SOURCE_RUN}/shards" -maxdepth 1 -type f -name '*.jsonl' | sort)
if [[ "${#INPUTS[@]}" -eq 0 ]]; then
  echo "Source run has no JSONL shards: ${SOURCE_RUN}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="fliptrack_aggregate_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/metrics.json"
INPUT_GLOB="${SOURCE_RUN}/shards/*.jsonl"
COMMAND=".venv/bin/python scripts/aggregate_fliptrack_eval.py --inputs '${INPUT_GLOB}' --output ${OUTPUT} --bootstrap 2000 --permutations 1000"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$({ sha256sum "${SOURCE_RUN}/run_manifest.json"; sha256sum "${INPUTS[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg source_run "${SOURCE_RUN}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  '{
    run_id: $run_id,
    job_type: "fliptrack_metric_aggregation",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only FlipTrack metric aggregation on the login node.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: ($source_run + "/run_manifest.json"),
    data_manifest_hash: $data_hash,
    source_run: $source_run,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output]
  }' > "${MANIFEST}"

if [[ "${LAUNCH_MODE}" == "async" ]]; then
  mkdir -p "${RUN_DIR}/pids"
  nohup setsid --wait "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py \
    "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null &
  echo "$!" > "${RUN_DIR}/pids/login.pid"
else
  "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
fi
printf '%s\n' "${RUN_DIR}"
