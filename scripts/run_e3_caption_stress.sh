#!/usr/bin/env bash
# =============================================================================
# Track-4 premise-v2 acceptance gate E3 — CAPTION STRESS (1 GPU: an29 GPU 3)
# =============================================================================
# This script RUNS AND RECORDS the registered E3 command chain
# (docs/registered_track4_premise_v2_design_v1.md section 7, "E3 — caption
# stress") with its placeholders resolved, under the PI's binding captioning
# decision for this run.  It DOES NOT JUDGE.  No pass/fail verdict, no
# comparison against the blind-floor threshold, and no interpretation is
# emitted anywhere by this script: it produces predictions.jsonl, metrics.json
# and a provenance record, and the registered criterion
#   "per type: caption member accuracy <= blind-floor threshold + 0.10 absolute"
# is read separately, by whoever owns the verdict.  Note for that reader: the
# registered eval (scripts/eval_caption_qa_fliptrack.py -> aggregate_pair_metrics)
# emits ONE FLAT AGGREGATE dict with no per-type breakdown, and the QA rows carry
# no intervention_type; the per-type readout is a post-hoc join of
# predictions.jsonl to $DATA/manifest_causal_pairs.jsonl on pair_id and is NOT
# part of the registered chain. predictions.jsonl is preserved so that join stays
# possible.
#
# REGISTERED COMMANDS, VERBATIM (placeholders resolved, criteria untouched):
#   (a) scripts/launch_caption_store_shards.sh <node> 0 <shards> \
#         artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct $DATA/images <run_dir>
#   (b) merge
#   (c) scripts/build_caption_qa_pairs.py
#   (d) scripts/eval_caption_qa_fliptrack.py --model-path $BASE \
#         --input <qa.jsonl> --output ... --max-new-tokens 32
# with, from the registration's own preamble (lines 217-220):
#   ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
#   BASE=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct   (the frozen 3B of E1/E2)
#   DATA=data/track4_premise_v2_dev_v1
#
# PI DECISION APPLIED HERE: caption ALL images in $DATA/images (the registered
# command verbatim; the directory holds 640 files / 480 distinct sha256) and
# restrict at the QA-BUILD step via the documented --allow-extra-captions flag of
# scripts/build_caption_qa_pairs.py, so the 160 non-causal images are carried but
# unused.  The 320-hash caption-QA release+key
# ($DATA/caption_qa_inputs/{manifest,key}.jsonl) are passed to the QA build
# unchanged and their sha256 are verified against the fixture-backed values
# before any GPU is spent.
#
# MERGE-BOUNDARY DEVIATION (recorded, never silent; see $MERGE_RESOLUTION_NOTE,
# which is copied verbatim into the provenance JSON): scripts/merge_caption_stores.py
# accepts exactly one --release-manifest and src/captioning/store.py::merge_caption_rows
# (lines 148-152) treats EXTRA caption hashes as fatal, with no override flag, so
# merging the 480-image store against the 320-hash caption-QA release fails with
# missing=0 extra=160 AFTER the GPU pass is paid for.  No documented option covers
# it.  This script therefore derives, INSIDE ITS OWN RUN DIR and from the batch's
# own two pair manifests, a coverage manifest whose members[].image_sha256 union is
# exactly the 480 distinct sha256 of $DATA/images, and passes THAT to the merge.
# No hash is invented, the dev batch is not mutated or even written to, and no
# coverage check is disabled or weakened — the merge's own enforcement still runs
# and must report coverage_complete=true over 480.
#
# ONE-GPU TRAP (load-bearing, not a deviation): the registered launcher line stops
# at <run_dir>; with NUM_SHARDS=1 and the launcher's DEFAULT GPU_LIST the position
# loop leaves ACTIVE_GPU_IDS=(0) and would seize an29 GPU 0 (the a2b eval).
# GPU_LIST="3" is passed as the launcher's operator-discretion arg 7.
#
# GPU BUDGET: exactly one GPU, an29 GPU 3, taken via guard -> claim -> re-check
# exactly as scripts/run_e4_gate.sh does, held across the whole chain and
# refreshed inside every wait loop (claims expire at 30 minutes).
#
# WRITE SCOPE: this script writes only to
#   experiments/runs/track4_premise_v2_e3_an29_<stamp>/            (its run dir)
#   experiments/runs/track4_premise_v2_caption_store_an29_<stamp>/ (caption store)
#   experiments/runs/caption_store_merge_track4_premise_v2_dev_v1_<stamp>/ (merge)
#   logs/track4_gates/e3_caption_stress.log
#   reports/track4_premise_v2_e3_caption_stress_run_provenance_v1*.json
#   /dev/shm/blind-gains/gpu_claims/an29_gpu3.claim on an29 (its own claim)
# It never writes inside data/track4_premise_v2_dev_v1.
#
# Run it FROM A LOGIN NODE (ln206/ln207): the caption launcher sshes to the node
# itself.  Detach it:
#   setsid nohup bash /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/run_e3_caption_stress.sh </dev/null >/dev/null 2>&1 & disown
# =============================================================================
set -uo pipefail

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

NODE=an29
GPU=3
CLAIMS=/dev/shm/blind-gains/gpu_claims
CLAIM_RUN_ID=t4v2_e3_caption_stress
CLAIM_HELD=0

