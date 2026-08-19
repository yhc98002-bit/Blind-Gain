#!/usr/bin/env bash
# Sample per-worker host RSS during a Ray trainer run.
#
# Characterises the growth that OOM-killed ST3 arm 1 at step 39: eight
# `ray::WorkerDict.actor_rollout_ref_generate_sequences` workers reached
# 109-113.6 GB each (~886 GB / 1007 GiB), up from 94.5-98.9 GB at step 19 in the
# prior attempt -- roughly +0.8 GB per worker per step. Whether that is a leak
# or steady-state ramp decides whether recycling the generation workers can
# recover the 100-step budget.
#
# Run ON the node (it reads /proc). Emits one JSON line per sample; join to
# training steps afterwards by timestamp against the run's reward_shadow.jsonl.
#
# Usage: sample_trainer_host_ram.sh OUT_JSONL [INTERVAL_SECONDS]
set -uo pipefail
OUT="${1:?usage: sample_trainer_host_ram.sh OUT_JSONL [INTERVAL]}"
INT="${2:-120}"
PAT="WorkerDict"

mkdir -p "$(dirname "$OUT")"
while true; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  AVAIL_KB=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  TOTAL_KB=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
  # rss in KB per matching worker; grep -v grep drops the pipeline's own grep
  RSS_LIST=$(ps -eo rss,args --no-headers 2>/dev/null \
             | grep -F "$PAT" | grep -v grep | awk '{print $1}' | sort -rn)
  if [ -n "$RSS_LIST" ]; then
    N=$(printf '%s\n' "$RSS_LIST" | wc -l)
    SUM=$(printf '%s\n' "$RSS_LIST" | awk '{s+=$1} END{print s+0}')
    MAX=$(printf '%s\n' "$RSS_LIST" | head -1)
    MIN=$(printf '%s\n' "$RSS_LIST" | tail -1)
  else
    N=0; SUM=0; MAX=0; MIN=0
  fi
  printf '{"ts":"%s","mem_total_bytes":%d,"mem_available_bytes":%d,"worker_count":%d,"worker_rss_sum_bytes":%d,"worker_rss_max_bytes":%d,"worker_rss_min_bytes":%d}\n' \
    "$TS" "$((TOTAL_KB*1024))" "$((AVAIL_KB*1024))" "$N" "$((SUM*1024))" "$((MAX*1024))" "$((MIN*1024))" >> "$OUT"
  sleep "$INT"
done
