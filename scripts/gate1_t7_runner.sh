#!/usr/bin/env bash
# Gate-1 T7 runner: when an29 frees (last 7B arm trained + merged), run the two
# 8-GPU plumbing smokes sequentially, their audits, the two 1-GPU step-0 reward
# audits, and the summaries — inside the 3-hour window the an29 seed-2 waiter
# holds after the T6 marker. Cleans the claim files each launcher leaves behind.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/gate1_t7_runner.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "T7 runner start"
CLAIMDIR=/dev/shm/blind-gains/gpu_claims
DEADLINE=$(( $(date -u +%s) + 24*3600 ))

# wait for an29 fully free + A1 7B merge verified (same condition the seed-2 waiter uses)
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "DEADLINE"; exit 4; }
  tr=$(ssh -o ConnectTimeout=15 an29 "pgrep -fc 'verl.trainer.mai[n]' || true" 2>/dev/null | head -1)
  mm=$(ssh -o ConnectTimeout=15 an29 "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sort -n | tail -1" 2>/dev/null || echo 999999)
  merged=no
  .venv/bin/python -c "
import json,sys
d=json.load(open('checkpoints/c5/c5_a1_real_seed1_7b/global_step_100/actor/huggingface/model.safetensors.index.json'))
assert d['metadata']['total_size']==16584333312
" 2>/dev/null && merged=yes
  log "an29 trainers=$tr maxmem=${mm}MiB merged=$merged"
  [[ "$tr" == "0" && "${mm:-999999}" -lt 1024 && "$merged" == yes ]] && break
  sleep 300
done

clean_an29_claims() { ssh -o ConnectTimeout=15 an29 "rm -f $CLAIMDIR/an29_gpu*.claim" 2>/dev/null || true; }

for mode in std necessity; do
  log "[$mode] launching plumbing smoke on an29"
  out=$(bash scripts/launch_mini_a5_gate1_plumbing_smoke.sh "$mode" an29 0,1,2,3,4,5,6,7 2>&1 | tail -1)
  log "[$mode] smoke -> $out"
  if [[ "$out" != experiments/runs/* ]]; then log "[$mode] SMOKE LAUNCH REFUSED; stopping"; clean_an29_claims; exit 1; fi
  for i in $(seq 1 24); do
    s=$(grep -oE '"status": *"[a-z]+"' "$out/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *complete* ]] && break
    [[ "$s" == *fail* ]] && { log "[$mode] SMOKE FAILED"; clean_an29_claims; exit 1; }
    sleep 120
  done
  log "[$mode] smoke status: $(grep -oE '\"status\": *\"[a-z]+\"' "$out/run_manifest.json" | tail -1)"
  clean_an29_claims
  .venv/bin/python scripts/audit_mini_a5_gate1_plumbing_smoke.py --run-dir "$out" --mode "$mode" \
    --output-json "reports/mini_a5_gate1_smoke_audit_${mode}_v1.json" >> "$LOG" 2>&1 \
    || { log "[$mode] SMOKE AUDIT FAILED (or CLI differs — check usage); stopping"; exit 1; }
  log "[$mode] smoke audit written"
done

for mode in std necessity; do
  log "[$mode] step-0 reward audit on an29 gpu 0"
  out=$(bash scripts/launch_mini_a5_gate1_step0.sh "$mode" an29 0 2>&1 | tail -1)
  log "[$mode] step0 -> $out"
  if [[ "$out" != experiments/runs/* ]]; then log "[$mode] STEP0 LAUNCH REFUSED; stopping"; clean_an29_claims; exit 1; fi
  for i in $(seq 1 30); do
    s=$(grep -oE '"status": *"[a-z]+"' "$out/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *complete* ]] && break
    [[ "$s" == *fail* ]] && { log "[$mode] STEP0 FAILED"; clean_an29_claims; exit 1; }
    sleep 120
  done
  clean_an29_claims
  .venv/bin/python scripts/summarize_mini_a5_gate1_step0.py --run-dir "$out" --mode "$mode" \
    --output-json "reports/mini_a5_gate1_step0_summary_${mode}_v1.json" >> "$LOG" 2>&1 \
    || { log "[$mode] STEP0 SUMMARY FAILED (or CLI differs); stopping"; exit 1; }
done

log "*** T7 COMPLETE: both smokes audited, both step-0 summaries written. Gate-1 main arms are launch-ready. ***"
