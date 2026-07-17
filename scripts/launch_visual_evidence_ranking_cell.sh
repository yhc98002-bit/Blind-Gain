#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 || $# -gt 6 ]]; then
  echo "Usage: $0 NODE GPU MODEL_KEY CONDITION RUN_DIR [LIMIT]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
MODEL_KEY="$3"
CONDITION="$4"
RUN_DIR="$5"
LIMIT="${6:-}"
ROOT="$(pwd)"
CONFIG="configs/eval/seed1_visual_evidence_ranking_v1.json"
REGISTRATION="docs/registered_seed1_visual_evidence_ranking_v1.md"

[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "unsupported node" >&2; exit 2; }
[[ "${GPU}" =~ ^[0-7]$ ]] || { echo "GPU must be in [0,7]" >&2; exit 2; }
[[ "${CONDITION}" =~ ^(real|gray|no_image)$ ]] || { echo "unsupported condition" >&2; exit 2; }
[[ "${MODEL_KEY}" =~ ^(base|a1_step60|a1_step100)$ ]] || { echo "unsupported model key" >&2; exit 2; }
[[ -z "${LIMIT}" || "${LIMIT}" =~ ^[1-9][0-9]*$ ]] || { echo "LIMIT must be positive" >&2; exit 2; }
[[ "${RUN_DIR}" != /* && "${RUN_DIR}" == experiments/runs/* ]] || { echo "RUN_DIR must be relative under experiments/runs" >&2; exit 2; }
[[ ! -e "${RUN_DIR}" ]] || { echo "refusing to overwrite run directory" >&2; exit 73; }

git ls-files --error-unmatch "${CONFIG}" "${REGISTRATION}" data/fliptrack_r19_visual_evidence_candidates_v1.jsonl >/dev/null
[[ -z "$(git status --porcelain -- "${CONFIG}" "${REGISTRATION}" data/fliptrack_r19_visual_evidence_candidates_v1.jsonl)" ]] || {
  echo "registered diagnostic inputs must be committed and clean" >&2
  exit 2
}
MODEL_PATH="$(jq -er --arg key "${MODEL_KEY}" '.models[$key].path' "${CONFIG}")"
EXPECTED_MODEL_HASH="$(jq -er --arg key "${MODEL_KEY}" '.models[$key].model_index_sha256' "${CONFIG}")"
OBSERVED_MODEL_HASH="$(sha256sum "${MODEL_PATH}/model.safetensors.index.json" | awk '{print $1}')"
[[ "${OBSERVED_MODEL_HASH}" == "${EXPECTED_MODEL_HASH}" ]] || { echo "model hash mismatch" >&2; exit 2; }
REGISTRATION_COMMIT="$(git log -1 --format=%H -- "${REGISTRATION}")"
git merge-base --is-ancestor "${REGISTRATION_COMMIT}" HEAD

if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
  echo "GPU ${NODE}:${GPU} is occupied" >&2
  exit 75
fi

mkdir -p "${RUN_DIR}/logs"
GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
DATA_PATH="$(jq -er '.candidate_registry.path' "${CONFIG}")"
DATA_HASH="$(sha256sum "${DATA_PATH}" | awk '{print $1}')"
LIMIT_JSON=null
LIMIT_ARG=""
if [[ -n "${LIMIT}" ]]; then
  LIMIT_JSON="${LIMIT}"
  LIMIT_ARG="--limit ${LIMIT}"
fi
cat > "${RUN_DIR}/run_manifest.json" <<JSON
{
  "schema_version": "blind-gains.visual-evidence-ranking-run.v1",
  "run_id": "$(basename "${RUN_DIR}")",
  "job_type": "post_seed1_visual_evidence_ranking",
  "status": "running",
  "node": "${NODE}",
  "gpu_ids": [${GPU}],
  "tensor_parallel_width": 1,
  "replica_count": 1,
  "placement_justification": "One independent Qwen2.5-VL-3B teacher-forced ranking cell fits on one A800; TP1 is the minimum required width and the GPU is disjoint from neighboring jobs.",
  "git_hash": "${GIT_HASH}",
  "registration_commit": "${REGISTRATION_COMMIT}",
  "config_path": "${CONFIG}",
  "config_hash": "${CONFIG_HASH}",
  "data_manifest": "${DATA_PATH}",
  "data_manifest_hash": "${DATA_HASH}",
  "model_key": "${MODEL_KEY}",
  "model_path": "${MODEL_PATH}",
  "model_index_sha256": "${OBSERVED_MODEL_HASH}",
  "condition": "${CONDITION}",
  "processor_artifact_sha256": "$(jq -er '.processor.artifact_sha256' "${CONFIG}")",
  "prompt_contract_sha256": "$(jq -er '.prompt_contract.sha256' "${CONFIG}")",
  "scorer_version": "$(jq -er '.scoring.version' "${CONFIG}")",
  "limit": ${LIMIT_JSON},
  "seed": 0,
  "decoding": null,
  "scoring": "teacher-forced exact-candidate mean token log probability",
  "command": "scripts/launch_visual_evidence_ranking_cell.sh ${NODE} ${GPU} ${MODEL_KEY} ${CONDITION} ${RUN_DIR}${LIMIT:+ ${LIMIT}}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "exit_code": null,
  "expected_artifacts": ["${RUN_DIR}/scores.jsonl"]
}
JSON

cat > "${RUN_DIR}/worker.sh" <<EOF
#!/usr/bin/env bash
set +e
cd '${ROOT}'
source .venv/bin/activate
env CUDA_VISIBLE_DEVICES='${GPU}' TRANSFORMERS_OFFLINE=1 HF_HOME='${ROOT}/artifacts/hf_home' PYTHONUNBUFFERED=1 EASYR1_ATTN_IMPLEMENTATION=sdpa \
  python scripts/eval_qwen_vl_visual_evidence_ranking.py \
    --config '${CONFIG}' \
    --model-key '${MODEL_KEY}' \
    --condition '${CONDITION}' \
    --output '${RUN_DIR}/scores.jsonl' \
    --cache-dir '${RUN_DIR}/image_cache' ${LIMIT_ARG}
rc=\$?
python scripts/finalize_run_manifest.py '${RUN_DIR}/run_manifest.json' \${rc}
finalize_rc=\$?
if [[ \${rc} -eq 0 && \${finalize_rc} -ne 0 ]]; then
  rc=\${finalize_rc}
fi
exit \${rc}
EOF
chmod 755 "${RUN_DIR}/worker.sh"
ssh "${NODE}" "nohup bash '${ROOT}/${RUN_DIR}/worker.sh' > '${ROOT}/${RUN_DIR}/logs/stdout_stderr.log' 2>&1 < /dev/null & echo \$! > '${ROOT}/${RUN_DIR}/process.pid'"
echo "launched ${MODEL_KEY}/${CONDITION} on ${NODE}:${GPU} in ${RUN_DIR}"