BASE=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct
CAPTIONER=artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct
# E3_DATA_DIR / E3_PROV_TAG overrides (2026-08-16, item 4): the branch-(c)+
# balance regeneration re-runs E3 on data/track4_premise_v2_dev_v2 with this
# same instrument. Defaults reproduce the registered v1 invocation exactly;
# the v1 provenance stays protected by its own overwrite refusal.
DATA="${E3_DATA_DIR:-data/track4_premise_v2_dev_v1}"
IMAGES="$DATA/images"
RELEASE_MANIFEST="$DATA/caption_qa_inputs/manifest.jsonl"
RELEASE_KEY="$DATA/caption_qa_inputs/key.jsonl"
# Fixture-backed sha256 of the caption-QA release+key that define the 320 causal
# member images. A mismatch means the release changed under this run and the PI's
# premise no longer holds, so the chain refuses before spending any GPU.
# Overridable ONLY together with E3_DATA_DIR (a different batch has different
# releases); the v1 defaults stay pinned.
RELEASE_MANIFEST_SHA256_EXPECTED="${E3_RELEASE_MANIFEST_SHA256:-82842b6cf2a9e4734e393e2825d790277439e8c3f196d98f32cc3a95f1707ccd}"
RELEASE_KEY_SHA256_EXPECTED="${E3_RELEASE_KEY_SHA256:-56be7961fb6c8139c2e479f24849185b820f999615a47673590bb34a9af8c68f}"

REGISTRATION=docs/registered_track4_premise_v2_design_v1.md
MERGE_RUN_TAG="$(basename "$DATA")"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN="track4_premise_v2_e3_an29_${STAMP}"
RUN_DIR="experiments/runs/${RUN}"
RUN_DIR_ABS="${ROOT}/${RUN_DIR}"
CAP_RUN_DIR="experiments/runs/track4_premise_v2_caption_store_an29_${STAMP}"
CAP_SHARD="${CAP_RUN_DIR}/shards/store_shard_0.jsonl"
COVERAGE_MANIFEST="${RUN_DIR}/merge_inputs/coverage_release_480.jsonl"
COVERAGE_SUMMARY="${RUN_DIR}/merge_inputs/coverage_manifest_summary.json"
QA_JSONL="${RUN_DIR}/caption_qa/qa.jsonl"
QA_SUMMARY="${RUN_DIR}/caption_qa/qa_input_summary.json"
PRED_JSONL="${RUN_DIR}/caption_qa/predictions.jsonl"
METRICS_JSON="${RUN_DIR}/caption_qa/metrics.json"
EVAL_JOB="${RUN_DIR}/caption_qa/eval_gpu_job.sh"
EVAL_LOG="${RUN_DIR}/caption_qa/eval_gpu_job.log"
EVAL_RC_FILE="${RUN_DIR}/caption_qa/eval_gpu_job.rc"
EVAL_PID_FILE="${RUN_DIR}/caption_qa/eval_gpu_job.pid"
STAGES="${RUN_DIR}/e3_stage_records.jsonl"

LOG="${ROOT}/logs/track4_gates/e3_caption_stress.log"
PROV_TAG="${E3_PROV_TAG:-v1}"
PROV="reports/track4_premise_v2_e3_caption_stress_run_provenance_${PROV_TAG}.json"
PROV_FAILED="reports/track4_premise_v2_e3_caption_stress_run_provenance_${PROV_TAG}.failed_${STAMP}.json"

CAPTION_TIMEOUT_SECONDS=43200   # 12 h; prior 7B/384 anchor is ~39 min for 600 images on one A800
EVAL_TIMEOUT_SECONDS=21600      # 6 h; 320 caption-only generations at 32 new tokens on the 3B
POLL_SECONDS=60
CLAIM_REFRESH_POLLS=10          # refresh the claim every ~10 min (claims go stale at 30 min)

mkdir -p "$(dirname "$LOG")" "${RUN_DIR}/merge_inputs" "${RUN_DIR}/caption_qa" || exit 1

utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(utc) $*" >> "$LOG"; }

GIT_HASH="$(git rev-parse HEAD 2>/dev/null)"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
GIT_DIRTY_COUNT="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
START_UTC="$(utc)"

MERGE_RESOLUTION_NOTE="E3 merge: scripts/merge_caption_stores.py accepts exactly one --release-manifest and src/captioning/store.py::merge_caption_rows (lines 148-152) treats EXTRA caption hashes as fatal, with no override flag. The registered E3 command captions all of \$DATA/images (640 files / 480 distinct sha256) while the caption-QA release covers 320, so merging against caption_qa_inputs/manifest.jsonl fails with missing=0 extra=160 after the GPU pass. No documented option covers this. Resolution: --release-manifest points at a NEW derived coverage manifest, ${COVERAGE_MANIFEST}, written inside this run dir (the dev batch is not written to at all), whose members[].image_sha256 union is exactly the 480 distinct sha256 of \$DATA/images (= hashes(manifest_causal_pairs.jsonl) union hashes(manifest_invariance_pairs.jsonl), asserted equal to the image dir's own distinct-hash set as computed by src.captioning.store.discover_images, with 0 outside, before any GPU is spent; the causal half is additionally asserted identical to the 320 hashes of caption_qa_inputs/manifest.jsonl). Derived by a minimal emitter over the two flat pair manifests' image_a_sha256/image_b_sha256 fields, not by scripts/build_track4_premise_v2_caption_qa_inputs.py. No hash is invented; the dev batch is not mutated; no coverage check is disabled -- the merge's own enforcement still runs and must report coverage_complete=true over 480. The restriction to the 160 causal pairs / 320 member images is applied one step later, at scripts/build_caption_qa_pairs.py, via its documented --allow-extra-captions (src/captioning/qa_pairs.py:87-89), which carries the 160 non-causal captions unused. The 320-hash caption-QA release+key (manifest sha256 82842b6c..., key 56be7961...) are passed to the QA build unchanged."

