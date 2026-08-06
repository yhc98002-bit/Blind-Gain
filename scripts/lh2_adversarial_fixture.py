#!/usr/bin/env python3
"""Adversarial fixture for scripts/check_lh2_config_diff.py.

Runs three cases against the checker WITHOUT touching repo files:
  1. clean: the committed LH2 config must PASS (exit 0).
  2. tampered-value: lr changed 1.0e-06 -> 2.0e-06 (an unregistered leaf
     difference) must FAIL (exit 1).
  3. tampered-registered-leaf: data.seed changed 2 -> 3 (a registered leaf
     with an unregistered value) must FAIL (exit 1).

All tampered configs and outputs are written under tmp/; the real
reports/lh2_config_diff_check_v1.json is only (re)written by the clean case,
which is content-identical when the config is unchanged.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
CHECKER = ROOT / "scripts/check_lh2_config_diff.py"
TMP = ROOT / "tmp/lh2_adversarial_fixture"
TMP.mkdir(parents=True, exist_ok=True)


def load_module():
    spec = importlib.util.spec_from_file_location("check_lh2_config_diff", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_case(name: str, lh2_path: Path, out_path: Path) -> int:
    mod = load_module()
    mod.LH2_PATH = lh2_path
    mod.OUT_PATH = out_path
    try:
        return mod.main()
    except SystemExit as exc:  # pragma: no cover
        return int(exc.code or 0)


def main() -> int:
    clean = ROOT / "configs/train/lh2_anchor_seed2_3b_geo3k.yaml"
    text = clean.read_text(encoding="utf-8")

    tampered_value = TMP / "lh2_tampered_lr.yaml"
    assert "lr: 1.0e-06" in text
    tampered_value.write_text(text.replace("lr: 1.0e-06", "lr: 2.0e-06"), encoding="utf-8")

    tampered_seed = TMP / "lh2_tampered_seed3.yaml"
    assert "  seed: 2" in text
    tampered_seed.write_text(text.replace("  seed: 2", "  seed: 3"), encoding="utf-8")

    results = {
        "clean_pass": run_case("clean", clean, ROOT / "reports/lh2_config_diff_check_v1.json"),
        "tampered_lr_fail": run_case("tampered_lr", tampered_value, TMP / "out_tampered_lr.json"),
        "tampered_seed3_fail": run_case("tampered_seed3", tampered_seed, TMP / "out_tampered_seed3.json"),
    }
    verdict = {
        "schema": "blind-gains.lh2-adversarial-fixture.v1",
        "exit_codes": results,
        "expected": {"clean_pass": 0, "tampered_lr_fail": 1, "tampered_seed3_fail": 1},
        "status": "pass"
        if results["clean_pass"] == 0
        and results["tampered_lr_fail"] == 1
        and results["tampered_seed3_fail"] == 1
        else "fail",
    }
    (TMP / "fixture_result.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
