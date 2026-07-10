#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_geo3k_layer1_hash_text_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
TRAIN_RECORDS="${RUN_DIR}/geometry3k_train_records.jsonl"
EVAL_RECORDS="${RUN_DIR}/layer1_eval_records.jsonl"
SUMMARY="${RUN_DIR}/record_summary.json"
COMPARISON="${RUN_DIR}/hash_text_comparison.json"

GEOMETRY_MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
MMSTAR_TSV="data/vlmevalkit/MMStar_VLMEVAL.tsv"
MMSTAR_IMAGES="data/vlmevalkit/images/MMStar_VLMEVAL"
MATHVISTA_TSV="data/vlmevalkit/MathVista_LOCAL.tsv"
BLINK_TSV="data/vlmevalkit/BLINK_LOCAL.tsv"
BUILD_COMMAND=".venv/bin/python scripts/build_decon_records.py --geometry-manifest ${GEOMETRY_MANIFEST} --mmstar-tsv ${MMSTAR_TSV} --mmstar-image-root ${MMSTAR_IMAGES} --mathvista-tsv ${MATHVISTA_TSV} --blink-tsv ${BLINK_TSV} --train-output ${TRAIN_RECORDS} --eval-output ${EVAL_RECORDS} --summary-output ${SUMMARY}"
COMPARE_COMMAND=".venv/bin/python scripts/compare_decon_hash_text.py --train-records ${TRAIN_RECORDS} --eval-records ${EVAL_RECORDS} --output ${COMPARISON}"
COMMAND="${BUILD_COMMAND} && ${COMPARE_COMMAND}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${GEOMETRY_MANIFEST}" "${MMSTAR_TSV}" "${MATHVISTA_TSV}" "${BLINK_TSV}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg train_records "${TRAIN_RECORDS}" \
  --arg eval_records "${EVAL_RECORDS}" \
  --arg summary "${SUMMARY}" \
  --arg comparison "${COMPARISON}" \
  '{
    run_id: $run_id,
    job_type: "p1_10_decon_hash_text_baseline",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "geometry3k train x MMStar/MathVista/BLINK",
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$train_records, $eval_records, $summary, $comparison]
  }' > "${MANIFEST}"

nohup "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
