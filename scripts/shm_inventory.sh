#!/usr/bin/env bash
# READ-ONLY inventory of a node's /dev/shm, which is RAM-backed: bytes here are
# host memory, not disk, so stale segments shrink the budget that OOM-kills
# trainers. Prints size, mtime, and whether each entry is held open by a live
# process, so a cleanup pass can tell stale from in-use.
#
# Usage: shm_inventory.sh            (run ON the node; /dev/shm is node-local)
set -uo pipefail
UID_NUM=$(id -u)

echo "=== df /dev/shm ==="
df -h /dev/shm | tail -1

echo
echo "=== entries by size ==="
for e in /dev/shm/*; do
  [ -e "$e" ] || continue
  sz=$(du -sh "$e" 2>/dev/null | cut -f1)
  mt=$(stat -c %y "$e" 2>/dev/null | cut -d' ' -f1)
  own=$(stat -c %u "$e" 2>/dev/null)
  printf '%8s  %s  uid=%s  %s\n' "$sz" "$mt" "$own" "$e"
done | sort -h

echo
echo "=== ray tmpdirs of live processes (these must NOT be touched) ==="
for p in $(pgrep -u "$UID_NUM" -f ray 2>/dev/null); do
  tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null \
    | grep -E '^(RAY_TMPDIR|TMPDIR)=' || true
done | sort -u

echo
echo "=== /dev/shm paths currently held open ==="
for p in $(ls /proc 2>/dev/null | grep -E '^[0-9]+$'); do
  ls -l "/proc/$p/fd" 2>/dev/null | grep -o '/dev/shm/[^ ]*'
  tr '\0' '\n' < "/proc/$p/maps" 2>/dev/null | grep -o '/dev/shm/[^ ]*'
done 2>/dev/null | sed 's#\(/dev/shm/[^/]*\).*#\1#' | sort -u
