#!/usr/bin/env bash
# LH2 stage-1 segment chain: four 50-step segments (0->50->100->150->200) of the
# registered second-seed anchor run, per docs/registered_lh2_stage1_v1.md.
#
# Run detached on a login node (it drives an12 over ssh):
#   setsid nohup bash scripts/lh2_segment_chain.sh \
#     >> logs/lh2_segment_chain.launcher.log 2>&1 < /dev/null &
#
# Gates before segment 1 (all fail-closed, registration section 6):
#   - reports/c5_r4_readout_v1.json exists (R4 arm cells + readout finished
#     with an12 0-3 — never races the endgame waiter's eval cells)
#   - scripts/check_lh2_config_diff.py exits 0
#   - every git-tracked registered file byte-clean vs HEAD; EasyR1 r1v prompt /
#     reward and the base-model index match their registered sha256 pins
#   - an12 GPUs 0-3 all < 1 GiB used and no blind_solvability eval procs
#   - >= 650 GiB host RAM available (registered precondition)
#   - claim files written for GPUs 0-3 before launch
#
# Between segments (registration section 3): the previous boundary checkpoint
# must pass the hash-verified raw-state audit
# (scripts/audit_easyr1_resume_checkpoint.py: expected step, world_size 4,
# 4 model + 4 optimizer + 4 extra-state shards, per-file sha256 manifest,
# stable-during-hash) validated by the same jq contract the M5 recovery
# launcher enforces. A failed or absent audit blocks the next segment.
# I10 fixture for this gate: scripts/lh2_chain_boundary_fixture.sh
# (artifact reports/lh2_chain_boundary_fixture_v1.json).
#
# Segments never add optimizer budget: trainer.max_steps is the cumulative
# target (M5 pattern). A crashed segment is a deviations-log line and needs
# human attention; relaunching this chain resumes from the last hash-verified
# boundary in a new immutable run directory (stage id persists in
# logs/lh2_stage1_stage_run_id).
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"
NODE=an12
LOG="$ROOT/logs/lh2_segment_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "chain start (pid $$ on $(hostname))"

CONFIG="$ROOT/configs/train/lh2_anchor_seed2_3b_geo3k.yaml"
REGISTRATION="docs/registered_lh2_stage1_v1.md"
CKROOT="$ROOT/checkpoints/lh2_anchor_seed2_3b_geo3k"
STAGE_ID_FILE="$ROOT/logs/lh2_stage1_stage_run_id"
CLAIMDIR=/dev/shm/blind-gains/gpu_claims
GATE_DEADLINE=$(( $(date -u +%s) + 8*24*3600 ))

# Registered sha256 pins (registration section 7) for inputs outside git.
PIN_JINJA=f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca
PIN_REWARD=694c4197e8dd5088732b702dc4796f80a10319a9abfc125d2bc3c024aa097c5b
PIN_MODEL_INDEX=c7dd78a4c6bea60b51332f1baf37b8f8124ecab2c35395a29a29825bf2619768

if [[ -s "$STAGE_ID_FILE" ]]; then
  STAGE_RUN_ID=$(cat "$STAGE_ID_FILE")
  log "resuming stage run id $STAGE_RUN_ID"
else
  STAGE_RUN_ID="lh2_anchor_seed2_stage1_$(date -u +%Y%m%dT%H%M%SZ)"
  echo "$STAGE_RUN_ID" > "$STAGE_ID_FILE"
  log "new stage run id $STAGE_RUN_ID"
fi
STAGE_CKPT="$CKROOT/$STAGE_RUN_ID"
TRACKER="$STAGE_CKPT/checkpoint_tracker.json"

tracker_step() { jq -er '.last_global_step' "$TRACKER" 2>/dev/null || echo 0; }

pin_ok() { [[ "$(sha256sum "$1" 2>/dev/null | awk '{print $1}')" == "$2" ]]; }

