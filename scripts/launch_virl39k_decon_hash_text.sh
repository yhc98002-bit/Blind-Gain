#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="decon_virl39k_layer1_hash_text_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
TRAIN_RECORDS="${RUN_DIR}/virl39k_train_records.jsonl"
EVAL_RECORDS="${RUN_DIR}/layer1_eval_records.jsonl"
SUMMARY="${RUN_DIR}/record_summary.json"
COMPARISON="${RUN_DIR}/hash_text_comparison.json"

VIRL_PARQUET="artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K/snapshots/812ec617dea4bc8a4e751663b88e4ebb7de4d00e/39Krelease.parquet"
VIRL_IMAGES="data/virl39k"
MMSTAR_TSV="data/vlmevalkit/MMStar_VLMEVAL.tsv"
MMSTAR_IMAGES="data/vlmevalkit/images/MMStar_VLMEVAL"
MATHVISTA_TSV="data/vlmevalkit/MathVista_LOCAL.tsv"
BLINK_TSV="data/vlmevalkit/BLINK_LOCAL.tsv"
MMVP_TSV="data/vlmevalkit/MMVP_LOCAL_V2.tsv"
HALLUSION_TSV="data/vlmevalkit/HallusionBench_LOCAL_V2.tsv"
MATHVERSE_TSV="data/vlmevalkit/MathVerse_LOCAL.tsv"
MMMU_TSV="data/vlmevalkit/MMMU_LOCAL_V2.tsv"

BUILD_COMMAND=".venv/bin/python scripts/build_virl39k_decon_records.py --virl-parquet ${VIRL_PARQUET} --virl-image-root ${VIRL_IMAGES} --mmstar-tsv ${MMSTAR_TSV} --mmstar-image-root ${MMSTAR_IMAGES} --mathvista-tsv ${MATHVISTA_TSV} --blink-tsv ${BLINK_TSV} --mmvp-tsv ${MMVP_TSV} --hallusion-tsv ${HALLUSION_TSV} --mathverse-tsv ${MATHVERSE_TSV} --mmmu-tsv ${MMMU_TSV} --train-output ${TRAIN_RECORDS} --eval-output ${EVAL_RECORDS} --summary-output ${SUMMARY}"
COMPARE_COMMAND=".venv/bin/python scripts/compare_decon_hash_text.py --train-records ${TRAIN_RECORDS} --eval-records ${EVAL_RECORDS} --output ${COMPARISON}"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${RUN_DIR} --operation m7_virl39k_layer1_hash_text --required-bytes 536870912 && ${BUILD_COMMAND} && ${COMPARE_COMMAND}"

cd "${ROOT}"
for required in "${VIRL_PARQUET}" "${MMSTAR_TSV}" "${MATHVISTA_TSV}" "${BLINK_TSV}" "${MMVP_TSV}" "${HALLUSION_TSV}" "${MATHVERSE_TSV}" "${MMMU_TSV}"; do
  [[ -f "${required}" ]] || { echo "missing input: ${required}" >&2; exit 2; }
done
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${VIRL_PARQUET}" "${MMSTAR_TSV}" "${MATHVISTA_TSV}" "${BLINK_TSV}" "${MMVP_TSV}" "${HALLUSION_TSV}" "${MATHVERSE_TSV}" "${MMMU_TSV}" | sort -k2 | sha256sum | awk '{print $1}')"
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
    job_type: "m7_virl39k_layer1_decon_hash_text",
    node: "login",
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only deterministic record, hash, and lexical pass; no GPU allocation needed.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "ViRL39K full release x seven registered Layer-1 suites",
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
