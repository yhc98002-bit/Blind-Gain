#!/usr/bin/env bash
# Wait for the four M7 step-0 held-out evaluations to finalize, then run the
# R3 partial readout via the invocation its author validated
# (tmp/run_r3_partial_20260730.sh: step-0 columns + q_bar only; --partial mode
# refuses every gain/recovery/rho estimand by construction).
#
# CPU-only, touches no GPU. Fail-closed: if the readout's readiness gate
# refuses (e.g. a manifest never finalizes), that refusal is the logged result.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

LOG="$ROOT/logs/r3_partial_waiter.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "waiter start"

DEADLINE=$(( $(date -u +%s) + 8*3600 ))
while :; do
  n_complete=0
  for d in experiments/runs/m7_step0_heldout_base_*_an29_2026*; do
    s=$(grep -oE '"status": *"[a-z]+"' "$d/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *complete* ]] && n_complete=$((n_complete+1))
  done
  log "manifests complete: $n_complete/4"
  [[ $n_complete -eq 4 ]] && break
  if (( $(date -u +%s) > DEADLINE )); then
    log "DEADLINE: not all manifests finalized within 8h; stopping without running the readout"
    exit 4
  fi
  sleep 300
done

log "all four complete; running the author-validated partial invocation"
bash tmp/run_r3_partial_20260730.sh >> "$LOG" 2>&1
RC=$?
log "partial readout rc=$RC"
if [[ $RC -eq 0 ]]; then
  log "artifacts: $(ls -la reports/m7_r3_readout_v1_partial.json reports/m7_r3_readout_v1_partial.md 2>&1)"
fi
exit $RC
