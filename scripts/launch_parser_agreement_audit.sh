#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 SOURCE_RUN_DIR RUN_TAG" >&2
  exit 2
fi

SOURCE_RUN_DIR="$1"
RUN_TAG="$2"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi
if [[ "$(jq -r '.status' "${ROOT}/${SOURCE_RUN_DIR}/run_manifest.json")" != "complete" ]]; then
  echo "Parser generation source run is not complete" >&2
  exit 2
fi
mapfile -t INPUTS < <(find "${ROOT}/${SOURCE_RUN_DIR}/shards" -type f -name 'shard_*.jsonl' | sort)
if [[ "${#INPUTS[@]}" -lt 1 ]]; then
  echo "No parser generation shards found" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="parser_agreement_audit_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
ROWS="${RUN_DIR}/rows.jsonl"
METRICS="${RUN_DIR}/metrics.json"
REL_INPUTS=()
for input in "${INPUTS[@]}"; do
  REL_INPUTS+=("${input#${ROOT}/}")
done
COMMAND="PYTHONPATH=artifacts/repos/EasyR1:. .venv/bin/python scripts/audit_parser_agreement.py --inputs ${REL_INPUTS[*]} --rows-output ${ROWS} --metrics-output ${METRICS}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
DATA_HASH="$(sha256sum "${INPUTS[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg source_run "${SOURCE_RUN_DIR}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg rows "${ROWS}" \
  --arg metrics "${METRICS}" \
  '{
    run_id: $run_id,
    job_type: "p0_2_parser_agreement_audit",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $source_run,
    data_manifest_hash: $data_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$rows, $metrics]
  }' > "${MANIFEST}"

.venv/bin/python scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
