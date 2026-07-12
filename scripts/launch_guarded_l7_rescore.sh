#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 CONDITION SOURCE_RUN RUN_TAG" >&2
  exit 2
fi

CONDITION="$1"
SOURCE_RUN="$2"
RUN_TAG="$3"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_OUTPUT_BYTES=200000000

if [[ ! "${CONDITION}" =~ ^(real|gray|noise|none|caption)$ ]]; then
  echo "Invalid L7 condition" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "Invalid guarded-rescore run tag" >&2
  exit 2
fi
if [[ ! "${SOURCE_RUN}" =~ ^experiments/runs/[A-Za-z0-9._-]+$ ]]; then
  echo "SOURCE_RUN must be one direct immutable run directory" >&2
  exit 2
fi

cd "${ROOT}"
SOURCE_MANIFEST="${SOURCE_RUN}/run_manifest.json"
SOURCE_OUTPUT="${SOURCE_RUN}/per_item.jsonl"
for path in "${SOURCE_MANIFEST}" "${SOURCE_OUTPUT}"; do
  if [[ ! -s "${path}" ]]; then
    echo "Guarded L7 source is absent or empty: ${path}" >&2
    exit 2
  fi
done
if ! jq -e --arg condition "${CONDITION}" \
  '(.status == "complete") and (.condition == $condition)' \
  "${SOURCE_MANIFEST}" >/dev/null; then
  echo "Guarded L7 source manifest is not complete for ${CONDITION}" >&2
  exit 2
fi

LOCK_PATH="/tmp/blind_gains_l7_guarded_rescore_${CONDITION}.launch.lock"
exec 9>"${LOCK_PATH}"
if ! flock -n 9; then
  echo "Another ${CONDITION} guarded-rescore launch is active" >&2
  exit 3
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="blind_solvability_v2_guarded_rescore_${RUN_TAG}_${CONDITION}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
SOURCE_OUTPUT_HASH="$(sha256sum "${SOURCE_OUTPUT}" | awk '{print $1}')"
SOURCE_MANIFEST_HASH="$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')"
GUARD_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import SYMBOLIC_GRADER_GUARD_VERSION; print(SYMBOLIC_GRADER_GUARD_VERSION)')"
GUARD_TIMEOUT="$(PYTHONPATH=. .venv/bin/python -c 'from src.rewards.pilot_reward import DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS; print(DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS)')"
RESCORE_VERSION="$(PYTHONPATH=. .venv/bin/python -c 'from scripts.rescore_blind_solvability_v2_guarded import GUARDED_RESCORE_VERSION; print(GUARDED_RESCORE_VERSION)')"
COMMAND=".venv/bin/python scripts/storage_guard.py --tier S --path ${RUN_DIR} --operation l7_guarded_rescore_${CONDITION} --required-bytes ${EXPECTED_OUTPUT_BYTES} && flock -n --no-fork /tmp/blind_gains_l7_guarded_rescore_${CONDITION}.run.lock env PYTHONPATH=. .venv/bin/python scripts/rescore_blind_solvability_v2_guarded.py --source-run ${SOURCE_RUN} --condition ${CONDITION} --output ${OUTPUT} --run-manifest ${MANIFEST}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --slurpfile source "${SOURCE_MANIFEST}" \
  --arg run_id "${RUN_ID}" \
  --arg condition "${CONDITION}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg source_run "${SOURCE_RUN}" \
  --arg source_output_hash "${SOURCE_OUTPUT_HASH}" \
  --arg source_manifest_hash "${SOURCE_MANIFEST_HASH}" \
  --arg guard_version "${GUARD_VERSION}" \
  --argjson guard_timeout "${GUARD_TIMEOUT}" \
  --arg rescore_version "${RESCORE_VERSION}" \
  --arg command "${COMMAND}" \
  --arg output "${OUTPUT}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '($source[0]) as $s | {
    run_id: $run_id,
    job_type: "l7_blind_solvability_geo3k_v2_guarded_rescore",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only immutable posthoc grading of fixed L7 responses under the pinned L3 symbolic guard; no response is regenerated.",
    placement_policy_version: "pi-2026-07-11",
    condition: $condition,
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $s.data_manifest,
    data_manifest_hash: $s.data_manifest_hash,
    source_manifest_sha256: $s.source_manifest_sha256,
    train_filter_ids: $s.train_filter_ids,
    train_filter_sha256: $s.train_filter_sha256,
    model_revision: $s.model_revision,
    format_prompt_sha256: $s.format_prompt_sha256,
    parser_version: $s.parser_version,
    pilot_reward_version: $s.pilot_reward_version,
    scoring_mode: $s.scoring_mode,
    prompt_contract: $s.prompt_contract,
    prompt_contract_sha256: $s.prompt_contract_sha256,
    group_size: $s.group_size,
    sample_count: $s.sample_count,
    sample_temperature: $s.sample_temperature,
    max_tokens: $s.max_tokens,
    format_weight: $s.format_weight,
    seed: $s.seed,
    decoding: $s.decoding,
    caption_source_run: $s.caption_source_run,
    guarded_rescore_version: $rescore_version,
    rescore_source_run: $source_run,
    rescore_source_output_sha256: $source_output_hash,
    rescore_source_manifest_sha256: $source_manifest_hash,
    symbolic_grader_guard_version: $guard_version,
    symbolic_grader_timeout_seconds: $guard_timeout,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output],
    deviations: ["Responses were generated by the recorded source run; every score field is recomputed under the pinned L3 guard because legacy source prefixes lacked uniform runtime-guard stamps."]
  }' > "${MANIFEST}"

(nohup .venv/bin/python scripts/run_manifest_job.py "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null & echo $! > "${PID_FILE}")
printf '%s\n' "${RUN_DIR}"
