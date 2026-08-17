"""Fixture for scripts/build_hier_p23_readout.py: criterion flags computed
from the folded statistics, blind member accuracy re-derivation, and
overwrite refusal."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_hier_p23_readout", ROOT / "scripts/build_hier_p23_readout.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def _stats(folded, ci_up, auc):
    return {"gate_statistic": folded, "pair_bootstrap_ci_95": [folded - 0.02, ci_up],
            "directed_oof_auc": auc,
            "directed_oof_auc_unfolded_ci_95": [auc - 0.03, auc + 0.03],
            "n_pairs": 100}


def _gate_json(path: Path, family: str, folded: float, ci_up: float) -> None:
    payload = {
        "attacks": {"dinov2": {
            "pooled": _stats(folded, ci_up, folded),
            "per_template": {f"{family}_c1": _stats(folded, ci_up, folded)}}},
        "gate": {"checks": {"all_attackers_available": True,
                            "all_point_estimates_at_most_0_55": folded <= 0.55,
                            "no_ci_upper_above_0_62": ci_up <= 0.62},
                 "point_failures": [], "status": folded <= 0.55 and ci_up <= 0.62},
        "n_pairs": 100, "split": "grouped-5fold"}
    path.write_text(json.dumps(payload))


def _blind_run(tmp_path: Path, name: str, acc_hits: list[tuple[bool, bool]]) -> Path:
    run = tmp_path / name
    cell = run / "hier_coord_v1_c1_l3"
    cell.mkdir(parents=True)
    rows = [{"pair_id": f"p{i}", "correct_a": a, "correct_b": b}
            for i, (a, b) in enumerate(acc_hits)]
    (cell / "predictions.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows))
    return run


def _run(argv: list[str]) -> None:
    saved = sys.argv
    sys.argv = ["build_hier_p23_readout.py", *argv]
    try:
        MOD.main()
    finally:
        sys.argv = saved


def test_flags_and_blind_accuracy(tmp_path):
    coord = tmp_path / "gate_hier_coord_v1.json"
    chart = tmp_path / "gate_hier_chart_v1.json"
    _gate_json(coord, "hier_coord_v1", 0.51, 0.55)   # clean
    _gate_json(chart, "hier_chart_v1", 0.9819, 0.9962)  # both flags fire
    gray = _blind_run(tmp_path, "gray", [(True, False), (False, False)])  # 0.25
    noimg = _blind_run(tmp_path, "noimg", [(False, False), (False, False)])  # 0.0
    leak = tmp_path / "leak.json"
    leak.write_text(json.dumps({"cells": {"hier_chart_v1": {"c1": {
        "target_switch": {"n": 50, "value_delta_neg": 50, "value_delta_pos": 0,
                          "multi_field_edits": 0, "png_size_edited_gt_base": 50,
                          "png_size_edited_lt_base": 0, "png_size_equal": 0,
                          "png_size_mean_delta_bytes": 1412.0}}}}}))
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    argv = ["--attacker-gate", str(coord), str(chart),
            "--blind-gray-run", str(gray), "--blind-no-image-run", str(noimg),
            "--leak-verification", str(leak),
            "--output-json", str(out_json), "--output-md", str(out_md)]
    _run(argv)

    payload = json.loads(out_json.read_text())
    chart_rows = payload["attacker_gates"]["hier_chart_v1"]["rows"]
    assert all(r["point_over_0_55"] and r["ci_upper_over_0_62"]
               for r in chart_rows)
    coord_rows = payload["attacker_gates"]["hier_coord_v1"]["rows"]
    assert not any(r["point_over_0_55"] or r["ci_upper_over_0_62"]
                   for r in coord_rows)
    blind = payload["blind_floors"]["member_accuracy"]
    assert blind["gray"]["hier_coord_v1_c1_l3"] == 0.25
    assert blind["no_image"]["hier_coord_v1_c1_l3"] == 0.0
    md = out_md.read_text()
    assert "point>0.55 ci_up>0.62" in md
    assert "| hier_chart_v1 | c1 | target_switch | 50 | 50 | 0 |" in md

    with pytest.raises(FileExistsError):
        _run(argv)
