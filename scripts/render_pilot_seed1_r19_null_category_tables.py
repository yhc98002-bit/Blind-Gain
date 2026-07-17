#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from scripts import build_pilot_4arm_seed1_readout as seed1


ROOT = Path(__file__).resolve().parents[1]


def combined_rows(
    null_payload: dict[str, Any], readout: dict[str, Any]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cell in null_payload["key_shuffle_cells"]:
        arm = str(cell["arm"])
        checkpoint = int(cell["checkpoint"])
        category_id = str(cell["category_id"])
        observed = float(cell["observed_pair_accuracy"])
        if checkpoint == 0:
            baseline = observed
            delta = 0.0
            ci95 = None
        else:
            registered = readout["fliptrack_r19"]["arms"][arm][str(checkpoint)][
                f"category:{category_id}"
            ]
            if abs(float(registered["pair_accuracy_observed"]) - observed) > 1e-12:
                raise ValueError("null/readout observed pair accuracy mismatch")
            baseline = float(registered["pair_accuracy_step0"])
            delta = float(registered["delta_pair_accuracy"]["estimate"])
            ci95 = [float(value) for value in registered["delta_pair_accuracy"]["ci95"]]
        result.append(
            {
                **cell,
                "pair_accuracy_step0": baseline,
                "delta_pair_accuracy": delta,
                "delta_ci95": ci95,
            }
        )
    if len(result) != 36:
        raise ValueError(f"expected 36 category/checkpoint null cells, got {len(result)}")
    return result


def render(rows: list[dict[str, Any]], null_path: Path, readout_path: Path) -> str:
    lines = [
        "# Seed-1 R19 Category Tables with Registered Null V1",
        "",
        "Status:",
        "- This companion places the registered within-template key-shuffle null beside every existing seed-1 R19 category/checkpoint row.",
        "- It uses cached predictions only and makes no scientific interpretation or gate decision.",
        "- Null rejection alone does not establish perceptual learning.",
        "",
        "Evidence:",
        f"- Null and chart diagnostics: `{null_path}`.",
        f"- PI-verified core readout: `{readout_path}`.",
        "- Human-facing chart label: `cued chart point-value reading`.",
        "",
        "| Arm | Checkpoint | R19 construct | n | Step-0 pair acc | Observed pair acc | Delta (95% CI) | Null mean | p(null >= observed) |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        ci = row["delta_ci95"]
        delta = f"{row['delta_pair_accuracy']:.4f}"
        if ci is not None:
            delta += f" [{ci[0]:.4f}, {ci[1]:.4f}]"
        else:
            delta += " [reference checkpoint]"
        lines.append(
            f"| {seed1.DISPLAY_NAMES[row['arm']]} | {row['checkpoint']} | "
            f"{row['category_display_name']} | {row['n_pairs']} | "
            f"{row['pair_accuracy_step0']:.4f} | {row['observed_pair_accuracy']:.4f} | "
            f"{delta} | {row['null_mean']:.4f} | {row['p_value_ge_observed']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Decision:",
            "- None. The registered chart diagnostics remain in the companion null report and must accompany any later chart delta.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    partial = path.with_name(f".{path.name}.partial.{os.getpid()}")
    partial.write_text(content, encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--null-json", type=Path, default=Path("reports/pilot_4arm_seed1_r19_null_v1.json")
    )
    parser.add_argument(
        "--readout", type=Path, default=Path("reports/pilot_4arm_seed1_results_v1.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/pilot_4arm_seed1_r19_null_category_tables_v1.md"),
    )
    args = parser.parse_args()
    null_payload = json.loads(args.null_json.read_text(encoding="utf-8"))
    readout = json.loads(args.readout.read_text(encoding="utf-8"))
    rows = combined_rows(null_payload, readout)
    _write_new(
        args.output,
        render(rows, args.null_json, args.readout),
    )


if __name__ == "__main__":
    main()
