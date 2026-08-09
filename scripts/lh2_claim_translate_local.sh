#!/usr/bin/env bash
# Runs ON an12: rewrite any plain-text LH2 claim files under /dev/shm into the
# JSON shape the M7 GPU-scope guard parses. run_id and gpu copied verbatim.
set -u
export PATH="$HOME/.local/bin:$PATH"
CLAIMDIR=/dev/shm/blind-gains/gpu_claims
for g in 0 1 2 3; do
  f="$CLAIMDIR/an12_gpu${g}.claim"
  [ -f "$f" ] || continue
  head -c1 "$f" | grep -q '{' && continue
  rid=$(head -1 "$f")
  case "$rid" in
    lh2_seed2_*)
      jq -nc --argjson gpu "$g" --arg run_id "$rid" \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{gpu:$gpu, run_id:$run_id, pid:null, eval_run_dir:"", written_utc:$ts, written_by:"lh2_claim_normalizer"}' \
        > "$f.tmp" && mv "$f.tmp" "$f"
      ;;
  esac
done
