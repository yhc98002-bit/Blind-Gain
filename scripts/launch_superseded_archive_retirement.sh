#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <dry-run|execute> [completed-dry-run-dir]" >&2
  exit 2
fi
MODE="$1"
DRY_RUN_DIR="${2:-}"
[[ "${MODE}" == "dry-run" || "${MODE}" == "execute" ]] || { echo "invalid mode" >&2; exit 2; }
if [[ "${MODE}" == "dry-run" && -n "${DRY_RUN_DIR}" ]]; then
  echo "dry-run mode does not accept a prior run" >&2
  exit 2
fi
if [[ "${MODE}" == "execute" && -z "${DRY_RUN_DIR}" ]]; then
  echo "execute mode requires a completed dry-run directory" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
PLAN="reports/storage_retirement_plan_20260722.json"
PREFLIGHT="reports/storage_retirement_preflight_20260722.md"
CRITICAL=(
  scripts/retire_superseded_archives.py
  scripts/launch_superseded_archive_retirement.sh
  reports/storage_retirement_plan_20260722.json
  reports/storage_retirement_preflight_20260722.md
  reports/storage_relocations/20260716/login_tmp_mech_a1_real_an12_20260713T031454Z_source.sha256
  reports/storage_relocations/20260716/login_tmp_mech_a3_caption_an29_20260713T033039Z_source.sha256
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked retirement contract: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "retirement contract differs from HEAD" >&2; exit 2; }
jq -e '(.status=="approved_for_exact_retirement") and (.entries|length==2) and
       (.total_files==63) and (.total_bytes==106351449820) and
       (.active_run_paths_included==false) and (.model_or_dataset_paths_included==false)' \
  "${PLAN}" >/dev/null
if pgrep -af '[r]etire_superseded_archives.py'; then
  echo "another retirement operation is active" >&2
  exit 73
fi

PRIOR_DRY_RUN_MANIFEST=""
PRIOR_DRY_RUN_OUTPUT=""
if [[ "${MODE}" == "execute" ]]; then
  PRIOR_DRY_RUN_MANIFEST="${DRY_RUN_DIR%/}/run_manifest.json"
  PRIOR_DRY_RUN_OUTPUT="${DRY_RUN_DIR%/}/retirement_result.json"
  [[ -s "${PRIOR_DRY_RUN_MANIFEST}" && -s "${PRIOR_DRY_RUN_OUTPUT}" ]] || {
    echo "completed dry-run artifacts are absent" >&2
    exit 3
  }
  jq -e '(.job_type=="superseded_archive_retirement_dry_run") and
         (.status=="complete") and (.exit_code==0) and (.artifacts_exist==true)' \
    "${PRIOR_DRY_RUN_MANIFEST}" >/dev/null
  jq -e --arg plan_sha "$(sha256sum "${PLAN}" | awk '{print $1}')" \
    '(.status=="validated_not_executed") and (.execute_requested==false) and
     (.plan_sha256==$plan_sha) and (.total_files==63) and (.total_bytes==106351449820) and
     ([.entries[].all_file_hashes_match]|all)' "${PRIOR_DRY_RUN_OUTPUT}" >/dev/null
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="superseded_archive_retirement_${MODE//-/_}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/retirement_result.json"
PID_FILE="${RUN_DIR}/pids/login.pid"
EXECUTE_ARG=""
JOB_TYPE="superseded_archive_retirement_dry_run"
if [[ "${MODE}" == "execute" ]]; then
  EXECUTE_ARG=" --execute"
  JOB_TYPE="superseded_archive_retirement_execute"
fi
COMMAND="PYTHONPATH=. .venv/bin/python scripts/retire_superseded_archives.py --plan ${PLAN} --output ${OUTPUT}${EXECUTE_ARG}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg job_type "${JOB_TYPE}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg plan "${PLAN}" --arg plan_hash "$(sha256sum "${PLAN}" | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg output "${OUTPUT}" --arg prior "${DRY_RUN_DIR}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:$job_type,
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only exact-path SHA256 validation of two failed and superseded checkpoint archives; active training and foreign paths are outside the allowlist.",
    git_hash:$git_hash,config_path:"reports/storage_retirement_plan_20260722.json",config_hash:$config_hash,
    data_manifest:$plan,data_manifest_hash:$plan_hash,seed:null,command:$command,
    prior_dry_run:(if $prior=="" then null else $prior end),start_time_utc:$start,end_time_utc:null,
    status:"running",stdout_stderr_log:$log,expected_artifacts:[$output],
    performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || { echo "retirement ${MODE} exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
