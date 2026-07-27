#!/usr/bin/env python3
"""Fail-closed finalizer for the registered D2 test-time image-access ablation.

Implements docs/registered_d2_testtime_ablation_v1.md and nothing beyond it:
verifies the eight cells, runs the reproduction check against the published
step-100 values, computes the registered primary and secondary statistics with
the registered bootstrap, and applies the pre-committed bands.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
EXPECTED_ROWS = 601
N_BOOT = 1000
BOOT_SEED = 20260710
# Pinned registered inputs (arm step-0 evaluations of the identical frozen base)
BASE = {"real": 0.1747, "gray": 0.0899, "none": 0.0682}
PUBLISHED_A1_REAL = {"a1_seed1_step100": 0.4276, "a1_seed2_step100": 0.4210, "a1_seed3_step100": 0.4060}
PUBLISHED_A2B_NONE = {"a2b_seed1_step100": 0.0982, "a2b_seed2_step100": 0.1231, "a2b_seed3_step100": 0.1215}
REPRO_TOLERANCE = 0.01
CELLS = [("a1_seed1_step100", c) for c in ("real", "gray", "none")] + \
        [("a1_seed2_step100", c) for c in ("real", "gray", "none")] + \
        [("a1_seed3_step100", c) for c in ("real", "gray", "none")] + \
        [("a2b_seed1_step100", "real"), ("a2b_seed2_step100", "real"),
         ("a2b_seed3_step100", "real")]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def find_cell(model_key: str, condition: str) -> Path:
    complete = []
    for match in sorted(glob.glob(str(ROOT / f"experiments/runs/d2_testtime_{model_key}_{condition}_an12_*"))):
        manifest = Path(match) / "run_manifest.json"
        if manifest.is_file():
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            if payload.get("status") == "complete" and payload.get("exit_code") == 0:
                complete.append(Path(match))
    if len(complete) != 1:
        raise ValueError(f"expected one complete cell for {model_key}/{condition}, found {len(complete)}")
    return complete[0]


def bootstrap_ci(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOT_SEED)
    means = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(array), size=len(array))
        means.append(float(array[idx].mean()))
    means.sort()
    return [means[int(0.025 * N_BOOT)], means[min(N_BOOT - 1, int(0.975 * N_BOOT))]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    outputs = [Path(args.json_output), Path(args.markdown_output), Path(args.audit_output)]
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite D2 result artifacts")

    cells: dict[str, Any] = {}
    per_item: dict[str, dict[str, bool]] = {}
    evidence: list[dict[str, Any]] = []
    for model_key, condition in CELLS:
        run_dir = find_cell(model_key, condition)
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        rows = _read_jsonl(run_dir / "predictions.jsonl")
        if len(rows) != EXPECTED_ROWS:
            raise ValueError(f"row count mismatch: {run_dir} ({len(rows)})")
        if any(str(row.get("condition")) != condition for row in rows):
            raise ValueError(f"condition mismatch inside {run_dir}")
        if manifest.get("prompt_contract_sha256") != rows[0].get("prompt_contract_sha256"):
            raise ValueError(f"prompt contract drift: {run_dir}")
        key = f"{model_key}|{condition}"
        correct = [bool(row["acc_final"]) for row in rows]
        per_item[key] = {str(row["qid"]): bool(row["acc_final"]) for row in rows}
        cells[key] = {
            "model_key": model_key,
            "condition": condition,
            "n_items": len(rows),
            "acc_final": sum(correct) / len(correct),
            "acc_final_ci95": bootstrap_ci([float(v) for v in correct]),
            "acc_strict": sum(bool(row["acc_strict"]) for row in rows) / len(rows),
        }
        evidence.append(
            {
                "cell": key,
                "run_dir": str(run_dir.relative_to(ROOT)),
                "predictions_sha256": _sha256(run_dir / "predictions.jsonl"),
                "checkpoint_index_sha256": manifest.get("checkpoint_index_sha256"),
                "rows": len(rows),
            }
        )

    repro: dict[str, Any] = {}
    repro_ok = True
    for model_key, published in PUBLISHED_A1_REAL.items():
        measured = cells[f"{model_key}|real"]["acc_final"]
        delta = measured - published
        ok = abs(delta) <= REPRO_TOLERANCE
        repro_ok = repro_ok and ok
        repro[model_key] = {
            "published": published,
            "measured": measured,
            "delta": delta,
            "within_tolerance": ok,
        }

    primary: dict[str, Any] = {}
    secondary: dict[str, Any] = {}
    for seed, model_key in (("seed1", "a1_seed1_step100"), ("seed2", "a1_seed2_step100"), ("seed3", "a1_seed3_step100")):
        acc_real = cells[f"{model_key}|real"]["acc_final"]
        acc_none = cells[f"{model_key}|none"]["acc_final"]
        acc_gray = cells[f"{model_key}|gray"]["acc_final"]
        denominator = acc_real - BASE["real"]
        primary[seed] = {
            "acc_real": acc_real,
            "acc_none": acc_none,
            "base_real": BASE["real"],
            "base_none": BASE["none"],
            "gain_real": denominator,
            "gain_blind": acc_none - BASE["none"],
            "retained_gain_blind": (acc_none - BASE["none"]) / denominator if abs(denominator) > 1e-9 else None,
        }
        secondary[seed] = {
            "retained_gain_gray": (acc_gray - BASE["gray"]) / denominator if abs(denominator) > 1e-9 else None,
            "absolute_test_time_drop_real_minus_none": acc_real - acc_none,
            "acc_gray": acc_gray,
        }
    for seed, model_key in (("seed1", "a2b_seed1_step100"), ("seed2", "a2b_seed2_step100"), ("seed3", "a2b_seed3_step100")):
        acc_real = cells[f"{model_key}|real"]["acc_final"]
        published_none = PUBLISHED_A2B_NONE[model_key]
        secondary[seed]["a2b_real"] = acc_real
        secondary[seed]["a2b_published_none"] = published_none
        secondary[seed]["a2b_test_time_image_benefit"] = acc_real - published_none

    def band(value: float | None) -> str:
        if value is None:
            return "undefined"
        if value <= 0.25:
            return "a_image_mediated_at_test_time"
        if value < 0.75:
            return "b_mixed"
        return "c_image_independent_at_test_time"

    bands = {seed: band(primary[seed]["retained_gain_blind"]) for seed in primary}
    if not repro_ok:
        verdict = "invalid_reproduction_check_failed"
    elif len(set(bands.values())) == 1:
        verdict = bands["seed1"]
    else:
        verdict = "no_branch_seeds_disagree"

    result = {
        "schema_version": "blind-gains.d2-testtime-ablation-results.v1",
        "status": "complete",
        "registration": "docs/registered_d2_testtime_ablation_v1.md",
        "reproduction_check": repro,
        "primary_retained_gain_blind": primary,
        "per_seed_band": bands,
        "registered_verdict": verdict,
        "secondary": secondary,
        "cells": cells,
        "provenance": {"cells": sorted(evidence, key=lambda item: item["cell"])},
    }

    lines = [
        "# D2 test-time image-access ablation results (v1)",
        "",
        "Registered: `docs/registered_d2_testtime_ablation_v1.md`. Layer: open-form",
        "realization on the frozen 601-row Geometry3K pilot evaluation set, decoding",
        "contract identical to the registered pilot evaluations. Base cells are the",
        "pinned registered arm step-0 evaluations, not re-measured.",
        "",
        "## Reproduction check (A1 real vs published step-100)",
        "",
        "| model | published | measured | delta | within +/-0.01 |",
        "|---|---|---|---|---|",
    ]
    for model_key, record in repro.items():
        lines.append(
            f"| {model_key} | {record['published']:.4f} | {record['measured']:.4f}"
            f" | {record['delta']:+.4f} | {record['within_tolerance']} |"
        )
    lines += [
        "",
        "## Registered primary: retained gain without test-time image access",
        "",
        "| seed | Acc(A1,real) | Acc(A1,none) | gain real | gain blind | RetainedGainBlind | band |",
        "|---|---|---|---|---|---|---|",
    ]
    for seed, record in primary.items():
        retained = record["retained_gain_blind"]
        lines.append(
            f"| {seed} | {record['acc_real']:.4f} | {record['acc_none']:.4f}"
            f" | {record['gain_real']:+.4f} | {record['gain_blind']:+.4f}"
            f" | {retained if retained is None else format(retained, '.4f')} | {bands[seed]} |"
        )
    lines += [
        "",
        f"**Registered verdict: {verdict}**",
        "",
        "## Registered secondary",
        "",
        "| seed | RetainedGain(gray) | drop real-none | A2b real | A2b published none | A2b test-time image benefit |",
        "|---|---|---|---|---|---|",
    ]
    for seed, record in secondary.items():
        gray = record["retained_gain_gray"]
        lines.append(
            f"| {seed} | {gray if gray is None else format(gray, '.4f')}"
            f" | {record['absolute_test_time_drop_real_minus_none']:+.4f}"
            f" | {record['a2b_real']:.4f} | {record['a2b_published_none']:.4f}"
            f" | {record['a2b_test_time_image_benefit']:+.4f} |"
        )
    lines += [
        "",
        "## All cells",
        "",
        "| cell | n | Acc_final | 95% CI | Acc_strict |",
        "|---|---|---|---|---|",
    ]
    for key in sorted(cells):
        cell = cells[key]
        lines.append(
            f"| {key} | {cell['n_items']} | {cell['acc_final']:.4f}"
            f" | [{cell['acc_final_ci95'][0]:.4f}, {cell['acc_final_ci95'][1]:.4f}]"
            f" | {cell['acc_strict']:.4f} |"
        )
    lines += ["", "No interpretation beyond the registered bands.", ""]

    Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    audit = {
        "schema_version": "blind-gains.d2-testtime-ablation-audit.v1",
        "status": "pass" if repro_ok else "fail",
        "cells_verified": len(evidence),
        "reproduction_check_passed": repro_ok,
        "machine_output_sha256": _sha256(Path(args.json_output)),
        "markdown_output_sha256": _sha256(Path(args.markdown_output)),
        "performance_values_opened": True,
        "registered_verdict": verdict,
    }
    Path(args.audit_output).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
