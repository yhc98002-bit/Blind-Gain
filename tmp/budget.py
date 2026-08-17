#!/usr/bin/env python3
"""Measured checkpoint sizes and the projected quota draw for arms 2-4."""
import json, subprocess
from pathlib import Path
R = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
snap = json.loads((R / "reports/storage_usage_snapshot.json").read_text())
ck = R / "checkpoints/m7/m7_virl_a1_real_seed1"
print("=== measured: arm 1 full-checkpoint sizes (save_model_only: false) ===")
tot = 0
n = 0
for d in sorted(ck.glob("global_step_*")):
    b = int(subprocess.run(["du","-sb",str(d)],capture_output=True,text=True).stdout.split()[0])
    tot += b; n += 1
    print(f"  {d.name:16} {b/1e9:8.2f} GB")
print(f"  mean per full checkpoint: {tot/n/1e9:.2f} GB  (n={n})")
print()
print("=== quota state (from reports/storage_usage_snapshot.json) ===")
for k in ("measured_at_utc","quota_bytes","used_bytes","free_bytes","status"):
    v = snap[k]
    print(f"  {k:16} {v if not isinstance(v,int) else f'{v:,} ({v/1e9:.1f} GB)'}")
print()
print("=== projected additional draw ===")
full = tot/n
model_only = 7.6e9  # amendment's stated figure, NOT measured here
print(f"  arm 1 remaining (steps 80,100 @ full):        {2*full/1e9:8.1f} GB")
print(f"  arms 2-4 @ model-only, 5 ckpts each (stated): {3*5*model_only/1e9:8.1f} GB")
print(f"  total projected:                              {(2*full+15*model_only)/1e9:8.1f} GB")
print(f"  free now:                                     {snap['free_bytes']/1e9:8.1f} GB")
print(f"  headroom after:                               {(snap['free_bytes']-2*full-15*model_only)/1e9:8.1f} GB")
print()
print("  counterfactual, arms 2-4 at full checkpoints:")
print(f"    {3*5*full/1e9:.1f} GB needed vs {snap['free_bytes']/1e9:.1f} GB free -> "
      f"{'FITS' if 3*5*full+2*full < snap['free_bytes'] else 'DOES NOT FIT'}")
