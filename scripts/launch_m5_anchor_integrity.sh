#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 NODE GPU0,GPU1,GPU2,GPU3 RESTORE_RUN_DIR" >&2
  exit 2
fi

NODE="$1"
GPU_LIST="$2"
RESTORE_RUN_DIR="$3"
if [[ "${NODE}" != "an12" && "${NODE}" != "an29" ]]; then
  echo "M5 integrity node must be an12 or an29" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "${GPU_LIST}"
if [[ "${#GPUS[@]}" -ne 4 || "$(printf '%s\n' "${GPUS[@]}" | sort -u | wc -l)" -ne 4 ]]; then
  echo "M5 integrity requires four unique GPU ids" >&2
  exit 2
fi
for gpu in "${GPUS[@]}"; do
  [[ "${gpu}" =~ ^[0-7]$ ]] || { echo "invalid GPU id: ${gpu}" >&2; exit 2; }
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ID="anchor_a0_recipe_3b_geo3k_20260709T224852Z"
SOURCE_CHECKPOINT="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${SOURCE_ID}/global_step_100"
RESTORE_MARKER="${SOURCE_CHECKPOINT}/actor/RAW_STATE_RESTORED_FOR_RESUME.json"
RESTORE_AUDIT="${ROOT}/${RESTORE_RUN_DIR}/restored_checkpoint_audit.json"
CONFIG="${ROOT}/configs/train/m5_anchor_resume_integrity_step101.yaml"
SAVE_ROOT="${ROOT}/checkpoints/m5_anchor_resume_integrity_step101"
SOURCE_METRICS="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${SOURCE_ID}/experiment_log.jsonl"
LOCK="/tmp/blind_gains_${NODE}_m5_anchor_integrity.lock"
EXPECTED_CONFIG_HASH="e99535a24e75d451976e7a13caf031c388e7905748b56cdcb3f52cc9bdb04112"

cd "${ROOT}"
if ! git diff --quiet HEAD -- \
  configs/train/m5_anchor_resume_integrity_step101.yaml \
  reports/m5_restore_resume_plan_v1.md \
  scripts/launch_m5_anchor_integrity.sh; then
  echo "M5 integrity launcher/config/plan must be committed at HEAD" >&2
  exit 2
fi
[[ "$(sha256sum "${CONFIG}" | awk '{print $1}')" == "${EXPECTED_CONFIG_HASH}" ]] || {
  echo "M5 integrity config hash changed" >&2
  exit 2
}
[[ "$(jq -r .status "${ROOT}/${RESTORE_RUN_DIR}/run_manifest.json")" == "complete" ]] || {
  echo "M5 raw restore run is not complete" >&2
  exit 2
}
[[ "$(jq -r .status "${RESTORE_MARKER}")" == "restored_for_optimizer_resume" ]] || {
  echo "M5 source raw state is not restored" >&2
  exit 2
}
[[ "$(jq -r .status "${RESTORE_AUDIT}")" == "pass" ]] || {
  echo "M5 restored checkpoint audit does not pass" >&2
  exit 2
}
[[ ! -e "${SAVE_ROOT}" ]] || {
  echo "Refusing existing M5 integrity checkpoint root: ${SAVE_ROOT}" >&2
  exit 2
}
if ssh "${NODE}" "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"; then
  echo "Another project EasyR1 trainer is already active on ${NODE}" >&2
  exit 74
fi

