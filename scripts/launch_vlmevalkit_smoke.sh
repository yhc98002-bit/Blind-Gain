#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an29}"
GPUS="${2:-1,2}"
CONFIG="${3:-configs/eval/vlmevalkit_p1_2_smoke.json}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="vlmevalkit_smoke_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
WORK_DIR="${RUN_DIR}/work"
COMMAND="PYTHONPATH=artifacts/repos/VLMEvalKit LMUData=${ROOT}/data/vlmevalkit VLLM_WORKER_MULTIPROC_METHOD=spawn CUDA_VISIBLE_DEVICES=${GPUS} artifacts/envs/vlmevalkit/bin/python artifacts/repos/VLMEvalKit/run.py --config ${CONFIG} --work-dir ${WORK_DIR} --mode all"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${WORK_DIR}"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
COMMAND_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
cat > "${MANIFEST}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_2_vlmevalkit_mmstar_mini_smoke",
  "node": "${NODE}",
  "gpu_allocation": "${GPUS}",
  "git_hash": "$(git rev-parse HEAD)",
  "config_path": "${CONFIG}",
  "config_hash": "${CONFIG_HASH}",
  "command_hash": "${COMMAND_HASH}",
  "data_manifest": "VLMEvalKit MMStar_MINI pinned URL/MD5 at commit 6a02ab92471a8c544ff0769da5968a29fd75971f",
  "data_manifest_hash": null,
  "model_revision": "Qwen2.5-VL-3B-Instruct ModelScope master",
  "command": "${COMMAND}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_artifacts": ["${WORK_DIR}"]
}
JSON

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${WORK_DIR}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
echo "${RUN_DIR}"
echo "pid_file=${PID_FILE} log=${LOG}"
