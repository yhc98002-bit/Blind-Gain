#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

SOURCE="data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
DIAGNOSTIC_DIR="data/fliptrack_chart_v08_calibration_v1_diagnostics_v2"
SIDECAR="data/fliptrack_chart_v08_calibration_v1_diagnostics_v2.jsonl"
AUDIT_JSON="reports/chart_v08_mechanical_audit_v2.json"
AUDIT_MD="reports/chart_v08_mechanical_audit_v2.md"

for path in "${DIAGNOSTIC_DIR}" "${SIDECAR}" "${AUDIT_JSON}" "${AUDIT_MD}"; do
  if [[ -e "${path}" ]]; then
    echo "refusing to overwrite chart-v08 mechanical audit artifact: ${path}" >&2
    exit 2
  fi
done
if [[ ! -s "${SOURCE}" ]]; then
  echo "chart-v08 source manifest is absent: ${SOURCE}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="chart_v08_mechanical_audit_v2_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path data --operation chart_v08_mechanical_audit_v2 --required-bytes 300000000 && PYTHONPATH=. .venv/bin/python scripts/build_chart_v08_mechanical_audit_v2.py --source-manifest ${SOURCE} --output-dir ${DIAGNOSTIC_DIR} --sidecar-output ${SIDECAR} --audit-json-output ${AUDIT_JSON} --audit-markdown-output ${AUDIT_MD}"

mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(sha256sum scripts/build_chart_v08_mechanical_audit_v2.py | awk '{print $1}')" \
  --arg data_hash "$(sha256sum "${SOURCE}" | awk '{print $1}')" \
  --arg source "${SOURCE}" \
  --arg command "${COMMAND}" \
  --arg diagnostic_dir "${DIAGNOSTIC_DIR}" \
  --arg sidecar "${SIDECAR}" \
  --arg audit_json "${AUDIT_JSON}" \
  --arg audit_md "${AUDIT_MD}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m12_chart_v08_mechanical_audit_v2",
    status: "running",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "Deterministic CPU reconstruction, pair-mechanics audit, and member-specific necessity-diagnostic rendering; no GPU is required.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $source,
    data_manifest_hash: $data_hash,
    seed: null,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    expected_artifacts: [$diagnostic_dir, $sidecar, $audit_json, $audit_md],
    deviations: []
  }' > "${MANIFEST}"

.venv/bin/python scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
