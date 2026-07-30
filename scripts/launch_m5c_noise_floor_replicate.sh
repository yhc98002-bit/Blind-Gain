#!/usr/bin/env bash
# shellcheck disable=SC2029
# M5C noise-floor replicate launcher.
#
# Purpose: re-evaluate an ALREADY-EVALUATED geo3k checkpoint with the byte-identical
# decoding contract used by the cached run, so that R1-vs-R2 discordance measures the
# harness's own replicate noise floor. Mirrors scripts/launch_m5_geo3k_checkpoint_eval.sh
# exactly except that (a) step 100 is also permitted, (b) the run id carries a replicate
# tag, and (c) the source-training-manifest is supplied explicitly so the replicate can
# reuse the cached run's own frozen snapshot byte-for-byte.
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "usage: $0 NODE GPU GLOBAL_STEP REPLICATE CHECKPOINT SOURCE_TRAINING_MANIFEST" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
GLOBAL_STEP="$3"
REPLICATE="$4"
CHECKPOINT_INPUT="$5"
SOURCE_TRAINING_MANIFEST_INPUT="$6"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
MAX_TOKENS=2048
SEED=20260710
BATCH_SIZE=4
MIN_MEM_AVAILABLE_KIB=471859200  # 450 GiB, same guard as the registered M5 eval launcher.

[[ "${NODE}" =~ ^(an12|an29)$ && "${GPU}" =~ ^[0-7]$ ]] || { echo "invalid node or GPU" >&2; exit 2; }
[[ "${GLOBAL_STEP}" =~ ^(100|400)$ ]] || { echo "replicate step must be 100 or 400" >&2; exit 2; }
[[ "${REPLICATE}" =~ ^(r1|r2)$ ]] || { echo "replicate must be r1 or r2" >&2; exit 2; }

if [[ "${GLOBAL_STEP}" == "100" ]]; then
  ROW_SCHEMA="blind-gains.pilot-geo3k-step100-eval.v1"
else
  ROW_SCHEMA="blind-gains.m5-geo3k-checkpoint-eval.v1"
fi

cd "${ROOT}"
CHECKPOINT="$(realpath -m "${CHECKPOINT_INPUT}")"
SOURCE_TRAINING_MANIFEST="$(realpath -m "${SOURCE_TRAINING_MANIFEST_INPUT}")"
for path in "${SOURCE_TRAINING_MANIFEST}" "${CHECKPOINT}/model.safetensors.index.json" \
  "${SOURCE_MANIFEST}" "${FORMAT_PROMPT}" scripts/run_pilot_geo3k_step100_eval.py; do
  [[ -s "${path}" ]] || { echo "required replicate input is absent or empty: ${path}" >&2; exit 2; }
done

# The evaluation harness itself must be byte-identical to the committed version that
# produced the cached runs; otherwise the replicate is not a replicate.
git diff --quiet HEAD -- scripts/run_pilot_geo3k_step100_eval.py src/eval/blind_solvability.py \
  src/eval/prompt_contract.py src/eval/conditioned_inputs.py src/rewards/ || {
  echo "evaluation contract differs from HEAD" >&2; exit 3;
}

PYTHONPATH=. .venv/bin/python - "${CHECKPOINT}" <<'PY'
import sys
from pathlib import Path
from scripts.watch_anchor_checkpoints import merged_checkpoint_complete

if not merged_checkpoint_complete(Path(sys.argv[1])):
    raise SystemExit("merged checkpoint is incomplete")
PY

