#!/usr/bin/env bash
# ST3 endpoint readout chain: merge -> evaluate one arm's banked checkpoints.
#
# Usage: st3_readout_chain.sh CKPT_LABEL NODE
#   e.g. st3_readout_chain.sh st3_igpo_seed1_7b an29
#
# Evaluates steps 10/20/30 on the FROZEN r2 hierarchy instrument in both the
# real and matched gray (blind) conditions, six evals in parallel on GPUs 0-5 of
# NODE, so the arm is directly comparable to the other arm's columns.
#
# Every eval is launched DETACHED with a settle delay: run_hier_p2_openform.sh
# loops its 12 cells in the foreground, so an eval sharing an ssh session dies
# with that session (this cost a readout at 8/12 cells on 2026-08-18).
set -uo pipefail
LABEL="${1:?usage: st3_readout_chain.sh CKPT_LABEL NODE}"
NODE="${2:?usage: st3_readout_chain.sh CKPT_LABEL NODE}"
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"     # jq lives here; ssh command lists lack it
LOG="$ROOT/logs/st3_readout_chain_${LABEL}_$(date -u +%Y%m%dT%H%M%SZ).log"
DATA_DIR=data/hier_v1_dev_r2
TAG=hier_d1_st3

say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
hf()  { echo "checkpoints/st3/$LABEL/global_step_$1/actor/huggingface"; }

# --- merge every step that is not already merged -----------------------------
for s in 30 20 10; do
  d=$(hf "$s")
  if [ -f "$d/model.safetensors.index.json" ]; then say "step_$s already merged"; continue; fi
  [ -d "checkpoints/st3/$LABEL/global_step_$s/actor" ] || { say "step_$s absent"; continue; }
  say "merging step_$s"
  bash scripts/launch_easyr1_checkpoint_merge.sh "$NODE" \
      "checkpoints/st3/$LABEL/global_step_$s/actor" "${LABEL}_step$s" >>"$LOG" 2>&1
done

# --- evaluate: 3 steps x 2 conditions across GPUs 0-5 ------------------------
gpu=0
for s in 30 20 10; do
  d=$(hf "$s")
  for _ in $(seq 1 60); do [ -f "$d/model.safetensors.index.json" ] && break; sleep 30; done
  if [ ! -f "$d/model.safetensors.index.json" ]; then say "step_$s merge TIMEOUT; skip"; gpu=$((gpu+2)); continue; fi
  for mode in real gray; do
    say "launch eval ${LABEL} step_$s mode=$mode gpu=$gpu"
    ( setsid nohup bash scripts/run_hier_p2_openform.sh \
        "${LABEL}_step$s" "$d" "$NODE" "$gpu" "$mode" "$DATA_DIR" "$TAG" \
        >/dev/null 2>&1 </dev/null & )
    sleep 25
    gpu=$((gpu+1))
  done
done

# --- wait for all 12/12 ------------------------------------------------------
for _ in $(seq 1 180); do
  pending=0
  for d in experiments/runs/${TAG}_${LABEL}_step*; do
    [ -d "$d" ] || continue
    [ "$(ls "$d"/*/metrics.json 2>/dev/null | wc -l)" -eq 12 ] || pending=$((pending+1))
  done
  [ "$pending" -eq 0 ] && { say "all $LABEL evals complete"; exit 0; }
  sleep 60
done
say "eval wait TIMEOUT"
