#!/usr/bin/env python3
"""Make 'seed 2' run dirs whose per_item.jsonl is byte-identical to seed 1 but
whose manifest carries the seed-2 checkpoint label.  Under the registered
estimator gain = mean(acc100_s1, acc100_s2) - acc0, feeding identical data as
both seeds must reproduce the ONE-SEED numbers exactly.  Any divergence means a
quantity is being re-derived rather than inherited."""
import json
import shutil
import sys
from pathlib import Path

ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
root = Path(sys.argv[1]).resolve()
for arm in ARMS:
    src = root / "runs" / f"step100_{arm}_seed1"
    dst = root / "runs" / f"dup_step100_{arm}_seed2"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    m = json.loads((dst / "run_manifest.json").read_text())
    m["run_id"] = f"dup_step100_{arm}_seed2"
    m["model_path"] = (
        f"checkpoints/m7/m7_virl_{arm}_seed2/global_step_100/actor/huggingface"
    )
    (dst / "run_manifest.json").write_text(
        json.dumps(m, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
print("dup ok")
