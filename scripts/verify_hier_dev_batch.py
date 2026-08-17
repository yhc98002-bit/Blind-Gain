#!/usr/bin/env python3
"""Independent from-disk verification of the hier_v1 dev batches (P1.1
obligations (a)–(e), registration §2 + A1/A2). Trusts nothing from the
builder run: rehashes every image and mask, recomputes every gold from the
serialized scene truth, re-checks the cue ink rule pixel-by-pixel, the
L2/L3 byte-identity, the cross-layer mother matching, the split rule, the
coord balance budget, and the question-operand naming (I21) — including that
the L3 question does NOT name the target (oracle absence is part of the
construct).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image

from scripts.build_track4_premise_v2_dev_batch import split_of
from scripts.hier_v1_lib import (
    CHART_ALLOWED,
    COORD_ALLOWED,
    EXTREMUM_KINDS,
    HIER_LABELS,
    PROCEDURE_TOKENS,
    REGISTERED_TEXT,
    chart_argmax,
    coord_extremum,
    cue_ink_disjoint,
)

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "hier_coord_v1": ("n8", "n12", "n20"),
    "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high"),
}
LAYERS = ("l3", "l2", "l1", "probe")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows_of(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def recompute_coord(row: dict, side: str) -> tuple[str, str]:
    points = {label: (x, y) for label, x, y in row[f"scene_{side}"]}
    kind = row["verifier_results"]["extremum_kind"]
    target, gap = coord_extremum(points, kind)
    if gap < row["verifier_results"]["extremum_margin"]:
        raise AssertionError("extremum margin violated")
    return target, str(points[target][EXTREMUM_KINDS[kind]["read"]])


def recompute_chart(row: dict, side: str) -> tuple[str, str]:
    values = row[f"scene_{side}"]
    vr = row["verifier_results"]
    target, gap = chart_argmax(values, vr["series_count"], vr["xa"] - 1)
    if gap < vr["granularity"]:
        raise AssertionError("argmax margin violated")
    from scripts.hier_v1_lib import HIER_LABELS
    return HIER_LABELS[target], str(values[target][vr["xr"] - 1])


def verify_cell(data_dir: Path, family: str, cell: str,
                problems: list[str]) -> dict:
    manifests = {
        layer: data_dir / f"manifest_{family}_{cell}_{layer}.jsonl"
        for layer in LAYERS
    }
    rows = {layer: rows_of(path) for layer, path in manifests.items()}
    allowed = COORD_ALLOWED if family == "hier_coord_v1" else CHART_ALLOWED
    recompute = recompute_coord if family == "hier_coord_v1" else recompute_chart
    images_rehashed = cue_checked = 0
    gold_counts: Counter = Counter()

    by_mother: dict[str, dict[str, dict]] = {}
    for layer in ("l3", "l2", "l1"):
        for row in rows[layer]:
            by_mother.setdefault(row["mother_item_id"], {})[layer] = row
    probes = {row["mother_item_id"]: row for row in rows["probe"]}

    # registered in-image text policy (pre-freeze cleanup amendment): rows
    # built or re-rendered after the amendment carry provenance.rendered_text,
    # which must equal the registered per-family strings exactly.
    for layer in LAYERS:
        for row in rows[layer]:
            rendered = row["provenance"].get("rendered_text")
            if rendered is not None and rendered != REGISTERED_TEXT[family]:
                problems.append(
                    f"{row['pair_id']}: rendered_text is not the registered "
                    f"in-image text for {family}")

    for mid, layer_rows in by_mother.items():
        l3 = layer_rows["l3"]
        pid = l3["pair_id"]
        # split rule
        if l3["split"] != "development" or split_of(l3["scene_program_id"]) != "development":
            problems.append(f"{pid}: split rule violated")
        # (b) golds + targets from scene truth, per side; probe targets
        for side in ("a", "b"):
            try:
                target, answer = recompute(l3, side)
            except AssertionError as error:
                problems.append(f"{pid}: {error}")
                continue
            if str(answer) != str(l3[f"answer_{side}"]):
                problems.append(f"{pid}: recomputed answer_{side} {answer} != {l3[f'answer_{side}']}")
            if str(target) != str(l3["verifier_results"][f"target_label_{side}"]):
                problems.append(f"{pid}: recomputed target_{side} {target} != recorded")
            if mid in probes and str(probes[mid][f"answer_{side}"]) != str(target):
                problems.append(f"{pid}: probe gold_{side} != recomputed target")
        # question-operand rule: L3 must NOT name the target; L2/L1 must
        target_name = str(l3["verifier_results"]["target_label_a"])
        if target_name in l3["question"]:
            problems.append(f"{pid}: L3 question names the target (oracle leak)")
        for layer in ("l2", "l1"):
            if layer in layer_rows and target_name not in layer_rows[layer]["question"]:
                problems.append(f"{pid}: {layer} question does not name the target")
        # (d) cross-layer matching
        reference = (json.dumps([l3["answer_a"], l3["answer_b"], l3["hard_negatives"],
                                 l3["scene_a"], l3["scene_b"]], sort_keys=True, default=str))
        for layer in ("l2", "l1"):
            if layer not in layer_rows:
                continue
            row = layer_rows[layer]
            candidate = (json.dumps([row["answer_a"], row["answer_b"], row["hard_negatives"],
                                     row["scene_a"], row["scene_b"]], sort_keys=True, default=str))
            if candidate != reference:
                problems.append(f"{pid}: {layer} mother-matching violated (d)")
        # A2 matrix
        if l3["role"] == "target_switch" and ("l2" in layer_rows or "l1" in layer_rows):
            problems.append(f"{pid}: switch mother carries l2/l1 rows (A2)")
        if l3["role"] != "target_switch" and ("l2" not in layer_rows or "l1" not in layer_rows):
            problems.append(f"{pid}: stable/invariance mother missing l2/l1 rows (A2)")
        # (c) + (a) + image/mask integrity
        for layer, row in layer_rows.items():
            for side in ("a", "b"):
                path = Path(row[f"image_{side}_path"])
                if sha256_file(path) != row[f"image_{side}_sha256"]:
                    problems.append(f"{pid}: {layer} image_{side} sha mismatch")
                images_rehashed += 1
            mask_path = Path(row["changed_region_mask_a"])
            if sha256_file(mask_path) != row["mask_sha256"]:
                problems.append(f"{pid}: {layer} mask sha mismatch")
            with Image.open(row["image_a_path"]) as ia, Image.open(row["image_b_path"]) as ib:
                diff = np.any(np.asarray(ia, dtype=np.uint8) != np.asarray(ib, dtype=np.uint8), axis=2)
                with Image.open(mask_path) as mask:
                    if not np.array_equal(diff.astype(np.uint8) * 255,
                                          np.asarray(mask, dtype=np.uint8)):
                        problems.append(f"{pid}: {layer} mask is not the exact pixel diff")
        if "l2" in layer_rows:
            l2, l1 = layer_rows["l2"], layer_rows["l1"]
            for side in ("a", "b"):
                if l2[f"image_{side}_sha256"] != l3[f"image_{side}_sha256"]:
                    problems.append(f"{pid}: (c) l2/l3 image_{side} not byte-identical")
                with Image.open(l2[f"image_{side}_path"]) as base, \
                        Image.open(l1[f"image_{side}_path"]) as cued:
                    if not cue_ink_disjoint(base, cued, allowed):
                        problems.append(f"{pid}: (a) cue ink rule violated on side {side}")
                    cue_checked += 1
        if family == "hier_coord_v1" and l3["role"] != "invariance":
            gold_counts[str(l3["answer_a"])] += 1
            gold_counts[str(l3["answer_b"])] += 1

    balance = None
    if family == "hier_coord_v1" and gold_counts:
        total = sum(gold_counts.values())
        top_value, top_count = gold_counts.most_common(1)[0]
        budget = max(1, int(0.10 * total))
        balance = {"max_count": top_count, "budget": budget, "total": total,
                   "max_share_value": top_value}
        if top_count > budget:
            problems.append(f"{family}/{cell}: balance budget violated ({balance})")

    registries = {}
    for layer in ("l3", "l2"):
        registry_path = data_dir / f"candidates_{family}_{cell}_{layer}.jsonl"
        registry_rows = rows_of(registry_path)
        causal = [r for r in rows[layer] if r["role"] != "invariance"]
        if len(registry_rows) != len(causal):
            problems.append(f"{family}/{cell}: {layer} registry rows != causal rows")
        for registry_row in registry_rows:
            ids = {c["candidate_id"] for c in registry_row["candidates"]}
            if registry_row["gold_candidate_id_a"] not in ids or \
                    registry_row["gold_candidate_id_b"] not in ids:
                problems.append(f"{registry_row['pair_id']}: registry gold id missing")
        registries[layer] = len(registry_rows)

    return {
        "mothers": len(by_mother),
        "rows": {layer: len(rows[layer]) for layer in LAYERS},
        "images_rehashed": images_rehashed,
        "cue_pairs_checked": cue_checked,
        "balance": balance,
        "registries": registries,
    }


def registered_text_policy_problems() -> list[str]:
    """Static policy: registered in-image strings must be layer-neutral —
    no task-procedure tokens, no series names, no point-label patterns."""
    problems: list[str] = []
    for family, texts in REGISTERED_TEXT.items():
        for kind, text in texts.items():
            low = text.lower()
            for token in PROCEDURE_TOKENS:
                if token in low:
                    problems.append(
                        f"{family} {kind}: procedure token {token!r} in "
                        f"registered in-image text")
            for name in HIER_LABELS:
                if name in text:
                    problems.append(
                        f"{family} {kind}: series name {name!r} in "
                        f"registered in-image text")
            if re.search(r"\bpoint [A-Z][A-Za-z0-9]*\b", text):
                problems.append(
                    f"{family} {kind}: point label in registered in-image text")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_v1_dev")
    parser.add_argument("--families", nargs="+", choices=sorted(FAMILIES),
                        default=sorted(FAMILIES))
    args = parser.parse_args()
    problems: list[str] = registered_text_policy_problems()
    summary: dict = {}
    for family in args.families:
        for cell in FAMILIES[family]:
            summary[f"{family}/{cell}"] = verify_cell(
                args.data_dir, family, cell, problems)
    print(json.dumps({"cells": summary, "n_problems": len(problems),
                      "problems": problems[:20]}, indent=2, sort_keys=True))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
