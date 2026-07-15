#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <an12|an29> <completed-pilot-run-dir> <failed-watcher-manifest>" >&2
  exit 2
fi
NODE="$1"
TRAINING_RUN="$2"
FAILED_WATCHER_INPUT="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || { echo "invalid compute node" >&2; exit 2; }
TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
[[ -f "${TRAINING_MANIFEST}" ]] || { echo "pilot parent manifest absent" >&2; exit 2; }
[[ "$(jq -r '.job_type' "${TRAINING_MANIFEST}")" == "l13_mechanical_pilot_arm" ]] || { echo "not a pilot parent" >&2; exit 2; }
[[ "$(jq -r '.status' "${TRAINING_MANIFEST}")" == "complete" && "$(jq -r '.exit_code' "${TRAINING_MANIFEST}")" == "0" ]] || { echo "retention recovery requires a completed pilot parent" >&2; exit 2; }
[[ "$(jq -r '.node' "${TRAINING_MANIFEST}")" == "${NODE}" ]] || { echo "parent node mismatch" >&2; exit 2; }

FAILED_WATCHER="$(realpath -m "${FAILED_WATCHER_INPUT}")"
case "${FAILED_WATCHER}" in
  "${ROOT}"/experiments/runs/*/run_manifest.json) ;;
  *) echo "failed watcher must be under experiments/runs" >&2; exit 2 ;;
esac
[[ -f "${FAILED_WATCHER}" ]] || { echo "failed watcher manifest absent" >&2; exit 2; }
case "$(jq -r '.job_type' "${FAILED_WATCHER}")" in
  pilot_checkpoint_retention_watch|pilot_resume_checkpoint_retention_watch|pilot_resume60_checkpoint_retention_watch) ;;
  *) echo "unsupported failed watcher type" >&2; exit 2 ;;
esac
[[ "$(jq -r '.status' "${FAILED_WATCHER}")" == "fail" ]] || { echo "recovery target watcher is not failed" >&2; exit 2; }
[[ "$(realpath -m "$(jq -er '.parent_training_run' "${FAILED_WATCHER}")")" == "$(realpath -m "${TRAINING_RUN}")" ]] || { echo "recovery watcher parent mismatch" >&2; exit 2; }

while IFS= read -r ACTIVE; do
  if jq -e '(.job_type == "pilot_checkpoint_retention_recovery") and (.status == "running")' "${ACTIVE}" >/dev/null; then
    echo "another pilot retention recovery is active: ${ACTIVE}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -type f -name run_manifest.json | sort)

PARENT_RUN_ID="$(jq -er '.run_id' "${TRAINING_MANIFEST}")"
RUN_LABEL="$(jq -er '.arm_run_name' "${TRAINING_MANIFEST}")"
RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_MANIFEST}")"
[[ "${RUN_ROOT}" == "${ROOT}/checkpoints/pilot/"* ]] || { echo "unapproved checkpoint root" >&2; exit 2; }
ARCHIVE_ROOT="$(jq -er '.archive_root' "${FAILED_WATCHER}")"
[[ "${ARCHIVE_ROOT}" == "/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}" ]] || { echo "failed watcher archive lineage mismatch" >&2; exit 2; }
CODE_HASH="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.watch_pilot_retention_recovery import recovery_code_bundle_hash; print(recovery_code_bundle_hash())')"
FAILED_HASH="$(sha256sum "${FAILED_WATCHER}" | awk '{print $1}')"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_retention_recovery_${RUN_LABEL}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_retention_recovery.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${TRAINING_MANIFEST} --node ${NODE} --run-label ${RUN_LABEL} --expected-code-hash ${CODE_HASH}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq -n \
  --arg run_id "${RUN_ID}" --arg parent "${TRAINING_RUN}" --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CODE_HASH}" \
  --arg data_hash "$(jq -r '.data_manifest_hash' "${TRAINING_MANIFEST}")" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg root "${RUN_ROOT}" --arg archive "${ARCHIVE_ROOT}" \
  --arg failed "${FAILED_WATCHER#"${ROOT}/"}" --arg failed_hash "${FAILED_HASH}" \
  --arg final_index "${RUN_ROOT}/global_step_100/actor/huggingface/model.safetensors.index.json" \
  --arg final_raw "${RUN_ROOT}/global_step_100/actor/RAW_STATE_RELOCATED.json" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_checkpoint_retention_recovery",
    parent_training_run: $parent,
    recovery_of_failed_watcher: $failed,
    recovery_of_manifest_sha256: $failed_hash,
    node: "login",
    compute_node: $node,
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "One serialized login-node recovery resumes only idempotent step-80/100 retention after a transient quota-scan failure; it allocates no GPU and sends no process signals.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest_hash: $data_hash,
    seed: 1,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    run_root: $root,
    archive_root: $archive,
    raw_retention: "latest raw state only",
    recovery_schedule: [80, 100],
    expected_artifacts: [$final_index, $final_raw],
    deviations: [{code: "restart_after_transient_quota_scan_failure", scientific_config_change: false}]
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || { echo "retention recovery exited during startup" >&2; exit 1; }
printf '%s\n' "${RUN_DIR}"
