#!/usr/bin/env bash
# E1b with-image column — an12 GPUs 4-7 ONLY, four cells at a time.
#
# Reuses scripts/launch_vlmevalkit_eval.sh so each cell gets the project's normal
# vlmevalkit manifest, hashes and validation rather than a bespoke invocation.
# That launcher is fire-and-forget, so this wrapper supplies the batching: it
# starts one cell per permitted GPU and waits for all four before the next batch.
#
# M7 holds GPUs 0-3 at its registered 4-GPU width and is never touched.
set -uo pipefail

# jq lives in ~/.local/bin, which a non-interactive shell does not inherit;
# launch_vlmevalkit_eval.sh needs it to write the run manifest.
export PATH="$HOME/.local/bin:$PATH"
command -v jq >/dev/null || { echo "ABORT: jq not on PATH" >&2; exit 4; }

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOGDIR="$ROOT/logs/e1b_image_$STAMP"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/orchestrator.log"

for g in 4 5 6 7; do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g" 2>/dev/null || echo 0)
  if [[ "${used:-0}" -gt 5000 ]]; then
    echo "ABORT: GPU $g holds ${used} MiB; E1b image column will not contend." | tee -a "$LOG" >&2
    exit 3
  fi
done
echo "isolation OK: GPUs 4-7 free, M7 untouched on 0-3" | tee -a "$LOG"

mapfile -t QUEUE < <(ls configs/eval/e1b/e1b_*_image.json | sort)
echo "queue: ${#QUEUE[@]} with-image cells" | tee -a "$LOG"

GPUS=(4 5 6 7)
i=0
while (( i < ${#QUEUE[@]} )); do
  pids=() ; dirs=()
  for gpu in "${GPUS[@]}"; do
    (( i < ${#QUEUE[@]} )) || break
    cfg="${QUEUE[$i]}"
    tag="$(basename "$cfg" .json)"          # e1b_<arm>_seed<n>_<bench>_image
    out="$(bash scripts/launch_vlmevalkit_eval.sh an12 "$gpu" "$cfg" "$tag" 2>&1)"
    rd="$(echo "$out" | head -1)"
    pf="$(echo "$out" | grep -o 'pid_file=[^ ]*' | cut -d= -f2)"
    if [[ -f "$ROOT/$pf" ]]; then
      pids+=("$(cat "$ROOT/$pf")") ; dirs+=("$rd")
      echo "$(date -u +%H:%M:%SZ) started gpu$gpu $tag -> $rd" >> "$LOG"
    else
      echo "$(date -u +%H:%M:%SZ) LAUNCH-FAIL gpu$gpu $tag :: $out" >> "$LOG"
    fi
    ((i++))
  done

  # wait for this batch
  for p in "${pids[@]}"; do
    while kill -0 "$p" 2>/dev/null; do sleep 15; done
  done
  for d in "${dirs[@]}"; do
    st=$(grep -o '"status": *"[a-z]*"' "$ROOT/$d/run_manifest.json" 2>/dev/null | tail -1)
    echo "$(date -u +%H:%M:%SZ) finished $d $st" >> "$LOG"
  done
  echo "$(date -u +%H:%M:%SZ) batch done ($i/${#QUEUE[@]})" >> "$LOG"
done

echo "ALL E1b IMAGE CELLS FINISHED $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
