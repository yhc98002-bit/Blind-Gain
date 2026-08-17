#!/usr/bin/env python3
"""Route Ray's temp directory off the node root filesystem for Mini-A5.

an29's root filesystem (backing /tmp, /var/tmp, /) is 100% full with other
users' data, which crashed the eight-GPU CP arm inside compute_log_probs.
This is an operational placement change only: no scientific parameter, batch
size, seed, or step budget is touched.
"""
from pathlib import Path
import sys

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/launch_mini_a5_main.sh")
t = p.read_text()
if "RAY_TMPDIR" in t:
    print("already patched")
    sys.exit(0)

needle = "CUDA_VISIBLE_DEVICES="
idx = t.find(needle)
if idx == -1:
    print("ABORT: could not find the command environment prefix")
    sys.exit(1)
addition = (
    "RAY_TMPDIR=/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_ray_tmp/${MODE} TMPDIR=/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_ray_tmp/${MODE} "
)
t = t[:idx] + addition + t[idx:]

# ensure the directory exists on the compute node before launch
marker = "ssh \"${NODE}\""
first = t.find(marker)
if first == -1:
    print("ABORT: could not find the remote launch call")
    sys.exit(1)
prep = (
    "ssh \"${NODE}\" \"mkdir -p /XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_ray_tmp/${MODE}\"\n"
)
t = t[:first] + prep + t[first:]
p.write_text(t)
print("patched: RAY_TMPDIR and TMPDIR routed to shared storage")
