#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <plan|execute> [completed-plan-run-dir]" >&2
  exit 2
fi
MODE="$1"
PLAN_RUN="${2:-}"
[[ "${MODE}" == "plan" || "${MODE}" == "execute" ]] || { echo "invalid mode" >&2; exit 2; }
if [[ "${MODE}" == "plan" && -n "${PLAN_RUN}" ]]; then
  echo "plan mode does not accept a prior run" >&2
  exit 2
fi
if [[ "${MODE}" == "execute" && -z "${PLAN_RUN}" ]]; then
  echo "execute mode requires a completed plan run" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
CRITICAL=(
  scripts/relocate_rederivable_tree.py
  scripts/run_seed2_archive_preservation.py
  scripts/launch_seed2_archive_preservation.sh
  scripts/measure_storage_usage.py
  src/ops/storage_guard.py
  reports/pilot_4arm_seed2_results_v1.json
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked preservation contract: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "preservation contract differs from HEAD" >&2; exit 2; }
jq -e '(.status=="complete") and (.seed==2) and
       (.checks.strict_gain_identity_all_arms==true) and
       (.registered_arms==["a1_real","a2_gray","a2b_noimage","a3_caption"])' \
  reports/pilot_4arm_seed2_results_v1.json >/dev/null
if pgrep -af '[r]un_seed2_archive_preservation.py'; then
  echo "another seed-2 preservation operation is active" >&2
  exit 73
fi

PRIOR_ARG=""
PRIOR_HASH=""
if [[ "${MODE}" == "execute" ]]; then
  [[ -s "${PLAN_RUN}/run_manifest.json" && -s "${PLAN_RUN}/operation_result.json" ]] || {
    echo "completed plan artifacts are absent" >&2
    exit 3
  }
  jq -e '(.job_type=="seed2_archive_preservation_plan") and
         (.status=="complete") and (.exit_code==0) and (.artifacts_exist==true)' \
    "${PLAN_RUN}/run_manifest.json" >/dev/null
  jq -e '(.status=="validated_not_executed") and (.mode=="plan") and
         (.entries|length==2) and (.deletion_authorized==false) and
         (.combined_storage_guard.status=="pass")' "${PLAN_RUN}/operation_result.json" >/dev/null
  PRIOR_ARG=" --plan-run-dir ${PLAN_RUN}"
  PRIOR_HASH="$(sha256sum "${PLAN_RUN}/operation_result.json" | awk '{print $1}')"
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="seed2_archive_preservation_${MODE}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/operation_result.json"
PID_FILE="${RUN_DIR}/pids/login.pid"
JOB_TYPE="seed2_archive_preservation_${MODE}"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_seed2_archive_preservation.py --mode ${MODE} --run-dir ${RUN_DIR}${PRIOR_ARG}"
READOUT_HASH="$(sha256sum reports/pilot_4arm_seed2_results_v1.json | awk '{print $1}')"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" --arg job_type "${JOB_TYPE}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg output "${OUTPUT}" --arg prior "${PLAN_RUN}" --arg prior_hash "${PRIOR_HASH}" \
  --arg data_hash "${READOUT_HASH}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:$job_type,
    node:"login",gpu_allocation:[],gpu_ids:[],tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only exact-path preservation of two completed seed-2 training-state archives; every file is hashed before and after copying and no active run path is allowlisted.",
    git_hash:$git_hash,config_path:"scripts/run_seed2_archive_preservation.py",config_hash:$config_hash,
    data_manifest:"reports/pilot_4arm_seed2_results_v1.json",
    data_manifest_hash:$data_hash,seed:2,command:$command,
    prior_plan_run:(if $prior=="" then null else $prior end),
    prior_plan_result_sha256:(if $prior_hash=="" then null else $prior_hash end),
    start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    expected_artifacts:[$output],performance_values_opened:false,
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
sleep 2
kill -0 "$(cat "${PID_FILE}")" 2>/dev/null || { echo "preservation ${MODE} exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
