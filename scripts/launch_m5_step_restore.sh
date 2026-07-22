#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <m5-source-run-dir> <resume-step>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SOURCE_RUN="$1"
STEP="$2"
[[ "${STEP}" =~ ^(200|250|300|350)$ ]] || { echo "unsupported M5 restore step" >&2; exit 2; }
SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
[[ -s "${SOURCE_MANIFEST}" ]] || { echo "M5 source manifest is absent" >&2; exit 2; }

CRITICAL=(
  scripts/launch_m5_step_restore.sh
  scripts/restore_easyr1_raw_checkpoint.py
  scripts/audit_easyr1_resume_checkpoint.py
  src/ops/checkpoint_restore.py
  src/ops/storage_guard.py
  scripts/run_manifest_job.py
  scripts/finalize_run_manifest.py
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked M5 restore contract: ${FILE}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "M5 restore contract differs from HEAD" >&2; exit 3;
}

jq -e --argjson step "${STEP}" '
  (.job_type=="m5_anchor_longhorizon_400") and
  (.status=="complete" or .status=="fail") and
  (.target_global_step==400) and (.terminal_no_extension==true) and
  ((.segment_end_step // .resumed_from_global_step) >= $step or
   (.checkpoint_schedule | index($step)) != null)
' "${SOURCE_MANIFEST}" >/dev/null || { echo "M5 source identity is invalid" >&2; exit 3; }

CHECKPOINT_ROOT="$(jq -er '.checkpoint_path' "${SOURCE_MANIFEST}")"
CHECKPOINT="${CHECKPOINT_ROOT}/global_step_${STEP}"
ACTOR="${CHECKPOINT}/actor"
RELOCATION_MARKER="${ACTOR}/RAW_STATE_RELOCATED.json"
RESTORE_MARKER="${ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json"
[[ -s "${RELOCATION_MARKER}" && -s "${CHECKPOINT}/dataloader.pt" ]] || {
  echo "M5 relocation or dataloader evidence is incomplete" >&2; exit 3;
}
[[ "$(find "${ACTOR}" -maxdepth 1 -type f \( -name 'model_world_size_*_rank_*.pt' -o -name 'optim_world_size_*_rank_*.pt' \) | wc -l)" -eq 0 ]] || {
  echo "M5 restore refuses pre-existing raw shards" >&2; exit 73;
}
[[ ! -e "${RESTORE_MARKER}" ]] || { echo "M5 restore marker already exists" >&2; exit 73; }

ARCHIVE="$(jq -er '.archive_path' "${RELOCATION_MARKER}")"
case "${ARCHIVE}" in
  /tmp/blindgain_checkpoint_archive/*/global_step_"${STEP}"/actor) ;;
  *) echo "M5 restore archive path is outside the approved exact layout" >&2; exit 3 ;;
esac
[[ -s "${ARCHIVE}/raw_training_state.source.sha256" ]] || {
  echo "M5 raw archive checksum manifest is absent" >&2; exit 3;
}
[[ "$(jq -r '.archive_path' "${RELOCATION_MARKER}")" == "${ARCHIVE}" ]] || exit 3

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_step${STEP}_raw_restore_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
GUARD_LOG="${RUN_DIR}/storage_guard.jsonl"
AUDIT_JSON="${RUN_DIR}/restored_checkpoint_audit.json"
AUDIT_SHA="${RUN_DIR}/restored_checkpoint.sha256"
COMMAND="PYTHONPATH=${ROOT} .venv/bin/python scripts/restore_easyr1_raw_checkpoint.py --actor-dir '${ACTOR}' --archive-dir '${ARCHIVE}' --guard-log '${GUARD_LOG}' && PYTHONPATH=${ROOT} .venv/bin/python scripts/audit_easyr1_resume_checkpoint.py --checkpoint-dir '${CHECKPOINT}' --expected-step ${STEP} --expected-world-size 4 --output-json '${AUDIT_JSON}' --output-sha256 '${AUDIT_SHA}'"
DATA_HASH="$({ sha256sum "${SOURCE_MANIFEST}" "${RELOCATION_MARKER}" "${ARCHIVE}/raw_training_state.source.sha256"; } | sort -k2 | sha256sum | awk '{print $1}')"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg marker "${RESTORE_MARKER}" --arg audit_json "${AUDIT_JSON}" \
  --arg audit_sha "${AUDIT_SHA}" --arg relocation "${RELOCATION_MARKER}" \
  --arg archive "${ARCHIVE}" --arg source "${SOURCE_RUN}" --arg checkpoint "${CHECKPOINT}" \
  --argjson step "${STEP}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m5_raw_checkpoint_restore",node:"login",gpu_allocation:[],gpu_ids:[],
    tensor_parallel_width:0,replica_count:0,
    placement_justification:"CPU-only hash-verified restore from the login-node Tier-T archive to shared storage; active GPU jobs are untouched.",
    git_hash:$git_hash,config_path:"scripts/launch_m5_step_restore.sh",config_hash:$config_hash,
    data_manifest:$relocation,data_manifest_hash:$data_hash,source_training_run:$source,
    source_checkpoint:$checkpoint,seed:1,command:$command,start_time_utc:$start,end_time_utc:null,
    status:"running",stdout_stderr_log:$log,archive_path:$archive,resume_step:$step,
    expected_artifacts:[$marker,$audit_json,$audit_sha],scientific_gate_decision:null,
    performance_values_opened:false,deviations:[]}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
