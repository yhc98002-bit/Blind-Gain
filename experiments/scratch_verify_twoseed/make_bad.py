#!/usr/bin/env python3
"""Build malformed seed-2 run dirs for the adversarial gate probes."""
import json
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
src = root / "runs" / "step100_a1_real_seed2"

# (a) manifest status "running"
d = root / "runs" / "bad_running_a1_real_seed2"
if d.exists():
    shutil.rmtree(d)
shutil.copytree(src, d)
m = json.loads((d / "run_manifest.json").read_text())
m["status"] = "running"
(d / "run_manifest.json").write_text(json.dumps(m, sort_keys=True, indent=2) + "\n")

# (b) one item dropped from per_item.jsonl
d = root / "runs" / "bad_short_a1_real_seed2"
if d.exists():
    shutil.rmtree(d)
shutil.copytree(src, d)
lines = (d / "per_item.jsonl").read_text().strip().split("\n")
(d / "per_item.jsonl").write_text("\n".join(lines[:-1]) + "\n")

# (c) checkpoint label points at global_step_60
d = root / "runs" / "bad_step60_a1_real_seed2"
if d.exists():
    shutil.rmtree(d)
shutil.copytree(src, d)
m = json.loads((d / "run_manifest.json").read_text())
m["model_path"] = (
    "checkpoints/m7/m7_virl_a1_real_seed2/global_step_60/actor/huggingface"
)
(d / "run_manifest.json").write_text(json.dumps(m, sort_keys=True, indent=2) + "\n")
print("bad dirs ok")
