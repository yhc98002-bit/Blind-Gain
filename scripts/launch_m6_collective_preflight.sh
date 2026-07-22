#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
NODE="${1:-an29}"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || {
  echo "M6 collective preflight node must be an12 or an29" >&2
  exit 2
}
CRITICAL=(scripts/probe_single_node_collectives.py scripts/launch_m6_collective_preflight.sh)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked M6 collective preflight file: ${FILE}" >&2
    exit 2
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "M6 collective preflight code differs from HEAD" >&2
  exit 2
}

node_ready() {
  ssh "${NODE}" "
    set -euo pipefail
    test \"\$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '\$1 >= 1024 {bad=1} END {print bad+0}')\" = 0
    test \"\$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '\$1 > 10 {bad=1} END {print bad+0}')\" = 0
    ! ps -eo args= | awk -v root='${ROOT}' '\$0 ~ /[p]ython.*verl[.]trainer[.]main/ && index(\$0, root) {found=1} END {exit found ? 0 : 1}'
    test \"\$(awk '/MemAvailable:/{print \$2}' /proc/meminfo)\" -ge 681574400
    test \"\$(df -Pk /dev/shm | awk 'NR==2 {print \$4}')\" -ge 41943040
  "
}
node_ready || { echo "${NODE} is not ready for an isolated eight-GPU preflight" >&2; exit 75; }
sleep 30
node_ready || { echo "${NODE} did not remain ready for 30 seconds" >&2; exit 75; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m6_collective_preflight_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
OUTPUT="${RUN_DIR}/preflight.json"
DEFAULT_DIR="${RUN_DIR}/default"
IB0_DIR="${RUN_DIR}/ib0"
mkdir -p "${RUN_DIR}/logs" "${DEFAULT_DIR}" "${IB0_DIR}"
COMMAND="two fresh torchrun rounds (default socket selection, then ib0-pinned), 8 ranks each"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CONFIG_HASH}" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg output "${OUTPUT}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"m6_single_node_collective_preflight",status:"running",node:$node,
    gpu_allocation:"0,1,2,3,4,5,6,7",gpu_ids:[0,1,2,3,4,5,6,7],
    tensor_parallel_width:1,replica_count:8,
    placement_justification:"Two short single-node eight-rank collective checks exercise the exact NCCL and Gloo backends required before retrying the failed M6 member smoke.",
    git_hash:$git_hash,config_path:"scripts/probe_single_node_collectives.py",
    config_hash:$config_hash,data_manifest:"runtime-only collective preflight",
    data_manifest_hash:$config_hash,seed:null,command:$command,start_time_utc:$start,
    end_time_utc:null,exit_code:null,stdout_stderr_log:$log,
    expected_artifacts:[$output],scientific_gate_decision:null,deviations:[]}' > "${MANIFEST}"

set +e
ssh "${NODE}" "
  set -euo pipefail
  cd '${ROOT}'
  timeout --signal=TERM --kill-after=30s 300s env -u GLOO_SOCKET_IFNAME -u NCCL_SOCKET_IFNAME \
    CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 TORCH_NCCL_ASYNC_ERROR_HANDLING=1 \
    OMP_NUM_THREADS=2 '${ROOT}/.venv/bin/torchrun' --standalone --nnodes=1 \
    --nproc-per-node=8 '${ROOT}/scripts/probe_single_node_collectives.py' worker \
    --output-dir '${ROOT}/${DEFAULT_DIR}' --round-name default
  timeout --signal=TERM --kill-after=30s 300s env GLOO_SOCKET_IFNAME=ib0 NCCL_SOCKET_IFNAME=ib0 \
    CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 TORCH_NCCL_ASYNC_ERROR_HANDLING=1 \
    OMP_NUM_THREADS=2 '${ROOT}/.venv/bin/torchrun' --standalone --nnodes=1 \
    --nproc-per-node=8 '${ROOT}/scripts/probe_single_node_collectives.py' worker \
    --output-dir '${ROOT}/${IB0_DIR}' --round-name ib0
" > "${LOG}" 2>&1
RC=$?
if [[ "${RC}" -eq 0 ]]; then
  "${ROOT}/.venv/bin/python" scripts/probe_single_node_collectives.py combine \
    --round "${DEFAULT_DIR}/round.json" --round "${IB0_DIR}/round.json" \
    --output "${OUTPUT}" >> "${LOG}" 2>&1
  RC=$?
fi
set -e
STATUS="fail"
ARTIFACTS=false
if [[ "${RC}" -eq 0 ]] && jq -e '.status == "pass" and ([.checks[]] | all)' "${OUTPUT}" >/dev/null; then
  STATUS="complete"
  ARTIFACTS=true
fi
TMP="${MANIFEST}.partial.$$"
jq --arg status "${STATUS}" --arg end "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson rc "${RC}" --argjson artifacts "${ARTIFACTS}" \
  '.status=$status | .end_time_utc=$end | .exit_code=$rc | .artifacts_exist=$artifacts' \
  "${MANIFEST}" > "${TMP}"
mv "${TMP}" "${MANIFEST}"
printf '%s\n' "${RUN_DIR}"
exit "${RC}"
