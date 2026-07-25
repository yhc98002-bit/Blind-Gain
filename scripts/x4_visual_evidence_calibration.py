#!/usr/bin/env python3
"""X4 — EXPLORATORY visual-evidence calibration endpoint (CPU, X1 dumps only).

Per model x image condition, member-level reliability of the candidate-evidence
ranking layer: confidence = softmax probability of the top-ranked candidate
over the frozen per-candidate mean-token log probabilities; correctness = the
member's own gold is top-ranked. Reports 10-bin equal-width reliability
curves, ECE, and the mean-confidence minus accuracy overconfidence gap.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
MODELS = ("base", "a1_step100", "a2_step100", "a2b_step100", "a3_step100")
CONDITIONS = ("real", "mismatched_real", "twin_counterfactual", "gray", "no_image")
X1_QUEUE = "x1_ranking_matrix_queue_login_20260724T085613Z"
SEED1_QUEUE = "d1_visual_evidence_matrix_queue_login_20260717T175951Z"
CAL_QUEUE = "blindarm_margin_calibration_matrix_queue_login_20260723T143504Z"
BINS = 10


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def find_cell(model: str, condition: str) -> Path:
    if condition in ("mismatched_real", "twin_counterfactual"):
        suffixes = [X1_QUEUE]
    elif model in ("base", "a1_step100"):
        suffixes = [SEED1_QUEUE]
    else:
        suffixes = [CAL_QUEUE]
    for suffix in suffixes:
        pattern = str(
            ROOT / f"experiments/runs/d1_visual_evidence_{model}_{condition}_*_{suffix}"
        )
        for match in sorted(glob.glob(pattern)):
            manifest = json.loads((Path(match) / "run_manifest.json").read_text())
            if manifest.get("status") == "complete" and manifest.get("exit_code") == 0:
                return Path(match)
    raise ValueError(f"no complete cell for {model}/{condition}")


def member_records(rows: list[dict[str, Any]]) -> list[tuple[float, bool]]:
    records: list[tuple[float, bool]] = []
    for row in rows:
        for side in ("a", "b"):
            scores = [float(v) for v in row[f"candidate_scores_{side}"].values()]
            peak = max(scores)
            exps = [math.exp(s - peak) for s in scores]
            total = sum(exps)
            confidence = max(exps) / total
            correct = int(row[f"rank_{side}"]) == 1
            records.append((confidence, correct))
    return records


def reliability(records: list[tuple[float, bool]]) -> dict[str, Any]:
    n = len(records)
    bins: list[dict[str, Any]] = []
    ece = 0.0
    for b in range(BINS):
        lo, hi = b / BINS, (b + 1) / BINS
        members = [
            (c, k) for c, k in records if (lo <= c < hi) or (b == BINS - 1 and c == 1.0)
        ]
        if not members:
            bins.append({"bin": [lo, hi], "n": 0})
            continue
        conf = sum(c for c, _ in members) / len(members)
        acc = sum(1 for _, k in members if k) / len(members)
        ece += (len(members) / n) * abs(acc - conf)
        bins.append(
            {"bin": [lo, hi], "n": len(members), "mean_confidence": conf, "accuracy": acc}
        )
    mean_conf = sum(c for c, _ in records) / n
    accuracy = sum(1 for _, k in records if k) / n
    return {
        "members": n,
        "mean_confidence": mean_conf,
        "accuracy": accuracy,
        "overconfidence_gap": mean_conf - accuracy,
        "ece_10bin": ece,
        "reliability_bins": bins,
    }


def main() -> None:
    out_json = ROOT / "reports/x4_visual_evidence_calibration_v1.json"
    out_md = ROOT / "reports/x4_visual_evidence_calibration_v1.md"
    if out_json.exists() or out_md.exists():
        raise FileExistsError("refusing to overwrite X4 artifacts")

    cells: dict[str, Any] = {}
    provenance: list[dict[str, str]] = []
    for model in MODELS:
        for condition in CONDITIONS:
            run_dir = find_cell(model, condition)
            rows = _read_jsonl(run_dir / "scores.jsonl")
            if len(rows) != 1200:
                raise ValueError(f"row count mismatch: {run_dir}")
            cells[f"{model}|{condition}"] = reliability(member_records(rows))
            provenance.append(
                {
                    "cell": f"{model}|{condition}",
                    "run_dir": str(run_dir.relative_to(ROOT)),
                    "scores_sha256": hashlib.sha256(
                        (run_dir / "scores.jsonl").read_bytes()
                    ).hexdigest(),
                }
            )

    result = {
        "schema_version": "blind-gains.x4-visual-evidence-calibration.v1",
        "label": "EXPLORATORY",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "confidence_definition": "softmax probability of the top-ranked candidate over frozen per-candidate mean-token log probabilities, member level",
        "correctness_definition": "member's own gold candidate is top-ranked (rank == 1)",
        "cells": cells,
        "provenance": sorted(provenance, key=lambda item: item["cell"]),
    }

    lines = [
        "# X4 — Visual-evidence calibration endpoint (v1) — EXPLORATORY",
        "",
        "Computed from the X1 candidate-evidence ranking dumps only. Confidence is",
        "the softmax probability of the top-ranked candidate; correctness is the",
        "member's own gold ranked first. Facts only.",
        "",
        "## ECE and overconfidence gap (member level, 2,400 members per cell)",
        "",
        "| model | condition | accuracy | mean confidence | overconfidence gap | ECE (10-bin) |",
        "|---|---|---|---|---|---|",
    ]
    for model in MODELS:
        for condition in CONDITIONS:
            cell = cells[f"{model}|{condition}"]
            lines.append(
                f"| {model} | {condition} | {cell['accuracy']:.4f}"
                f" | {cell['mean_confidence']:.4f}"
                f" | {cell['overconfidence_gap']:+.4f} | {cell['ece_10bin']:.4f} |"
            )
    lines += [
        "",
        "Reliability-curve bin tables are in the machine JSON.",
        "",
    ]

    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "cells": len(cells),
                "base_real_ece": cells["base|real"]["ece_10bin"],
                "a1_real_ece": cells["a1_step100|real"]["ece_10bin"],
                "output_sha256": hashlib.sha256(out_json.read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
