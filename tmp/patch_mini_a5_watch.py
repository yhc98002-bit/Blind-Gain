#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/launch_mini_a5_checkpoint_watch.sh")
t = p.read_text()
old = 'MODE="$(jq -er \'.mini_a5_mode // .mode // empty\' "${TRAINING_RUN}/run_manifest.json")"'
new = 'MODE="$(jq -r \'.mini_a5_mode // .mode // ""\' "${TRAINING_RUN}/run_manifest.json" 2>/dev/null || true)"'
if new in t:
    print("already patched")
    sys.exit(0)
if t.count(old) != 1:
    print(f"ABORT: found {t.count(old)} matches")
    sys.exit(1)
p.write_text(t.replace(old, new))
print("patched")