# --- stage bookkeeping -------------------------------------------------------
record_stage() { # name command rc start_utc end_utc artifacts_json
  jq -nc --arg name "$1" --arg command "$2" --argjson rc "$3" \
         --arg start_utc "$4" --arg end_utc "$5" --argjson artifacts "$6" \
    '{name:$name, command:$command, rc:$rc, start_utc:$start_utc, end_utc:$end_utc, artifacts:$artifacts}' \
    >> "$STAGES"
}

release_claim() {
  if [[ "$CLAIM_HELD" == "1" ]]; then
    ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" >/dev/null 2>&1 || true
    CLAIM_HELD=0
    log "claim released ($NODE gpu$GPU)"
  fi
}

claim_write() { # pid_json ("null" or an integer)
  local payload
  payload="$(jq -nc --argjson gpu "$GPU" --arg run_id "$CLAIM_RUN_ID" --argjson pid "$1" \
    --arg dir "$RUN_DIR" --arg ts "$(utc)" \
    '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts, written_by:"scripts/run_e3_caption_stress.sh"}')" || return 1
  printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
    "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'"
}

CLAIM_PID_JSON=null
refresh_claim() {
  if claim_write "$CLAIM_PID_JSON"; then
    log "claim refreshed ($NODE gpu$GPU pid=$CLAIM_PID_JSON)"
  else
    log "WARN claim refresh failed ($NODE gpu$GPU); the claim may go stale at 30 minutes"
  fi
}

# jq --slurpfile refuses a path that does not exist; every embedded summary is
# optional because an early failure can abort before it is written.
slurp_path() { if [[ -s "${1:-}" ]]; then printf '%s' "$1"; else printf '%s' /dev/null; fi; }

RELEASE_FIXTURE_VERIFIED=false

