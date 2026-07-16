#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

OUTPUT="data/mini_a5_train_v1"
EVAL_MANIFESTS=(
  "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
  "data/fliptrack_r20_source_manifest.jsonl"
  "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
)
if [[ -e "${OUTPUT}" ]]; then
  echo "refusing to overwrite immutable mini-A5 corpus: ${OUTPUT}" >&2
  exit 2
fi
for path in "${EVAL_MANIFESTS[@]}"; do
  [[ -s "${path}" ]] || { echo "evaluation manifest is absent: ${path}" >&2; exit 2; }
done

"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/data" \
  --operation mini_a5_train_v1_generation \
  --required-bytes 3221225472 \
  --log "${ROOT}/logs/storage_guard.jsonl"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_corpus_v1_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

COMMAND="PYTHONPATH=. .venv/bin/python -m src.fliptrack.build_mini_a5_train --output-dir ${OUTPUT} --n-per-template 1000 --seed 2026071606"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${EVAL_MANIFESTS[@]}"
  sha256sum src/fliptrack/build_mini_a5_train.py src/fliptrack/schema.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg output "${OUTPUT}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_pair_corpus_generation",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only deterministic rendering and decontamination; no GPU resource is requested.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "R19 + R20 + chart-v08 evaluation template/hash identity",
    data_manifest_hash: $data_hash,
    seed: 2026071606,
    n_pairs_expected: 3000,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [
      ($output + "/pairs.jsonl"),
      ($output + "/train.jsonl"),
      ($output + "/train.parquet"),
      ($output + "/decontamination.json")
    ],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

printf '%s\n' "$$" > "${RUN_DIR}/pids/login.pid"
"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
