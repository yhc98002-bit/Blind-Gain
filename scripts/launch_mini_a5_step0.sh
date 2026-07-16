#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

NODE="${NODE:-an12}"
GPU="${GPU:-7}"
MODEL_PATH="${ROOT}/artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"
MODEL_REVISION="ModelScope:Qwen/Qwen2.5-VL-3B-Instruct@master-tree_sha256_84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568"
SAMPLE="data/mini_a5_step0_sample_v1.jsonl"
FORMAT_PROMPT="${ROOT}/artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"

[[ -s "${SAMPLE}" ]] || { echo "fixed step-0 sample is absent: ${SAMPLE}" >&2; exit 2; }
[[ -d "${MODEL_PATH}" ]] || { echo "model is absent: ${MODEL_PATH}" >&2; exit 2; }
[[ -s "${FORMAT_PROMPT}" ]] || { echo "format prompt is absent: ${FORMAT_PROMPT}" >&2; exit 2; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_step0_qwen25vl3b_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
OUTPUT="${RUN_DIR}/predictions.jsonl"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=. .venv/bin/python scripts/run_mini_a5_step0.py --model-path ${MODEL_PATH} --model-revision ${MODEL_REVISION} --sample ${SAMPLE} --format-prompt ${FORMAT_PROMPT} --output ${OUTPUT} --batch-pairs 2 --max-model-len 8192 --gpu-memory-utilization 0.72 --seed 20260716"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${SAMPLE}" data/mini_a5_fixed_subsets_v1_manifest.json
  sha256sum configs/train/mini_a5_cp_3b_v1.yaml configs/train/mini_a5_same_data_3b_v1.yaml
  sha256sum scripts/run_mini_a5_step0.py src/rewards/cp_grpo_reward.py src/train/cp_grouping.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg log "${LOG}" \
  --arg sample_sha "$(sha256sum "${SAMPLE}" | awk '{print $1}')" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m6_mini_a5_step0_base_reward_diagnostic",
    status: "running",
    node: $node,
    gpu_ids: [($gpu | tonumber)],
    gpu_allocation: [($gpu | tonumber)],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "One TP1 3B base-inference replica on an otherwise unassigned GPU; no training or optimizer step is performed.",
    git_hash: $git_hash,
    config_path: null,
    config_hash: $config_hash,
    data_manifest: "data/mini_a5_step0_sample_v1.jsonl",
    data_manifest_hash: $data_hash,
    sample_sha256: $sample_sha,
    seed: 20260716,
    decoding: {temperature: 1.0, top_p: 1.0, n: 5, max_tokens: 2048},
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    exit_code: null,
    stdout_stderr_log: $log,
    expected_artifacts: [$output],
    scientific_gate_decision: null,
    optimizer_steps: 0,
    performance_values_opened: false,
    deviations: []
  }' > "${MANIFEST}"

REMOTE="cd $(printf '%q' "${ROOT}") && mkdir -p /dev/shm/blind-gains/mini_a5_step0_cache && ${ROOT}/.venv/bin/python scripts/run_manifest_job.py $(printf '%q' "${MANIFEST}") $(printf '%q' "${LOG}")"
# The client deliberately quotes the complete command before sending it.
# shellcheck disable=SC2029
ssh "${NODE}" "nohup bash -lc $(printf '%q' "${REMOTE}") >/dev/null 2>&1 & echo \$!" > "${RUN_DIR}/pids/ssh_launcher.pid"
printf '%s\n' "${RUN_DIR}"
