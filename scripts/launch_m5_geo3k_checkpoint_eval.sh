#!/usr/bin/env bash
# shellcheck disable=SC2029
set -euo pipefail

if [[ $# -lt 5 || $# -gt 7 ]]; then
  echo "usage: $0 NODE GPU SOURCE_RUN GLOBAL_STEP CHECKPOINT [RESUME_FROM|-] [BATCH_SIZE]" >&2
  exit 2
fi

NODE="$1"
GPU="$2"
SOURCE_RUN_INPUT="$3"
GLOBAL_STEP="$4"
CHECKPOINT_INPUT="$5"
RESUME_FROM="${6:--}"
BATCH_SIZE="${7:-4}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
REGISTRATION="docs/registered_extensions_v1.md"
AUTHORIZATION="reports/registered_extensions_authorization_v4.json"
INCIDENT="reports/m5_host_memory_incident_v1.json"
MAX_TOKENS=2048
SEED=20260710
MIN_MEM_AVAILABLE_KIB=471859200  # 450 GiB; protects the colocated trainer from host-RAM pressure.

[[ "${NODE}" =~ ^(an12|an29)$ && "${GPU}" =~ ^[0-7]$ ]] || {
  echo "invalid node or GPU" >&2; exit 2;
}
[[ "${GLOBAL_STEP}" =~ ^(150|200|300|400)$ ]] || {
  echo "M5 Geometry3K step must be 150, 200, 300, or 400" >&2; exit 2;
}
[[ "${BATCH_SIZE}" =~ ^[1-9][0-9]*$ ]] || { echo "batch size must be positive" >&2; exit 2; }

cd "${ROOT}"
SOURCE_RUN="$(realpath -m "${SOURCE_RUN_INPUT}")"
CHECKPOINT="$(realpath -m "${CHECKPOINT_INPUT}")"
case "${SOURCE_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "M5 source run must be under experiments/runs" >&2; exit 2 ;;
esac
SOURCE_RUN_REL="${SOURCE_RUN#"${ROOT}/"}"
SOURCE_TRAINING_MANIFEST="${SOURCE_RUN}/run_manifest.json"
for path in "${SOURCE_TRAINING_MANIFEST}" "${CHECKPOINT}/model.safetensors.index.json" \
  "${SOURCE_MANIFEST}" "${FORMAT_PROMPT}" "${REGISTRATION}" "${AUTHORIZATION}"; do
  [[ -s "${path}" ]] || { echo "required M5 evaluation input is absent or empty: ${path}" >&2; exit 2; }
done
for path in "${REGISTRATION}" "${AUTHORIZATION}" scripts/run_pilot_geo3k_step100_eval.py \
  scripts/launch_m5_geo3k_checkpoint_eval.sh; do
  git ls-files --error-unmatch "${path}" >/dev/null 2>&1 || {
    echo "M5 evaluation contract file is untracked: ${path}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- "${REGISTRATION}" "${AUTHORIZATION}" \
  scripts/run_pilot_geo3k_step100_eval.py scripts/launch_m5_geo3k_checkpoint_eval.sh || {
  echo "M5 evaluation contract differs from HEAD" >&2; exit 3;
}
jq -e '(.status=="authorized") and (.authorization.m5=="authorized_after_restore_integrity_pass") and
  ([.checks[]] | all)' "${AUTHORIZATION}" >/dev/null || {
  echo "M5 authorization artifact is invalid" >&2; exit 3;
}
REGISTRATION_SHA256="$(sha256sum "${REGISTRATION}" | awk '{print $1}')"
[[ "$(jq -r '.artifacts.active_registration.sha256' "${AUTHORIZATION}")" == "${REGISTRATION_SHA256}" ]] || {
  echo "M5 authorization does not bind the active registration" >&2; exit 3;
}

if [[ "${GLOBAL_STEP}" == "150" ]]; then
  [[ -s "${INCIDENT}" ]] || { echo "step-150 incident record is absent" >&2; exit 3; }
  git diff --quiet HEAD -- "${INCIDENT}" || { echo "M5 incident record differs from HEAD" >&2; exit 3; }
  EXPECTED_FAILED_RUN="$(jq -r '.failed_run' "${INCIDENT}")"
  [[ "$(realpath -m "${EXPECTED_FAILED_RUN}")" == "${SOURCE_RUN}" ]] || {
    echo "step-150 evaluation must bind the recorded failed parent run" >&2; exit 3;
  }
  jq -e '(.status=="recoverable_blocked") and (.last_verified_checkpoint.step==150) and
    (.checks.step150_merge_complete==true)' "${INCIDENT}" >/dev/null || {
    echo "step-150 incident does not certify the merged checkpoint" >&2; exit 3;
  }
  jq -e '(.job_type=="m5_anchor_longhorizon_400") and (.status=="fail") and
    (.exit_code==1) and (.target_global_step==400) and (.terminal_no_extension==true)' \
    "${SOURCE_TRAINING_MANIFEST}" >/dev/null || {
    echo "step-150 source is not the recorded failed M5 parent" >&2; exit 3;
  }
else
  jq -e --argjson step "${GLOBAL_STEP}" '
    (.job_type=="m5_anchor_longhorizon_400") and
    (.status=="running" or .status=="complete") and
    (.target_global_step==400) and (.terminal_no_extension==true) and
    (.registered_evaluation_steps | index($step) != null)' \
    "${SOURCE_TRAINING_MANIFEST}" >/dev/null || {
    echo "M5 source run does not authorize this checkpoint endpoint" >&2; exit 3;
  }
