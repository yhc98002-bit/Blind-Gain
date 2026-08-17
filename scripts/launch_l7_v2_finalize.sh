#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 REAL_RUN GRAY_RUN NOISE_RUN NONE_RUN CAPTION_RUN" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
CONDITIONS=(real gray noise none caption)
RUNS=("$1" "$2" "$3" "$4" "$5")
OUTPUTS=(
  reports/blind_solvability_geo3k_v2.json
  reports/blind_solvability_geo3k_v2.md
  reports/blind_solvability_geo3k_v2_audited.json
  reports/blind_solvability_geo3k_v2_audited.md
)

for output in "${OUTPUTS[@]}"; do
  if [[ -e "${output}" ]]; then
    echo "Refusing to overwrite L7 v2 artifact: ${output}" >&2
    exit 2
  fi
done

RUN_ARGS=()
SOURCE_HASH_ARGS=()
for index in "${!CONDITIONS[@]}"; do
  condition="${CONDITIONS[$index]}"
  run="${RUNS[$index]}"
  if [[ ! "${run}" =~ ^experiments/runs/[A-Za-z0-9._-]+$ ]]; then
    echo "Invalid immutable run path for ${condition}: ${run}" >&2
    exit 2
  fi
  manifest="${run}/run_manifest.json"
  output="${run}/per_item.jsonl"
  if [[ ! -s "${manifest}" || ! -s "${output}" ]]; then
    echo "Missing L7 source artifact for ${condition}: ${run}" >&2
    exit 2
  fi
  if ! jq -e --arg condition "${condition}" '
    .status == "complete"
    and .exit_code == 0
    and .condition == $condition
    and .job_type == "l7_blind_solvability_geo3k_v2_guarded_rescore"
    and (.output_sha256 | type == "string" and length == 64)
    and .guarded_rescore_stats.n_rows == 1889
    and .guarded_rescore_stats.n_responses == 32113
    and .guarded_rescore_stats.mathruler_error_count == 0
    and .guarded_rescore_stats.native_r1v_shadow_invalid_count == 0
  ' "${manifest}" >/dev/null; then
    echo "L7 source contract failed for ${condition}: ${run}" >&2
    exit 2
  fi
  RUN_ARGS+=(--run "${condition}=${run}")
  SOURCE_HASH_ARGS+=(
    --arg "${condition}_run" "${run}"
    --arg "${condition}_manifest_sha256" "$(sha256sum "${manifest}" | awk '{print $1}')"
    --arg "${condition}_output_sha256" "$(sha256sum "${output}" | awk '{print $1}')"
  )
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="blind_solvability_geo3k_v2_finalize_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path reports --operation l7_v2_finalize --required-bytes 200000000 && env PYTHONPATH=. .venv/bin/python scripts/summarize_blind_solvability_v2.py"
for argument in "${RUN_ARGS[@]}"; do
  COMMAND+=" $(printf '%q' "${argument}")"
done
COMMAND+=" --json-output reports/blind_solvability_geo3k_v2.json --markdown-output reports/blind_solvability_geo3k_v2.md --audit-json-output reports/blind_solvability_geo3k_v2_audited.json --audit-markdown-output reports/blind_solvability_geo3k_v2_audited.md"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_MANIFEST="$(jq -r '.data_manifest' "${RUNS[0]}/run_manifest.json")"
DATA_MANIFEST_HASH="$(jq -r '.source_manifest_sha256' "${RUNS[0]}/run_manifest.json")"
SOURCE_HASHES_JSON="$(jq -n "${SOURCE_HASH_ARGS[@]}" '{
  real: {run: $real_run, manifest_sha256: $real_manifest_sha256, output_sha256: $real_output_sha256},
  gray: {run: $gray_run, manifest_sha256: $gray_manifest_sha256, output_sha256: $gray_output_sha256},
  noise: {run: $noise_run, manifest_sha256: $noise_manifest_sha256, output_sha256: $noise_output_sha256},
  none: {run: $none_run, manifest_sha256: $none_manifest_sha256, output_sha256: $none_output_sha256},
  caption: {run: $caption_run, manifest_sha256: $caption_manifest_sha256, output_sha256: $caption_output_sha256}
}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "${DATA_MANIFEST}" \
  --arg data_manifest_hash "${DATA_MANIFEST_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --argjson source_runs "${SOURCE_HASHES_JSON}" \
  '{
    run_id: $run_id,
    job_type: "l7_blind_solvability_geo3k_v2_finalize",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only cross-condition recomputation and report generation on the login node.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_manifest_hash,
    seed: 20260710,
    source_runs: $source_runs,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [
      "reports/blind_solvability_geo3k_v2.json",
      "reports/blind_solvability_geo3k_v2.md",
      "reports/blind_solvability_geo3k_v2_audited.json",
      "reports/blind_solvability_geo3k_v2_audited.md"
    ],
    stdout_stderr_log: $log,
    deviations: []
  }' > "${MANIFEST}"

(nohup setsid .venv/bin/python scripts/run_manifest_job.py "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null & echo $! > "${PID_FILE}")
printf '%s\n' "${RUN_DIR}"
