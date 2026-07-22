#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 7 ]]; then
  echo "usage: $0 <an12|an29> <gpu0,gpu1,gpu2,gpu3> <start-step> <restore-run-dir> <ray-preflight-run-dir> <prior-training-run-dir> <boundary-handoff-run-dir|->" >&2
  exit 2
fi
NODE="$1"
GPU_LIST="$2"
START_STEP="$3"
RESTORE_RUN="$4"
PREFLIGHT_RUN="$5"
PRIOR_RUN="$6"
BOUNDARY_RUN="$7"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }
[[ "${START_STEP}" =~ ^(200|250|300|350)$ ]] || { echo "invalid M5 segment start" >&2; exit 2; }
END_STEP="$((START_STEP + 50))"
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
[[ "${#GPUS[@]}" -eq 4 && "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -eq 4 ]] || {
  echo "M5 segment requires four unique GPU ids" >&2; exit 2;
}
for GPU in "${GPUS[@]}"; do [[ "${GPU}" =~ ^[0-7]$ ]] || exit 2; done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
BASE_CONFIG="configs/train/m5_anchor_longhorizon_400.yaml"
EXPECTED_BASE_HASH="73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c"
REGISTRATION="docs/registered_extensions_v1.md"
AUTHORIZATION="reports/registered_extensions_authorization_v4.json"
PRIOR_MANIFEST="${PRIOR_RUN}/run_manifest.json"
RESTORE_MANIFEST="${RESTORE_RUN}/run_manifest.json"
RESTORE_AUDIT="${RESTORE_RUN}/restored_checkpoint_audit.json"
PREFLIGHT_MANIFEST="${PREFLIGHT_RUN}/run_manifest.json"
PREFLIGHT_OUTPUT="${PREFLIGHT_RUN}/preflight.json"

CRITICAL=(
  "${BASE_CONFIG}"
  "${REGISTRATION}"
  "${AUTHORIZATION}"
  scripts/build_m5_segment_config.py
  scripts/launch_m5_anchor_segment.sh
  scripts/probe_m5_ray_startup.py
  scripts/launch_m5_ray_startup_preflight.sh
  scripts/watch_m5_checkpoints.py
  scripts/watch_m5_merged_relocation.py
  scripts/launch_m5_checkpoint_watch.sh
  scripts/launch_m5_merged_relocation_watch.sh
  scripts/run_m5_checkpoint_evaluation_queue.py
  scripts/launch_m5_checkpoint_evaluation_queue.sh
  scripts/launch_m5_geo3k_checkpoint_eval.sh
  scripts/launch_m5_fliptrack_checkpoint_eval.sh
  scripts/watch_m5_step_evaluation.py
  scripts/finalize_m5_step_evaluation.py
  scripts/launch_m5_step_evaluation_watch.sh
  scripts/run_manifest_job.py
  scripts/finalize_run_manifest.py
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked M5 segment contract: ${FILE}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "M5 segment contract differs from HEAD" >&2; exit 3;
}
[[ "$(sha256sum "${BASE_CONFIG}" | awk '{print $1}')" == "${EXPECTED_BASE_HASH}" ]] || {
  echo "M5 base config hash changed" >&2; exit 3;
}
jq -e '(.status=="authorized") and (.authorization.m5=="authorized_after_restore_integrity_pass")' \
  "${AUTHORIZATION}" >/dev/null || { echo "M5 authorization invalid" >&2; exit 3; }

[[ -s "${PRIOR_MANIFEST}" && -s "${RESTORE_MANIFEST}" && -s "${RESTORE_AUDIT}" ]] || {
  echo "M5 segment source/restore evidence is absent" >&2; exit 3;
}
jq -e --argjson start "${START_STEP}" '
  (.job_type=="m5_anchor_longhorizon_400") and (.target_global_step==400) and
  (.terminal_no_extension==true) and (.checkpoint_schedule | index($start) != null)
' "${PRIOR_MANIFEST}" >/dev/null || { echo "prior M5 manifest identity is invalid" >&2; exit 3; }
jq -e --arg source "${PRIOR_RUN}" --argjson start "${START_STEP}" '
  (.status=="complete") and (.exit_code==0) and (.job_type=="m5_raw_checkpoint_restore") and
  (.resume_step==$start) and (.source_training_run==$source) and (.performance_values_opened==false)
' "${RESTORE_MANIFEST}" >/dev/null || { echo "M5 raw restore run is incomplete" >&2; exit 3; }
jq -e --argjson start "${START_STEP}" '
  (.status=="pass") and (.expected_step==$start) and (.world_size==4) and
  (.model_rank_count==4) and (.optimizer_rank_count==4) and (.extra_state_rank_count==4) and
  (.files_stable_during_hash==true)
' "${RESTORE_AUDIT}" >/dev/null || { echo "M5 restored checkpoint audit is invalid" >&2; exit 3; }

if [[ "${START_STEP}" -eq 200 ]]; then
  [[ "${BOUNDARY_RUN}" != "-" ]] || { echo "step-200 segment requires boundary handoff evidence" >&2; exit 3; }
  jq -e --arg source "${PRIOR_RUN}" '
    (.status=="handoff_complete") and (.source_run==$source) and
    (.resume_required_from_step==200) and (.boundary_evidence.status=="pass") and
    (.wrapper_exited==true) and (.sigkill_used==false) and
    (.signal_selection.selected_signal=="SIGTERM")
  ' "${BOUNDARY_RUN}/handoff_result.json" >/dev/null || { echo "step-200 boundary handoff is invalid" >&2; exit 3; }
  jq -e '(.status=="fail") and (.exit_code==-6)' "${PRIOR_MANIFEST}" >/dev/null || {
    echo "step-200 prior run is not the controlled handoff parent" >&2; exit 3;
  }
  jq -e '(.status=="complete") and (.global_step==200) and (.geo3k_status=="complete") and (.r19_status=="complete")' \
    "${PRIOR_RUN}/evaluations/step200_evaluation_complete.json" >/dev/null || {
    echo "step-200 registered evaluation is incomplete" >&2; exit 3;
  }
else
  [[ "${BOUNDARY_RUN}" == "-" ]] || { echo "later M5 segments must not reuse step-200 handoff evidence" >&2; exit 3; }
  jq -e --argjson start "${START_STEP}" '
    (.status=="complete") and (.exit_code==0) and (.operational_segment==true) and
    (.segment_end_step==$start)
  ' "${PRIOR_MANIFEST}" >/dev/null || { echo "prior M5 segment did not complete naturally" >&2; exit 3; }
fi

CHECKPOINT_ROOT="$(jq -er '.checkpoint_path' "${PRIOR_MANIFEST}")"
SOURCE_CHECKPOINT="${CHECKPOINT_ROOT}/global_step_${START_STEP}"
SOURCE_ACTOR="${SOURCE_CHECKPOINT}/actor"
SOURCE_MARKER="${SOURCE_ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json"
TARGET_CHECKPOINT="${CHECKPOINT_ROOT}/global_step_${END_STEP}"
ARCHIVE_ROOT="$(jq -r '.checkpoint_archive_root // empty' "${PRIOR_MANIFEST}")"
if [[ -z "${ARCHIVE_ROOT}" ]]; then
  PRIOR_ID="$(jq -er '.run_id' "${PRIOR_MANIFEST}")"
  ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PRIOR_ID}"
