#!/usr/bin/env python3
"""Adversarial fixture test for the X1 source-image selection contract."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.eval_qwen_vl_visual_evidence_ranking import select_source_image

ROW = {
    "pair_id": "p1",
    "image_a_path": "img/p1_a.png",
    "image_b_path": "img/p1_b.png",
}
OVERRIDE = {
    "per_pair": {
        "p1": {"a": "img/p9_a.png", "b": "img/p9_b.png", "source_pair_id": "p9"}
    }
}
SELF_OVERRIDE = {
    "per_pair": {
        "p1": {"a": "img/p1_a.png", "b": "img/p9_b.png", "source_pair_id": "p1"}
    }
}

failures: list[str] = []


def check(name: str, actual, expected) -> None:
    if actual != expected:
        failures.append(f"{name}: expected {expected!r}, got {actual!r}")


def check_raises(name: str, fn) -> None:
    try:
        fn()
    except (ValueError, KeyError):
        return
    failures.append(f"{name}: expected a refusal, none raised")


check("real_a", select_source_image(ROW, "a", "real", None), "img/p1_a.png")
check("real_b", select_source_image(ROW, "b", "real", None), "img/p1_b.png")
check("gray_a", select_source_image(ROW, "a", "gray", None), "img/p1_a.png")
check("no_image_b", select_source_image(ROW, "b", "no_image", None), "img/p1_b.png")
check("twin_a_gets_b", select_source_image(ROW, "a", "twin_counterfactual", None), "img/p1_b.png")
check("twin_b_gets_a", select_source_image(ROW, "b", "twin_counterfactual", None), "img/p1_a.png")
check("mismatched_a", select_source_image(ROW, "a", "mismatched_real", OVERRIDE), "img/p9_a.png")
check("mismatched_b", select_source_image(ROW, "b", "mismatched_real", OVERRIDE), "img/p9_b.png")
check_raises("mismatched_without_map", lambda: select_source_image(ROW, "a", "mismatched_real", None))
check_raises("mismatched_self_image", lambda: select_source_image(ROW, "a", "mismatched_real", SELF_OVERRIDE))
check_raises("mismatched_unknown_pair", lambda: select_source_image({**ROW, "pair_id": "p2"}, "a", "mismatched_real", OVERRIDE))
check("real_ignores_map", select_source_image(ROW, "a", "real", OVERRIDE), "img/p1_a.png")

if failures:
    print("FIXTURE FAILURES:")
    for failure in failures:
        print(" -", failure)
    sys.exit(1)
print("x1 source-selection fixture: 12/12 pass")
