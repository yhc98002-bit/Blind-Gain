#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="data/virl39k_blind_sample_4096.jsonl"
SAMPLE_SPEC="reports/virl39k_blind_sample_4096.json"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
OUTPUT_JSON="reports/blind_solvability_virl39k_sample_v1.json"
OUTPUT_MD="reports/blind_solvability_virl39k_sample_v1.md"
AUDIT_JSON="reports/blind_solvability_virl39k_sample_v1_audited.json"
AUDIT_MD="reports/blind_solvability_virl39k_sample_v1_audited.md"
REAL="experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_real_an12_20260712T052034Z"
GRAY="experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_gray_an12_20260712T052044Z"
NOISE="experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_noise_an12_20260712T052048Z"
NONE="experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_none_an12_20260712T052051Z"
CAPTION="experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_caption_an12_20260712T052054Z"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="virl39k_blind_v1_summary_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"

cd "${ROOT}"
for OUTPUT in "${OUTPUT_JSON}" "${OUTPUT_MD}" "${AUDIT_JSON}" "${AUDIT_MD}"; do
  if [[ -e "${OUTPUT}" ]]; then
    echo "Refusing to overwrite M1 artifact: ${OUTPUT}" >&2
    exit 2
  fi
done
INPUTS=(
  "${SOURCE}" "${SAMPLE_SPEC}" "${FORMAT_PROMPT}"
  "${REAL}/run_manifest.json" "${REAL}/per_item.jsonl"
  "${GRAY}/run_manifest.json" "${GRAY}/per_item.jsonl"
  "${NOISE}/run_manifest.json" "${NOISE}/per_item.jsonl"
  "${NONE}/run_manifest.json" "${NONE}/per_item.jsonl"
  "${CAPTION}/run_manifest.json" "${CAPTION}/per_item.jsonl"
)
for INPUT in "${INPUTS[@]}"; do
  if [[ ! -s "${INPUT}" ]]; then
    echo "Missing M1 summary input: ${INPUT}" >&2
    exit 2
  fi
done

COMMAND="PYTHONPATH=. .venv/bin/python scripts/summarize_blind_solvability_virl39k_v1.py --run real=${REAL} --run gray=${GRAY} --run noise=${NOISE} --run none=${NONE} --run caption=${CAPTION} --source-manifest ${SOURCE} --sample-spec ${SAMPLE_SPEC} --format-prompt ${FORMAT_PROMPT} --json-output ${OUTPUT_JSON} --markdown-output ${OUTPUT_MD} --audit-json-output ${AUDIT_JSON} --audit-markdown-output ${AUDIT_MD}"
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$(sha256sum "${INPUTS[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg source "${SOURCE}" \
  --arg output_json "${OUTPUT_JSON}" \
  --arg output_md "${OUTPUT_MD}" \
  --arg audit_json "${AUDIT_JSON}" \
  --arg audit_md "${AUDIT_MD}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m1_virl39k_blind_solvability_summary_audit",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only deterministic aggregation and independent score recomputation over five completed condition artifacts.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $source,
    data_manifest_hash: $data_hash,
    seed: 20260710,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output_json, $output_md, $audit_json, $audit_md],
    deviations: []
  }' > "${MANIFEST}"

"${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