fi
case "${ARCHIVE_ROOT}" in /tmp/blindgain_checkpoint_archive/*) ;; *) echo "invalid M5 archive root" >&2; exit 3;; esac
jq -e '(.status=="restored_for_optimizer_resume") and (.files|length==8)' "${SOURCE_MARKER}" >/dev/null || {
  echo "M5 source raw state is not restored" >&2; exit 3;
}
[[ "$(find "${SOURCE_ACTOR}" -maxdepth 1 -type f \( -name 'model_world_size_4_rank_*.pt' -o -name 'optim_world_size_4_rank_*.pt' \) | wc -l)" -eq 8 ]] || {
  echo "M5 source raw shard count is not eight" >&2; exit 3;
}
[[ "$(jq -er '.last_global_step' "${CHECKPOINT_ROOT}/checkpoint_tracker.json")" == "${START_STEP}" ]] || {
  echo "M5 checkpoint tracker does not match the segment source" >&2; exit 3;
}
[[ ! -e "${TARGET_CHECKPOINT}" ]] || { echo "refusing existing M5 target checkpoint" >&2; exit 73; }

[[ -s "${PREFLIGHT_MANIFEST}" && -s "${PREFLIGHT_OUTPUT}" ]] || { echo "M5 Ray preflight artifacts are absent" >&2; exit 3; }
PREFLIGHT_AGE="$(( $(date -u +%s) - $(date -u -d "$(jq -er '.end_time_utc' "${PREFLIGHT_MANIFEST}")" +%s) ))"
PREFLIGHT_GPUS="$(jq -c '.gpu_ids|sort' "${PREFLIGHT_MANIFEST}")"
REQUESTED_GPUS="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)|sort')"
jq -e --arg node "${NODE}" --arg head "$(git rev-parse HEAD)" '
  (.job_type=="m5_ray_startup_preflight") and (.status=="complete") and (.exit_code==0) and
  (.node==$node) and (.git_hash==$head) and (.performance_values_opened==false)
' "${PREFLIGHT_MANIFEST}" >/dev/null || { echo "M5 Ray preflight manifest identity is invalid" >&2; exit 3; }
[[ "${PREFLIGHT_GPUS}" == "${REQUESTED_GPUS}" ]] || { echo "M5 Ray preflight GPU set differs from launch" >&2; exit 3; }
[[ "${PREFLIGHT_AGE}" -ge 0 && "${PREFLIGHT_AGE}" -le 900 ]] || { echo "M5 Ray preflight is older than 15 minutes" >&2; exit 3; }
jq -e '(.status=="pass") and (.expected_rounds==2) and (.rounds|length==2) and ([.checks[]]|all)' \
  "${PREFLIGHT_OUTPUT}" >/dev/null || { echo "M5 Ray preflight result is not pass" >&2; exit 3; }

if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"; then
  echo "another project EasyR1 trainer is active on ${NODE}" >&2; exit 74
fi
capacity_ok() {
  local OBS ROW MEMORY UTIL
  OBS="$(ssh "${NODE}" "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits")"
  for GPU in "${GPUS[@]}"; do
    ROW="$(awk -F',' -v target="${GPU}" '{gsub(/ /,"",$1); if($1==target)print}' <<< "${OBS}")"
    MEMORY="$(awk -F',' '{gsub(/ /,"",$2);print $2}' <<< "${ROW}")"
    UTIL="$(awk -F',' '{gsub(/ /,"",$3);print $3}' <<< "${ROW}")"
    [[ "${MEMORY}" =~ ^[0-9]+$ && "${UTIL}" =~ ^[0-9]+$ && "${MEMORY}" -le 1024 && "${UTIL}" -le 10 ]] || return 1
  done
}
capacity_ok || { echo "selected M5 segment GPUs are not free" >&2; exit 75; }
sleep 20
capacity_ok || { echo "selected M5 segment GPUs did not remain free" >&2; exit 75; }
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
[[ "${MEM_AVAILABLE_KIB}" -ge 681574400 ]] || { echo "M5 segment needs 650 GiB host memory" >&2; exit 76; }
[[ ! -e "${TARGET_CHECKPOINT}" ]] || { echo "M5 target appeared during preflight" >&2; exit 73; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_anchor_longhorizon_segment${START_STEP}_${END_STEP}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
CONFIG_SNAPSHOT="${ROOT}/${RUN_DIR}/effective_config.yaml"
CONFIG_AUDIT="${ROOT}/${RUN_DIR}/effective_config_audit.json"
REGISTRATION_SNAPSHOT="${ROOT}/${RUN_DIR}/registered_extensions_v1.md"
RESTORE_AUDIT_SNAPSHOT="${ROOT}/${RUN_DIR}/source_restore_audit.json"
PREFLIGHT_MANIFEST_SNAPSHOT="${ROOT}/${RUN_DIR}/ray_preflight_manifest.json"
PREFLIGHT_OUTPUT_SNAPSHOT="${ROOT}/${RUN_DIR}/ray_preflight.json"
PRIOR_MANIFEST_SNAPSHOT="${ROOT}/${RUN_DIR}/prior_training_manifest.json"
EASYR1_DIR="${ROOT}/artifacts/repos/EasyR1"
EASYR1_PATCH="${ROOT}/${RUN_DIR}/easyr1_worktree.patch"
RAY_ROOT="/dev/shm/bg-ray-$(printf '%s' "${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
JOB_TMP="${RAY_ROOT}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_m5_anchor_longhorizon_400.lock"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/evaluations"
.venv/bin/python scripts/build_m5_segment_config.py --base "${BASE_CONFIG}" \
  --output "${CONFIG_SNAPSHOT}" --load-checkpoint-path "${SOURCE_CHECKPOINT}" \
  --save-checkpoint-path "${CHECKPOINT_ROOT}" --segment-start-step "${START_STEP}" \
  --audit-output "${CONFIG_AUDIT}"
install -m 0444 "${REGISTRATION}" "${REGISTRATION_SNAPSHOT}"
install -m 0444 "${RESTORE_AUDIT}" "${RESTORE_AUDIT_SNAPSHOT}"
install -m 0444 "${PREFLIGHT_MANIFEST}" "${PREFLIGHT_MANIFEST_SNAPSHOT}"
install -m 0444 "${PREFLIGHT_OUTPUT}" "${PREFLIGHT_OUTPUT_SNAPSHOT}"
install -m 0444 "${PRIOR_MANIFEST}" "${PRIOR_MANIFEST_SNAPSHOT}"
git -C "${EASYR1_DIR}" diff --binary --no-ext-diff > "${EASYR1_PATCH}"
chmod 0444 "${EASYR1_PATCH}"
COMMAND="python -u -m verl.trainer.main config=${CONFIG_SNAPSHOT}"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
LOG_START_BYTES=0
[[ ! -f "${CHECKPOINT_ROOT}/experiment_log.jsonl" ]] || LOG_START_BYTES="$(stat -c '%s' "${CHECKPOINT_ROOT}/experiment_log.jsonl")"

jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${RUN_DIR}/effective_config.yaml" --arg config_hash "$(sha256sum "${CONFIG_SNAPSHOT}" | awk '{print $1}')" \
  --arg config_audit "${RUN_DIR}/effective_config_audit.json" --arg source "${SOURCE_CHECKPOINT}" \
  --arg source_marker "${SOURCE_MARKER}" --arg restore_run "${RESTORE_RUN}" \
  --arg restore_hash "$(sha256sum "${RESTORE_AUDIT}" | awk '{print $1}')" \
  --arg prior_run "${PRIOR_RUN}" --arg prior_hash "$(sha256sum "${PRIOR_MANIFEST}" | awk '{print $1}')" \
  --arg preflight_run "${PREFLIGHT_RUN}" --arg preflight_manifest_hash "$(sha256sum "${PREFLIGHT_MANIFEST}" | awk '{print $1}')" \
  --arg preflight_output_hash "$(sha256sum "${PREFLIGHT_OUTPUT}" | awk '{print $1}')" \
  --arg registration "${RUN_DIR}/registered_extensions_v1.md" --arg easyr1_revision "$(git -C "${EASYR1_DIR}" rev-parse HEAD)" \
  --arg easyr1_patch "${RUN_DIR}/easyr1_worktree.patch" --arg easyr1_patch_hash "$(sha256sum "${EASYR1_PATCH}" | awk '{print $1}')" \
  --arg command "PYTHONPATH=${EASYR1_DIR}:${ROOT} ${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg checkpoint "${CHECKPOINT_ROOT}" --arg archive "${ARCHIVE_ROOT}" --arg target "${TARGET_CHECKPOINT}" \
  --arg log "${LOG}" --arg ray_root "${RAY_ROOT}" --arg job_tmp "${JOB_TMP}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${PRIOR_MANIFEST}")" \
  --argjson start_step "${START_STEP}" --argjson end_step "${END_STEP}" \
  --argjson mem_available "${MEM_AVAILABLE_KIB}" --argjson log_start "${LOG_START_BYTES}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_anchor_longhorizon_400",
    operational_segment:true,segment_start_step:$start_step,segment_end_step:$end_step,
    node:$node,gpu_allocation:$allocation,gpu_ids:$gpu_ids,tensor_parallel_width:2,replica_count:2,
    placement_policy_version:"pi-2026-07-11",
    placement_justification:"Single-node synchronous native-reward M5 segment on four GPUs. TP2 is retained from the already-launched anchor recipe solely for checkpoint/config continuity; no cross-node disaggregation is used.",
    git_hash:$git_hash,config_path:$config,config_hash:$config_hash,config_derivation_audit:$config_audit,
    data_manifest:"hiyouga/geometry3k@train|hiyouga/geometry3k@test",data_manifest_hash:$data_hash,
    model_revision:"Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3",seed:1,
    resumed_from_global_step:$start_step,target_global_step:400,source_checkpoint:$source,source_restore_marker:$source_marker,
    restore_run:$restore_run,restore_audit_sha256:$restore_hash,prior_training_run:$prior_run,prior_training_manifest_sha256:$prior_hash,
    ray_startup_preflight_run:$preflight_run,ray_startup_preflight_manifest_sha256:$preflight_manifest_hash,
    ray_startup_preflight_output_sha256:$preflight_output_hash,registration_snapshot:$registration,
    easyr1_revision:$easyr1_revision,easyr1_worktree_patch:$easyr1_patch,easyr1_worktree_patch_sha256:$easyr1_patch_hash,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",checkpoint_path:$checkpoint,
    checkpoint_archive_root:$archive,target_checkpoint:$target,checkpoint_schedule:[200,250,300,350,400],
    registered_evaluation_steps:[200,300,400],terminal_step:400,terminal_no_extension:true,validation_cadence:10,
    raw_retention:"latest raw state only after verified merge",stdout_stderr_log:$log,ray_tmp_dir:$ray_root,runtime_tmp_dir:$job_tmp,
    shared_experiment_log_append_start_bytes:$log_start,
    host_memory_preflight:{minimum_mem_available_gib:650,observed_kib:$mem_available,exclusive_project_trainer:true},
    optimizer_schedule:{resolved_type:"constant",warmup_ratio:0.0,state_restored:true,scientific_terminal_step:400},
    expected_artifacts:[$target,($checkpoint+"/checkpoint_tracker.json")],scientific_gate_decision:null,
    performance_values_opened:false,
    deviations:["Operational process segmentation at a hash-verified 50-step checkpoint boundary mitigates the measured Ray/worker host-memory ramp; the registered scientific terminal remains step 400.","trainer.max_steps is set to the segment end only to obtain a natural process exit. The registered constant zero-warmup scheduler and its checkpointed state are unchanged.","TP2 is retained from the already-launched anchor recipe for exact continuation even though the standing placement preference for <=7B models is TP1."]}' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=60000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${EASYR1_DIR}:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' >/dev/null 2>&1 </dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || { echo "M5 segment exited during startup" >&2; exit 1; }
STARTUP_READY=0
for _ in $(seq 1 40); do
  if ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
    echo "M5 segment exited before startup readiness" >&2
    tail -n 120 "${LOG}" >&2 || true
    exit 1
  fi
  if rg -q 'runtime_env_agent.*timed out|ActorDiedError|Owner.s node has crashed' "${LOG}"; then
    echo "M5 segment reported a Ray startup failure" >&2
    exit 1
  fi
  ACTIVE_GPU_COUNT=0
  for GPU in "${GPUS[@]}"; do
    if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits" | sed '/^[[:space:]]*$/d')" ]]; then
      ACTIVE_GPU_COUNT="$((ACTIVE_GPU_COUNT + 1))"
    fi
  done
  if rg -q 'Started a local Ray instance' "${LOG}" && [[ "${ACTIVE_GPU_COUNT}" -eq 4 ]]; then
    STARTUP_READY=1
    break
  fi
  sleep 15
done
[[ "${STARTUP_READY}" -eq 1 ]] || { echo "M5 segment did not reach four-GPU startup readiness in 10 minutes" >&2; exit 1; }

EVALUATION_QUEUE="none"
if [[ "${END_STEP}" -eq 300 || "${END_STEP}" -eq 400 ]]; then
  EVALUATION_QUEUE="$(bash scripts/launch_m5_checkpoint_evaluation_queue.sh "${RUN_DIR}" "${END_STEP}")"
  printf '%s\n' "${EVALUATION_QUEUE}" > "${RUN_DIR}/evaluation_queue_run.txt"
fi
CHECKPOINT_WATCH="$(bash scripts/launch_m5_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
RELOCATION_WATCH="$(bash scripts/launch_m5_merged_relocation_watch.sh "${RUN_DIR}")"
printf '%s\n' "${CHECKPOINT_WATCH}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\n' "${RELOCATION_WATCH}" > "${RUN_DIR}/relocation_watcher_run.txt"
printf '%s\n' "${RUN_DIR}"
printf 'checkpoint_watcher=%s\nrelocation_watcher=%s\nevaluation_queue=%s\n' \
  "${CHECKPOINT_WATCH}" "${RELOCATION_WATCH}" "${EVALUATION_QUEUE}"
