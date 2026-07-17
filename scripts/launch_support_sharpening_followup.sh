#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <an12|an29> <gpu-id> <a1_real|a2_gray|a2b_noimage|a3_caption>" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
ARM="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="configs/eval/support_sharpening_v2.json"
REGISTRATION="reports/support_sharpening_registry_v3.md"
MODEL_PATH="artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct"

if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "invalid node or GPU" >&2
  exit 2
fi
if [[ ! "${ARM}" =~ ^(a1_real|a2_gray|a2b_noimage|a3_caption)$ ]]; then
  echo "invalid registered arm" >&2
  exit 2
fi

cd "${ROOT}"
CRITICAL=(
  "${CONFIG}"
  "${REGISTRATION}"
  scripts/run_support_sharpening_followup.py
  scripts/launch_support_sharpening_followup.sh
  src/analysis/support_sharpening.py
  src/eval/blind_solvability.py
  src/eval/conditioned_inputs.py
)
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "support-sharpening critical code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked support-sharpening critical file: ${FILE}" >&2
    exit 2
  }
done
grep -Fx -- '- Registration state: merged-at-HEAD; merge is sign-off.' "${REGISTRATION}" >/dev/null || {
  echo "M10 execution registration is not merged" >&2
  exit 2
}
PYTHONPATH=. .venv/bin/python - <<'PY'
import json
from pathlib import Path
from scripts.run_support_sharpening_followup import validate_execution_config
root = Path('.').resolve()
config = json.loads((root / 'configs/eval/support_sharpening_v2.json').read_text())
validate_execution_config(config, root)
PY

read -r MEMORY UTILIZATION < <(
  ssh "${NODE}" "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits -i '${GPU}'" |
    awk -F, '{gsub(/ /,"",$1); gsub(/ /,"",$2); print $1, $2}'
)
if (( MEMORY > 1024 || UTILIZATION > 10 )); then
  echo "GPU ${NODE}:${GPU} is not free: memory=${MEMORY} MiB utilization=${UTILIZATION}%" >&2
  exit 75
fi

ARM_CONFIG="$(jq -c --arg arm "${ARM}" '.arms[$arm]' "${CONFIG}")"
CONDITION="$(jq -r '.condition' <<<"${ARM_CONFIG}")"
CANDIDATE_PATH="$(jq -r '.candidate_path' <<<"${ARM_CONFIG}")"
BASELINE_PATH="$(jq -r '.baseline_path' <<<"${ARM_CONFIG}")"
CANDIDATE_COUNT="$(jq -r '.candidate_count' <<<"${ARM_CONFIG}")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m10_support_seed1_${ARM}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/draws.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"

if [[ -e "${RUN_DIR}" ]]; then
  echo "refusing to overwrite immutable M10 run" >&2
  exit 73
fi
.venv/bin/python scripts/storage_guard.py --tier S --path "${RUN_DIR}" \
  --operation "m10_${ARM}_followup" --required-bytes 500000000
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${CANDIDATE_PATH}" "${BASELINE_PATH}" \
    "$(jq -r '.source_manifest.path' "${CONFIG}")" \
    "$(jq -r '.format_prompt.path' "${CONFIG}")"
  if [[ "${CONDITION}" == "caption" ]]; then
    while IFS= read -r path; do sha256sum "${path}"; done < <(jq -r '.caption_store.shards[].path' "${CONFIG}")
  fi
} | sort -k2 | sha256sum | awk '{print $1}')"
COMMAND="env CUDA_VISIBLE_DEVICES=${GPU} PYTHONUNBUFFERED=1 PYTHONHASHSEED=0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' PYTHONPATH=. '${ROOT}/.venv/bin/python' scripts/run_support_sharpening_followup.py --config '${CONFIG}' --arm '${ARM}' --output '${OUTPUT}' --cache-dir '${CACHE_DIR}'"

jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --argjson gpu "${GPU}" \
  --arg arm "${ARM}" --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config "${CONFIG}" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg candidates "${CANDIDATE_PATH}" --arg baseline "${BASELINE_PATH}" \
  --arg model "${MODEL_PATH}" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg output "${OUTPUT}" --arg cache "${CACHE_DIR}" \
  --argjson candidate_count "${CANDIDATE_COUNT}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m10_support_sharpening_followup",
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "One frozen 3B TP1 replica executes one arm-specific M10 follow-up on one free GPU; no state crosses nodes.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: $candidates,
    baseline_path: $baseline,
    data_manifest_hash: $data_hash,
    model_path: $model,
    model_revision: "Qwen/Qwen2.5-VL-3B-Instruct local ModelScope snapshot",
    seed: null,
    draw_indices: {start_inclusive: 16, stop_exclusive: 80},
    draw_seeds: {first: 20260732, last: 20260795, count: 64, formula: "20260716 + draw_index"},
    candidate_count: $candidate_count,
    expected_row_count: ($candidate_count * 64),
    arm: $arm,
    condition: $condition,
    decoding: {temperature: 1.0, top_p: 1.0, n_per_call: 1, max_tokens: 2048},
    prompt_contract_sha256: "7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f",
    parser_version: "canonical-v2",
    pilot_reward_version: "pilot-reward-v1",
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    local_condition_cache: $cache,
    expected_artifacts: [$output],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${CACHE_DIR}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
sleep 2
REMOTE_PID="$(cat "${PID_FILE}")"
ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null" || {
  echo "M10 ${ARM} exited during startup; inspect ${LOG}" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
