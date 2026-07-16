#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

OUTPUT="data/mini_a5_catch_v1"
TRAIN_MANIFEST="data/mini_a5_train_v1/pairs.jsonl"
AUDIT_JSON="reports/mini_a5_catch_audit_v1.json"
AUDIT_MD="reports/mini_a5_catch_v1.md"
EVAL_MANIFESTS=(
  "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
  "data/fliptrack_r20_source_manifest.jsonl"
  "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
)

for path in "${OUTPUT}" "${AUDIT_JSON}" "${AUDIT_MD}"; do
  if [[ -e "${path}" ]]; then
    echo "refusing to overwrite immutable mini-A5 catch artifact: ${path}" >&2
    exit 2
  fi
done
for path in "${TRAIN_MANIFEST}" "${EVAL_MANIFESTS[@]}"; do
  [[ -s "${path}" ]] || { echo "source manifest is absent: ${path}" >&2; exit 2; }
done
git diff --quiet -- \
  src/fliptrack/build_mini_a5_catch.py \
  scripts/audit_mini_a5_catch.py \
  scripts/launch_mini_a5_catch_v1.sh

"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/data" \
  --operation mini_a5_catch_v1_generation \
  --required-bytes 1073741824 \
  --log "${ROOT}/logs/storage_guard.jsonl"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
GEN_RUN_ID="mini_a5_catch_v1_login_${STAMP}"
GEN_RUN_DIR="experiments/runs/${GEN_RUN_ID}"
GEN_MANIFEST="${GEN_RUN_DIR}/run_manifest.json"
GEN_LOG="${GEN_RUN_DIR}/logs/login.log"
mkdir -p "${GEN_RUN_DIR}/logs" "${GEN_RUN_DIR}/pids"

GEN_COMMAND="PYTHONPATH=. .venv/bin/python -m src.fliptrack.build_mini_a5_catch --output-dir ${OUTPUT} --n-per-template 100 --seed 2026071611 --train-manifest ${TRAIN_MANIFEST}"
GEN_CONFIG_HASH="$(printf '%s' "${GEN_COMMAND}" | sha256sum | awk '{print $1}')"
GEN_DATA_HASH="$({
  sha256sum "${TRAIN_MANIFEST}" "${EVAL_MANIFESTS[@]}"
  sha256sum src/fliptrack/build_mini_a5_catch.py src/fliptrack/build_mini_a5_train.py src/fliptrack/schema.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${GEN_RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${GEN_CONFIG_HASH}" \
  --arg data_hash "${GEN_DATA_HASH}" \
  --arg command "${GEN_COMMAND}" \
  --arg output "${OUTPUT}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${GEN_LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_catch_generation",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only deterministic answer-preserving catch rendering and decontamination.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "Mini-A5 training + R19 + R20 + chart-v08 identities",
    data_manifest_hash: $data_hash,
    seed: 2026071611,
    n_pairs_expected: 300,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [
      ($output + "/pairs.jsonl"),
      ($output + "/decontamination.json")
    ],
    scientific_gate_decision: null,
    deviations: []
  }' > "${GEN_MANIFEST}"

printf '%s\n' "$$" > "${GEN_RUN_DIR}/pids/login.pid"
"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${GEN_MANIFEST}" "${GEN_LOG}"

AUDIT_RUN_ID="mini_a5_catch_audit_v1_login_${STAMP}"
AUDIT_RUN_DIR="experiments/runs/${AUDIT_RUN_ID}"
AUDIT_MANIFEST="${AUDIT_RUN_DIR}/run_manifest.json"
AUDIT_LOG="${AUDIT_RUN_DIR}/logs/login.log"
mkdir -p "${AUDIT_RUN_DIR}/logs" "${AUDIT_RUN_DIR}/pids"
AUDIT_COMMAND="PYTHONPATH=. .venv/bin/python scripts/audit_mini_a5_catch.py --corpus-dir ${OUTPUT} --generation-manifest ${GEN_MANIFEST} --output-json ${AUDIT_JSON} --output-md ${AUDIT_MD}"
AUDIT_CONFIG_HASH="$(printf '%s' "${AUDIT_COMMAND}" | sha256sum | awk '{print $1}')"
AUDIT_DATA_HASH="$({
  sha256sum "${GEN_MANIFEST}" "${OUTPUT}/pairs.jsonl" "${OUTPUT}/decontamination.json"
  sha256sum scripts/audit_mini_a5_catch.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${AUDIT_RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${AUDIT_CONFIG_HASH}" \
  --arg data_hash "${AUDIT_DATA_HASH}" \
  --arg command "${AUDIT_COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${AUDIT_LOG}" \
  --arg audit_json "${AUDIT_JSON}" \
  --arg audit_md "${AUDIT_MD}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_catch_independent_audit",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only exhaustive file, mask, target-region, and disjointness audit.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "Frozen mini-A5 catch generation artifact",
    data_manifest_hash: $data_hash,
    seed: null,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [$audit_json, $audit_md],
    scientific_gate_decision: null,
    deviations: []
  }' > "${AUDIT_MANIFEST}"

printf '%s\n' "$$" > "${AUDIT_RUN_DIR}/pids/login.pid"
"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${AUDIT_MANIFEST}" "${AUDIT_LOG}"
printf '%s\n%s\n' "${GEN_RUN_DIR}" "${AUDIT_RUN_DIR}"
