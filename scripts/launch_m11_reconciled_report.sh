#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 QUEUE_RUN STAGE_MANIFEST [STAGE_MANIFEST ...]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
QUEUE_RUN="$1"
shift
STAGE_MANIFESTS=("$@")
MACHINE_OUTPUT="reports/generalization_audits_v2.json"
MARKDOWN_OUTPUT="reports/generalization_audits_v2.md"

CRITICAL_FILES=(
  scripts/build_generalization_audits.py
  scripts/finalize_m11_reconciled_report.py
  scripts/launch_m11_reconciled_report.sh
  src/eval/nonqwen_adapters.py
  src/eval/prompt_contract.py
  src/rewards/answer_reward.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "critical M11 final-report code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical M11 final-report file: ${FILE}" >&2
    exit 2
  }
done
[[ ! -e "${MACHINE_OUTPUT}" && ! -e "${MARKDOWN_OUTPUT}" ]] || {
  echo "registered M11 report output already exists" >&2
  exit 73
}

STAGE_ARGS=()
for STAGE in "${STAGE_MANIFESTS[@]}"; do
  STAGE_ARGS+=(--model-stage-manifest "${STAGE}")
done
PYTHONPATH=. .venv/bin/python scripts/finalize_m11_reconciled_report.py \
  --queue-run "${QUEUE_RUN}" "${STAGE_ARGS[@]}" --preflight-only >/dev/null

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m11_reconciled_final_report_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs"

INPUT_FILES=("${QUEUE_RUN}/run_manifest.json" "${QUEUE_RUN}/queue_state.json" "${STAGE_MANIFESTS[@]}")
while IFS= read -r METRIC; do
  INPUT_FILES+=("${METRIC}")
done < <(jq -r '.cells | to_entries[] | .value.metrics' "${QUEUE_RUN}/queue_state.json" | sort)
DATA_HASH="$(sha256sum "${INPUT_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
CONFIG_HASH="$(sha256sum "${CRITICAL_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"

COMMAND_PARTS=(
  env PYTHONPATH=. .venv/bin/python scripts/finalize_m11_reconciled_report.py
  --queue-run "${QUEUE_RUN}"
  "${STAGE_ARGS[@]}"
  --machine-output "${MACHINE_OUTPUT}"
  --markdown-output "${MARKDOWN_OUTPUT}"
)
printf -v COMMAND '%q ' "${COMMAND_PARTS[@]}"
COMMAND="${COMMAND% }"

.venv/bin/python scripts/storage_guard.py --tier S --path reports \
  --operation m11_reconciled_final_report --required-bytes 16777216
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg queue_run "${QUEUE_RUN}" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg machine "${MACHINE_OUTPUT}" --arg markdown "${MARKDOWN_OUTPUT}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m11_reconciled_final_report",
    node: "login",
    gpu_allocation: [], gpu_ids: [], tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only finalizer opens M11 values only after the exact 18-cell reconciled queue has completed.",
    git_hash: $git_hash, config_hash: $config_hash,
    data_manifest: $queue_run, data_manifest_hash: $data_hash,
    queue_run: $queue_run,
    performance_values_opening_policy: "after complete 18-cell queue gate only",
    command: $command, start_time_utc: $started, end_time_utc: null,
    status: "running", stdout_stderr_log: $log,
    expected_artifacts: [$machine, $markdown],
    scientific_gate_decision: null, deviations: []
  }' > "${MANIFEST}"

.venv/bin/python scripts/run_manifest_job.py "${MANIFEST}" "${LOG}"
printf '%s\n' "${RUN_DIR}"
