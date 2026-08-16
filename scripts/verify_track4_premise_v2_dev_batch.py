#!/usr/bin/env python3
"""Independent from-disk verification of the Track-4 v2 development batch.

Trusts nothing from the builder run: recomputes nearest-neighbour structure
from the serialized scene programs, re-validates every group with the v2
loader, proves the v1 loader refuses them, re-hashes every referenced image,
and re-checks the constraint inversion on every transition row.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

# 2026-08-16 (dispatch item 4): parameterized so the dev_v2 regeneration gets
# its own from-disk verification. Defaults reproduce the original v1
# invocation byte-for-byte; unknown arguments now REFUSE instead of being
# silently ignored (the pre-fix script had no argparse, so a caller passing
# --data-dir unknowingly verified v1 — caught by the 2026-08-16 round's
# adversarial verification pass).
_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument(
    "--data-dir",
    type=Path,
    default=ROOT / "data/track4_premise_v2_dev_v1",
    help="batch directory (default: the declared v1 batch)",
)
_parser.add_argument(
    "--easy-n-points",
    type=int,
    default=8,
    help="expected n_points for *_easy types (v1: 8; dev_v2 under branch (c): 5)",
)
_args = _parser.parse_args()
DATA = _args.data_dir if _args.data_dir.is_absolute() else ROOT / _args.data_dir
EASY_N_POINTS = _args.easy_n_points

from src.train.intervention_group_schema import (  # noqa: E402
    InterventionGroupSchemaError,
    validate_batch_v2,
    validate_group,
)


def rows(name):
    return [json.loads(l) for l in (DATA / name).read_text().splitlines() if l.strip()]


def ranked(points, target):
    tx, ty = points[target]
    return sorted(
        (math.hypot(px - tx, py - ty), lab)
        for lab, (px, py) in points.items()
        if lab != target
    )


def pts(serialized):
    return {lab: (x, y) for lab, x, y in serialized}


causal = rows("manifest_causal_pairs.jsonl")
inv = rows("manifest_invariance_pairs.jsonl")
probe = rows("manifest_premise_probe.jsonl")
groups = rows("groups_v2.jsonl")

problems = []
by_type = Counter(r["intervention_type"] for r in causal)

# 1. every causal row: recompute final + premise golds from scene programs
n_transition = n_chained = 0
for r in causal:
    t = r["verifier_results"]["target_label"]
    for side in ("a", "b"):
        p = pts(r[f"scene_points_{side}"])
        if r["intervention_type"] == "fact_read":
            want = str(p[t][0])
            if str(r[f"answer_{side}"]) != want:
                problems.append(f"{r['pair_id']} fact_read answer_{side}")
            continue
        rk = ranked(p, t)
        if rk[0][1] != r[f"premise_answer_{side}"]:
            problems.append(f"{r['pair_id']} premise_{side} mismatch")
        if str(p[rk[0][1]][0]) != str(r[f"answer_{side}"]):
            problems.append(f"{r['pair_id']} final_{side} mismatch")
        # registered margins: semantic-A side >= 1.0 (G1) for all premise
        # types; semantic-B side >= 1.0 for transitions (G2, the mirror)
        # but only > 0.5 for chained (B1's frozen stay-margin, d < d2-0.5)
        swapped = r["provenance"]["semantic_side_assignment_swapped"]
        semantic = {False: {"a": "A", "b": "B"}, True: {"a": "B", "b": "A"}}[swapped][side]
        if r["intervention_type"].startswith("premise_transition") or semantic == "A":
            floor = 1.0
        else:
            floor = 0.5
        if rk[1][0] - rk[0][0] < floor - 1e-9:
            problems.append(
                f"{r['pair_id']} semantic {semantic} margin "
                f"{rk[1][0] - rk[0][0]:.3f} < {floor}")
    if r["intervention_type"].startswith("premise_transition"):
        n_transition += 1
        if r["premise_answer_a"] == r["premise_answer_b"]:
            problems.append(f"{r['pair_id']} transition with equal premise golds")
        if r["premise_transition"] is not True:
            problems.append(f"{r['pair_id']} transition flag not True")
        # constraint inversion: semantic-original side, moved point beyond d2+1
        swapped = r["provenance"]["semantic_side_assignment_swapped"]
        pa = pts(r["scene_points_b"] if swapped else r["scene_points_a"])
        pb = pts(r["scene_points_a"] if swapped else r["scene_points_b"])
        moved = [lab for lab in pa if pa[lab] != pb[lab]]
        if len(moved) != 1:
            problems.append(f"{r['pair_id']} moved != 1 point")
        else:
            m = moved[0]
            ra = ranked(pa, t)
            d2 = ra[1][0]
            tx, ty = pa[t]
            d_new = math.hypot(pb[m][0] - tx, pb[m][1] - ty)
            if not (d_new >= d2 + 1.0 - 1e-9):
                problems.append(f"{r['pair_id']} inversion violated d_new={d_new:.2f} d2={d2:.2f}")
            if d_new < d2 - 0.5:
                problems.append(f"{r['pair_id']} satisfies frozen B1 filter (!)")
            if ra[0][1] != m:
                problems.append(f"{r['pair_id']} moved point was not the nearest")
    elif r["intervention_type"].startswith("chained_premise"):
        n_chained += 1
        if r["premise_answer_a"] != r["premise_answer_b"]:
            problems.append(f"{r['pair_id']} chained with differing premise golds")

# 2. invariance rows: equal answers, equal premises, recomputable
for r in inv:
    if str(r["answer_a"]) != str(r["answer_b"]):
        problems.append(f"{r['pair_id']} invariance answers differ")
    t = r["verifier_results"]["target_label"]
    if r["intervention_type"] != "fact_read":
        if r["premise_answer_a"] != r["premise_answer_b"]:
            problems.append(f"{r['pair_id']} invariance premise differs")
        for side in ("a", "b"):
            p = pts(r[f"scene_points_{side}"])
            rk = ranked(p, t)
            if rk[0][1] != r[f"premise_answer_{side}"]:
                problems.append(f"{r['pair_id']} inv premise_{side} mismatch")

# 3. n_points lever on disk
for r in causal + inv:
    want = EASY_N_POINTS if r["intervention_type"].endswith("_easy") else 20
    for side in ("a", "b"):
        if len(r[f"scene_points_{side}"]) != want:
            problems.append(f"{r['pair_id']} n_points != {want}")

# 4. image hashes on disk (every referenced image, causal + invariance)
n_img = 0
for r in causal + inv:
    for side in ("a", "b"):
        p = Path(r[f"image_{side}_path"])
        if not p.is_absolute():
            p = ROOT / p
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != r[f"image_{side}_sha256"]:
            problems.append(f"{r['pair_id']} image_{side} sha mismatch")
        n_img += 1

# 5. groups: v2 batch validation from disk + v1 refusal on all + premise glue
validate_batch_v2(groups, require_measured=False)
n_v1_refused = 0
for g in groups:
    try:
        validate_group(g)
        problems.append(f"{g['group_uid']} ACCEPTED by v1 loader")
    except InterventionGroupSchemaError:
        n_v1_refused += 1
    if g["blind_solvability"]["measurement_state"] != "pending":
        problems.append(f"{g['group_uid']} not pending")
try:
    validate_batch_v2(groups, require_measured=True)
    problems.append("training-path validation ACCEPTED pending groups")
except InterventionGroupSchemaError:
    pass

# 6. probe rows: derived golds match causal premise golds; count transitions
if len(probe) != sum(c for tpe, c in by_type.items() if tpe != "fact_read"):
    problems.append("probe row count mismatch")
cmap = {r["pair_id"]: r for r in causal}
for r in probe:
    src = cmap[r["pair_id"]]
    if (r["answer_a"], r["answer_b"]) != (src["premise_answer_a"], src["premise_answer_b"]):
        problems.append(f"probe {r['pair_id']} golds mismatch")
    if r["answers_equal"] != (r["answer_a"] == r["answer_b"]):
        problems.append(f"probe {r['pair_id']} answers_equal wrong")

# 7. mismatched-real donors are same-type, different-group originals
gmap = {g["group_uid"]: g for g in groups}
for g in groups:
    for m in g["members"]:
        if m.get("condition") == "mismatched_real":
            donor = gmap[m["mismatched_source_group"]]
            if donor["intervention_type"] != g["intervention_type"]:
                problems.append(f"{g['group_uid']} cross-type donor")
            if donor["group_uid"] == g["group_uid"]:
                problems.append(f"{g['group_uid']} self donor")
            if m["image_sha256"] != donor["original"]["image_sha256"]:
                problems.append(f"{g['group_uid']} donor sha mismatch")

print(json.dumps({
    "data_dir": str(DATA), "easy_n_points": EASY_N_POINTS,
    "causal_rows": len(causal), "invariance_rows": len(inv),
    "probe_rows": len(probe), "groups": len(groups),
    "by_type": dict(by_type),
    "transition_rows": n_transition, "chained_rows": n_chained,
    "probe_transition_rows": sum(1 for r in probe if not r["answers_equal"]),
    "images_rehashed": n_img, "v1_refused_all": n_v1_refused == len(groups),
    "problems": problems[:20], "n_problems": len(problems),
}, indent=2, sort_keys=True))
sys.exit(1 if problems else 0)
