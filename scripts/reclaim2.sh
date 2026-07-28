#!/usr/bin/env bash
# Storage reclamation, pass 2 — the AudioDiffusion runtime tree.
#
# Deletes benchmark_v2_runtime: downloaded public model weights
# (stable-audio-open-1.0, including a .partial duplicate of the same weights)
# plus two Python environments. Everything in it is re-downloadable or
# rebuildable, and the AudioDiffusion project is shelved.
#
# DELIBERATELY NOT DELETED: the AudioDiffusion research trees. Their large files
# are rater bundles and listening-review packets -- human-annotation artifacts
# that cannot be regenerated. Per the PI's "retain some of the experimental
# results", those are the results worth retaining, and at ~12.5 GiB they are not
# what is constraining the quota.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
Q=/XYFS02/HDD_POOL/paratera_xy/pxy1289
LOG=$Q/HaocunYe/Research/BlindGain/reports/storage_reclamation_20260728.md
QUOTA_KIB=1572864000

used_kib() {
  local v
  v=$(lfs quota -p 2228473301 "$Q" 2>/dev/null | awk '$1 ~ /^[0-9]+$/ {print $1; exit}')
  if ! printf '%s' "$v" | grep -Eq '^[0-9]+$'; then
    echo "FATAL: could not parse project quota (got: '$v')" >&2
    exit 1
  fi
  printf '%s' "$v"
}
gib() { echo $(( $1 / 1048576 )); }

# refuse to run while pass 1 is still deleting
if pgrep -f "reclaim1.s[h]" > /dev/null; then
  echo "pass 1 still running; not starting pass 2"
  exit 0
fi

start=$(used_kib)
echo "pass 2 start: used $(gib $start) GiB, free $(gib $((QUOTA_KIB - start))) GiB"

T=$Q/HaocunYe/Research/benchmark_v2_runtime
if [ -e "$T" ]; then
  before=$(used_kib)
  rm -rf "$T"
  sleep 8
  after=$(used_kib)
  freed=$(( (before - after) / 1048576 ))
  echo "| \`HaocunYe/Research/benchmark_v2_runtime\` | downloaded stable-audio-open-1.0 weights (plus a .partial duplicate) and two Python environments; all re-downloadable, project shelved | $freed |" >> "$LOG"
  echo "  freed ${freed} GiB : benchmark_v2_runtime"
else
  echo "  skip (absent): benchmark_v2_runtime"
fi

end=$(used_kib)
{
  echo
  echo "## Pass 2"
  echo
  echo "Reclaimed a further $(gib $((start - end))) GiB. Free after both passes:"
  echo "**$(gib $((QUOTA_KIB - end))) GiB** of $(gib $QUOTA_KIB) GiB."
  echo
  echo "### Deliberately retained"
  echo
  echo "The AudioDiffusion research trees were pruned of nothing. Their large"
  echo "files are rater bundles and listening-review packets"
  echo "(\`t2_aprime_core.zip\`, \`t6_calibration.zip\`,"
  echo "\`pi_listening_review_packet_20260529.zip\`, and similar) — human-annotation"
  echo "artifacts that cannot be regenerated. At ~12.5 GiB they are not what"
  echo "constrains the quota, and they are the experimental results most worth"
  echo "keeping if the project is ever revived."
} >> "$LOG"

echo "PASS2 TOTAL: $(gib $((start - end))) GiB"
echo "FREE NOW: $(gib $((QUOTA_KIB - end))) GiB"
