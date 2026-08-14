#!/usr/bin/env bash
# Storage cleanup 2026-08-14 — unblock the storage-guard deadlock (approved policy:
# archived failed-attempt dirs + non-terminal global_step dirs of runs that are
# complete AND eval-banked AND ledgered; every evaluated/best step kept).
# Live trainer dirs (m7_virl_a2_gray_seed2, m7_virl_a3_caption_seed2) are NOT touched.
set -u
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
REC=$ROOT/reports/storage_cleanup_20260814.md

TARGETS=(
  "$ROOT/checkpoints/c5/c5_a1_real_seed1_7b_attempt1_hostoom_20260803"
  "$ROOT/checkpoints/m7/m7_virl_a2_gray_seed2_attempt1_hostoom_20260810"
  "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed2_attempt1_hostram_20260810"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed1/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed1/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed1/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed1/global_step_80"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed2/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed2/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a1_real_seed2/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed1/global_step_80"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a2b_noimage_seed2/global_step_80"
  "$ROOT/checkpoints/m7/m7_virl_a2_gray_seed1/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a2_gray_seed1/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a2_gray_seed1/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a2_gray_seed1/global_step_80"
  "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed1/global_step_20"
  "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed1/global_step_40"
  "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed1/global_step_60"
  "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed1/global_step_80"
)

# Refuse to run if any target path mentions a live trainer dir.
for t in "${TARGETS[@]}"; do
  case "$t" in
    */m7_virl_a2_gray_seed2/*|*/m7_virl_a3_caption_seed2/*)
      echo "SAFETY ABORT: live trainer dir in target list: $t"; exit 9;;
  esac
done

{
  echo "# Storage cleanup — 2026-08-14"
  echo
  echo "Deadlock: storage guard refusing all checkpoint saves since 2026-08-12"
  echo "(free 63.5 GB < required 55 GB + floor 21.5 GB against 2.5 TiB capacity)."
  echo "Policy (PI-approved 2026-08-14): delete only archived failed-attempt dirs and"
  echo "non-terminal global_step dirs of complete + eval-banked + ledgered runs;"
  echo "keep every evaluated/best step; do not touch live seed-2 trainer dirs,"
  echo "mini_a5, completed c5 runs, pilot, smoke, m5 (those stay on the PI menu)."
  echo
  echo "Kept on purpose: a1_real_seed1 step100 (best+evaluated); a1_real_seed2"
  echo "step80 (best) + step100 (evaluated); every other m7 run's step100;"
  echo "all c5 completed-run steps (C6 evaluated their terminal checkpoints)."
  echo
  echo "| deleted path (repo-relative) | bytes |"
  echo "|---|---|"
} > "$REC"

TOTAL=0
for t in "${TARGETS[@]}"; do
  if [ ! -d "$t" ]; then echo "MISSING (skip): $t"; continue; fi
  B=$(du -sb "$t" | cut -f1)
  rm -rf "$t"
  if [ -e "$t" ]; then echo "DELETE FAILED: $t"; continue; fi
  TOTAL=$((TOTAL + B))
  echo "| ${t#$ROOT/} | $B |" >> "$REC"
  echo "deleted $B  ${t#$ROOT/}"
done

{
  echo
  echo "Total bytes deleted: $TOTAL"
  echo
  echo "Executed $(date -u +%Y-%m-%dT%H:%M:%SZ) on $(hostname) at git $(cd "$ROOT" && git rev-parse --short HEAD)."
} >> "$REC"
echo "TOTAL_BYTES_DELETED=$TOTAL"
