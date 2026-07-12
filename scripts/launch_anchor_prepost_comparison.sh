#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <base-guarded-rescore-run> <step100-guarded-rescore-run>" >&2
  exit 2
fi

BEFORE_RUN="$1"
AFTER_RUN="$2"
OUTPUT_JSON="reports/grpo_anchor_step100_prepost_v1.json"
OUTPUT_MD="reports/grpo_anchor_step100_prepost_v1.md"
if [[ -e "${OUTPUT_JSON}" || -e "${OUTPUT_MD}" ]]; then
  echo "refusing to overwrite versioned anchor comparison outputs" >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="anchor_step100_prepost_analysis_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(sha256sum scripts/compare_anchor_prepost.py | awk '{print $1}')"
DATA_HASH="$(jq -r '.data_manifest_hash' "${BEFORE_RUN}/run_manifest.json")"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${RUN_DIR} --operation anchor_step100_prepost --required-bytes 10000000 && .venv/bin/python scripts/compare_anchor_prepost.py --before-run ${BEFORE_RUN} --after-run ${AFTER_RUN} --output-json ${OUTPUT_JSON} --output-md ${OUTPUT_MD} --bootstrap-draws 2000 --seed 20260712"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "${GIT_HASH}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg before_run "${BEFORE_RUN}" \
  --arg after_run "${AFTER_RUN}" \
  --arg output_json "${OUTPUT_JSON}" \
  --arg output_md "${OUTPUT_MD}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "anchor_step100_prepost_analysis",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only paired analysis of fixed, hash-pinned base and step-100 outputs; no model serving or training.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: $data_hash,
    seed: 20260712,
    bootstrap_draws: 2000,
    before_run: $before_run,
    after_run: $after_run,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    expected_artifacts: [$output_json, $output_md],
    deviations: []
  }' > "${RUN_DIR}/run_manifest.json"

printf '%s\n' "$$" > "${RUN_DIR}/pids/login.pid"
.venv/bin/python scripts/run_manifest_job.py \
  "${RUN_DIR}/run_manifest.json" \
  "${RUN_DIR}/logs/login.log"
printf '%s\n' "${RUN_DIR}"
