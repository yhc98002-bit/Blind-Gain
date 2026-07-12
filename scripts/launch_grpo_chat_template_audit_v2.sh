#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ( "$1" != "an12" && "$1" != "an29" ) ]]; then
  echo "usage: $0 <an12|an29>" >&2
  exit 2
fi

NODE="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
OUTPUT_JSON="reports/grpo_chat_template_audit_v2.json"
OUTPUT_MD="reports/grpo_chat_template_audit_v2.md"
if [[ -e "${OUTPUT_JSON}" || -e "${OUTPUT_MD}" ]]; then
  echo "refusing to overwrite versioned chat-template outputs" >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="grpo_chat_template_audit_v2_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
mkdir -p "${RUN_DIR}/logs"
COMMAND="env CUDA_VISIBLE_DEVICES='' TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home PYTHONPATH=. .venv/bin/python scripts/audit_grpo_chat_template_v2.py --config configs/train/anchor_a0_recipe_3b_geo3k.yaml --manifest data/geometry3k_caption_images_manifest.jsonl --model-path artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct --output-json ${OUTPUT_JSON} --output-md ${OUTPUT_MD}"

jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(sha256sum scripts/audit_grpo_chat_template_v2.py | awk '{print $1}')" \
  --arg data_hash "$(sha256sum data/geometry3k_caption_images_manifest.jsonl | awk '{print $1}')" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output_json "${OUTPUT_JSON}" \
  --arg output_md "${OUTPUT_MD}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "grpo_chat_template_audit_v2",
    node: $node,
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_policy_version: "pi-2026-07-11",
    placement_justification: "CPU-only rendering/tokenization audit on one compute node; no model weights are loaded and no GPU is allocated.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: "data/geometry3k_caption_images_manifest.jsonl",
    data_manifest_hash: $data_hash,
    model_revision: "Qwen/Qwen2.5-VL-3B-Instruct@66285546d2b821cf421d4f5eb2576359d3770cd3",
    seed: 0,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output_json, $output_md],
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && '${ROOT}/.venv/bin/python' scripts/run_manifest_job.py '${MANIFEST}' '${LOG}'"
printf '%s\n' "${RUN_DIR}"
