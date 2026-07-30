#!/usr/bin/env python3
"""Verify each E1c blind cell: row count vs the with-image column, exit 0, image_removed true."""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
EXPECTED = {"blink": 1901, "hallusion": 1129, "mmvp": 300, "mathverse": 3940, "mmmu": 1050}
WITH_IMAGE_N = {"blink": 1901, "hallusion": 1129, "mmvp": 300, "mathverse": 3940, "mmmu": 1050}

problems = 0
for directory in sorted(glob.glob(str(ROOT / "experiments/runs/layer1_blind_e1c_*"))):
    d = Path(directory)
    name = d.name
    stem = name.split("_")[3]  # layer1_blind_e1c_<stem><scale>_...
    key = next((k for k in EXPECTED if stem.startswith(k)), None)
    manifest_path = d / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    status = manifest.get("status")
    exit_code = manifest.get("exit_code")
    metrics_path = d / "metrics.json"
    predictions_path = d / "predictions.jsonl"
    if not metrics_path.is_file():
        print(f"{name:<58} status={status} exit={exit_code} (still running / no metrics)")
        continue
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    overall = metrics["overall"]
    n_rows = sum(1 for _ in predictions_path.open(encoding="utf-8"))
    expected = WITH_IMAGE_N.get(key)
    ok = (
        exit_code == 0
        and status == "complete"
        and metrics.get("image_removed") is True
        and int(overall["n"]) == expected
        and n_rows == expected
    )
    if not ok:
        problems += 1
    print(
        f"{name:<58} exit={exit_code} status={status:<8} image_removed={metrics.get('image_removed')} "
        f"n_metrics={int(overall['n']):5d} n_jsonl={n_rows:5d} expected={expected:5d} "
        f"dtype={metrics['dataset_type']:<15} Acc_final={overall['Acc_final']:.4f} "
        f"Acc_strict={overall['Acc_strict']:.4f} Format_valid={overall['Format_valid']:.3f} "
        f"{'OK' if ok else '<<< PROBLEM'}"
    )
print(f"\ncells with problems: {problems}")
