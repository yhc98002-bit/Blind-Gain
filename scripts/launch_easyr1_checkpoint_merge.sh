#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 NODE ACTOR_DIR RUN_TAG" >&2
  exit 2
fi

NODE="$1"
ACTOR_DIR="$2"
RUN_TAG="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi
if [[ ! -f "${ROOT}/${ACTOR_DIR}/model_world_size_2_rank_0.pt" ]]; then
  echo "Missing EasyR1 actor shards: ${ACTOR_DIR}" >&2
  exit 2
fi
if compgen -G "${ROOT}/${ACTOR_DIR}/huggingface/*.safetensors" > /dev/null; then
  echo "Refusing to overwrite an already merged checkpoint" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="easyr1_checkpoint_merge_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
OUTPUT_INDEX="${ACTOR_DIR}/huggingface/model.safetensors.index.json"
COMMAND="PYTHONPATH=artifacts/repos/EasyR1 TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home .venv/bin/python scripts/model_merger_no_deepspeed.py --local_dir ${ACTOR_DIR}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
SHARD_HASH="$(sha256sum "${ACTOR_DIR}"/model_world_size_*_rank_*.pt | sort -k2 | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg actor_dir "${ACTOR_DIR}" \
  --arg shard_hash "${SHARD_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output_index "${OUTPUT_INDEX}" \
  '{
    run_id: $run_id,
    job_type: "p0_2_easyr1_checkpoint_merge",
    node: $node,
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $actor_dir,
    data_manifest_hash: $shard_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output_index]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
