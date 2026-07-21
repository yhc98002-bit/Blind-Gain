#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
SEED=2
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed2_locked_eval_lifecycle_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CHILDREN="${RUN_DIR}/children.json"
OUTPUT="${RUN_DIR}/lifecycle_complete.json"
LOG="${RUN_DIR}/logs/login.log"
WRAPPER_LOG="${RUN_DIR}/logs/wrapper.log"
MANIFEST="${RUN_DIR}/run_manifest.json"

CRITICAL_FILES=(
  scripts/launch_pilot_seed2_eval_lifecycle.sh
  scripts/watch_pilot_followup_eval_lifecycle.py
  scripts/launch_pilot_followup_r19_queue.sh
  scripts/launch_pilot_followup_geo3k_queue.sh
  scripts/run_pilot_step100_eval_queue.py
  scripts/run_pilot_geo3k_step100_queue.py
  scripts/launch_fliptrack_eval_shards.sh
  scripts/watch_pilot_step_evaluation.py
  scripts/launch_pilot_geo3k_step100_eval.sh
  scripts/run_pilot_geo3k_step100_eval.py
  scripts/launch_pilot_geo3k_step100_audit.sh
  scripts/audit_pilot_geo3k_step100_eval.py
)
CONFIG_FILES=(configs/eval/m3_seed2_*_step*_queue_v1.json)
CRITICAL_FILES+=("${CONFIG_FILES[@]}")
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "seed-2 evaluation lifecycle code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${FILE}" >&2
    exit 2
  }
done

while IFS= read -r ACTIVE; do
  [[ "$(jq -r '.job_type // ""' "${ACTIVE}" 2>/dev/null)" == "pilot_followup_evaluation_lifecycle" ]] || continue
  [[ "$(jq -r '.status // ""' "${ACTIVE}" 2>/dev/null)" == "running" ]] || continue
  [[ "$(jq -r '.pilot_seed // -1' "${ACTIVE}" 2>/dev/null)" == "${SEED}" ]] || continue
  echo "an active seed-2 evaluation lifecycle already exists: $(dirname "${ACTIVE}")" >&2
  exit 73
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -print)

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
printf '{"schema_version":"blind-gains.pilot-followup-eval-children.v1","seed":2,"endpoints":[]}\n' > "${CHILDREN}.partial"

ARMS=(a1_real a2_gray a2b_noimage a3_caption)
STEPS=(60 100)
for ARM in "${ARMS[@]}"; do
  for GLOBAL_STEP in "${STEPS[@]}"; do
    R19_CONFIG="configs/eval/m3_seed2_${ARM}_step${GLOBAL_STEP}_r19_queue_v1.json"
    GEO_CONFIG="configs/eval/m3_seed2_${ARM}_step${GLOBAL_STEP}_geo3k_queue_v1.json"
    [[ -f "${R19_CONFIG}" && -f "${GEO_CONFIG}" ]] || {
      echo "endpoint config absent for ${ARM}/step${GLOBAL_STEP}" >&2
      exit 2
    }
    R19_RUN="$(scripts/launch_pilot_followup_r19_queue.sh "${R19_CONFIG}")"
    GEO_RUN="$(scripts/launch_pilot_followup_geo3k_queue.sh "${GEO_CONFIG}" "${R19_RUN}")"
    jq \
      --arg arm "${ARM}" --argjson global_step "${GLOBAL_STEP}" \
      --arg r19 "${R19_RUN}" --arg geo "${GEO_RUN}" \
      '.endpoints += [{arm: $arm, global_step: $global_step, r19_queue_run: $r19, geo3k_queue_run: $geo}]' \
      "${CHILDREN}.partial" > "${CHILDREN}.next"
    mv "${CHILDREN}.next" "${CHILDREN}.partial"
  done
done
mv "${CHILDREN}.partial" "${CHILDREN}"
PYTHONPATH=. .venv/bin/python -c \
  'import json,sys; from pathlib import Path; from scripts.watch_pilot_followup_eval_lifecycle import validate_children; validate_children(json.loads(Path(sys.argv[1]).read_text()), Path.cwd())' \
  "${CHILDREN}"

COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_followup_eval_lifecycle.py --children '${CHILDREN}' --output '${OUTPUT}' --poll-seconds 60"
CONFIG_HASH="$(sha256sum configs/eval/m3_seed2_*_step*_queue_v1.json | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${CHILDREN}" | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg children "${CHILDREN}" --arg command "${COMMAND}" --arg log "${LOG}" \
  --arg output "${OUTPUT}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_followup_evaluation_lifecycle",
    pilot_seed: 2,
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    child_target_node: "an29",
    child_r19_gpu_ids: [0, 1, 2, 3],
    child_geo3k_gpu_ids: [4, 5, 6, 7],
    placement_justification: "CPU-only coordinator keeps all four-arm seed-2 values sealed while eight R19 endpoints serialize on four TP1 replicas and audited Geometry3K endpoints use disjoint TP1 GPUs on an29.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $children,
    data_manifest_hash: $data_hash,
    seed: 0,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$children, $output],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${WRAPPER_LOG}" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "seed-2 evaluation lifecycle watcher exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
