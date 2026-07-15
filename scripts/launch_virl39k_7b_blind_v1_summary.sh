#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 QUEUE_CONFIG_JSON" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
CONFIG="$(realpath -m "$1")"
case "${CONFIG}" in
  "${ROOT}"/experiments/runs/*/config.json) ;;
  *) echo "summary config must be an immutable queue-run config" >&2; exit 2 ;;
esac
[[ -s "${CONFIG}" ]] || { echo "summary config is absent" >&2; exit 2; }

CRITICAL_FILES=(
  scripts/summarize_blind_solvability_virl39k_v1.py
  scripts/run_m8_virl39k_7b_summary_queue.py
  scripts/launch_virl39k_7b_blind_v1_summary.sh
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "M8 summary code differs from HEAD" >&2
  exit 2
}
for file in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${file}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${file}" >&2
    exit 2
  }
done

SOURCE="data/virl39k_blind_sample_4096.jsonl"
SAMPLE_SPEC="reports/virl39k_blind_sample_4096.json"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
EXPECTED_JOB="$(jq -er .expected_job_type "${CONFIG}")"
EXPECTED_MODEL="$(jq -er .expected_model_revision "${CONFIG}")"
OUTPUT_JSON="$(jq -er .outputs.summary_json "${CONFIG}")"
OUTPUT_MD="$(jq -er .outputs.summary_markdown "${CONFIG}")"
AUDIT_JSON="$(jq -er .outputs.audit_json "${CONFIG}")"
AUDIT_MD="$(jq -er .outputs.audit_markdown "${CONFIG}")"

declare -A RUNS
for condition in real gray noise none caption; do
  RUNS["${condition}"]="$(jq -er --arg condition "${condition}" '.runs[$condition]' "${CONFIG}")"
done
for output in "${OUTPUT_JSON}" "${OUTPUT_MD}" "${AUDIT_JSON}" "${AUDIT_MD}"; do
  [[ ! -e "${output}" ]] || { echo "refusing to overwrite M8 artifact: ${output}" >&2; exit 2; }
done

INPUTS=("${SOURCE}" "${SAMPLE_SPEC}" "${FORMAT_PROMPT}" "${CONFIG}")
for condition in real gray noise none caption; do
  run="${RUNS[${condition}]}"
  manifest="${run}/run_manifest.json"
  output="${run}/per_item.jsonl"
  jq -e \
    --arg condition "${condition}" \
    --arg job "${EXPECTED_JOB}" \
    --arg model "${EXPECTED_MODEL}" \
    '(.status == "complete") and (.exit_code == 0) and (.artifacts_exist == true) and
     (.job_type == $job) and (.condition == $condition) and (.node == "an29") and
     (.tensor_parallel_width == 1) and (.replica_count == 1) and
     (.model_revision == $model) and (.sample_size == 4096)' \
    "${manifest}" >/dev/null || {
      echo "M8 source is not structurally complete: ${condition}" >&2
      exit 3
    }
  [[ "$(wc -l < "${output}")" -eq 4096 ]] || {
    echo "M8 source does not contain 4096 rows: ${condition}" >&2
    exit 3
  }
  INPUTS+=("${manifest}" "${output}")
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m8_virl39k_7b_summary_audit_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
RUN_ARGS=""
for condition in real gray noise none caption; do
  printf -v RUN_ARGS '%s --run %q=%q' "${RUN_ARGS}" "${condition}" "${RUNS[${condition}]}"
done
COMMAND="PYTHONPATH=. .venv/bin/python scripts/summarize_blind_solvability_virl39k_v1.py${RUN_ARGS} --source-manifest ${SOURCE} --sample-spec ${SAMPLE_SPEC} --format-prompt ${FORMAT_PROMPT} --json-output ${OUTPUT_JSON} --markdown-output ${OUTPUT_MD} --audit-json-output ${AUDIT_JSON} --audit-markdown-output ${AUDIT_MD} --expected-job-type ${EXPECTED_JOB} --expected-model-revision ${EXPECTED_MODEL}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
DATA_HASH="$(sha256sum "${INPUTS[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg queue_config "${CONFIG#"${ROOT}"/}" \
  --arg queue_config_sha256 "$(sha256sum "${CONFIG}" | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg source "${SOURCE}" \
  --arg output_json "${OUTPUT_JSON}" \
  --arg output_md "${OUTPUT_MD}" \
  --arg audit_json "${AUDIT_JSON}" \
  --arg audit_md "${AUDIT_MD}" \
  --arg log "${LOG}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m8_virl39k_7b_summary_audit",
    node: "login",
    gpu_allocation: [], gpu_ids: [], tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only deterministic aggregation and independent score recomputation over five exact completed 7B condition artifacts.",
    git_hash: $git_hash, config_hash: $config_hash,
    queue_config: $queue_config,
    queue_config_sha256: $queue_config_sha256,
    data_manifest: $source, data_manifest_hash: $data_hash,
    seed: 20260710, command: $command,
    start_time_utc: $start, end_time_utc: null, status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output_json, $output_md, $audit_json, $audit_md],
    performance_values_inspected_by_launcher: false,
    scientific_gate_decision: null, deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
