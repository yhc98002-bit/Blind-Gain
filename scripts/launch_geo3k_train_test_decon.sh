#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_geo3k_train_test_hash_text_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SOURCE="data/geometry3k_caption_images_manifest.jsonl"
TRAIN="${RUN_DIR}/geometry3k_train_records.jsonl"
TEST="${RUN_DIR}/geometry3k_test_records.jsonl"
SUMMARY="${RUN_DIR}/record_summary.json"
COMPARISON="${RUN_DIR}/hash_text_comparison.json"
COMMAND=".venv/bin/python scripts/build_geo3k_train_test_decon.py --manifest ${SOURCE} --train-output ${TRAIN} --test-output ${TEST} --summary-output ${SUMMARY} && .venv/bin/python scripts/compare_decon_hash_text.py --train-records ${TRAIN} --eval-records ${TEST} --output ${COMPARISON}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "$(sha256sum "${SOURCE}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg train "${TRAIN}" \
  --arg test "${TEST}" \
  --arg summary "${SUMMARY}" \
  --arg comparison "${COMPARISON}" \
  '{
    run_id: $run_id,
    job_type: "l5_geo3k_train_test_hash_text",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "data/geometry3k_caption_images_manifest.jsonl train versus test",
    data_manifest_hash: $data_hash,
    seed: 20260710,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$train, $test, $summary, $comparison],
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
