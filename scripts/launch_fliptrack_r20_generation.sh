#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an29}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="fliptrack_r20_generation_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID="${RUN_DIR}/pids/${NODE}.pid"
OUTPUT="data/fliptrack_r20_source_manifest.jsonl"
METADATA="data/fliptrack_r20_generation.json"
CONTACTS="reports/contact_sheets/fliptrack_r20"
COMMAND="PYTHONPATH=. .venv/bin/python -m src.fliptrack.build_r20"

cd "${ROOT}"
"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/data/fliptrack_r20_source" \
  --operation fliptrack_r20_generation \
  --required-bytes 4294967296 \
  --log "${ROOT}/logs/storage_guard.jsonl"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$({ sha256sum src/fliptrack/build_v02.py src/fliptrack/schema.py src/eval/fliptrack_metrics.py; sha256sum configs/data/fliptrack_v02r19_artifact_expanded.json reports/fliptrack_v02r19_exact_package.json data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg metadata "${METADATA}" \
  --arg contacts "${CONTACTS}" \
  '{
    run_id: $run_id,
    job_type: "l8_fliptrack_r20_one_shot_generation",
    node: $node,
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "frozen R19 generator/config/result hashes",
    data_manifest_hash: $data_hash,
    seed: {document: 20261001, geometry: 20261002, chart: 20261003},
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $metadata, $contacts],
    deviations: ["R10 historical generation was dirty; current geometry AST matches the clean R18 source." ]
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID}')"
printf '%s\n' "${RUN_DIR}"
