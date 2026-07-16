#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ID="anchor_a0_recipe_3b_geo3k_20260709T224852Z"
CHECKPOINT="${ROOT}/checkpoints/anchor_a0_recipe_3b_geo3k/${SOURCE_ID}/global_step_100"
ACTOR="${CHECKPOINT}/actor"
ARCHIVE="/tmp/blindgain_checkpoint_archive/${SOURCE_ID}/global_step_100/actor"
RELOCATION_MARKER="${ACTOR}/RAW_STATE_RELOCATED.json"
RESTORE_MARKER="${ACTOR}/RAW_STATE_RESTORED_FOR_RESUME.json"
AUTHORIZATION="${ROOT}/reports/registered_extensions_authorization_v4.json"

cd "${ROOT}"
if [[ ! -f "${RELOCATION_MARKER}" || ! -f "${ARCHIVE}/raw_training_state.source.sha256" ]]; then
  echo "Anchor step-100 relocation evidence is incomplete" >&2
  exit 2
fi
if [[ -e "${RESTORE_MARKER}" ]]; then
  echo "Refusing to overwrite existing restore marker: ${RESTORE_MARKER}" >&2
  exit 2
fi
if ! jq -e '
  .status == "authorized" and
  .authorization.m5 == "authorized_after_restore_integrity_pass" and
  ([.checks[]] | all)
' "${AUTHORIZATION}" >/dev/null; then
  echo "M5 authorization artifact is not valid" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m5_anchor_step100_raw_restore_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
GUARD_LOG="${RUN_DIR}/storage_guard.jsonl"
AUDIT_JSON="${RUN_DIR}/restored_checkpoint_audit.json"
AUDIT_SHA="${RUN_DIR}/restored_checkpoint.sha256"
COMMAND="PYTHONPATH=${ROOT} .venv/bin/python scripts/restore_easyr1_raw_checkpoint.py --actor-dir '${ACTOR}' --archive-dir '${ARCHIVE}' --guard-log '${GUARD_LOG}' && PYTHONPATH=${ROOT} .venv/bin/python scripts/audit_easyr1_resume_checkpoint.py --checkpoint-dir '${CHECKPOINT}' --expected-step 100 --expected-world-size 4 --output-json '${AUDIT_JSON}' --output-sha256 '${AUDIT_SHA}'"
CONFIG_HASH="$(sha256sum configs/train/anchor_a0_recipe_3b_geo3k.yaml | awk '{print $1}')"
DATA_HASH="$({
  sha256sum "${RELOCATION_MARKER}"
  sha256sum "${ARCHIVE}/raw_training_state.source.sha256"
  sha256sum "${AUTHORIZATION}"
} | sort -k2 | sha256sum | awk '{print $1}')"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg data_hash "${DATA_HASH}" \
  --arg command "${COMMAND}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" \
  --arg marker "${RESTORE_MARKER}" \
  --arg audit_json "${AUDIT_JSON}" \
  --arg audit_sha "${AUDIT_SHA}" \
  --arg relocation "${RELOCATION_MARKER}" \
  --arg archive "${ARCHIVE}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m5_anchor_step100_raw_restore",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only hash-verified restore from the login-node archive to shared storage; no GPU is allocated.",
    git_hash: $git_hash,
    config_path: "configs/train/anchor_a0_recipe_3b_geo3k.yaml",
    config_hash: $config_hash,
    data_manifest: $relocation,
    data_manifest_hash: $data_hash,
    seed: 1,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    archive_path: $archive,
    expected_artifacts: [$marker, $audit_json, $audit_sha],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
printf '%s\n' "${RUN_DIR}"
