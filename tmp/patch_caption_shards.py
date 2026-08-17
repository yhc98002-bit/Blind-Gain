#!/usr/bin/env python3
"""Pass --caption-shards for the caption condition (D4).

`run_pilot_geo3k_step100_eval.py` fails closed on `--condition caption` without
the frozen question-blind caption store, and the D2/D3 orchestrator never passed
it because the original three conditions do not need one. This adds the frozen
geo3k store used by the A3 arm's own step-100 evaluation, so D4 reads captions
from exactly the same store A3 trained and was evaluated against.
"""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/run_d2_testtime_ablation.py")
t = p.read_text()

anchor = 'MANIFEST = "data/geometry3k_caption_images_manifest.jsonl"'
assert t.count(anchor) == 1, "MANIFEST anchor"
t = t.replace(anchor, anchor + '''
# Frozen question-blind caption store, identical to the one the A3 arm's own
# step-100 evaluation used (see m2_geo3k_a3_caption_seed1 run manifest).
CAPTION_STORE_DIR = (
    "experiments/runs/geometry3k_qwen25vl3b_captionstore384_20260710T005300Z/shards"
)''', 1)

old = ('        f"--checkpoint-index-sha256 {index_sha} --batch-size 4 --max-model-len 8192 "\n'
       '        f"--max-tokens {MAX_TOKENS} --seed {SEED} --global-step 100 "')
new = ('        f"--checkpoint-index-sha256 {index_sha} --batch-size 4 --max-model-len 8192 "\n'
       '        f"--max-tokens {MAX_TOKENS} --seed {SEED} --global-step 100 "\n'
       '        f"{caption_args} "')
assert t.count(old) == 1, "command anchor"
t = t.replace(old, new, 1)

old2 = '    command = (\n        f"cd \'{ROOT}\' && "'
new2 = '''    if condition == "caption":
        shards = sorted((ROOT / CAPTION_STORE_DIR).glob("store_shard_*.jsonl"))
        if not shards:
            raise RuntimeError(f"caption store is empty: {CAPTION_STORE_DIR}")
        caption_args = "--caption-shards " + " ".join(
            str(s.relative_to(ROOT)) for s in shards
        )
    else:
        caption_args = ""
    command = (
        f"cd '{ROOT}' && "'''
assert t.count(old2) == 1, "command open anchor"
t = t.replace(old2, new2, 1)

p.write_text(t)
print("patched: caption shards now passed for --condition caption")
