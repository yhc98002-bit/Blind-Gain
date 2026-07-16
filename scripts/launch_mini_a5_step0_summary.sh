#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 STEP0_RUN_DIR" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_RUN="$1"
case "${SOURCE_RUN}" in
  experiments/runs/mini_a5_step0_qwen25vl3b_*) ;;
  *) echo "source must be an immutable mini-A5 step-0 run" >&2; exit 2 ;;
esac

CRITICAL_FILES=(
  scripts/summarize_mini_a5_step0.py
  scripts/launch_mini_a5_step0_summary.sh
  src/rewards/cp_grpo_reward.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "step-0 summary code differs from HEAD" >&2
  exit 2
}
for file in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${file}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${file}" >&2
    exit 2
  }
done

SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
PREDICTIONS="${SOURCE_RUN}/predictions.jsonl"
jq -e '
  .status == "complete"
  and .exit_code == 0
  and .artifacts_exist == true
  and .job_type == "m6_mini_a5_step0_base_reward_diagnostic"
  and .tensor_parallel_width == 1
  and .replica_count == 1
  and .optimizer_steps == 0
  and .decoding == {temperature: 1.0, top_p: 1.0, n: 5, max_tokens: 2048}
' "${SOURCE_MANIFEST}" >/dev/null || {
  echo "step-0 source manifest is not structurally complete" >&2
  exit 3
}
[[ "$(wc -l < "${PREDICTIONS}")" -eq 1920 ]] || {
  echo "step-0 source does not contain exactly 1,920 rows" >&2
  exit 3
}

OUTPUT_JSON="reports/mini_a5_step0_reward_audit_v1.json"
OUTPUT_MD="reports/mini_a5_step0_reward_audit_v1.md"
for output in "${OUTPUT_JSON}" "${OUTPUT_MD}"; do
  [[ ! -e "${output}" ]] || { echo "refusing to overwrite ${output}" >&2; exit 2; }
done

"${ROOT}/.venv/bin/python" scripts/storage_guard.py \
  --tier S \
  --path "${ROOT}/reports" \
  --operation mini_a5_step0_summary \
  --required-bytes 104857600 \
  --log "${ROOT}/logs/storage_guard.jsonl"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_step0_summary_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/summarize_mini_a5_step0.py --predictions ${PREDICTIONS} --json-output ${OUTPUT_JSON} --markdown-output ${OUTPUT_MD}"
DATA_HASH="$({
  sha256sum "${SOURCE_MANIFEST}" "${PREDICTIONS}"
  sha256sum scripts/summarize_mini_a5_step0.py src/rewards/cp_grpo_reward.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg source_run "${SOURCE_RUN}" \
  --arg source_manifest_sha "$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')" \
  --arg predictions_sha "$(sha256sum "${PREDICTIONS}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output_json "${OUTPUT_JSON}" \
  --arg output_md "${OUTPUT_MD}" \
  --arg log "${LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_step0_summary_audit",
    status: "running",
    node: "login",
    gpu_ids: [], gpu_allocation: [], tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only independent reward recomputation and deterministic aggregation over the completed fixed step-0 artifact.",
    git_hash: $git_hash, config_hash: $config_hash,
    data_manifest: $source_run, data_manifest_hash: $data_hash,
    source_run: $source_run,
    source_manifest_sha256: $source_manifest_sha,
    predictions_sha256: $predictions_sha,
    seed: 20260716,
    command: $command,
    start_time_utc: $started, end_time_utc: null, exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [$output_json, $output_md],
    scientific_gate_decision: null,
    source_performance_values_opened_by_launcher: false,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
