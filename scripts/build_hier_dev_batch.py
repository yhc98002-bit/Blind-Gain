#!/usr/bin/env python3
"""hier_v1 development batches — one shot per knob cell (P1.2 of the 08-12
dispatch; registered_hier_benchmark_v1.md §6–§7 + Amendments A1/A2).

Per family per cell: 150 mother-pairs = 50 target-switch + 50 target-stable +
50 invariance. Layer × role matrix per Amendment A2: L3 rows for all roles;
L2/L1 rows for the side-stable roles; one discovery probe per mother. One
manifest per (family, cell, layer) so the frozen eval harness runs each cell
as-is. Candidate registries are built at generation time over the causal
(switch + stable) rows of every L2/L3 manifest via the frozen registry
builder; invariance ranking remains the catch-stability instrument's job.

Coord cells honor the §8 balance cap (per cell, pooled causal member golds:
no value above a 0.10 share) by deterministic constrained resampling.
One-shot: refuses to overwrite; no acceptance iteration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import socket
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_track4_premise_v2_dev_batch import split_of
from scripts.hier_v1_lib import (
    CHART_GRANULARITY,
    COORD_MARGIN,
    CROSSING_BANDS,
    EXTREMUM_ROTATION,
    REGISTERED_TEXT,
    _render_hier_coordinate_register,
    build_chart_geometry,
    build_chart_v2_geometry,
    build_coord_geometry,
    chart_hard_negatives,
    chart_value_px,
    coord_hard_negatives,
    coord_target_px,
    hier_palette_report,
    render_chart_layers,
    render_coord_layers,
    render_hier_chart,
    sha256_image,
)
from src.eval.visual_evidence_ranking import build_candidate_registry_rows

ROOT = Path(__file__).resolve().parents[1]
BATCH_SEED = 20260817
ROLES = ("target_switch", "target_stable", "invariance")
PER_ROLE = 50
BALANCE_CAP = 0.10  # registered_hier_benchmark_v1.md §8, coord causal golds

COORD_CELLS = (("n8", 8), ("n12", 12), ("n20", 20))
CHART_CELLS = (("s5_low", 5, "low"), ("s5_high", 5, "high"),
               ("s9_low", 9, "low"), ("s9_high", 9, "high"))
# Amendment A4: hier_chart_v2 reuses the identical knob grid; only the causal
# edit construction changes (column transposition).
CHART_V2_CELLS = CHART_CELLS
# Mother-id tags must not collide across chart families: the old rule
# family.split("_")[1] yields "chart" for BOTH v1 and v2.
FAMILY_TAG = {"hier_coord_v1": "coord", "hier_chart_v1": "chart",
              "hier_chart_v2": "chartv2"}


def attempt_rng(family: str, cell: str, role: str, attempt: int) -> random.Random:
    seed = int(hashlib.sha256(
        f"{BATCH_SEED}|{family}|{cell}|{role}|{attempt}".encode()
    ).hexdigest()[:12], 16)
    return random.Random(seed)


def scene_program_id(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str)
    return "hier1_" + hashlib.sha256(("hier1|" + blob).encode()).hexdigest()[:16]


def _save_image(image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    image.save(path, format="PNG", optimize=False, compress_level=9)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mask(image_a, image_b, path: Path) -> str:
    import numpy as np
    from PIL import Image as PILImage
    changed = np.any(
        np.asarray(image_a, dtype=np.uint8) != np.asarray(image_b, dtype=np.uint8),
        axis=2,
    )
    if not changed.any():
        raise AssertionError(f"pair has no pixel change: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    PILImage.fromarray(changed.astype(np.uint8) * 255, mode="L").save(
        path, format="PNG", optimize=False, compress_level=9)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_family_cell(family: str, cell_name: str, cell_args: dict,
                      out_dir: Path, split: str = "development",
                      per_role: int | None = None) -> dict[str, Any]:
    rows_by_layer: dict[str, list[dict]] = {"l3": [], "l2": [], "l1": [], "probe": []}
    attempts_by_role: dict[str, int] = {}
    cue_rejections = 0
    split_rejections = 0
    balance_rejections = 0
    gold_counts: Counter = Counter()
    # switch+stable pooled member golds; max(1, ...) keeps smoke-scale builds
    # (tiny PER_ROLE in fixtures) from a zero budget while real cells get 20.
    per_role = PER_ROLE if per_role is None else per_role
    causal_gold_budget = max(1, int(BALANCE_CAP * 2 * 2 * per_role))

    for role_index, role in enumerate(ROLES):
        built = 0
        attempt = 0
        cap_attempts = per_role * 4000
        while built < per_role:
            attempt += 1
            if attempt > cap_attempts:
                raise RuntimeError(
                    f"{family}/{cell_name}/{role}: exhausted {cap_attempts} attempts "
                    f"at mother {built} (cue rejections {cue_rejections}, "
                    f"split {split_rejections}, balance {balance_rejections})")
            rng = attempt_rng(family, cell_name, role, attempt)
            if family == "hier_coord_v1":
                kind = EXTREMUM_ROTATION[(role_index * per_role + built) % 4]
                geometry = build_coord_geometry(role, kind, cell_args["n_points"], rng)
            elif family == "hier_chart_v2":
                geometry = build_chart_v2_geometry(
                    role, cell_args["series_count"], cell_args["density"], rng)
            elif family == "hier_chart_v1":
                geometry = build_chart_geometry(
                    role, cell_args["series_count"], cell_args["density"], rng)
            else:
                raise AssertionError(f"unknown family {family}")
            if geometry is None:
                continue
            scene_payload = (sorted(geometry["points_a"].items())
                             if family == "hier_coord_v1" else geometry["values_a"])
            spid = scene_program_id(scene_payload)
            if split_of(spid) != split:
                split_rejections += 1
                continue
            causal = role != "invariance"
            if family == "hier_coord_v1" and causal:
                projected = gold_counts.copy()
                projected[str(geometry["answer_a"])] += 1
                projected[str(geometry["answer_b"])] += 1
                if max(projected.values()) > causal_gold_budget:
                    balance_rejections += 1
                    continue

            # ---- render ----
            derive_l2_l1 = role != "target_switch"
            if family == "hier_coord_v1":
                if derive_l2_l1:
                    layers_a = render_coord_layers(geometry["points_a"], geometry["target_a"])
                    layers_b = render_coord_layers(geometry["points_b"], geometry["target_b"])
                    if layers_a is None or layers_b is None:
                        cue_rejections += 1
                        continue
                    base_a, l1_a, cue_a = layers_a
                    base_b, l1_b, cue_b = layers_b
                else:
                    base_a = _render_hier_coordinate_register(geometry["points_a"])
                    base_b = _render_hier_coordinate_register(geometry["points_b"])
                    l1_a = l1_b = cue_a = cue_b = None
                scene_a = [[l, p[0], p[1]] for l, p in sorted(geometry["points_a"].items())]
                scene_b = [[l, p[0], p[1]] for l, p in sorted(geometry["points_b"].items())]
                negatives = coord_hard_negatives(geometry)
            else:
                xr0 = geometry["xr"] - 1
                if derive_l2_l1:
                    layers_a = render_chart_layers(
                        geometry["values_a"], cell_args["series_count"],
                        geometry["target_a"], xr0)
                    layers_b = render_chart_layers(
                        geometry["values_b"], cell_args["series_count"],
                        geometry["target_b"], xr0)
                    if layers_a is None or layers_b is None:
                        cue_rejections += 1
                        continue
                    base_a, l1_a, cue_a = layers_a
                    base_b, l1_b, cue_b = layers_b
                else:
                    base_a = render_hier_chart(geometry["values_a"], cell_args["series_count"])
                    base_b = render_hier_chart(geometry["values_b"], cell_args["series_count"])
                    l1_a = l1_b = cue_a = cue_b = None
                scene_a, scene_b = geometry["values_a"], geometry["values_b"]
                negatives = chart_hard_negatives(geometry)

            swap = rng.random() < 0.5
            mid = (f"hier1_{FAMILY_TAG[family]}_{cell_name}_{role}_{spid[-12:]}")

            def side(a_thing, b_thing):
                return (b_thing, a_thing) if swap else (a_thing, b_thing)

            image_a_l3, image_b_l3 = side(base_a, base_b)
            answer_a, answer_b = side(geometry["answer_a"], geometry["answer_b"])
            scene_side_a, scene_side_b = side(scene_a, scene_b)
            target_side_a, target_side_b = side(
                geometry.get("target_a_name", geometry["target_a"]),
                geometry.get("target_b_name", geometry["target_b"]))

            cell_dir = out_dir / family / cell_name
            sha_a_l3 = _save_image(image_a_l3, cell_dir / "images" / f"{mid}_a_l3.png")
            sha_b_l3 = _save_image(image_b_l3, cell_dir / "images" / f"{mid}_b_l3.png")
            sha_a_l2 = _save_image(image_a_l3, cell_dir / "images" / f"{mid}_a_l2.png")
            sha_b_l2 = _save_image(image_b_l3, cell_dir / "images" / f"{mid}_b_l2.png")
            mask_l3 = _mask(image_a_l3, image_b_l3, cell_dir / "masks" / f"{mid}_l3_mask.png")

            common = {
                "schema_version": "blind-gains.hier-v1.pair.v1",
                "mother_item_id": mid,
                "family": family,
                "cell": cell_name,
                "role": role,
                "category": "hier_v1",
                "template_id": f"{family}_{cell_name}",
                "scene_program_id": spid,
                "split": split,
                "answers_equal": answer_a == answer_b,
                "answer_a": answer_a,
                "answer_b": answer_b,
                "scene_a": scene_side_a,
                "scene_b": scene_side_b,
                "hard_negatives": negatives,
                "provenance": {
                    "generator": "scripts.build_hier_dev_batch",
                    "batch_seed": BATCH_SEED,
                    "semantic_side_assignment_swapped": swap,
                    "registration": "docs/registered_hier_benchmark_v1.md",
                    "rendered_text": REGISTERED_TEXT[family],
                },
            }
            vr_common = {
                "exact_by_construction": True,
                "role": role,
                "target_label_a": str(target_side_a),
                "target_label_b": str(target_side_b),
                **({"extremum_kind": geometry["extremum_kind"],
                    "n_points": cell_args["n_points"],
                    "extremum_margin": COORD_MARGIN}
                   if family == "hier_coord_v1" else
                   {"xa": geometry["xa"], "xr": geometry["xr"],
                    "series_count": cell_args["series_count"],
                    "density": cell_args["density"],
                    "crossing_fraction_a": geometry["crossing_fraction_a"],
                    "granularity": CHART_GRANULARITY,
                    **({"crossing_fraction_b": geometry["crossing_fraction_b"],
                        "edit_kind": geometry["edit_kind"],
                        "changed": geometry["changed"]}
                       if family == "hier_chart_v2" else {})}),
            }

            rows_by_layer["l3"].append({
                **common,
                "pair_id": f"{mid}__l3",
                "layer": "l3",
                "question": geometry["questions"]["l3"],
                "image_a_path": str(cell_dir / "images" / f"{mid}_a_l3.png"),
                "image_b_path": str(cell_dir / "images" / f"{mid}_b_l3.png"),
                "image_a_sha256": sha_a_l3,
                "image_b_sha256": sha_b_l3,
                "changed_region_mask_a": str(cell_dir / "masks" / f"{mid}_l3_mask.png"),
                "changed_region_mask_b": str(cell_dir / "masks" / f"{mid}_l3_mask.png"),
                "mask_sha256": mask_l3,
                "verifier_results": {**vr_common, "layer": "l3", "oracle": "none"},
            })
            rows_by_layer["probe"].append({
                **common,
                "pair_id": f"{mid}__probe",
                "layer": "probe",
                "question": geometry["questions"]["probe"],
                "answer_a": str(target_side_a),
                "answer_b": str(target_side_b),
                "answers_equal": str(target_side_a) == str(target_side_b),
                "hard_negatives": None,
                "image_a_path": str(cell_dir / "images" / f"{mid}_a_l3.png"),
                "image_b_path": str(cell_dir / "images" / f"{mid}_b_l3.png"),
                "image_a_sha256": sha_a_l3,
                "image_b_sha256": sha_b_l3,
                "changed_region_mask_a": str(cell_dir / "masks" / f"{mid}_l3_mask.png"),
                "changed_region_mask_b": str(cell_dir / "masks" / f"{mid}_l3_mask.png"),
                "mask_sha256": mask_l3,
                "verifier_results": {**vr_common, "layer": "probe",
                                     "oracle": "none", "probe": "discovery"},
            })
            if derive_l2_l1:
                image_a_l1, image_b_l1 = side(l1_a, l1_b)
                cue_side_a, cue_side_b = side(cue_a, cue_b)
                sha_a_l1 = _save_image(image_a_l1, cell_dir / "images" / f"{mid}_a_l1.png")
                sha_b_l1 = _save_image(image_b_l1, cell_dir / "images" / f"{mid}_b_l1.png")
                mask_l1 = _mask(image_a_l1, image_b_l1,
                                cell_dir / "masks" / f"{mid}_l1_mask.png")
                for layer, q_key, ia, ib, sa, sb, mask, cue in (
                    ("l2", "l2", f"{mid}_a_l2.png", f"{mid}_b_l2.png",
                     sha_a_l2, sha_b_l2, mask_l3, None),
                    ("l1", "l2", f"{mid}_a_l1.png", f"{mid}_b_l1.png",
                     sha_a_l1, sha_b_l1, mask_l1,
                     {"a": cue_side_a, "b": cue_side_b}),
                ):
                    rows_by_layer[layer].append({
                        **common,
                        "pair_id": f"{mid}__{layer}",
                        "layer": layer,
                        "question": geometry["questions"][q_key],
                        "image_a_path": str(cell_dir / "images" / ia),
                        "image_b_path": str(cell_dir / "images" / ib),
                        "image_a_sha256": sa,
                        "image_b_sha256": sb,
                        "changed_region_mask_a": str(cell_dir / "masks" / f"{mid}_{'l3' if layer == 'l2' else 'l1'}_mask.png"),
                        "changed_region_mask_b": str(cell_dir / "masks" / f"{mid}_{'l3' if layer == 'l2' else 'l1'}_mask.png"),
                        "mask_sha256": mask,
                        "verifier_results": {
                            **vr_common, "layer": layer,
                            "oracle": "target_identity" if layer == "l2"
                            else "target_identity+location_cue",
                            **({"cue": cue} if cue else {}),
                        },
                    })
            if family == "hier_coord_v1" and causal:
                gold_counts[str(geometry["answer_a"])] += 1
                gold_counts[str(geometry["answer_b"])] += 1
            built += 1
        attempts_by_role[role] = attempt

    balance = None
    if family == "hier_coord_v1":
        total = sum(gold_counts.values())
        top_value, top_count = gold_counts.most_common(1)[0]
        balance = {
            "n_causal_member_golds": total,
            "answer_support_k": len(gold_counts),
            "max_share_value": top_value,
            "max_share": top_count / total,
            "cap": BALANCE_CAP,
            "enforced_budget_per_value": causal_gold_budget,
            # The enforced invariant is the integer budget; at full scale
            # (PER_ROLE=50, budget 20/200) it equals the 0.10 share cap. At
            # smoke scale the integer floor makes the share test meaningless.
            "pass": top_count <= causal_gold_budget,
        }
        if not balance["pass"]:
            raise AssertionError(f"balance cap violated: {balance}")

    return {
        "rows_by_layer": rows_by_layer,
        "attempts_by_role": attempts_by_role,
        "cue_rejections": cue_rejections,
        "split_rejections": split_rejections,
        "balance_rejections": balance_rejections,
        "balance": balance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/hier_v1_dev")
    parser.add_argument("--split", choices=("training", "development", "confirmatory"),
                        default="development",
                        help="scene-program bucket to generate (I6 split policy)")
    parser.add_argument("--per-role", type=int, default=None,
                        help="mother-items per role per cell (default: PER_ROLE=50)")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/hier_v1_dev_build_v1.json")
    parser.add_argument("--family", choices=("hier_coord_v1", "hier_chart_v1",
                                            "hier_chart_v2", "both"),
                        default="both")
    args = parser.parse_args()
    # --out-dir/--report may be given relative; every later relative_to(ROOT)
    # needs them absolute (this bit the chart-v2 build at manifest write).
    args.out_dir = args.out_dir.resolve()
    args.report = args.report.resolve()
    if args.report.exists():
        raise FileExistsError("refusing to overwrite the declared hier_v1 dev build report")

    cells: list[tuple[str, str, dict]] = []
    if args.family in ("hier_coord_v1", "both"):
        cells += [("hier_coord_v1", name, {"n_points": n}) for name, n in COORD_CELLS]
    if args.family in ("hier_chart_v1", "both"):
        cells += [("hier_chart_v1", name, {"series_count": s, "density": d})
                  for name, s, d in CHART_CELLS]
    if args.family == "hier_chart_v2":
        cells += [("hier_chart_v2", name, {"series_count": s, "density": d})
                  for name, s, d in CHART_V2_CELLS]

    report: dict[str, Any] = {
        "schema_version": "blind-gains.hier-v1-dev-build.v1",
        "registrations": ["docs/registered_hier_benchmark_v1.md (§6–§7, A1, A2)"],
        "batch_seed": BATCH_SEED,
        "per_role": args.per_role or PER_ROLE,
        "split": args.split,
        "roles": ROLES,
        "layer_role_matrix": "A2: l3 all roles; l2/l1 stable+invariance; probe all",
        "palette_report_9_series": hier_palette_report(),
        "crossing_bands": CROSSING_BANDS,
        "deviations": [
            "2026-08-16 attempt 1 failed pre-declaration at hier_chart_v1/"
            "s9_low/target_switch (200k attempts): the random-values proposal "
            "essentially never lands in the registered low-crossing band at 9 "
            "series. Partial artifacts (173M, no report, never declared or "
            "consumed) were removed; low-density cells now use a banded "
            "PROPOSAL while the registered band filter is unchanged and still "
            "decides acceptance."
        ],
        "cells": {},
        "file_sha256": {},
    }
    for family, cell_name, cell_args in cells:
        result = build_family_cell(family, cell_name, cell_args, args.out_dir,
                                   split=args.split, per_role=args.per_role)
        manifests = {}
        for layer, rows in result["rows_by_layer"].items():
            manifest = args.out_dir / f"manifest_{family}_{cell_name}_{layer}.jsonl"
            if manifest.exists():
                raise FileExistsError(manifest)
            blob = "".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows)
            manifest.write_text(blob, encoding="utf-8")
            manifests[layer] = {
                "path": str(manifest.relative_to(ROOT)),
                "rows": len(rows),
                "sha256": hashlib.sha256(blob.encode()).hexdigest(),
            }
        # candidate registries over the causal rows of L2/L3 (HB.5 / A2)
        registries = {}
        for layer in ("l3", "l2"):
            causal_rows = [r for r in result["rows_by_layer"][layer]
                           if r["role"] != "invariance"]
            registry_rows = build_candidate_registry_rows(causal_rows, max_candidates=16)
            registry = args.out_dir / f"candidates_{family}_{cell_name}_{layer}.jsonl"
            blob = "".join(json.dumps(r, sort_keys=True, default=str) + "\n"
                           for r in registry_rows)
            registry.write_text(blob, encoding="utf-8")
            registries[layer] = {
                "path": str(registry.relative_to(ROOT)),
                "rows": len(registry_rows),
                "sha256": hashlib.sha256(blob.encode()).hexdigest(),
            }
        report["cells"][f"{family}/{cell_name}"] = {
            "cell_args": cell_args,
            "manifests": manifests,
            "candidate_registries": registries,
            "attempts_by_role": result["attempts_by_role"],
            "cue_rejections": result["cue_rejections"],
            "split_rejections": result["split_rejections"],
            "balance_rejections": result["balance_rejections"],
            "balance": result["balance"],
        }
        print(json.dumps({f"{family}/{cell_name}": report["cells"][f"{family}/{cell_name}"]["attempts_by_role"]}))

    report["node"] = socket.gethostname()
    report["git_hash"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    report["command"] = " ".join(sys.argv)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"cells": list(report["cells"]),
                      "palette_report_9_series": report["palette_report_9_series"]},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
