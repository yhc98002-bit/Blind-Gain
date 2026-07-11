#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
  echo "Usage: $0 NODE GPU CONDITION RUN_TAG [RESUME_FROM|-]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
CONDITION="$3"
RUN_TAG="$4"
RESUME_FROM="${5:--}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_PATH="artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"
MANIFEST="data/virl39k_blind_sample_4096.jsonl"
SAMPLE_SPEC="reports/virl39k_blind_sample_4096.json"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
CAPTION_RUN="experiments/runs/virl39k_sample4096_qwen25vl3b_captionstore384_20260710T094300Z"

if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "Invalid node or GPU" >&2
  exit 2
fi
if [[ ! "${CONDITION}" =~ ^(real|gray|noise|none|caption)$ ]]; then
  echo "Invalid condition" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid run tag" >&2
  exit 2
fi

cd "${ROOT}"
if ! rg -q '^L3 \| pass \|' reports/prelaunch_progress.md; then
  echo "L10 ViRL39K scoring is blocked until the L3 smoke is recorded pass" >&2
  exit 3
fi
for path in "${MODEL_PATH}" "${MANIFEST}" "${SAMPLE_SPEC}" "${FORMAT_PROMPT}"; do
  if [[ ! -e "${path}" ]]; then
    echo "Required ViRL39K audit input is absent: ${path}" >&2
    exit 2
  fi
done
USED_MIB="$(ssh "${NODE}" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i '${GPU}'" | tr -d '[:space:]')"
if [[ ! "${USED_MIB}" =~ ^[0-9]+$ || "${USED_MIB}" -ge 1024 ]]; then
  echo "Refusing ViRL39K audit: ${NODE} GPU ${GPU} has ${USED_MIB:-unknown} MiB allocated" >&2
  exit 75
fi

CAPTION_ARGS=""
DATA_FILES=("${MANIFEST}" "${SAMPLE_SPEC}" "${FORMAT_PROMPT}")
if [[ "${CONDITION}" == "caption" ]]; then
  if ! jq -e '(.status == "complete") and (.max_new_tokens == 384)' "${CAPTION_RUN}/run_manifest.json" >/dev/null; then
    echo "Fixed ViRL39K 3B caption store is not complete" >&2
    exit 2
  fi
  mapfile -t CAPTION_FILES < <(find "${CAPTION_RUN}/shards" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)
  if [[ "${#CAPTION_FILES[@]}" -ne 3 ]]; then
    echo "Fixed ViRL39K caption store must contain three shards" >&2
    exit 2
  fi
  printf -v CAPTION_ARGS ' %q' "${CAPTION_FILES[@]}"
  CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"
  DATA_FILES+=("${CAPTION_RUN}/run_manifest.json" "${CAPTION_FILES[@]}")
fi

RESUME_ARGS=""
if [[ "${RESUME_FROM}" != "-" ]]; then
  if [[ ! -s "${RESUME_FROM}" ]]; then
    echo "Resume source is absent or empty: ${RESUME_FROM}" >&2
    exit 2
  fi
  printf -v RESUME_ARGS ' --resume-from %q' "${RESUME_FROM}"
  DATA_FILES+=("${RESUME_FROM}")
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="blind_solvability_virl39k_v1_${RUN_TAG}_${CONDITION}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
PROMPT_CONTRACT_JSON="$(PYTHONPATH=. .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
PARSER_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.answer_reward import PARSER_VERSION; print(PARSER_VERSION)')"
REWARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import PILOT_REWARD_VERSION; print(PILOT_REWARD_VERSION)')"
SOURCE_HASH="$(sha256sum "${MANIFEST}" | awk '{print $1}')"
SAMPLE_HASH="$(sha256sum "${SAMPLE_SPEC}" | awk '{print $1}')"
DATA_HASH="$(sha256sum "${DATA_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_blind_solvability_v2.py --model-path ${MODEL_PATH} --manifest ${MANIFEST} --format-prompt ${FORMAT_PROMPT} --condition ${CONDITION} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} ${CAPTION_ARGS}${RESUME_ARGS} --splits audit --batch-size 2 --max-model-len 8192 --max-tokens 2048 --sample-count 16 --sample-temperature 1.0 --group-size 5 --format-weight 0.5 --seed 20260710"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg source_hash "${SOURCE_HASH}" \
  --arg sample_hash "${SAMPLE_HASH}" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg cache "${CACHE_DIR}" \
  --arg caption_run "${CAPTION_RUN}" \
  --arg resume "${RESUME_FROM}" \
  --arg parser_version "${PARSER_VERSION}" \
  --arg reward_version "${REWARD_VERSION}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" \
  --arg prompt_hash "${PROMPT_CONTRACT_HASH}" \
  '{
    run_id: $run_id,
    job_type: "l10_virl39k_blind_solvability_v1",
    node: $node,
    gpu_allocation: [$gpu],
    condition: $condition,
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "data/virl39k_blind_sample_4096.jsonl",
    data_manifest_hash: $data_hash,
    source_manifest_sha256: $source_hash,
    sample_spec: "reports/virl39k_blind_sample_4096.json",
    sample_spec_sha256: $sample_hash,
    train_filter_ids: null,
    train_filter_sha256: null,
    model_revision: "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
    parser_version: $parser_version,
    pilot_reward_version: $reward_version,
    scoring_mode: "pilot-reward-v1+canonical-v2",
    prompt_contract: $prompt_contract,
    prompt_contract_sha256: $prompt_hash,
    group_size: 5,
    sample_count: 16,
    sample_temperature: 1,
    max_tokens: 2048,
    max_model_len: 8192,
    batch_size: 2,
    format_weight: 0.5,
    seed: 20260710,
    decoding: {
      greedy: {temperature: 0, top_p: 1, n: 1},
      sampled: {temperature: 1, top_p: 1, n: 16},
      max_tokens: 2048,
      seed: 20260710
    },
    caption_source_run: (if $condition == "caption" then $caption_run else null end),
    resume_from: (if $resume == "-" then null else $resume end),
    local_condition_cache: $cache,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output],
    deviations: []
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
