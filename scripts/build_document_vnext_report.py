#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CELLS = ("qwen25vl3b_real", "qwen25vl7b_real", "qwen25vl7b_caption")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload(
    metadata: dict[str, Any],
    metrics: dict[str, dict[str, Any]],
    metric_paths: dict[str, Path],
) -> dict[str, Any]:
    if metadata.get("n_pairs") != 100:
        raise ValueError("L11 calibration must contain exactly 100 pairs")
    if metadata.get("iteration_policy") != (
        "one declared batch; no regeneration or threshold change in this round"
    ):
        raise ValueError("L11 one-shot iteration policy drift")
    if metadata.get("selection_applied") is not False or metadata.get(
        "regeneration_applied"
    ) is not False:
        raise ValueError("L11 calibration cannot use selection or regeneration")
    if set(metrics) != set(CELLS):
        raise ValueError(f"expected L11 cells {CELLS}, found {sorted(metrics)}")
    for name, cell in metrics.items():
        if int(cell.get("n_pairs", -1)) != 100:
            raise ValueError(f"L11 cell {name} does not contain 100 pairs")
        for field in ("pair_accuracy", "member_accuracy", "collapse_rate"):
            value = float(cell[field])
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"L11 cell {name} has invalid {field}: {value}")

    lower, upper = map(float, metadata["target_7b_real_pair_accuracy"])
    observed = float(metrics["qwen25vl7b_real"]["pair_accuracy"])
    if lower <= observed <= upper:
        verdict = "within-target-range"
    elif observed > upper:
        verdict = "too-easy"
    else:
        verdict = "too-hard"
    return {
        "schema_version": "blind-gains.document-vnext-calibration-report.v1",
        "status": "complete",
        "task": "L11",
        "template_id": metadata["template_id"],
        "n_pairs": 100,
        "seed": metadata["seed"],
        "manifest": metadata["manifest"],
        "manifest_sha256": metadata["manifest_sha256"],
        "target_7b_real_pair_accuracy": [lower, upper],
        "observed_7b_real_pair_accuracy": observed,
        "calibration_verdict": verdict,
        "iteration_policy": metadata["iteration_policy"],
        "cells": metrics,
        "metric_artifacts": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in sorted(metric_paths.items())
        },
    }


def render_report(payload: dict[str, Any], machine_path: Path) -> str:
    rows = []
    labels = {
        "qwen25vl3b_real": "Qwen2.5-VL-3B real",
        "qwen25vl7b_real": "Qwen2.5-VL-7B real",
        "qwen25vl7b_caption": "Qwen2.5-VL-7B caption",
    }
    for name in CELLS:
        cell = payload["cells"][name]
        rows.append(
            f"| {labels[name]} | {float(cell['pair_accuracy']):.4f} | "
            f"{float(cell['member_accuracy']):.4f} | {float(cell['collapse_rate']):.4f} |"
        )
    target = payload["target_7b_real_pair_accuracy"]
    return "\n".join(
        [
            "# Document V-Next Calibration",
            "",
            "Status:",
            "- The single declared 100-pair L11 batch and all three registered cells are complete.",
            f"- Calibration verdict: `{payload['calibration_verdict']}`. The 7B-real target was [{target[0]:.2f}, {target[1]:.2f}] and the observed pair accuracy was {payload['observed_7b_real_pair_accuracy']:.4f}.",
            "- This is a calibration outcome, not a PI gate declaration.",
            "",
            "Evidence:",
            f"- Source manifest: `{payload['manifest']}`, SHA256 `{payload['manifest_sha256']}`.",
            f"- Machine report: `{machine_path}`.",
            f"- Template: `{payload['template_id']}`; seed `{payload['seed']}`; pairs `{payload['n_pairs']}`.",
            "",
            "| Cell | Pair accuracy | Member accuracy | Collapse rate |",
            "|---|---:|---:|---:|",
            *rows,
            "",
            "Problems:",
            "- A result outside the target range means this declared family did not achieve the intended 7B difficulty. It is reported as observed and is not repaired by selection.",
            "",
            "Decision:",
            f"- Preserve the one-shot result. Iteration policy: `{payload['iteration_policy']}`.",
            "- Do not generate a second L11 batch in this round.",
            "",
            "Next actions:",
            "- Carry this calibration result into instrument limitations and defer any redesign to a separately preregistered round.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--metric", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--machine-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.machine_output.exists():
        raise FileExistsError("refusing to overwrite L11 calibration reports")
    metric_paths: dict[str, Path] = {}
    for value in args.metric:
        name, separator, path = value.partition("=")
        if not separator or name not in CELLS or name in metric_paths:
            raise ValueError(f"invalid L11 metric mapping: {value}")
        metric_paths[name] = Path(path)
    if set(metric_paths) != set(CELLS):
        raise ValueError(f"expected all L11 metric cells, found {sorted(metric_paths)}")
    metrics = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in metric_paths.items()
    }
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    payload = build_payload(metadata, metrics, metric_paths)
    args.machine_output.parent.mkdir(parents=True, exist_ok=True)
    args.machine_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.output.write_text(render_report(payload, args.machine_output), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "verdict": payload["calibration_verdict"]}))


if __name__ == "__main__":
    main()
