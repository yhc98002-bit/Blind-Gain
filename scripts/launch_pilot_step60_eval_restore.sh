#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <training-run-dir> <checkpoint-archive-root>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_RUN="$(realpath -m "$1")"
ARCHIVE_ROOT="$(realpath -m "$2")"
case "${TRAINING_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "training run must be under experiments/runs" >&2; exit 2 ;;
esac
case "${ARCHIVE_ROOT}" in
  /tmp/blindgain_checkpoint_archive/*) ;;
  *) echo "archive root must be under the approved login scratch archive" >&2; exit 2 ;;
esac
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
[[ -s "${TRAINING_MANIFEST}" ]] || { echo "training manifest absent" >&2; exit 2; }
jq -e '
  (.job_type == "m3_mechanical_pilot_arm") and
  (.seed == 2 or .seed == 3) and
  (.status == "complete") and (.exit_code == 0) and
  (.artifacts_exist == true)
' "${TRAINING_MANIFEST}" >/dev/null || {
  echo "training run is not a completed follow-up pilot" >&2
  exit 2
}

CRITICAL=(
  scripts/restore_pilot_step60_merged.py
  scripts/launch_pilot_step60_eval_restore.sh
  src/ops/storage_guard.py
)
for file in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${file}" >/dev/null 2>&1 || {
    echo "untracked restore-critical file: ${file}" >&2
    exit 3
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "restore-critical code differs from HEAD" >&2
  exit 3
}

RUN_ROOT="$(jq -er .checkpoint_path "${TRAINING_MANIFEST}")"
DESTINATION="${RUN_ROOT}/global_step_60/actor/huggingface"
RELOCATION_MARKER="${RUN_ROOT}/global_step_60/actor/MERGED_CHECKPOINT_RELOCATED.json"
R19_MARKER="${TRAINING_RUN}/step60_fliptrack_complete.json"
ARCHIVE="${ARCHIVE_ROOT}/global_step_60/actor/huggingface"
[[ ! -e "${DESTINATION}" ]] || { echo "restore destination already exists" >&2; exit 73; }
[[ -s "${RELOCATION_MARKER}" && -s "${R19_MARKER}" ]] || {
  echo "relocation or R19 marker absent" >&2
  exit 2
}
[[ -s "${ARCHIVE}/merged_checkpoint.source.sha256" ]] || {
  echo "archive checksum manifest absent" >&2
  exit 2
}

ARM="$(jq -er .arm "${TRAINING_MANIFEST}")"
SEED="$(jq -er .seed "${TRAINING_MANIFEST}")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_step60_eval_restore_${ARM}_seed${SEED}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
OUTPUT="${RUN_DIR}/restore.json"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/restore_pilot_step60_merged.py --archive '${ARCHIVE}' --destination '${DESTINATION}' --relocation-marker '${RELOCATION_MARKER}' --r19-marker '${R19_MARKER}' --output '${OUTPUT}'"
DATA_HASH="$({ sha256sum "${ARCHIVE}/merged_checkpoint.source.sha256" "${RELOCATION_MARKER}" "${R19_MARKER}"; } | sort -k2 | sha256sum | awk '{print $1}')"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" --arg arm "${ARM}" --argjson seed "${SEED}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CONFIG_HASH}" \
  --arg data_manifest "${ARCHIVE}/merged_checkpoint.source.sha256" \
  --arg data_hash "${DATA_HASH}" --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" \
  --arg archive "${ARCHIVE}" --arg destination "${DESTINATION}" \
  --arg output "${OUTPUT}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_step60_merged_restore_for_evaluation",
    arm: $arm,
    pilot_seed: $seed,
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only, hash-verified restore of one archived merged checkpoint; the archive is preserved and no optimizer state is touched.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    seed: 0,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    archive: $archive,
    destination: $destination,
    expected_artifacts: [$output, ($destination + "/model.safetensors.index.json")],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: [{
      code: "restore_step60_after_evaluation_relocation_race",
      scientific_config_change: false
    }]
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "step-60 restore exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