wait_gate1() {
  while :; do
    (( $(date -u +%s) > GATE_DEADLINE )) && { log "GATE DEADLINE — no launch"; exit 4; }
    if [[ ! -f "$ROOT/reports/c5_r4_readout_v1.json" ]]; then
      log "gate: R4 readout not yet on disk"; sleep 600; continue
    fi
    "$PY" scripts/check_lh2_config_diff.py >/dev/null 2>&1 \
      || { log "gate: config diff checker FAILED — fail-closed stop"; exit 5; }
    git diff --quiet HEAD -- "$REGISTRATION" "$CONFIG" \
        configs/train/anchor_a0_recipe_3b_geo3k.yaml \
        configs/train/m5_anchor_longhorizon_400.yaml \
        scripts/check_lh2_config_diff.py scripts/lh2_adversarial_fixture.py \
        scripts/audit_easyr1_resume_checkpoint.py \
        reports/lh2_config_diff_check_v1.json reports/lh2_adversarial_fixture_v1.json \
        reports/m5b_trajectory_v1.json reports/m5_host_memory_incident_v1.md \
      || { log "gate: registered files dirty vs HEAD — fail-closed stop"; exit 5; }
    pin_ok "$ROOT/artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja" "$PIN_JINJA" \
      || { log "gate: r1v.jinja hash != registered pin — fail-closed stop"; exit 5; }
    pin_ok "$ROOT/artifacts/repos/EasyR1/examples/reward_function/r1v.py" "$PIN_REWARD" \
      || { log "gate: r1v.py hash != registered pin — fail-closed stop"; exit 5; }
    pin_ok "$ROOT/artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct/model.safetensors.index.json" "$PIN_MODEL_INDEX" \
      || { log "gate: base model index hash != registered pin — fail-closed stop"; exit 5; }
    local bad=0 g used
    for g in 0 1 2 3; do
      used=$(ssh -o ConnectTimeout=15 "$NODE" "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g" 2>/dev/null | head -1)
      used=${used:-999999}
      [[ "$used" -ge 1024 ]] && bad=1
    done
    local procs ram
    procs=$(ssh -o ConnectTimeout=15 "$NODE" "pgrep -fc 'run_blind_solvabilit[y]|run_manifest_blin[d]' || true" 2>/dev/null | head -1)
    procs=${procs:-1}
    ram=$(ssh -o ConnectTimeout=15 "$NODE" "free -g | sed -n 2p | awk '{print \$7}'" 2>/dev/null | head -1)
    ram=${ram:-0}
    log "gate: gpus_busy=$bad eval_procs=$procs host_avail=${ram}GB"
    if [[ "$bad" -eq 0 && "$procs" == "0" && "$ram" -ge 650 ]]; then return 0; fi
    sleep 600
  done
}

write_claims() {
  local run_id="$1" g
  for g in 0 1 2 3; do
    ssh -o ConnectTimeout=15 "$NODE" "mkdir -p $CLAIMDIR && printf '%s\n%s\n%s\n' '$run_id' 'pid pending' \"\$(date -u +%s)\" > $CLAIMDIR/an12_gpu${g}.claim"
  done
}
clear_claims() { local g; for g in 0 1 2 3; do ssh -o ConnectTimeout=15 "$NODE" "rm -f $CLAIMDIR/an12_gpu${g}.claim"; done; }

audit_boundary() {  # step out_dir  -> 0 iff the boundary checkpoint passes the registered audit
  local step="$1" out_dir="$2"
  local ck="$STAGE_CKPT/global_step_${step}"
  local aj="$out_dir/boundary_checkpoint_audit_step${step}.json"
  local as="$out_dir/boundary_checkpoint_audit_step${step}.sha256"
  log "boundary audit: $ck"
  "$PY" scripts/audit_easyr1_resume_checkpoint.py \
      --checkpoint-dir "$ck" --expected-step "$step" --expected-world-size 4 \
      --output-json "$aj" --output-sha256 "$as" >> "$LOG" 2>&1 \
    || { log "boundary audit FAILED (tool) for step $step — blocking"; return 1; }
  jq -e --argjson step "$step" '
      (.status=="pass") and (.expected_step==$step) and (.world_size==4) and
      (.model_rank_count==4) and (.optimizer_rank_count==4) and
      (.extra_state_rank_count==4) and (.files_stable_during_hash==true)
    ' "$aj" >/dev/null \
    || { log "boundary audit FAILED (contract) for step $step — blocking"; return 1; }
  local trk; trk=$(tracker_step)
  [[ "$trk" == "$step" ]] || { log "tracker=$trk != boundary $step — blocking"; return 1; }
  log "boundary audit PASS for step $step ($aj)"
  return 0
}

