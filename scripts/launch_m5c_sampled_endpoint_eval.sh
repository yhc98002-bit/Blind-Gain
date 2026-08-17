#!/usr/bin/env bash
# Task-B launcher: run the REGISTERED L7 v2 sampled protocol (16 samples,
# temperature 1.0, top_p 1.0, seed 20260710, max_tokens 2048) on the Geometry3K
# TEST split only, for one checkpoint.
#
# Derived verbatim from scripts/launch_blind_solvability_v2_condition.sh with a
# single documented deviation: --splits test instead of --splits train test.
# That deviation preserves per-item batch grouping for the test rows because in
# the registered step-100 run the 601 test rows begin at global row index 1288
# and 1288 % batch_size(4) == 0, so the test rows already formed their own
# 4-row batches there.
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 NODE GPU MODEL_PATH RUN_TAG GLOBAL_STEP" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
MODEL_PATH="$3"
RUN_TAG="$4"
GLOBAL_STEP="$5"
CONDITION="real"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
TRAIN_FILTER="data/geo3k_pilot_filtered_ids.json"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
MAX_TOKENS=2048
SAMPLE_COUNT=16
SAMPLE_TEMPERATURE=1.0
GROUP_SIZE=5
FORMAT_WEIGHT=0.5
SYMBOLIC_GRADER_TIMEOUT_SECONDS=5.0
SEED=20260710
SPLITS="test"
BATCH_SIZE=4

export PATH="${HOME}/.local/bin:${PATH}"

if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "Invalid node or GPU" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag" >&2
  exit 2
fi

cd "${ROOT}"
if ! grep -q '^L3 | pass |' reports/prelaunch_progress.md; then
  echo "L7 is blocked until L3 is recorded pass after the five-step reward smoke" >&2
  exit 3
fi
for path in "${MANIFEST}" "${TRAIN_FILTER}" "${FORMAT_PROMPT}" "${MODEL_PATH}"; do
  if [[ ! -e "${path}" ]]; then
    echo "Required L7 input is absent: ${path}" >&2
    exit 2
  fi
done

DATA_FILES=("${MANIFEST}" "${TRAIN_FILTER}" "${FORMAT_PROMPT}")

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5c_sampled_${RUN_TAG}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
PROMPT_CONTRACT_JSON="$(PYTHONPATH=. .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
PARSER_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.answer_reward import PARSER_VERSION; print(PARSER_VERSION)')"
PILOT_REWARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import PILOT_REWARD_VERSION; print(PILOT_REWARD_VERSION)')"
SYMBOLIC_GRADER_GUARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import SYMBOLIC_GRADER_GUARD_VERSION; print(SYMBOLIC_GRADER_GUARD_VERSION)')"
TRAIN_FILTER_HASH="$(sha256sum "${TRAIN_FILTER}" | awk '{print $1}')"
SOURCE_MANIFEST_HASH="$(sha256sum "${MANIFEST}" | awk '{print $1}')"
FORMAT_PROMPT_HASH="$(sha256sum "${FORMAT_PROMPT}" | awk '{print $1}')"
DATA_HASH="$(sha256sum "${DATA_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_blind_solvability_v2.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} --train-filter-ids ${TRAIN_FILTER} --format-prompt ${FORMAT_PROMPT} --condition ${CONDITION} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} --splits ${SPLITS} --batch-size ${BATCH_SIZE} --max-model-len 8192 --max-tokens ${MAX_TOKENS} --sample-count ${SAMPLE_COUNT} --sample-temperature ${SAMPLE_TEMPERATURE} --group-size ${GROUP_SIZE} --format-weight ${FORMAT_WEIGHT} --symbolic-grader-timeout-seconds ${SYMBOLIC_GRADER_TIMEOUT_SECONDS} --seed ${SEED}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg model "${MODEL_PATH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg cache_dir "${CACHE_DIR}" \
  --arg train_filter "${TRAIN_FILTER}" \
  --arg train_filter_hash "${TRAIN_FILTER_HASH}" \
  --arg source_manifest_hash "${SOURCE_MANIFEST_HASH}" \
  --arg format_prompt_hash "${FORMAT_PROMPT_HASH}" \
  --arg parser_version "${PARSER_VERSION}" \
  --arg reward_version "${PILOT_REWARD_VERSION}" \
  --arg symbolic_guard_version "${SYMBOLIC_GRADER_GUARD_VERSION}" \
  --arg splits "${SPLITS}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" \
  --arg prompt_contract_hash "${PROMPT_CONTRACT_HASH}" \
  --argjson max_tokens "${MAX_TOKENS}" \
  --argjson sample_count "${SAMPLE_COUNT}" \
  --argjson sample_temperature "${SAMPLE_TEMPERATURE}" \
  --argjson group_size "${GROUP_SIZE}" \
  --argjson format_weight "${FORMAT_WEIGHT}" \
  --argjson symbolic_timeout "${SYMBOLIC_GRADER_TIMEOUT_SECONDS}" \
  --argjson seed "${SEED}" \
  --argjson batch_size "${BATCH_SIZE}" \
  --argjson global_step "${GLOBAL_STEP}" \
  '{
    run_id: $run_id,
    job_type: "m5c_geo3k_sampled_endpoint_eval",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [($gpu | tonumber)],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "Independent single-GPU TP1 evaluation replica on an idle A800; one cell per GPU, disjoint from concurrent training jobs.",
    placement_policy_version: "pi-2026-07-11",
    condition: $condition,
    global_step: ($global_step | tonumber),
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "data/geometry3k_caption_images_manifest.jsonl",
    data_manifest_hash: $data_hash,
    source_manifest_sha256: $source_manifest_hash,
    train_filter_ids: $train_filter,
    train_filter_sha256: $train_filter_hash,
    model_revision: $model,
    format_prompt_sha256: $format_prompt_hash,
    parser_version: $parser_version,
    pilot_reward_version: $reward_version,
    symbolic_grader_guard_version: $symbolic_guard_version,
    symbolic_grader_timeout_seconds: $symbolic_timeout,
    scoring_mode: "pilot-reward-v1+canonical-v2",
    prompt_contract: $prompt_contract,
    prompt_contract_sha256: $prompt_contract_hash,
    group_size: $group_size,
    sample_count: $sample_count,
    sample_temperature: $sample_temperature,
    max_tokens: $max_tokens,
    format_weight: $format_weight,
    seed: $seed,
    splits: [$splits],
    batch_size: $batch_size,
    expected_row_count: 601,
    decoding: {
      greedy: {temperature: 0, top_p: 1, n: 1},
      sampled: {temperature: $sample_temperature, top_p: 1, n: $sample_count},
      max_tokens: $max_tokens,
      seed: $seed
    },
    caption_source_run: null,
    resume_from: null,
    local_condition_cache: $cache_dir,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output],
    deviations: [
      "--splits test (registered v2 protocol uses --splits train test); test rows begin at global index 1288 and 1288 % 4 == 0, so per-item 4-row batch grouping for test items is unchanged",
      "reference step-100 sampled run scripts/launch_blind_solvability_v2_condition.sh was not reused verbatim only because it hardcodes --splits train test"
    ]
  }' > "${RUN_MANIFEST}"

ssh -o ConnectTimeout=20 "${NODE}" "cd '${ROOT}' && (setsid nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
