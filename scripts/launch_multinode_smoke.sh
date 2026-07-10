#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 bandwidth|fsdp [MASTER_PORT]" >&2
  exit 2
fi

MODE="$1"
MASTER_PORT="${2:-29671}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MASTER_ADDR="99.72.4.13"
MODEL_PATH="artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"

if [[ "${MODE}" != "bandwidth" && "${MODE}" != "fsdp" ]]; then
  echo "MODE must be bandwidth or fsdp" >&2
  exit 2
fi
if [[ ! "${MASTER_PORT}" =~ ^[1-9][0-9]{3,4}$ ]] || (( MASTER_PORT > 65535 )); then
  echo "MASTER_PORT must be an integer from 1000 to 65535" >&2
  exit 2
fi

PREFLIGHT_BLOCKED=0
for NODE in an12 an29; do
  GPU_COUNT="$(ssh "${NODE}" "nvidia-smi -L | wc -l")"
  if [[ "${GPU_COUNT}" != "8" ]]; then
    echo "${NODE}: expected 8 GPUs, found ${GPU_COUNT}" >&2
    PREFLIGHT_BLOCKED=1
  fi
  ACTIVE="$(ssh "${NODE}" "nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader,nounits" | sed '/^[[:space:]]*$/d')"
  if [[ -n "${ACTIVE}" ]]; then
    echo "${NODE}: all 8 GPUs are required but compute processes are active:" >&2
    printf '%s\n' "${ACTIVE}" >&2
    PREFLIGHT_BLOCKED=1
  fi
done
if (( PREFLIGHT_BLOCKED != 0 )); then
  exit 3
fi
if ssh an12 "ss -lnt | awk '{print \$4}' | grep -Eq '[:.]${MASTER_PORT}$'"; then
  echo "an12: master port ${MASTER_PORT} is already in use" >&2
  exit 3
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="multinode_${MODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
METRICS="${RUN_DIR}/metrics.json"
EXIT_CODES="${RUN_DIR}/node_exit_codes.json"
LOG_AN12="${RUN_DIR}/logs/an12.log"
LOG_AN29="${RUN_DIR}/logs/an29.log"

if [[ "${MODE}" == "bandwidth" ]]; then
  WORKER_COMMAND="scripts/nccl_allreduce_bench.py --tensor-mib 256 --warmup 5 --iterations 20 --expected-world-size 16 --output ${METRICS}"
  DATA_MANIFEST="scripts/nccl_allreduce_bench.py"
  DATA_HASH="$(sha256sum "${ROOT}/scripts/nccl_allreduce_bench.py" | awk '{print $1}')"
  JOB_TYPE="p1_3_multinode_nccl_bandwidth"
else
  WORKER_COMMAND="scripts/fsdp_qwen25vl_smoke.py --model-path ${MODEL_PATH} --steps 1 --sequence-length 64 --expected-world-size 16 --output ${METRICS}"
  DATA_MANIFEST="${MODEL_PATH}/config.json"
  DATA_HASH="$(sha256sum "${ROOT}/${MODEL_PATH}/config.json" | awk '{print $1}')"
  JOB_TYPE="p1_3_multinode_fsdp_qwen25vl3b"
fi

TORCHRUN_COMMON="timeout --signal=TERM --kill-after=60s 3600s env NCCL_SOCKET_IFNAME=ib0 GLOO_SOCKET_IFNAME=ib0 NCCL_IB_DISABLE=0 NCCL_DEBUG=INFO TORCH_NCCL_ASYNC_ERROR_HANDLING=1 TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home OMP_NUM_THREADS=4 ${ROOT}/.venv/bin/torchrun --nnodes=2 --nproc-per-node=8 --master-addr=${MASTER_ADDR} --master-port=${MASTER_PORT}"
COMMAND_AN12="${TORCHRUN_COMMON} --node-rank=0 ${WORKER_COMMAND}"
COMMAND_AN29="${TORCHRUN_COMMON} --node-rank=1 ${WORKER_COMMAND}"
LAUNCH_COMMAND="scripts/launch_multinode_smoke.sh ${MODE} ${MASTER_PORT}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg job_type "${JOB_TYPE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s\n%s\n' "${COMMAND_AN12}" "${COMMAND_AN29}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "${DATA_MANIFEST}" \
  --arg data_hash "${DATA_HASH}" \
  --arg launch_command "${LAUNCH_COMMAND}" \
  --arg command_an12 "${COMMAND_AN12}" \
  --arg command_an29 "${COMMAND_AN29}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg metrics "${METRICS}" \
  --arg exit_codes "${EXIT_CODES}" \
  '{
    run_id: $run_id,
    job_type: $job_type,
    node: ["an12", "an29"],
    gpu_allocation: {an12: [0,1,2,3,4,5,6,7], an29: [0,1,2,3,4,5,6,7]},
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    command: $launch_command,
    node_commands: {an12: $command_an12, an29: $command_an29},
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$metrics, $exit_codes]
  }' > "${MANIFEST}"

set +e
ssh an12 "cd '${ROOT}' && exec ${COMMAND_AN12}" > "${LOG_AN12}" 2>&1 &
PID_AN12=$!
ssh an29 "cd '${ROOT}' && exec ${COMMAND_AN29}" > "${LOG_AN29}" 2>&1 &
PID_AN29=$!
wait "${PID_AN12}"
EXIT_AN12=$?
wait "${PID_AN29}"
EXIT_AN29=$?
set -e

jq -n --argjson an12 "${EXIT_AN12}" --argjson an29 "${EXIT_AN29}" \
  '{an12: $an12, an29: $an29}' > "${EXIT_CODES}"
EXIT_CODE=0
if (( EXIT_AN12 != 0 || EXIT_AN29 != 0 )); then
  EXIT_CODE=1
fi
"${ROOT}/.venv/bin/python" scripts/finalize_run_manifest.py "${MANIFEST}" "${EXIT_CODE}"
printf '%s\n' "${RUN_DIR}"
exit "${EXIT_CODE}"