write_provenance() { # status failed_stage failure_message
  local status="$1" failed_stage="$2" message="$3" out
  if [[ "$status" == "complete" ]]; then out="$PROV"; else out="$PROV_FAILED"; fi
  [[ -f "$STAGES" ]] || : > "$STAGES"
  mkdir -p "$(dirname "$out")"
  jq -n \
    --arg schema_version "blind-gains.track4-premise-v2-e3-caption-stress-provenance.v1" \
    --arg gate "E3" \
    --arg registration "${REGISTRATION}#7-E3" \
    --arg status "$status" \
    --arg failed_stage "$failed_stage" \
    --arg failure_message "$message" \
    --arg node "$NODE" \
    --argjson gpu "$GPU" \
    --arg git_hash "$GIT_HASH" \
    --arg git_branch "$GIT_BRANCH" \
    --argjson git_dirty_path_count "${GIT_DIRTY_COUNT:-0}" \
    --arg stamp "$STAMP" \
    --arg start_time_utc "$START_UTC" \
    --arg end_time_utc "$(utc)" \
    --arg runner "scripts/run_e3_caption_stress.sh" \
    --arg base_model "$BASE" \
    --arg captioner_model "$CAPTIONER" \
    --arg data "$DATA" \
    --arg release_manifest "$RELEASE_MANIFEST" \
    --arg release_key "$RELEASE_KEY" \
    --arg release_manifest_sha256 "${RELEASE_MANIFEST_SHA256:-}" \
    --arg release_key_sha256 "${RELEASE_KEY_SHA256:-}" \
    --arg e3_run_dir "$RUN_DIR" \
    --arg caption_store_run_dir "$CAP_RUN_DIR" \
    --arg caption_merge_run_dir "${MERGE_RUN_DIR:-}" \
    --arg coverage_manifest "$COVERAGE_MANIFEST" \
    --arg predictions "$PRED_JSONL" \
    --arg metrics "$METRICS_JSON" \
    --arg qa_input "$QA_JSONL" \
    --arg merge_resolution_note "$MERGE_RESOLUTION_NOTE" \
    --argjson release_fixture_verified "$RELEASE_FIXTURE_VERIFIED" \
    --slurpfile stages "$(slurp_path "$STAGES")" \
    --slurpfile coverage_summary_raw "$(slurp_path "$COVERAGE_SUMMARY")" \
    --slurpfile merge_summary_raw "$(slurp_path "${MERGE_SUMMARY_PATH:-}")" \
    --slurpfile qa_summary_raw "$(slurp_path "$QA_SUMMARY")" \
    --slurpfile metrics_raw "$(slurp_path "$METRICS_JSON")" \
    '{
      schema_version: $schema_version,
      gate: $gate,
      registration: $registration,
      judged: false,
      judgement_note: "This runner runs and records only. The registered E3 criterion (per type: caption member accuracy <= blind-floor threshold + 0.10 absolute) is NOT evaluated here. metrics.json is aggregate-only; the per-type readout needs a post-hoc join of predictions.jsonl to \($data)/manifest_causal_pairs.jsonl on pair_id, which is not part of the registered chain.",
      status: $status,
      failed_stage: (if $failed_stage == "" then null else $failed_stage end),
      failure_message: (if $failure_message == "" then null else $failure_message end),
      node: $node,
      gpu: $gpu,
      gpu_budget: "exactly one GPU (an29 gpu3), taken via guard -> claim -> re-check and released at the end",
      git_hash: $git_hash,
      git_branch: $git_branch,
      git_dirty_path_count: $git_dirty_path_count,
      runner: $runner,
      stamp: $stamp,
      start_time_utc: $start_time_utc,
      end_time_utc: $end_time_utc,
      models: {base_model_under_test: $base_model, captioner: $captioner_model},
      inputs: {
        data_batch: $data,
        image_dir: ($data + "/images"),
        release_manifest: $release_manifest,
        release_key: $release_key,
        release_manifest_sha256: $release_manifest_sha256,
        release_key_sha256: $release_key_sha256,
        release_fixture_sha256_verified: $release_fixture_verified
      },
      run_dirs: {
        e3: $e3_run_dir,
        caption_store: $caption_store_run_dir,
        caption_merge: (if $caption_merge_run_dir == "" then null else $caption_merge_run_dir end)
      },
      artifacts: {
        caption_qa_input: $qa_input,
        predictions: $predictions,
        metrics: $metrics,
        coverage_manifest: $coverage_manifest
      },
      stages: $stages,
      caption_coverage: ($coverage_summary_raw[0] // null),
      merge_summary: ($merge_summary_raw[0] // null),
      caption_qa_input_summary: ($qa_summary_raw[0] // null),
      caption_qa_metrics_aggregate_only: ($metrics_raw[0] // null),
      deviations: [$merge_resolution_note]
    }' > "$out"
  log "provenance written: $out"
}

fail() { # stage_name message
  log "E3-FAIL ${1}: ${2}"
  release_claim
  write_provenance failed "$1" "$2"
  log "*** E3 ABORTED at stage ${1} — no verdict was produced ***"
  exit 1
}

log "=============================================================="
log "E3 caption stress start: node=$NODE gpu=$GPU git=$GIT_HASH branch=$GIT_BRANCH dirty_paths=$GIT_DIRTY_COUNT"
log "run_dir=$RUN_DIR caption_store_run_dir=$CAP_RUN_DIR"
log "registration=${REGISTRATION}#7-E3 ; this runner RUNS AND RECORDS ONLY (no judging)"

# =============================================================================
# STAGE P — preflight (CPU only, no claim held, no GPU spent)
# =============================================================================
P_START="$(utc)"
for required in "$RELEASE_MANIFEST" "$RELEASE_KEY" \
                "$DATA/manifest_causal_pairs.jsonl" \
                "$DATA/manifest_invariance_pairs.jsonl" \
                scripts/launch_caption_store_shards.sh \
                scripts/launch_caption_store_merge.sh \
                scripts/merge_caption_stores.py \
                scripts/build_caption_qa_pairs.py \
                scripts/eval_caption_qa_fliptrack.py \
                scripts/m7_gpu_occupancy_guard.py; do
  [[ -f "$required" ]] || fail preflight "missing required file: $required"
done
for required_dir in "$IMAGES" "$BASE" "$CAPTIONER"; do
  [[ -d "$required_dir" ]] || fail preflight "missing required directory: $required_dir"
done
command -v jq >/dev/null 2>&1 || fail preflight "jq is not on PATH (expected \$HOME/.local/bin)"
[[ -x .venv/bin/python ]] || fail preflight "missing interpreter: .venv/bin/python"
[[ -e "$PROV" ]] && fail preflight "provenance output already exists ($PROV); refusing to overwrite"
[[ -e "$CAP_RUN_DIR/run_manifest.json" ]] && fail preflight "caption-store run dir already initialized: $CAP_RUN_DIR"
[[ -e "$QA_JSONL" ]] && fail preflight "caption-QA input already exists: $QA_JSONL"

RELEASE_MANIFEST_SHA256="$(sha256sum "$RELEASE_MANIFEST" | awk '{print $1}')"
RELEASE_KEY_SHA256="$(sha256sum "$RELEASE_KEY" | awk '{print $1}')"
[[ "$RELEASE_MANIFEST_SHA256" == "$RELEASE_MANIFEST_SHA256_EXPECTED" ]] || \
  fail preflight "caption-QA release manifest sha256 $RELEASE_MANIFEST_SHA256 != fixture-backed $RELEASE_MANIFEST_SHA256_EXPECTED"
[[ "$RELEASE_KEY_SHA256" == "$RELEASE_KEY_SHA256_EXPECTED" ]] || \
  fail preflight "caption-QA release key sha256 $RELEASE_KEY_SHA256 != fixture-backed $RELEASE_KEY_SHA256_EXPECTED"
RELEASE_FIXTURE_VERIFIED=true
log "preflight: release manifest/key sha256 match the fixture-backed values"

# Derive the merge coverage manifest from the batch's own two pair manifests and
# assert, BEFORE the GPU pass, that its hash set is exactly what the registered
# caption command will produce.  Nothing is written into the dev batch.
COVERAGE_OUT="$(.venv/bin/python - "$IMAGES" "$DATA/manifest_causal_pairs.jsonl" "$DATA/manifest_invariance_pairs.jsonl" "$RELEASE_MANIFEST" "$COVERAGE_MANIFEST" "$COVERAGE_SUMMARY" 2>&1 <<'PYEOF'
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.captioning.store import discover_images

images_dir, causal_path, invariance_path, release_path, out_path, summary_path = sys.argv[1:7]


def flat_pairs(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(
                (str(row["pair_id"]), str(row["image_a_sha256"]), str(row["image_b_sha256"]))
            )
    return rows


def release_hashes(path):
    # byte-identical reading rule to scripts/merge_caption_stores.py::_release_hashes
    hashes = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            hashes.update(str(member["image_sha256"]) for member in row["members"])
    return hashes


out = Path(out_path)
summary_out = Path(summary_path)
for path in (out, summary_out):
    if path.exists():
        raise SystemExit(f"refusing to overwrite derived coverage artifact: {path}")

causal = flat_pairs(causal_path)
invariance = flat_pairs(invariance_path)
causal_hashes = {h for _, a, b in causal for h in (a, b)}
invariance_hashes = {h for _, a, b in invariance for h in (a, b)}
coverage_hashes = causal_hashes | invariance_hashes
release = release_hashes(release_path)

discovered = discover_images(images_dir)
disk_hashes = {str(item["image_sha256"]) for item in discovered}
n_image_files = sum(1 + len(item["duplicate_paths"]) for item in discovered)

if causal_hashes != release:
    raise SystemExit(
        "causal manifest hash set does not equal the caption-QA release hash set: "
        f"causal={len(causal_hashes)} release={len(release)} "
        f"causal_only={len(causal_hashes - release)} release_only={len(release - causal_hashes)}"
    )
if coverage_hashes != disk_hashes:
    raise SystemExit(
        "derived coverage hash set does not equal the image dir's distinct-hash set: "
        f"coverage={len(coverage_hashes)} disk={len(disk_hashes)} "
        f"missing_on_disk={len(coverage_hashes - disk_hashes)} "
        f"uncovered_on_disk={len(disk_hashes - coverage_hashes)}"
    )

rows = []
for tag, pairs in (("causal", causal), ("invariance", invariance)):
    for pair_id, hash_a, hash_b in pairs:
        rows.append(
            {
                "schema_version": "blind-gains.track4-premise-v2-caption-coverage-manifest.v1",
                "pair_id": f"{tag}:{pair_id}",
                "members": [
                    {"member_id": f"{tag}:{pair_id}:a", "image_sha256": hash_a},
                    {"member_id": f"{tag}:{pair_id}:b", "image_sha256": hash_b},
                ],
            }
        )

out.parent.mkdir(parents=True, exist_ok=True)
partial = Path(f"{out}.partial")
with partial.open("w", encoding="utf-8") as handle:
    for row in rows:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
partial.replace(out)

emitted = release_hashes(out)
if emitted != disk_hashes:
    out.unlink(missing_ok=True)
    raise SystemExit("emitted coverage manifest does not read back as the image dir hash set")

summary = {
    "schema_version": "blind-gains.track4-premise-v2-caption-coverage-summary.v1",
    "purpose": (
        "expected-hash set for scripts/merge_caption_stores.py, derived from the dev "
        "batch's own pair manifests so it describes exactly what the registered E3 "
        "caption command captions"
    ),
    "image_dir": images_dir,
    "n_image_files": n_image_files,
    "n_distinct_image_sha256": len(disk_hashes),
    "source_manifests": [causal_path, invariance_path],
    "n_causal_hashes": len(causal_hashes),
    "n_invariance_hashes": len(invariance_hashes),
    "n_shared_original_hashes": len(causal_hashes & invariance_hashes),
    "n_coverage_hashes": len(coverage_hashes),
    "caption_qa_release_manifest": release_path,
    "n_caption_qa_release_hashes": len(release),
    "causal_equals_caption_qa_release": True,
    "coverage_equals_image_dir": True,
    "n_extra_captions_carried_unused": len(disk_hashes - release),
    "coverage_manifest": str(out),
    "coverage_manifest_rows": len(rows),
    "coverage_manifest_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
}
summary_partial = Path(f"{summary_out}.partial")
summary_partial.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
summary_partial.replace(summary_out)
print(json.dumps(summary, sort_keys=True))
PYEOF
)"
P_RC=$?
if [[ "$P_RC" -ne 0 ]]; then
  record_stage preflight_coverage_manifest "derive ${COVERAGE_MANIFEST} from ${DATA}/manifest_causal_pairs.jsonl + ${DATA}/manifest_invariance_pairs.jsonl and assert it equals discover_images(${IMAGES})" "$P_RC" "$P_START" "$(utc)" '[]'
  fail preflight_coverage_manifest "coverage-manifest derivation failed (rc=$P_RC): $COVERAGE_OUT"
fi
log "preflight coverage: $(printf '%s' "$COVERAGE_OUT" | tail -1)"
N_IMAGE_FILES="$(jq -r '.n_image_files' "$COVERAGE_SUMMARY")"
N_DISTINCT_HASHES="$(jq -r '.n_distinct_image_sha256' "$COVERAGE_SUMMARY")"
N_RELEASE_HASHES="$(jq -r '.n_caption_qa_release_hashes' "$COVERAGE_SUMMARY")"
N_EXTRA_CARRIED="$(jq -r '.n_extra_captions_carried_unused' "$COVERAGE_SUMMARY")"
log "preflight coverage counts: image_files=$N_IMAGE_FILES distinct_sha256=$N_DISTINCT_HASHES release_hashes=$N_RELEASE_HASHES extra_carried_unused=$N_EXTRA_CARRIED"
record_stage preflight_coverage_manifest "derive ${COVERAGE_MANIFEST} from ${DATA}/manifest_causal_pairs.jsonl + ${DATA}/manifest_invariance_pairs.jsonl and assert it equals discover_images(${IMAGES})" 0 "$P_START" "$(utc)" "$(jq -nc --arg m "$COVERAGE_MANIFEST" --arg s "$COVERAGE_SUMMARY" '[$m,$s]')"

# =============================================================================
# STAGE 0 — guard -> claim -> re-check on an29 GPU 3 (scripts/run_e4_gate.sh pattern)
# =============================================================================
G_START="$(utc)"
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { record_stage gpu_guard_claim "m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU" 1 "$G_START" "$(utc)" '[]'; fail gpu_guard "guard denied $NODE:$GPU before claiming"; }
claim_write null \
  || { record_stage gpu_guard_claim "claim write $CLAIMS/${NODE}_gpu${GPU}.claim" 1 "$G_START" "$(utc)" '[]'; fail gpu_claim "claim write failed on $NODE"; }
CLAIM_HELD=1
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id "$CLAIM_RUN_ID" >> "$LOG" 2>&1 \
  || { record_stage gpu_guard_claim "m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU --ignore-claim-run-id $CLAIM_RUN_ID" 1 "$G_START" "$(utc)" '[]'; fail gpu_recheck "post-claim re-check denied $NODE:$GPU"; }
log "guard+claim ok ($NODE gpu$GPU, run_id=$CLAIM_RUN_ID)"
record_stage gpu_guard_claim "m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU  ->  write $CLAIMS/${NODE}_gpu${GPU}.claim  ->  m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU --ignore-claim-run-id $CLAIM_RUN_ID" 0 "$G_START" "$(utc)" "$(jq -nc --arg c "$CLAIMS/${NODE}_gpu${GPU}.claim" '[$c]')"

# =============================================================================
# STAGE A — caption store: the REGISTERED launcher command (GPU work on an29 gpu3)
#   registered form: scripts/launch_caption_store_shards.sh <node> 0 <shards> \
#     artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct $DATA/images <run_dir>
#   node=an29, shards=1 (one GPU), run_dir stamped; GPU_LIST="3" is the launcher's
#   operator-discretion arg 7 and is mandatory here (see the ONE-GPU TRAP note).
#   MAX_NEW_TOKENS is left at the launcher default 384 (store.py's floor).
# =============================================================================
A_START="$(utc)"
CAPTION_CMD="bash scripts/launch_caption_store_shards.sh ${NODE} 0 1 ${CAPTIONER} ${IMAGES} ${CAP_RUN_DIR} \"3\""
log "STAGE A command: $CAPTION_CMD"
bash scripts/launch_caption_store_shards.sh "$NODE" 0 1 "$CAPTIONER" "$IMAGES" "$CAP_RUN_DIR" "3" \
  >> "$LOG" 2>&1
A_LAUNCH_RC=$?
if [[ "$A_LAUNCH_RC" -ne 0 ]]; then
  record_stage caption_store_launch "$CAPTION_CMD" "$A_LAUNCH_RC" "$A_START" "$(utc)" '[]'
  fail caption_store_launch "registered caption-store launcher exited rc=$A_LAUNCH_RC (75 = GPU occupied / launch lock held)"
fi

# Stamp the live remote worker pid into the claim (belt and braces beside the
# 10-minute mtime refresh below).
WORKER_PID_FILE="$(find "${CAP_RUN_DIR}/pids" -maxdepth 1 -name '*_gpu*_store_shard*.pid' 2>/dev/null | sort | head -1)"
if [[ -n "$WORKER_PID_FILE" ]]; then
  WORKER_PID="$(tr -dc '0-9' < "$WORKER_PID_FILE")"
  if [[ -n "$WORKER_PID" && "$WORKER_PID" -gt 0 ]]; then
    CLAIM_PID_JSON="$WORKER_PID"
  fi
fi
refresh_claim
log "STAGE A launched; waiting for $CAP_RUN_DIR/run_manifest.json status (timeout ${CAPTION_TIMEOUT_SECONDS}s)"

A_STATUS=""
A_POLLS=$((CAPTION_TIMEOUT_SECONDS / POLL_SECONDS))
for ((i = 1; i <= A_POLLS; i++)); do
  sleep "$POLL_SECONDS"
  if (( i % CLAIM_REFRESH_POLLS == 0 )); then refresh_claim; fi
  A_STATUS="$(jq -r '.status // empty' "${CAP_RUN_DIR}/run_manifest.json" 2>/dev/null)"
  if [[ -n "$A_STATUS" && "$A_STATUS" != "running" ]]; then
    log "STAGE A run_manifest status=$A_STATUS after $((i * POLL_SECONDS))s"
    break
  fi
done
if [[ "$A_STATUS" != "complete" ]]; then
  record_stage caption_store "$CAPTION_CMD" 1 "$A_START" "$(utc)" "$(jq -nc --arg d "$CAP_RUN_DIR" '[$d]')"
  fail caption_store "caption store did not complete (run_manifest status='${A_STATUS:-running/unreadable}', run_dir $CAP_RUN_DIR)"
fi
[[ -s "$CAP_SHARD" ]] || { record_stage caption_store "$CAPTION_CMD" 1 "$A_START" "$(utc)" '[]'; fail caption_store "caption shard missing or empty: $CAP_SHARD"; }
CAP_ROWS="$(wc -l < "$CAP_SHARD" | tr -d ' ')"
if [[ "$CAP_ROWS" != "$N_DISTINCT_HASHES" ]]; then
  record_stage caption_store "$CAPTION_CMD" 1 "$A_START" "$(utc)" "$(jq -nc --arg s "$CAP_SHARD" '[$s]')"
  fail caption_store "caption store row count $CAP_ROWS != $N_DISTINCT_HASHES distinct image sha256; the merge would fail"
fi
log "STAGE A complete: $CAP_ROWS caption rows in $CAP_SHARD"
record_stage caption_store "$CAPTION_CMD" 0 "$A_START" "$(utc)" "$(jq -nc --arg d "$CAP_RUN_DIR" --arg s "$CAP_SHARD" '[$d,$s]')"
refresh_claim

# =============================================================================
# STAGE B — merge (CPU, login node).  Expected-hash set = the derived 480-hash
#   coverage manifest; see MERGE_RESOLUTION_NOTE (recorded as a deviation).
# =============================================================================
B_START="$(utc)"
MERGE_CMD="bash scripts/launch_caption_store_merge.sh ${MERGE_RUN_TAG} ${COVERAGE_MANIFEST} ${CAP_SHARD}"
log "STAGE B command: $MERGE_CMD"
log "STAGE B underlying: .venv/bin/python scripts/merge_caption_stores.py --release-manifest ${COVERAGE_MANIFEST} --shards ${CAP_SHARD} --output <MERGE_RUN_DIR>/captions.jsonl --summary <MERGE_RUN_DIR>/summary.json"
MERGE_STDOUT="${RUN_DIR}/merge_inputs/merge_launcher_stdout.txt"
bash scripts/launch_caption_store_merge.sh "$MERGE_RUN_TAG" "$COVERAGE_MANIFEST" "$CAP_SHARD" \
  > "$MERGE_STDOUT" 2>> "$LOG"
B_RC=$?
MERGE_RUN_DIR="$(tail -1 "$MERGE_STDOUT" 2>/dev/null)"
if [[ "$B_RC" -ne 0 || -z "$MERGE_RUN_DIR" || ! -d "$MERGE_RUN_DIR" ]]; then
  MERGE_RUN_DIR="$(find experiments/runs -maxdepth 1 -type d -name "caption_store_merge_${MERGE_RUN_TAG}_*" 2>/dev/null | sort | tail -1)"
  record_stage caption_merge "$MERGE_CMD" "${B_RC:-1}" "$B_START" "$(utc)" "$(jq -nc --arg d "${MERGE_RUN_DIR:-}" '[$d]')"
  fail caption_merge "merge failed rc=$B_RC (merge run dir '${MERGE_RUN_DIR:-unknown}'; see its logs/login.log)"
fi
MERGE_CAPTIONS="${MERGE_RUN_DIR}/captions.jsonl"
MERGE_SUMMARY_PATH="${MERGE_RUN_DIR}/summary.json"
[[ -s "$MERGE_CAPTIONS" && -s "$MERGE_SUMMARY_PATH" ]] \
  || { record_stage caption_merge "$MERGE_CMD" 1 "$B_START" "$(utc)" "$(jq -nc --arg d "$MERGE_RUN_DIR" '[$d]')"; fail caption_merge "merge artifacts missing under $MERGE_RUN_DIR"; }
MERGE_EXPECTED="$(jq -r '.expected_hashes' "$MERGE_SUMMARY_PATH")"
MERGE_N_IMAGES="$(jq -r '.n_images' "$MERGE_SUMMARY_PATH")"
MERGE_COMPLETE="$(jq -r '.coverage_complete' "$MERGE_SUMMARY_PATH")"
log "STAGE B complete: run_dir=$MERGE_RUN_DIR expected_hashes=$MERGE_EXPECTED n_images=$MERGE_N_IMAGES coverage_complete=$MERGE_COMPLETE"
if [[ "$MERGE_COMPLETE" != "true" ]]; then
  record_stage caption_merge "$MERGE_CMD" 1 "$B_START" "$(utc)" "$(jq -nc --arg c "$MERGE_CAPTIONS" --arg s "$MERGE_SUMMARY_PATH" '[$c,$s]')"
  fail caption_merge "merge summary reports coverage_complete=$MERGE_COMPLETE (expected_hashes=$MERGE_EXPECTED n_images=$MERGE_N_IMAGES)"
fi
record_stage caption_merge "$MERGE_CMD" 0 "$B_START" "$(utc)" "$(jq -nc --arg c "$MERGE_CAPTIONS" --arg s "$MERGE_SUMMARY_PATH" '[$c,$s]')"

# =============================================================================
# STAGE C — build QA rows (CPU, login node).  The restriction to the 160 causal
#   pairs / 320 member images happens HERE, against the fixture-backed
#   caption-QA release+key, with the documented --allow-extra-captions carrying
#   the 160 non-causal captions unused (the PI's decision).
# =============================================================================
C_START="$(utc)"
QA_CMD=".venv/bin/python scripts/build_caption_qa_pairs.py --release-manifest ${RELEASE_MANIFEST} --key-file ${RELEASE_KEY} --caption-store ${MERGE_CAPTIONS} --output ${QA_JSONL} --summary ${QA_SUMMARY} --allow-extra-captions"
log "STAGE C command: $QA_CMD"
PYTHONPATH=. .venv/bin/python scripts/build_caption_qa_pairs.py \
  --release-manifest "$RELEASE_MANIFEST" \
  --key-file "$RELEASE_KEY" \
  --caption-store "$MERGE_CAPTIONS" \
  --output "$QA_JSONL" \
  --summary "$QA_SUMMARY" \
  --allow-extra-captions >> "$LOG" 2>&1
C_RC=$?
if [[ "$C_RC" -ne 0 || ! -s "$QA_JSONL" || ! -s "$QA_SUMMARY" ]]; then
  record_stage caption_qa_build "$QA_CMD" "${C_RC:-1}" "$C_START" "$(utc)" '[]'
  fail caption_qa_build "build_caption_qa_pairs.py failed rc=$C_RC (see $LOG)"
fi
QA_PAIRS="$(jq -r '.n_pairs' "$QA_SUMMARY")"
QA_IMAGES="$(jq -r '.n_images' "$QA_SUMMARY")"
QA_ALLOW_EXTRA="$(jq -r '.allow_extra_captions' "$QA_SUMMARY")"
log "STAGE C complete: n_pairs=$QA_PAIRS n_images=$QA_IMAGES allow_extra_captions=$QA_ALLOW_EXTRA -> $QA_JSONL"
record_stage caption_qa_build "$QA_CMD" 0 "$C_START" "$(utc)" "$(jq -nc --arg q "$QA_JSONL" --arg s "$QA_SUMMARY" '[$q,$s]')"
refresh_claim

# =============================================================================
# STAGE D — caption-QA eval: the REGISTERED command (GPU work on an29 gpu3),
#   dispatched detached to the node from this login node.
#   registered: scripts/eval_caption_qa_fliptrack.py --model-path $BASE \
#     --input <qa.jsonl> --output ... --max-new-tokens 32
#   Mechanical resolutions only (same as the E1/E2/E4 runners recorded):
#   .venv/bin/python, PYTHONPATH/TRANSFORMERS_OFFLINE/HF_HOME/CUDA_VISIBLE_DEVICES,
#   and an explicit --metrics-output path.  --max-new-tokens 32 is verbatim.
# =============================================================================
D_START="$(utc)"
EVAL_CMD=".venv/bin/python scripts/eval_caption_qa_fliptrack.py --model-path ${BASE} --input ${QA_JSONL} --output ${PRED_JSONL} --metrics-output ${METRICS_JSON} --max-new-tokens 32"
log "STAGE D command (on ${NODE} with CUDA_VISIBLE_DEVICES=${GPU}): $EVAL_CMD"

cat > "$EVAL_JOB" <<EVALEOF
#!/usr/bin/env bash
# Generated by scripts/run_e3_caption_stress.sh for the registered E3 caption-QA
# eval. Runs on ${NODE}, CUDA_VISIBLE_DEVICES=${GPU}. Registered command verbatim
# with placeholders resolved.
set -uo pipefail
cd "${ROOT}" || exit 1
exec >> "${ROOT}/${EVAL_LOG}" 2>&1
echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) e3 caption-QA eval start host=\$(hostname) pid=\$\$ gpu=${GPU}"
echo "\$\$" > "${ROOT}/${EVAL_PID_FILE}"
export PYTHONUNBUFFERED=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME="${ROOT}/artifacts/hf_home"
export CUDA_VISIBLE_DEVICES=${GPU}
export PYTHONPATH=.
.venv/bin/python scripts/eval_caption_qa_fliptrack.py \\
  --model-path "${BASE}" \\
  --input "${QA_JSONL}" \\
  --output "${PRED_JSONL}" \\
  --metrics-output "${METRICS_JSON}" \\
  --max-new-tokens 32
RC=\$?
echo "\$RC" > "${ROOT}/${EVAL_RC_FILE}"
echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) e3 caption-QA eval end rc=\$RC"
EVALEOF
chmod +x "$EVAL_JOB"

ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "setsid nohup bash '${ROOT}/${EVAL_JOB}' </dev/null >/dev/null 2>&1 & echo dispatched" >> "$LOG" 2>&1
D_DISPATCH_RC=$?
if [[ "$D_DISPATCH_RC" -ne 0 ]]; then
  record_stage caption_qa_eval "$EVAL_CMD" "$D_DISPATCH_RC" "$D_START" "$(utc)" '[]'
  fail caption_qa_eval "could not dispatch the registered eval to $NODE (rc=$D_DISPATCH_RC)"
fi
log "STAGE D dispatched to $NODE gpu$GPU; waiting for $EVAL_RC_FILE (timeout ${EVAL_TIMEOUT_SECONDS}s)"

D_RC=""
D_POLLS=$((EVAL_TIMEOUT_SECONDS / POLL_SECONDS))
for ((i = 1; i <= D_POLLS; i++)); do
  sleep "$POLL_SECONDS"
  if (( i % CLAIM_REFRESH_POLLS == 0 )); then
    if [[ -s "$EVAL_PID_FILE" ]]; then CLAIM_PID_JSON="$(tr -dc '0-9' < "$EVAL_PID_FILE")"; fi
    [[ -n "${CLAIM_PID_JSON:-}" ]] || CLAIM_PID_JSON=null
    refresh_claim
  fi
  if [[ -s "$EVAL_RC_FILE" ]]; then
    D_RC="$(tr -dc '0-9' < "$EVAL_RC_FILE")"
    [[ -n "$D_RC" ]] || D_RC=250   # marker written but unreadable: treat as failure, never as success
    log "STAGE D finished after $((i * POLL_SECONDS))s with rc=$D_RC"
    break
  fi
done
if [[ -z "$D_RC" ]]; then
  record_stage caption_qa_eval "$EVAL_CMD" 1 "$D_START" "$(utc)" '[]'
  fail caption_qa_eval "registered eval did not finish within ${EVAL_TIMEOUT_SECONDS}s (see $EVAL_LOG)"
fi
if [[ "$D_RC" -ne 0 || ! -s "$PRED_JSONL" || ! -s "$METRICS_JSON" ]]; then
  record_stage caption_qa_eval "$EVAL_CMD" "$D_RC" "$D_START" "$(utc)" "$(jq -nc --arg p "$PRED_JSONL" --arg m "$METRICS_JSON" '[$p,$m]')"
  fail caption_qa_eval "registered eval exited rc=$D_RC or produced no predictions/metrics (see $EVAL_LOG)"
fi
PRED_ROWS="$(wc -l < "$PRED_JSONL" | tr -d ' ')"
log "STAGE D complete: $PRED_ROWS prediction rows -> $PRED_JSONL ; metrics -> $METRICS_JSON"
record_stage caption_qa_eval "$EVAL_CMD" 0 "$D_START" "$(utc)" "$(jq -nc --arg p "$PRED_JSONL" --arg m "$METRICS_JSON" --arg l "$EVAL_LOG" '[$p,$m,$l]')"

# =============================================================================
# STAGE Z — release the claim and record
# =============================================================================
release_claim
write_provenance complete "" ""
log "chain artifacts: caption_store=$CAP_RUN_DIR merge=$MERGE_RUN_DIR e3=$RUN_DIR"
log "*** E3 CHAIN COMPLETE — recorded, NOT judged. metrics: $METRICS_JSON (aggregate only); the registered per-type criterion needs a post-hoc join of $PRED_JSONL to $DATA/manifest_causal_pairs.jsonl on pair_id ***"
exit 0
