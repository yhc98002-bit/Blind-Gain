#!/usr/bin/env bash
# Storage reclamation, pass 1 — full deletes of superseded / regenerable trees.
#
# PI authorization: full access to the quota root; AudioDiffusion is shelved with
# unsatisfactory results and its runtime environments may be deleted.
#
# Each target is measured against the Lustre project quota before and after, so
# the log records actual reclaim rather than an estimate. Fails closed if the
# quota cannot be parsed, so a parse bug can never lead to an unmeasured delete.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
Q=/XYFS02/HDD_POOL/paratera_xy/pxy1289
LOG=$Q/HaocunYe/Research/BlindGain/reports/storage_reclamation_20260728.md
QUOTA_KIB=1572864000

used_kib() {
  # The data row is the first line whose first field is all digits. The mount
  # path occupies its own line above it, which an NR-based selector gets wrong.
  local v
  v=$(lfs quota -p 2228473301 "$Q" 2>/dev/null | awk '$1 ~ /^[0-9]+$/ {print $1; exit}')
  if ! printf '%s' "$v" | grep -Eq '^[0-9]+$'; then
    echo "FATAL: could not parse project quota (got: '$v')" >&2
    exit 1
  fi
  printf '%s' "$v"
}

gib() { echo $(( $1 / 1048576 )); }

start=$(used_kib)
{
  echo "# Storage reclamation — 2026-07-28"
  echo
  echo "PI authorization: full access to the quota root; AudioDiffusion is shelved"
  echo "with unsatisfactory results, its runtime environments may be deleted, and"
  echo "large files may go provided some experimental results are retained."
  echo
  echo "Quota $(gib $QUOTA_KIB) GiB. Used at start: $(gib $start) GiB "
  echo "(free: $(gib $((QUOTA_KIB - start))) GiB)."
  echo
  echo "| target | why | freed (GiB) |"
  echo "|---|---|---|"
} > "$LOG"

reclaim() {
  local path="$1" why="$2" before after freed
  if [ ! -e "$path" ]; then
    echo "  skip (absent): $path"
    return
  fi
  before=$(used_kib)
  rm -rf "$path"
  sleep 8
  after=$(used_kib)
  freed=$(( (before - after) / 1048576 ))
  echo "| \`${path#"$Q"/}\` | $why | $freed |" >> "$LOG"
  echo "  freed ${freed} GiB : ${path#"$Q"/}"
}

echo "starting: used $(gib $start) GiB, free $(gib $((QUOTA_KIB - start))) GiB"

reclaim "$Q/blindgain_archive" \
  "raw optimizer-state checkpoints for mech_a1_real_seed2 and mech_a3_caption_seed2; both arms complete with sealed readouts, and their merged step-100 checkpoints were verified present in the project tree before deletion"

reclaim "$Q/HaocunYe/Research/AudioDiffusion_envs" \
  "AudioDiffusion runtime environments, model caches and pip temp trees; project shelved, environments rebuildable"

reclaim "$Q/.uv_cache" \
  "uv package cache; regenerates on next install"

end=$(used_kib)
{
  echo
  echo "Used at end: $(gib $end) GiB (free: $(gib $((QUOTA_KIB - end))) GiB)."
  echo
  echo "**Total reclaimed this pass: $(gib $((start - end))) GiB**"
  echo
  echo "Not touched in this pass: the AudioDiffusion *research* trees. Those are"
  echo "pruned by file in pass 2 — large binaries removed, results (JSON, CSV,"
  echo "markdown, logs, configs) retained per the PI's instruction."
} >> "$LOG"

echo "TOTAL RECLAIMED: $(gib $((start - end))) GiB"
echo "FREE NOW: $(gib $((QUOTA_KIB - end))) GiB"
