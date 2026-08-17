#!/usr/bin/env bash
# ST3 C1 necessity measurement: one blind-solvability pass over the ST3
# training corpus, on one GPU, optionally restricted to a row-index shard.
#
# Forked from scripts/launch_blind_solvability_v2_condition.sh — the registered
# harness invocation, prompt-contract wiring and run-manifest shape are carried
# over verbatim; only the inputs (ST3 manifest instead of the geo3k one), the
# gate (ST3 registration instead of the pilot L3 row) and shard support differ.
# The registered sampling contract is untouched: 16 samples at T=1, the pilot
# prompt contract, seed 20260710.
#
# Usage: launch_st3_delta_q_condition.sh NODE GPU {real|none} SHARD_FILTER|-
set -euo pipefail
[[ $# -eq 4 ]] || { echo "usage: $0 NODE GPU {real|none} SHARD_FILTER|-" >&2; exit 2; }
NODE="$1"; GPU="$2"; CONDITION="$3"; SHARD="$4"
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"

MANIFEST="data/st3_train_blind_solvability_manifest_v1.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
MODEL_PATH="artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct"
MAX_TOKENS=2048; SAMPLE_COUNT=16; SAMPLE_TEMPERATURE=1.0
GROUP_SIZE=5; FORMAT_WEIGHT=0.5; GRADER_TIMEOUT=5.0; SEED=20260710

[[ "$NODE" =~ ^(an12|an29)$ && "$GPU" =~ ^[0-7]$ ]] || { echo "bad node/gpu" >&2; exit 2; }
[[ "$CONDITION" =~ ^(real|none)$ ]] || { echo "condition must be real or none" >&2; exit 2; }
grep -q "Launch amendment 1" docs/registered_stage3_7b_v1.md || {
  echo "ST3 registration carries no launch amendment" >&2; exit 3; }
for path in "$MANIFEST" "$FORMAT_PROMPT" "$MODEL_PATH"; do
  [[ -e "$path" ]] || { echo "missing input: $path" >&2; exit 2; }
done
FILTER_ARGS=""; TAG="full"
if [[ "$SHARD" != "-" ]]; then
  [[ -s "$SHARD" ]] || { echo "shard filter absent: $SHARD" >&2; exit 2; }
  FILTER_ARGS="--train-filter-ids ${SHARD}"
  TAG="$(basename "$SHARD" .json)"
fi

"$ROOT/.venv/bin/python" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" || exit 75

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="st3_delta_q_${CONDITION}_${TAG}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

PC_JSON="$(PYTHONPATH=. .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PC_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
PARSER_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.answer_reward import PARSER_VERSION; print(PARSER_VERSION)')"
PILOT_REWARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import PILOT_REWARD_VERSION; print(PILOT_REWARD_VERSION)')"
GUARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import SYMBOLIC_GRADER_GUARD_VERSION; print(SYMBOLIC_GRADER_GUARD_VERSION)')"
MANIFEST_HASH="$(sha256sum "$MANIFEST" | awk '{print $1}')"

COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_blind_solvability_v2.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} ${FILTER_ARGS} --format-prompt ${FORMAT_PROMPT} --condition ${CONDITION} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} --splits train --batch-size 4 --max-model-len 8192 --max-tokens ${MAX_TOKENS} --sample-count ${SAMPLE_COUNT} --sample-temperature ${SAMPLE_TEMPERATURE} --group-size ${GROUP_SIZE} --format-weight ${FORMAT_WEIGHT} --symbolic-grader-timeout-seconds ${GRADER_TIMEOUT} --seed ${SEED}"

jq -n --arg run_id "$RUN_ID" --arg node "$NODE" --arg gpu "$GPU" \
  --arg condition "$CONDITION" --arg git_hash "$(git rev-parse HEAD)" \
  --arg model "$MODEL_PATH" --arg command "$COMMAND" \
  --arg manifest "$MANIFEST" --arg manifest_hash "$MANIFEST_HASH" \
  --arg shard "$SHARD" \
  --argjson prompt_contract "$PC_JSON" --arg prompt_contract_sha256 "$PC_HASH" \
  --arg parser_version "$PARSER_VERSION" \
  --arg pilot_reward_version "$PILOT_REWARD_VERSION" \
  --arg symbolic_grader_guard_version "$GUARD_VERSION" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.run-manifest.v1", run_id:$run_id,
    job_type:"st3_delta_q_blind_solvability", status:"running", node:$node,
    gpu_ids:[($gpu|tonumber)], condition:$condition, model_path:$model,
    source_manifest:$manifest, source_manifest_sha256:$manifest_hash,
    shard_filter:$shard, git_hash:$git_hash, command:$command,
    prompt_contract:$prompt_contract, prompt_contract_sha256:$prompt_contract_sha256,
    parser_version:$parser_version, pilot_reward_version:$pilot_reward_version,
    symbolic_grader_guard_version:$symbolic_grader_guard_version,
    sample_count:16, sample_temperature:1.0,
    registration:"docs/registered_stage3_7b_v1.md §2 C1 (necessity sampling)",
    start_time_utc:$started, end_time_utc:null, exit_code:null, deviations:[]}' \
  > "$RUN_MANIFEST"

ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "cd '$ROOT' && (nohup setsid ${ROOT}/.venv/bin/python scripts/run_manifest_job.py '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid')"
echo "$RUN_DIR"
