#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <an12|an21|an29> <pilot-step60-resume-run-dir>" >&2
  exit 2
fi
NODE="$1"
TRAINING_RUN="$2"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
MANIFEST_IN="${TRAINING_RUN}/run_manifest.json"

[[ -f "${MANIFEST_IN}" ]] || { echo "resume parent manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${MANIFEST_IN}")" == "l13_mechanical_pilot_arm" ]] || { echo "not a pilot parent" >&2; exit 2; }
ARM="$(jq -er '.arm' "${MANIFEST_IN}")"
[[ "${ARM}" == "a1_real" || "${ARM}" == "a2_gray" ]] || { echo "step-60 watcher only supports A1/A2" >&2; exit 2; }
[[ "$(jq -r '.resumed_from_global_step' "${MANIFEST_IN}")" == "60" ]] || { echo "parent is not a step-60 resume" >&2; exit 2; }
[[ "$(jq -r '.node' "${MANIFEST_IN}")" == "${NODE}" ]] || { echo "node mismatch" >&2; exit 2; }
PARENT_STATUS="$(jq -r '.status' "${MANIFEST_IN}")"
[[ "${PARENT_STATUS}" == "running" || "${PARENT_STATUS}" == "complete" ]] || { echo "resume parent is neither running nor complete" >&2; exit 2; }

PARENT_RUN_ID="$(jq -er '.run_id' "${MANIFEST_IN}")"
RUN_LABEL="$(jq -er '.arm_run_name' "${MANIFEST_IN}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${MANIFEST_IN}")"
case "${ARM}" in
  a1_real) [[ "${RUN_LABEL}" =~ ^mech_a1_real_resume60(_retry[1-9][0-9]*)?$ ]] || { echo "unapproved A1 resume label" >&2; exit 2; } ;;
  a2_gray) [[ "${RUN_LABEL}" =~ ^mech_a2_gray_resume60(_retry[1-9][0-9]*)?$ ]] || { echo "unapproved A2 resume label" >&2; exit 2; } ;;
esac
EXPECTED_ROOT="${ROOT}/checkpoints/pilot/${RUN_LABEL}"
[[ "${RUN_ROOT}" == "${EXPECTED_ROOT}" ]] || { echo "unapproved resume checkpoint root" >&2; exit 2; }

RECOVERY_OF=""
RECOVERY_HASH=""
if [[ "${PARENT_STATUS}" == "complete" ]]; then
  RECOVERY_INPUT="${BLIND_GAINS_WATCHER_RECOVERY_OF:-}"
  [[ -n "${RECOVERY_INPUT}" ]] || { echo "completed parent requires a failed watcher recovery manifest" >&2; exit 2; }
  RECOVERY_OF="$(realpath -m "${RECOVERY_INPUT}")"
  case "${RECOVERY_OF}" in
    "${ROOT}"/experiments/runs/*/run_manifest.json) ;;
    *) echo "watcher recovery manifest must be under experiments/runs" >&2; exit 2 ;;
  esac
  [[ -f "${RECOVERY_OF}" ]] || { echo "watcher recovery manifest absent" >&2; exit 2; }
  [[ "$(jq -r '.job_type' "${RECOVERY_OF}")" == "pilot_resume60_checkpoint_retention_watch" ]] || { echo "recovery target is not a resume60 watcher" >&2; exit 2; }
  [[ "$(jq -r '.status' "${RECOVERY_OF}")" == "fail" ]] || { echo "recovery target watcher is not failed" >&2; exit 2; }
  [[ "$(realpath -m "$(jq -er '.parent_training_run' "${RECOVERY_OF}")")" == "$(realpath -m "${TRAINING_RUN}")" ]] || { echo "recovery watcher parent mismatch" >&2; exit 2; }
  RECOVERY_HASH="$(sha256sum "${RECOVERY_OF}" | awk '{print $1}')"
fi
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}"
CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_pilot_resume60_checkpoints import resume60_code_bundle_hash; print(resume60_code_bundle_hash())')"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_resume60_checkpoint_watch_${RUN_LABEL}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_resume60_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${MANIFEST_IN} --node ${NODE} --run-label ${RUN_LABEL} --expected-code-hash ${CODE_HASH}"

jq -n \
  --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CODE_HASH}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${MANIFEST_IN}")" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg root "${RUN_ROOT}" \
  --arg archive "${ARCHIVE_ROOT}" \
  --arg recovery_of "${RECOVERY_OF#"${ROOT}/"}" --arg recovery_hash "${RECOVERY_HASH}" \
  --arg final_index "${RUN_ROOT}/global_step_100/actor/huggingface/model.safetensors.index.json" \
  --arg final_raw "${RUN_ROOT}/global_step_100/actor/RAW_STATE_RELOCATED.json" \
  '({
    schema_version: "blind-gains.run-manifest.v1", run_id: $run_id,
    job_type: "pilot_resume60_checkpoint_retention_watch", parent_training_run: $parent,
    node: "login", compute_node: $node, gpu_ids: [], gpu_allocation: [],
    tensor_parallel_width: 0, replica_count: 0,
    placement_justification: "CPU-only login watcher handles immutable step-60 recovery checkpoints; it never signals GPU jobs.",
    git_hash: $git_hash, config_hash: $config_hash, data_manifest_hash: $data_hash,
    seed: 1, command: $command, start_time_utc: $started, end_time_utc: null,
    status: "running", run_root: $root, archive_root: $archive,
    raw_retention: "latest raw state only", resume_schedule: [80,100],
    expected_artifacts: [$final_index, $final_raw], deviations: []
  } + (if $recovery_of == "" then {} else {
    recovery_of_failed_watcher: $recovery_of,
    recovery_of_manifest_sha256: $recovery_hash,
    deviations: [{code: "restart_retention_after_code_bundle_fail_closed", scientific_config_change: false}]
  } end))' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "resume60 watcher exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
