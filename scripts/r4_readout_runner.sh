#!/usr/bin/env bash
# Run the registered R4 readout the moment all four arm-cell state files exist
# and their manifests are complete. Uses the exact handoff CLI documented by the
# readout build; the script itself is fail-closed (registered hashes, item
# identity, decoding seed all enforced internally), so this runner only waits
# and invokes.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/r4_readout_runner.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "runner start"

DEADLINE=$(( $(date -u +%s) + 30*3600 ))
CELLS=(cell_a1_real_real cell_a1_real_gray cell_a2_gray_real cell_a2_gray_gray)
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "DEADLINE 30h; stopping"; exit 4; }
  n=0
  for c in "${CELLS[@]}"; do
    d=$(cat "logs/c5_endgame_state/$c" 2>/dev/null) || continue
    [[ -n "$d" ]] || continue
    s=$(grep -oE '"status": *"[a-z]+"' "$d/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *complete* ]] && n=$((n+1))
    [[ "$s" == *fail* ]] && { log "FAIL in $c ($d); stopping"; exit 5; }
  done
  log "arm cells complete: $n/4"
  [[ $n -eq 4 ]] && break
  sleep 300
done

log "all cells complete; running the registered R4 readout"
.venv/bin/python scripts/build_c5_r4_readout.py \
  --cell base:real=experiments/runs/blind_solvability_v2_c5_7b_base_real_an29_20260731T123739Z \
  --cell base:gray=experiments/runs/blind_solvability_v2_c5_7b_base_gray_an29_20260731T123835Z \
  --cell a1_real:real="$(cat logs/c5_endgame_state/cell_a1_real_real)" \
  --cell a1_real:gray="$(cat logs/c5_endgame_state/cell_a1_real_gray)" \
  --cell a2_gray:real="$(cat logs/c5_endgame_state/cell_a2_gray_real)" \
  --cell a2_gray:gray="$(cat logs/c5_endgame_state/cell_a2_gray_gray)" \
  --json-output reports/c5_r4_readout_v1.json \
  --markdown-output reports/c5_r4_readout_v1.md \
  --artifact-dir reports/c5_r4_readout_v1_artifacts \
  >> "$LOG" 2>&1
RC=$?
log "R4 readout rc=$RC"
[[ $RC -eq 0 ]] && log "*** R4 READOUT COMPLETE — PAPER 1 LADDER CLOSED (pending collection) ***"
exit $RC
