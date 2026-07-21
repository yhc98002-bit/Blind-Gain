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
  echo "M5 Ray preflight requires four unique GPU ids" >&2; exit 2;
}
for GPU in "${GPUS[@]}"; do [[ "${GPU}" =~ ^[0-7]$ ]] || exit 2; done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
CRITICAL=(scripts/probe_m5_ray_startup.py scripts/launch_m5_ray_startup_preflight.sh)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || { echo "untracked M5 preflight file: ${FILE}" >&2; exit 3; }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || { echo "M5 preflight code differs from HEAD" >&2; exit 3; }
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
capacity_ok || { echo "selected M5 preflight GPUs are not free" >&2; exit 75; }
sleep 20
capacity_ok || { echo "selected M5 preflight GPUs did not remain free" >&2; exit 75; }
MEM_AVAILABLE_KIB="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
[[ "${MEM_AVAILABLE_KIB}" -ge 681574400 ]] || { echo "M5 preflight needs 650 GiB host memory" >&2; exit 76; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_ray_startup_preflight_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
OUTPUT="${RUN_DIR}/preflight.json"
CLEANUP="${RUN_DIR}/runtime_cleanup.json"
RAY_ROOT="/dev/shm/bg-${RUN_ID}"
COMMAND="CUDA_VISIBLE_DEVICES=${GPU_LIST} PYTHONUNBUFFERED=1 RAY_DEDUP_LOGS=0 ${ROOT}/.venv/bin/python ${ROOT}/scripts/probe_m5_ray_startup.py --runtime-root ${RAY_ROOT} --output ${ROOT}/${OUTPUT} --rounds 2 --timeout 120"
GPU_IDS_JSON="$(printf '%s\n' "${GPUS[@]}" | jq -sc 'map(tonumber)')"
mkdir -p "${RUN_DIR}/logs"
jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" --argjson gpu_ids "${GPU_IDS_JSON}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg output "${OUTPUT}" --arg cleanup "${CLEANUP}" --arg ray_root "${RAY_ROOT}" \
  --argjson mem_available "${MEM_AVAILABLE_KIB}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_ray_startup_preflight",
    node:$node,gpu_allocation:$gpu_ids,gpu_ids:$gpu_ids,tensor_parallel_width:1,replica_count:4,
    placement_policy_version:"pi-2026-07-11",placement_justification:"Two isolated local-Ray sessions exercise runtime_env and four one-GPU actors on the exact proposed M5 placement before optimizer launch.",
    git_hash:$git_hash,config_path:"scripts/probe_m5_ray_startup.py",config_hash:$config_hash,
    data_manifest:"runtime-only preflight",data_manifest_hash:$config_hash,seed:20260721,
    command:$command,start_time_utc:$start,end_time_utc:null,status:"running",stdout_stderr_log:$log,
    runtime_tmp_dir:$ray_root,host_memory_preflight:{minimum_mem_available_gib:650,observed_kib:$mem_available},
    expected_artifacts:[$output],cleanup_record:$cleanup,performance_values_opened:false,
    scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

set +e
ssh "${NODE}" "cd '${ROOT}' && '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
RC=$?
set -e
ssh "${NODE}" "case '${RAY_ROOT}' in /dev/shm/bg-m5_ray_startup_preflight_*) rm -rf -- '${RAY_ROOT}' ;; *) exit 2 ;; esac"
jq -n --arg root "${RAY_ROOT}" --arg deleted "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.ephemeral-cleanup.v1",path:$root,status:"deleted",deleted_utc:$deleted}' > "${CLEANUP}"
[[ "${RC}" -eq 0 ]] || exit "${RC}"
jq -e '(.status=="pass") and (.expected_rounds==2) and (.rounds|length==2) and ([.checks[]]|all)' "${OUTPUT}" >/dev/null || {
  echo "M5 Ray startup preflight did not pass" >&2; exit 1;
}
printf '%s\n' "${RUN_DIR}"
