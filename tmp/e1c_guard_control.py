#!/usr/bin/env python3
"""Positive control: the blind integrity guards must actually raise, not pass vacuously."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.eval.layer1_blind import build_text_prompt, load_rows

results = []

# 1. load_rows must reject a row whose built prompt retains an image token.
for dataset_type, question in [
    ("blink", "What is shown? <image>"),
    ("hallusionbench", "Is this <|vision_start|> true?"),
    ("mathverse", "Compute <image>"),
    ("mmmu", "Compute <image>"),
    ("mmvp", "Which one? <image>"),
]:
    frame = pd.DataFrame([{"index": "probe", "question": question, "answer": "A", "A": "x", "B": "y"}])
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as handle:
        frame.to_csv(handle.name, sep="\t", index=False)
        path = handle.name
    try:
        load_rows(path, dataset_type)
        results.append((dataset_type, "DID NOT RAISE <<< PROBLEM"))
    except ValueError as error:
        results.append((dataset_type, f"raised ValueError: {str(error)[:60]}"))
    finally:
        Path(path).unlink()

# 2. The MMMU builder must delete "<image N>" markers but NOT a bare "<image>",
#    which load_rows then catches.
row = {"index": 1, "question": "See <image 1> and <image>.", "answer": "A", "A": "x"}
prompt = build_text_prompt(row, "mmmu")
results.append(("mmmu marker deletion", f"'<image 1>' removed={'<image 1>' not in prompt}, bare '<image>' retained={'<image>' in prompt}"))

# 3. MMStar must keep "<image N>" (ImageMCQDataset does not split them).
row = {"index": 1, "question": "See <image 1>.", "answer": "A", "A": "x"}
results.append(("mmstar marker retention", f"'<image 1>' retained={'<image 1>' in build_text_prompt(row, 'mmstar')}"))

for name, outcome in results:
    print(f"{name:<26} {outcome}")
print("\nPROBLEMS:", sum(1 for _, o in results if "PROBLEM" in o))
