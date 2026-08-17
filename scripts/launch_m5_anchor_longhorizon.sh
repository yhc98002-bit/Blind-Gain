#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <an12|an29> <gpu0,gpu1,gpu2,gpu3>" >&2
  exit 2
fi
NODE="$1"
GPU_LIST="$2"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid node" >&2; exit 2; }
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
[[ "${#GPUS[@]}" -eq 4 && "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -eq 4 ]] || {
  echo "M5 requires four unique GPU ids" >&2; exit 2;
}
for GPU in "${GPUS[@]}"; do [[ "${GPU}" =~ ^[0-7]$ ]] || exit 2; done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
CONFIG_REL="configs/train/m5_anchor_longhorizon_400.yaml"
CONFIG="${ROOT}/${CONFIG_REL}"
EXPECTED_CONFIG_HASH="73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c"
REGISTRATION="docs/registered_extensions_v1.md"
AUTHORIZATION="reports/registered_extensions_authorization_v4.json"
INTEGRITY_JSON="reports/m5_restore_resume_integrity.json"
INTEGRITY_MD="reports/m5_restore_resume_integrity.md"
SOURCE_ID="anchor_a0_recipe_3b_geo3k_20260709T224852Z"
SOURCE_CHECKPOINT="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${SOURCE_ID}/global_step_100"
SOURCE_MARKER="${SOURCE_CHECKPOINT}/actor/RAW_STATE_RESTORED_FOR_RESUME.json"
SAVE_ROOT="${ROOT}/checkpoints/m5_anchor_longhorizon_400"
LOCK="/dev/shm/blind_gains_${NODE}_m5_anchor_longhorizon_400.lock"

for FILE in "${CONFIG_REL}" "${REGISTRATION}" scripts/launch_m5_anchor_longhorizon.sh \
  scripts/watch_m5_checkpoints.py scripts/watch_m5_merged_relocation.py \
  scripts/launch_m5_checkpoint_watch.sh scripts/launch_m5_merged_relocation_watch.sh; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked M5 critical file: ${FILE}" >&2; exit 2; }
done
git diff --quiet HEAD -- "${CONFIG_REL}" "${REGISTRATION}" scripts/launch_m5_anchor_longhorizon.sh \
  scripts/watch_m5_checkpoints.py scripts/watch_m5_merged_relocation.py \
  scripts/launch_m5_checkpoint_watch.sh scripts/launch_m5_merged_relocation_watch.sh || {
  echo "M5 registration/config/launcher differs from HEAD" >&2; exit 2;
}
[[ "$(sha256sum "${CONFIG}" | awk '{print $1}')" == "${EXPECTED_CONFIG_HASH}" ]] || {
  echo "M5 config hash changed" >&2; exit 2;
}
grep -Fx -- '- Registration state: merged-at-HEAD; merge is sign-off.' "${REGISTRATION}" >/dev/null || {
  echo "M5 registration marker absent" >&2; exit 2;
}
jq -e '(.status=="authorized") and (.authorization.m5=="authorized_after_restore_integrity_pass")' \
  "${AUTHORIZATION}" >/dev/null || { echo "M5 authorization invalid" >&2; exit 2; }
jq -e '(.schema_version=="blind-gains.m5-restore-resume-integrity.v1") and (.status=="pass") and (.checks|length>0) and all(.checks[];.==true)' \
  "${INTEGRITY_JSON}" >/dev/null || { echo "M5 restore integrity does not pass" >&2; exit 3; }
[[ -s "${INTEGRITY_MD}" ]] || { echo "M5 integrity Markdown absent" >&2; exit 3; }
jq -e '(.status=="restored_for_optimizer_resume") and (.files|length==8)' "${SOURCE_MARKER}" >/dev/null || {
  echo "source raw state is not restored" >&2; exit 3;
}
[[ ! -e "${SAVE_ROOT}" ]] || { echo "refusing existing M5 checkpoint root" >&2; exit 73; }
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"; then
  echo "another project EasyR1 trainer is already active on ${NODE}" >&2; exit 74;
fi

check_capacity() {
  local OBS ROW MEMORY UTIL
  OBS="$(ssh "${NODE}" "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits")"
  for GPU in "${GPUS[@]}"; do
    ROW="$(awk -F',' -v target="${GPU}" '{gsub(/ /,"",$1); if($1==target)print}' <<< "${OBS}")"
    MEMORY="$(awk -F',' '{gsub(/ /,"",$2);print $2}' <<< "${ROW}")"
    UTIL="$(awk -F',' '{gsub(/ /,"",$3);print $3}' <<< "${ROW}")"
    [[ "${MEMORY}" =~ ^[0-9]+$ && "${UTIL}" =~ ^[0-9]+$ && "${MEMORY}" -le 1024 && "${UTIL}" -le 10 ]] || return 1
  done
}
check_capacity || { echo "selected M5 GPUs are not free" >&2; exit 75; }
sleep 20
check_capacity || { echo "selected M5 GPUs did not remain free" >&2; exit 75; }
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"
[[ "${MEM_AVAILABLE_KIB}" -ge 681574400 ]] || { echo "M5 needs 650 GiB host memory" >&2; exit 76; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_anchor_longhorizon_400_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
CONFIG_SNAPSHOT="${ROOT}/${RUN_DIR}/effective_config.yaml"
REGISTRATION_SNAPSHOT="${ROOT}/${RUN_DIR}/registered_extensions_v1.md"
INTEGRITY_SNAPSHOT="${ROOT}/${RUN_DIR}/m5_restore_resume_integrity.json"
EASYR1_DIR="${ROOT}/artifacts/repos/EasyR1"
EASYR1_PATCH="${ROOT}/${RUN_DIR}/easyr1_worktree.patch"
RAY_ROOT="/dev/shm/bg-ray-$(printf '%s' "${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
JOB_TMP="${RAY_ROOT}/tmp"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
COMMAND="python -u -m verl.trainer.main config=${CONFIG_SNAPSHOT}"
DATA_HASH="$(jq -r '.data_manifest_hash' experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z/run_manifest.json)"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${RUN_DIR}/evaluations"
install -m 0444 "${CONFIG}" "${CONFIG_SNAPSHOT}"
install -m 0444 "${REGISTRATION}" "${REGISTRATION_SNAPSHOT}"
install -m 0444 "${INTEGRITY_JSON}" "${INTEGRITY_SNAPSHOT}"
git -C "${EASYR1_DIR}" diff --binary --no-ext-diff > "${EASYR1_PATCH}"
chmod 0444 "${EASYR1_PATCH}"
jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${RUN_DIR}/effective_config.yaml" --arg config_hash "${EXPECTED_CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" --arg source "${SOURCE_CHECKPOINT}" \
  --arg source_marker "${SOURCE_MARKER}" --arg integrity "${RUN_DIR}/m5_restore_resume_integrity.json" \
  --arg integrity_hash "$(sha256sum "${INTEGRITY_JSON}" | awk '{print $1}')" \
  --arg registration "${RUN_DIR}/registered_extensions_v1.md" \
  --arg registration_hash "$(sha256sum "${REGISTRATION}" | awk '{print $1}')" \
  --arg easyr1_revision "$(git -C "${EASYR1_DIR}" rev-parse HEAD)" \
  --arg easyr1_patch "${RUN_DIR}/easyr1_worktree.patch" \
  --arg easyr1_patch_hash "$(sha256sum "${EASYR1_PATCH}" | awk '{print $1}')" \
  --arg command "PYTHONPATH=${EASYR1_DIR}:${ROOT} ${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg checkpoint "${SAVE_ROOT}" --arg log "${LOG}" --arg ray_root "${RAY_ROOT}" --arg job_tmp "${JOB_TMP}" \
  --argjson mem_available "${MEM_AVAILABLE_KIB}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_anchor_longhorizon_400",
    node:$node,gpu_allocation:$allocation,gpu_ids:$gpu_ids,tensor_parallel_width:2,replica_count:2,
    placement_policy_version:"pi-2026-07-11",placement_justification:"One synchronous native-reward anchor continuation on four GPUs of one node; TP2/2 replicas preserve the launched anchor recipe exactly.",
    git_hash:$git_hash,config_path:$config,config_hash:$config_hash,
    data_manifest:"hiyouga/geometry3k@train|hiyouga/geometry3k@test",data_manifest_hash:$data_hash,
    model_revision:"Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3",seed:1,
    resumed_from_global_step:100,target_global_step:400,source_checkpoint:$source,source_restore_marker:$source_marker,
    restore_integrity_artifact:$integrity,restore_integrity_sha256:$integrity_hash,
    registration_snapshot:$registration,registration_sha256:$registration_hash,
    easyr1_revision:$easyr1_revision,easyr1_worktree_patch:$easyr1_patch,easyr1_worktree_patch_sha256:$easyr1_patch_hash,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",checkpoint_path:$checkpoint,
    checkpoint_schedule:[150,200,250,300,350,400],registered_evaluation_steps:[150,200,300,400],
    terminal_step:400,terminal_no_extension:true,validation_cadence:10,raw_retention:"latest raw state only after verified merge",
    stdout_stderr_log:$log,ray_tmp_dir:$ray_root,runtime_tmp_dir:$job_tmp,
    host_memory_preflight:{minimum_mem_available_gib:650,observed_kib:$mem_available},
    expected_artifacts:[($checkpoint+"/experiment_log.jsonl"),($checkpoint+"/checkpoint_tracker.json"),($checkpoint+"/global_step_400/actor")],
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=60000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${EASYR1_DIR}:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' >/dev/null 2>&1 </dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || { echo "M5 exited during startup" >&2; exit 1; }
CHECKPOINT_WATCH="$(bash scripts/launch_m5_checkpoint_watch.sh "${NODE}" "${RUN_DIR}")"
RELOCATION_WATCH="$(bash scripts/launch_m5_merged_relocation_watch.sh "${RUN_DIR}")"
printf '%s\n' "${CHECKPOINT_WATCH}" > "${RUN_DIR}/checkpoint_watcher_run.txt"
printf '%s\n' "${RELOCATION_WATCH}" > "${RUN_DIR}/relocation_watcher_run.txt"
printf '%s\n' "${RUN_DIR}"
printf 'checkpoint_watcher=%s\nrelocation_watcher=%s\n' "${CHECKPOINT_WATCH}" "${RELOCATION_WATCH}"
