#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 FINAL_COMPARISON RECORD_SUMMARY RUN_TAG" >&2
  exit 2
fi

FINAL_COMPARISON="$1"
RECORD_SUMMARY="$2"
RUN_TAG="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "invalid run tag: ${RUN_TAG}" >&2
  exit 2
fi
cd "${ROOT}"
for required in "${FINAL_COMPARISON}" "${RECORD_SUMMARY}"; do
  [[ -f "${required}" ]] || { echo "missing input: ${required}" >&2; exit 2; }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="virl39k_decon_finalize_${RUN_TAG}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
FILTER="experiments/manifests/decon_virl39k_vs_layer1_v1.json"
IDS="data/virl39k_main_filtered_ids.json"
DATASET="data/virl39k_main_filtered.jsonl"
FREEZE_SUMMARY="data/virl39k_main_filtered_manifest.json"
REPORT_JSON="reports/decon_virl39k_vs_layer1_v1.json"
REPORT_MD="reports/decon_virl39k_vs_layer1_v1.md"
SOURCE_PARQUET="artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K/snapshots/812ec617dea4bc8a4e751663b88e4ebb7de4d00e/39Krelease.parquet"

COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path data --operation m7_virl39k_decon_finalize --required-bytes 268435456 && .venv/bin/python scripts/summarize_decon.py --comparison ${FINAL_COMPARISON} --output ${FILTER} && .venv/bin/python scripts/freeze_virl39k_training_subset.py --source-parquet ${SOURCE_PARQUET} --image-root data/virl39k --filter-manifest ${FILTER} --ids-output ${IDS} --dataset-output ${DATASET} --summary-output ${FREEZE_SUMMARY} && .venv/bin/python scripts/build_virl39k_decon_report.py --record-summary ${RECORD_SUMMARY} --filter-manifest ${FILTER} --freeze-summary ${FREEZE_SUMMARY} --json-output ${REPORT_JSON} --markdown-output ${REPORT_MD}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${FINAL_COMPARISON}" "${RECORD_SUMMARY}" "${SOURCE_PARQUET}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg filter "${FILTER}" \
  --arg ids "${IDS}" \
  --arg dataset "${DATASET}" \
  --arg freeze_summary "${FREEZE_SUMMARY}" \
  --arg report_json "${REPORT_JSON}" \
  --arg report_md "${REPORT_MD}" \
  '{
    run_id: $run_id,
    job_type: "m7_virl39k_decon_finalize",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only deterministic filter, whole-item freeze, and report audit.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "complete ViRL39K x seven-suite Layer-1 decontamination merge",
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$filter, $ids, $dataset, $freeze_summary, $report_json, $report_md]
  }' > "${MANIFEST}"

command -v tmux >/dev/null 2>&1 || { echo "tmux is required for detached execution" >&2; exit 2; }
tmux new-session -d -s "${RUN_ID}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
tmux list-panes -t "${RUN_ID}" -F '#{pane_pid}' > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