check_capacity() {
  local observations
  observations="$(ssh "${NODE}" "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits")"
  for gpu in "${GPUS[@]}"; do
    local row memory utilization
    row="$(awk -F',' -v target="${gpu}" '{gsub(/ /, "", $1); if ($1 == target) print}' <<< "${observations}")"
    memory="$(awk -F',' '{gsub(/ /, "", $2); print $2}' <<< "${row}")"
    utilization="$(awk -F',' '{gsub(/ /, "", $3); print $3}' <<< "${row}")"
    [[ -n "${memory}" && "${memory}" -le 1024 && "${utilization}" -le 10 ]] || return 1
  done
}
check_capacity || { echo "selected GPUs are not free" >&2; exit 75; }
sleep 20
check_capacity || { echo "selected GPUs did not remain free" >&2; exit 75; }
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "awk '/MemAvailable:/ {print \$2}' /proc/meminfo")"
[[ "${MEM_AVAILABLE_KIB}" -ge 681574400 ]] || {
  echo "M5 integrity requires at least 650 GiB host MemAvailable" >&2
  exit 76
}

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_anchor_resume_integrity_step101_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
RAY_ROOT="/dev/shm/bg-ray-$(printf '%s' "${RUN_ID}" | sha256sum | awk '{print substr($1,1,12)}')"
JOB_TMP="${RAY_ROOT}/tmp"
STORAGE_LOG="${RUN_DIR}/storage_guard.jsonl"
COMMAND="PYTHONPATH=${ROOT}/artifacts/repos/EasyR1:${ROOT} python -u -m verl.trainer.main config=${CONFIG}"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
DATA_HASH="$(jq -r .data_manifest_hash experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z/run_manifest.json)"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
install -m 0444 "${CONFIG}" "${RUN_DIR}/effective_config.yaml"
install -m 0444 reports/m5_restore_resume_plan_v1.md "${RUN_DIR}/m5_restore_resume_plan_v1.md"
jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg gpu_allocation "${GPU_LIST}" \
  --argjson gpu_ids "${GPU_IDS_JSON}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${RUN_DIR}/effective_config.yaml" --arg config_hash "${EXPECTED_CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" --arg checkpoint "${SOURCE_CHECKPOINT}" \
  --arg restore_run "${RESTORE_RUN_DIR}" --arg restore_marker "${RESTORE_MARKER}" \
  --arg restore_audit "${RESTORE_AUDIT}" --arg source_metrics "${SOURCE_METRICS}" \
  --arg save_root "${SAVE_ROOT}" --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg ray_root "${RAY_ROOT}" --arg job_tmp "${JOB_TMP}" \
  --argjson mem_available "${MEM_AVAILABLE_KIB}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m5_anchor_resume_integrity_step101",
    node: $node,
    gpu_allocation: $gpu_allocation,
    gpu_ids: $gpu_ids,
    tensor_parallel_width: 2,
    replica_count: 2,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "One synchronous native-reward anchor integrity step on one node; TP2 is retained because this run must preserve the launched anchor recipe exactly.",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: "hiyouga/geometry3k@train|hiyouga/geometry3k@test",
    data_manifest_hash: $data_hash,
    seed: 1,
    resumed_from_global_step: 100,
    target_global_step: 101,
    source_checkpoint: $checkpoint,
    source_restore_run: $restore_run,
    source_restore_marker: $restore_marker,
    source_restore_audit: $restore_audit,
    source_metrics: $source_metrics,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    checkpoint_path: $save_root,
    checkpoint_schedule: [101],
    validation_cadence: 10,
    stdout_stderr_log: $log,
    ray_tmp_dir: $ray_root,
    runtime_tmp_dir: $job_tmp,
    host_memory_preflight: {minimum_mem_available_gib: 650, observed_kib: $mem_available},
    raw_retention: "integrity checkpoint is re-derivable and removed only after its audit is committed",
    expected_artifacts: [($save_root + "/experiment_log.jsonl"), ($save_root + "/checkpoint_tracker.json"), ($save_root + "/global_step_101/actor")],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RAY_ROOT}' '${JOB_TMP}' && source .venv/bin/activate && (nohup setsid flock -n --no-fork '${LOCK}' env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}' RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=60000000000 BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}':\${PYTHONPATH:-} '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"

sleep 20
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || {
  echo "M5 integrity run exited during startup; inspect ${LOG}" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
