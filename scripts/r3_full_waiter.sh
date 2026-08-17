#!/usr/bin/env bash
# Wait for the last two M7 step-100 evaluations (a3_caption, a2_gray) to reach
# status complete, then run the FULL R3 readout over all eight run dirs.
#
# Successor to m7_completion_chain.sh, which gave up loudly on 2026-08-01 after
# (a) its per-arm 30 h TRAIN_WAIT expired 37 minutes before a2_gray finished and
# (b) its ssh-to-an12 eval launches lost ~/.local/bin and died rc=127 on jq.
# Both arms in fact completed at step 100; their manifests are closed, their
# checkpoints merged and index-verified, and their evals launched 2026-08-03
# ~15:15Z from a login shell with PATH exported. This waiter only waits and
# then runs the fail-closed readout; if the readiness gate refuses, the refusal
# is the logged result.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

LOG="$ROOT/logs/r3_full_waiter.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "waiter start"

WAIT_A3=experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z
WAIT_GRAY=experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z

DEADLINE=$(( $(date -u +%s) + 16*3600 ))
while :; do
  n=0
  for d in "$WAIT_A3" "$WAIT_GRAY"; do
    s=$(grep -oE '"status": *"[a-z]+"' "$d/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *complete* ]] && n=$((n+1))
    [[ "$s" == *fail* ]] && { log "FAIL status in $d; stopping"; exit 5; }
  done
  log "step-100 evals complete: $n/2"
  [[ $n -eq 2 ]] && break
  (( $(date -u +%s) > DEADLINE )) && { log "DEADLINE after 16h; stopping"; exit 4; }
  sleep 300
done

log "both complete; running FULL R3 readout"
.venv/bin/python scripts/build_m7_r3_readout.py \
  --step0 a1_real=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z \
  --step0 a2_gray=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z \
  --step0 a2b_noimage=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z \
  --step0 a3_caption=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z \
  --step100 a1_real=experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z \
  --step100 a2b_noimage=experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z \
  --step100 a3_caption="$WAIT_A3" \
  --step100 a2_gray="$WAIT_GRAY" \
  --artifact-dir reports/m7_r3_readout_v1_artifacts \
  --json-output reports/m7_r3_readout_v1.json \
  --markdown-output reports/m7_r3_readout_v1.md \
  >> "$LOG" 2>&1
RC=$?
log "FULL R3 readout rc=$RC"
[[ $RC -eq 0 ]] && log "artifacts: $(ls -la reports/m7_r3_readout_v1.json reports/m7_r3_readout_v1.md 2>&1 | tr '\n' ' ')"
exit $RC