fi
EXPECTED_CHECKPOINT="$(realpath -m "$(jq -r '.checkpoint_path' "${SOURCE_TRAINING_MANIFEST}")/global_step_${GLOBAL_STEP}/actor/huggingface")"
[[ "${CHECKPOINT}" == "${EXPECTED_CHECKPOINT}" ]] || {
  echo "checkpoint does not match the exact M5 source run and global step" >&2; exit 3;
}
PYTHONPATH=. .venv/bin/python - "${CHECKPOINT}" <<'PY'
import sys
from pathlib import Path
from scripts.watch_anchor_checkpoints import merged_checkpoint_complete

if not merged_checkpoint_complete(Path(sys.argv[1])):
    raise SystemExit("M5 merged checkpoint is incomplete")
PY

RESUME_ARGS=""
if [[ "${RESUME_FROM}" != "-" ]]; then
  [[ -s "${RESUME_FROM}" ]] || { echo "resume source is absent or empty: ${RESUME_FROM}" >&2; exit 2; }
  printf -v RESUME_ARGS ' --resume-from %q' "${RESUME_FROM}"
fi

check_capacity() {
  local pids mem
  pids="$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits" | sed '/^[[:space:]]*$/d')"
  [[ -z "${pids}" ]] || return 1
  mem="$(ssh "${NODE}" "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'")"
  [[ "${mem}" =~ ^[0-9]+$ && "${mem}" -ge "${MIN_MEM_AVAILABLE_KIB}" ]]
}
check_capacity || { echo "M5 evaluation GPU or host-memory admission failed" >&2; exit 75; }
sleep 10
check_capacity || { echo "M5 evaluation capacity did not remain stable" >&2; exit 75; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_geo3k_step${GLOBAL_STEP}_${NODE}_gpu${GPU}_${STAMP}"
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
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=${ROOT}:${ROOT}/artifacts/repos/EasyR1 .venv/bin/python scripts/run_pilot_geo3k_step100_eval.py --arm anchor_real --condition real --model-path ${CHECKPOINT} --manifest ${SOURCE_MANIFEST} --format-prompt ${FORMAT_PROMPT} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} --source-training-manifest ${SOURCE_SNAPSHOT} --checkpoint-index-sha256 ${CHECKPOINT_INDEX_SHA256}${RESUME_ARGS} --batch-size ${BATCH_SIZE} --max-model-len 8192 --max-tokens ${MAX_TOKENS} --seed ${SEED} --global-step ${GLOBAL_STEP} --row-schema-version blind-gains.m5-geo3k-checkpoint-eval.v1"

jq -n --arg run_id "${RUN_ID}" --arg node "${NODE}" --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" --arg source_manifest "${SOURCE_MANIFEST}" \
  --arg source_manifest_sha256 "${SOURCE_MANIFEST_SHA256}" --arg source_run "${SOURCE_RUN_REL}" \
  --arg source_snapshot "${SOURCE_SNAPSHOT}" --arg source_snapshot_sha256 "${SOURCE_SNAPSHOT_SHA256}" \
  --arg checkpoint "${CHECKPOINT}" --arg checkpoint_index_sha256 "${CHECKPOINT_INDEX_SHA256}" \
  --arg parser_version "${PARSER_VERSION}" --arg reward_version "${REWARD_VERSION}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" --arg prompt_contract_sha256 "${PROMPT_CONTRACT_SHA256}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" --arg log "${LOG}" --arg resume_from "${RESUME_FROM}" \
  --argjson step "${GLOBAL_STEP}" --argjson batch_size "${BATCH_SIZE}" \
  --argjson max_tokens "${MAX_TOKENS}" --argjson seed "${SEED}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,job_type:"m5_geo3k_checkpoint_eval",
    arm:"anchor_real",condition:"real",global_step:$step,node:$node,gpu_allocation:[$gpu],gpu_ids:[($gpu|tonumber)],
    tensor_parallel_width:1,replica_count:1,placement_policy_version:"pi-2026-07-11",
    placement_justification:"One independent TP1 replica evaluates the registered M5 Geometry3K checkpoint on a disjoint A800 after stable GPU and 450-GiB host-memory admission.",
    git_hash:$git_hash,config_hash:$config_hash,data_manifest:$source_manifest,data_manifest_hash:$data_hash,
    source_manifest_sha256:$source_manifest_sha256,expected_row_count:601,source_training_run:$source_run,
    source_training_manifest_snapshot:$source_snapshot,source_training_manifest_sha256:$source_snapshot_sha256,
    model_revision:$checkpoint,checkpoint_index_sha256:$checkpoint_index_sha256,
    parser_version:$parser_version,pilot_reward_version:$reward_version,prompt_contract:$prompt_contract,
    prompt_contract_sha256:$prompt_contract_sha256,scoring_mode:"pilot-reward-v1+canonical-v2",
    row_schema_version:"blind-gains.m5-geo3k-checkpoint-eval.v1",
    decoding:{temperature:0,top_p:1,n:1,max_tokens:$max_tokens,seed:$seed},batch_size:$batch_size,
    resume_from:(if $resume_from=="-" then null else $resume_from end),command:$command,start_time_utc:$started,
    end_time_utc:null,status:"running",stdout_stderr_log:$log,expected_artifacts:[$output],
    performance_values_opened:false,scientific_gate_decision:null,deviations:[]}' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' >/dev/null 2>&1 </dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