run_segment() {  # n start_step target_step
  local n="$1" start="$2" target="$3"
  local run_id="lh2_seed2_seg${n}_an12_$(date -u +%Y%m%dT%H%M%SZ)"
  local run_dir="experiments/runs/$run_id"
  mkdir -p "$run_dir/logs"
  local load_arg="" load_path=null
  if [[ "$start" -gt 0 ]]; then
    audit_boundary "$start" "$run_dir" || return 1
    load_path="$STAGE_CKPT/global_step_${start}"
    load_arg="trainer.load_checkpoint_path=$load_path"
  fi
  cp "$CONFIG" "$run_dir/effective_config.yaml"
  local remote_cmd="cd $ROOT && mkdir -p $run_dir/logs /dev/shm/bgray/${run_id##*_} && (setsid nohup env PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 RAY_TMPDIR=/dev/shm/bgray/${run_id##*_} RAY_DEDUP_LOGS=0 CUDA_VISIBLE_DEVICES=0,1,2,3 EASYR1_ATTN_IMPLEMENTATION=sdpa HF_HOME=$ROOT/artifacts/hf_home HF_DATASETS_CACHE=$ROOT/artifacts/hf_home/datasets TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH=$ROOT/artifacts/repos/EasyR1 $PY -u -m verl.trainer.main config=$ROOT/$run_dir/effective_config.yaml trainer.max_steps=$target trainer.experiment_name=$run_id trainer.save_checkpoint_path=$STAGE_CKPT $load_arg > $run_dir/logs/an12.log 2>&1 < /dev/null & echo \$! > $run_dir/logs/pid)"
  jq -n --arg run_id "$run_id" --arg node "$NODE" --arg stage_run_id "$STAGE_RUN_ID" \
    --arg registration "$REGISTRATION" --arg git_hash "$(git rev-parse HEAD)" \
    --arg config "$CONFIG" --arg config_sha256 "$(sha256sum "$CONFIG" | awk '{print $1}')" \
    --argjson data_seed 2 --argjson start "$start" --argjson target "$target" \
    --arg save "$STAGE_CKPT" --arg load "$load_path" --arg command "$remote_cmd" \
    '{schema:"blind-gains.lh2-segment-manifest.v1", run_id:$run_id, node:$node,
      stage_run_id:$stage_run_id, registration:$registration, git_hash:$git_hash,
      config_path:$config, config_sha256:$config_sha256, data_seed:$data_seed,
      gpu_ids:[0,1,2,3], status:"running",
      segment:{start_step:$start, target_step:$target},
      save_checkpoint_path:$save, load_checkpoint_path:$load,
      command:$command, launched_at_utc:(now|todate)}' > "$run_dir/run_manifest.json"
  write_claims "$run_id"
  log "[seg$n] launching $run_id: steps $start -> $target"
  ssh -o ConnectTimeout=20 "$NODE" "$remote_cmd" \
    || { clear_claims; log "[seg$n] LAUNCH SSH FAILED"; return 1; }
  sleep 300
  local pid alive fatal
  pid=$(head -1 "$run_dir/logs/pid" 2>/dev/null); pid=${pid:-0}
  alive=$(ssh -o ConnectTimeout=15 "$NODE" "if kill -0 $pid 2>/dev/null || pgrep -f 'experiment_nam[e]=$run_id' >/dev/null 2>&1; then echo yes; else echo no; fi" 2>/dev/null | head -1)
  alive=${alive:-unknown}
  fatal=$(grep -ciE 'Traceback|OutOfMemoryError|ncclSystemError' "$run_dir/logs/an12.log" 2>/dev/null | head -1)
  fatal=${fatal:-0}
  log "[seg$n] pid=$pid alive=$alive fatal=$fatal after 5 min"
  [[ "$alive" == yes && "$fatal" == 0 ]] || { clear_claims; log "[seg$n] LAUNCH UNHEALTHY"; return 1; }
  while :; do
    local t2
    t2=$(tracker_step)
    alive=$(ssh -o ConnectTimeout=15 "$NODE" "if kill -0 $pid 2>/dev/null || pgrep -f 'experiment_nam[e]=$run_id' >/dev/null 2>&1; then echo yes; else echo no; fi" 2>/dev/null | head -1)
    alive=${alive:-unknown}
    fatal=$(grep -ciE 'Traceback|OutOfMemoryError|ncclSystemError' "$run_dir/logs/an12.log" 2>/dev/null | head -1)
    fatal=${fatal:-0}
    log "[seg$n] tracker=$t2 alive=$alive fatal=$fatal"
    if [[ "$alive" == unknown ]]; then sleep 900; continue; fi
    if [[ "$t2" -ge "$target" && "$alive" == no ]]; then
      clear_claims; log "[seg$n] COMPLETE at $target"; return 0
    fi
    if [[ "$alive" == no && "$t2" -lt "$target" ]]; then
      clear_claims
      log "[seg$n] TRAINER DIED at tracker=$t2 before $target (fatal=$fatal). Deviations-log line; relaunch this chain to resume from the last hash-verified boundary — NOT auto-retrying."
      return 1
    fi
    sleep 900
  done
}

wait_gate1
log "all gates passed; stage checkpoint root $STAGE_CKPT"
cur=$(tracker_step)
if (( cur % 50 != 0 )); then
  log "tracker=$cur is not a 50-step boundary — human attention"; exit 6
fi
for tgt in 50 100 150 200; do
  cur=$(tracker_step)
  if (( cur >= tgt )); then log "segment to $tgt already complete (tracker=$cur)"; continue; fi
  if (( cur != tgt - 50 )); then log "tracker=$cur cannot start segment to $tgt — human attention"; exit 6; fi
  n=$(( tgt / 50 ))
  run_segment "$n" "$cur" "$tgt" || { log "STOPPED at segment $n"; exit 1; }
done
TERMINAL_DIR="experiments/runs/lh2_seed2_stage1_terminal_audit_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$TERMINAL_DIR"
audit_boundary 200 "$TERMINAL_DIR" || { log "terminal step-200 audit FAILED — human attention"; exit 7; }
log "*** LH2 STAGE 1 TRAINING COMPLETE (step 200, boundary hash-verified). Registered evals at 100/150/200 and the step-200 go/no-go are the next round's work. ***"
