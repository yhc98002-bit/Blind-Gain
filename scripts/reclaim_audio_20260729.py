#!/usr/bin/env python3
"""Reclaim AudioDiffusion bulk while preserving experimental results.

The PI's instruction, twice given, is to delete the large files but retain some
of the experimental results. So this deletes by SIZE, not by directory: anything
at or above the threshold goes, anything below it stays. That keeps every
report, manifest, jsonl and csv (2,271 of them under orbit-research alone) while
removing the audio renders and archives that make up the bulk.

Run with --apply to delete. Without it, it only reports.
"""
import argparse
import os
import sys
from pathlib import Path

ROOTS = [
    Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion"),
    Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion-neutral-control-20260717"),
    Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion_v15_gate0_20260717"),
    Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion_exit1_20260716"),
]
THRESHOLD = 5 * 1024 * 1024  # 5 MiB

# Never touch anything under these, whatever its size.
FORBIDDEN = ("/BlindGain/", "/blind_gain/", "/blindgain")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

big, small_bytes, small_n, errs = [], 0, 0, 0
for root in ROOTS:
    if not root.is_dir():
        continue
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        if any(f in dirpath for f in FORBIDDEN):
            print(f"REFUSING to walk BlindGain path: {dirpath}", file=sys.stderr)
            sys.exit(2)
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.is_symlink():
                    continue
                sz = p.stat().st_size
            except OSError:
                errs += 1
                continue
            if sz >= THRESHOLD:
                big.append((sz, p))
            else:
                small_bytes += sz
                small_n += 1

big.sort(reverse=True)
total = sum(s for s, _ in big)
print(f"threshold           : {THRESHOLD // (1024*1024)} MiB")
print(f"files >= threshold  : {len(big):,}  totalling {total/2**30:,.1f} GiB  <- would be DELETED")
print(f"files <  threshold  : {small_n:,}  totalling {small_bytes/2**30:,.2f} GiB  <- PRESERVED")
print(f"stat errors         : {errs}")
print("\nlargest 8 to be deleted:")
for sz, p in big[:8]:
    print(f"  {sz/2**30:7.2f} GiB  {p}")

if not args.apply:
    print("\nDRY RUN — nothing deleted. Re-run with --apply.")
    sys.exit(0)

freed, failed = 0, 0
for sz, p in big:
    try:
        p.unlink()
        freed += sz
    except OSError as e:
        failed += 1
        if failed <= 5:
            print(f"  failed: {p}: {e}", file=sys.stderr)
print(f"\nDELETED {freed/2**30:,.1f} GiB across {len(big)-failed:,} files ({failed} failures)")