check_capacity() {
  local pids mem
  pids="$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits" | sed '/^[[:space:]]*$/d')"
  [[ -z "${pids}" ]] || return 1
  mem="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
  [[ "${mem}" =~ ^[0-9]+$ && "${mem}" -ge "${MIN_MEM_AVAILABLE_KIB}" ]]
}
check_capacity || { echo "replicate GPU or host-memory admission failed" >&2; exit 75; }
sleep 10
check_capacity || { echo "replicate capacity did not remain stable" >&2; exit 75; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5c_noisefloor_step${GLOBAL_STEP}_${REPLICATE}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
SOURCE_SNAPSHOT="${RUN_DIR}/source_training_manifest_snapshot.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
install -m 0444 "${SOURCE_TRAINING_MANIFEST}" "${SOURCE_SNAPSHOT}"

CHECKPOINT_INDEX_SHA256="$(sha256sum "${CHECKPOINT}/model.safetensors.index.json" | awk '{print $1}')"
SOURCE_MANIFEST_SHA256="$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')"
SOURCE_SNAPSHOT_SHA256="$(sha256sum "${SOURCE_SNAPSHOT}" | awk '{print $1}')"
PROMPT_CONTRACT_JSON="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_SHA256="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
PARSER_VERSION="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.rewards.answer_reward import PARSER_VERSION; print(PARSER_VERSION)')"
REWARD_VERSION="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.rewards.pilot_reward import PILOT_REWARD_VERSION; print(PILOT_REWARD_VERSION)')"
DATA_HASH="$({ sha256sum "${SOURCE_MANIFEST}" "${FORMAT_PROMPT}" "${SOURCE_SNAPSHOT}" \
  "${CHECKPOINT}/model.safetensors.index.json"; } | sort -k2 | sha256sum | awk '{print $1}')"

COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=${ROOT}:${ROOT}/artifacts/repos/EasyR1 .venv/bin/python scripts/run_pilot_geo3k_step100_eval.py --arm anchor_real --condition real --model-path ${CHECKPOINT} --manifest ${SOURCE_MANIFEST} --format-prompt ${FORMAT_PROMPT} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} --source-training-manifest ${SOURCE_SNAPSHOT} --checkpoint-index-sha256 ${CHECKPOINT_INDEX_SHA256} --batch-size ${BATCH_SIZE} --max-model-len 8192 --max-tokens ${MAX_TOKENS} --seed ${SEED} --global-step ${GLOBAL_STEP} --row-schema-version ${ROW_SCHEMA}"

jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" --arg source_manifest "${SOURCE_MANIFEST}" \
  --arg source_manifest_sha256 "${SOURCE_MANIFEST_SHA256}" \
  --arg source_snapshot "${SOURCE_SNAPSHOT}" --arg source_snapshot_sha256 "${SOURCE_SNAPSHOT_SHA256}" \
  --arg checkpoint "${CHECKPOINT}" --arg checkpoint_index_sha256 "${CHECKPOINT_INDEX_SHA256}" \
  --arg parser_version "${PARSER_VERSION}" --arg reward_version "${REWARD_VERSION}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" --arg prompt_contract_sha256 "${PROMPT_CONTRACT_SHA256}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" --arg log "${LOG}" --arg replicate "${REPLICATE}" \
  --arg row_schema "${ROW_SCHEMA}" \
  --argjson step "${GLOBAL_STEP}" --argjson batch_size "${BATCH_SIZE}" \
  --argjson max_tokens "${MAX_TOKENS}" --argjson seed "${SEED}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5c_noise_floor_replicate",
    arm:"anchor_real",condition:"real",global_step:$step,replicate:$replicate,
    node:$node,gpu_allocation:[$gpu],gpu_ids:[($gpu|tonumber)],
    tensor_parallel_width:1,replica_count:1,placement_policy_version:"pi-2026-07-11",
    placement_justification:"One independent TP1 replica re-evaluates an already-evaluated geo3k checkpoint on a free disjoint A800 to measure harness replicate discordance.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$source_manifest,data_manifest_hash:$data_hash,
    source_manifest_sha256:$source_manifest_sha256,expected_row_count:601,
    source_training_manifest_snapshot:$source_snapshot,source_training_manifest_sha256:$source_snapshot_sha256,
    model_revision:$checkpoint,checkpoint_index_sha256:$checkpoint_index_sha256,
    parser_version:$parser_version,pilot_reward_version:$reward_version,prompt_contract:$prompt_contract,
    prompt_contract_sha256:$prompt_contract_sha256,scoring_mode:"pilot-reward-v1+canonical-v2",
    row_schema_version:$row_schema,
    decoding:{temperature:0,top_p:1,n:1,max_tokens:$max_tokens,seed:$seed},batch_size:$batch_size,
    resume_from:null,command:$command,start_time_utc:$started,
    end_time_utc:null,status:"running",stdout_stderr_log:$log,expected_artifacts:[$output],
    performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (setsid nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' >/dev/null 2>&1 </dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
