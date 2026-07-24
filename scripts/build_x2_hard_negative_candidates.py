#!/usr/bin/env python3
"""Build the registered X2 structured hard-negative candidate sets (v2).

Scope: the geometry template (coordinate_register_twenty_point_x_v02, 600
registry pairs). Scenes are reconstructed exactly by replaying the recorded
per-pair generator seed; the replay is verified against the recorded pair_id
(a hash over seed, labels, target, and both positions), the recorded
verifier_results, the recorded side swap, and the frozen registry answers.
Negative types per docs/registered_x2_ladder_v1.md and docs/EXPERIMENT_TODO.md:
same-point y; nearest-neighbor point's x; most-similar-label point's x;
nearest gridline value; twin member's gold — sampled symmetrically over both
members so set composition never identifies gold. Candidate ids,
verbalizations, ordering, and set hashing reuse the frozen v1 machinery.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fliptrack.build_v02 import _answers_distinguishable, _sample_high_entropy_points
from src.fliptrack.schema import stable_id
from src.eval.visual_evidence_ranking import (
    _candidate_id,
    _hash_order,
    answer_signature,
    candidate_verbalization,
    sha256_json,
)

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TEMPLATE = "coordinate_register_twenty_point_x_v02"
LABEL_POOL = [f"{letter}{digit}" for letter in "BCDFGHJKLMNPRSTVWXYZ" for digit in "23456789"]
SCHEMA_VERSION = "blind-gains.visual-evidence-candidates.hard-negative.v2"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def replay_scene(pair_seed: int) -> dict[str, Any]:
    rng = random.Random(pair_seed)
    labels = rng.sample(LABEL_POOL, 20)
    coordinates = _sample_high_entropy_points(rng, len(labels))
    points_a = dict(zip(labels, coordinates))
    candidates_by_label: dict[str, list[tuple[int, int]]] = {}
    for label, point in points_a.items():
        other_points = {value for key, value in points_a.items() if key != label}
        candidates = [
            (x, point[1])
            for x in range(-7, 8)
            if x != 0
            and abs(x - point[0]) >= 3
            and _answers_distinguishable(str(point[0]), str(x))
            and all(max(abs(x - ox), abs(point[1] - oy)) >= 2 for ox, oy in other_points)
        ]
        if candidates:
            candidates_by_label[label] = candidates
    target_label = rng.choice(list(candidates_by_label))
    target_a = points_a[target_label]
    target_b = rng.choice(candidates_by_label[target_label])
    points_b = dict(points_a)
    points_b[target_label] = target_b
    swap = rng.random() < 0.5
    pair_id = "v02_register20x_" + stable_id(pair_seed, labels, target_label, target_a, target_b)
    return {
        "pair_id": pair_id,
        "labels": labels,
        "points_a": points_a,
        "points_b": points_b,
        "target_label": target_label,
        "target_a": target_a,
        "target_b": target_b,
        "swap": swap,
    }


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        previous = current
    return previous[-1]


def nearest_neighbor_x(points: dict[str, tuple[int, int]], target_label: str) -> int:
    target = points[target_label]
    best: tuple[float, str] | None = None
    for label in sorted(points):
        if label == target_label:
            continue
        point = points[label]
        distance = math.hypot(point[0] - target[0], point[1] - target[1])
        if best is None or (distance, label) < best:
            best = (distance, label)
    assert best is not None
    return points[best[1]][0]


def most_similar_label_x(points: dict[str, tuple[int, int]], target_label: str) -> int:
    best: tuple[int, str] | None = None
    for label in sorted(points):
        if label == target_label:
            continue
        distance = levenshtein(label, target_label)
        if best is None or (distance, label) < best:
            best = (distance, label)
    assert best is not None
    return points[best[1]][0]


def nearest_gridline(gold_x: int) -> int:
    candidate = gold_x + 1
    if candidate == 0:
        candidate = gold_x + 2
    if candidate > 7:
        candidate = gold_x - 1
        if candidate == 0:
            candidate = gold_x - 2
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite frozen X2 artifacts")

    registry_rows = [
        row for row in _read_jsonl(args.registry) if row["template_id"] == TEMPLATE
    ]
    if len(registry_rows) != 600:
        raise ValueError(f"expected 600 geometry registry rows, found {len(registry_rows)}")
    sources: dict[str, dict[str, Any]] = {}
    for name in ("fliptrack_v02r10_source_manifest.jsonl", "fliptrack_v02r18_source_manifest.jsonl"):
        for row in _read_jsonl(ROOT / "data" / name):
            if row.get("template_id") == TEMPLATE:
                sources[str(row["pair_id"])] = row

    output_rows: list[dict[str, Any]] = []
    set_sizes: list[int] = []
    verified = 0
    for registry_row in registry_rows:
        source_id = str(registry_row.get("source_pair_id") or registry_row["pair_id"])
        source = sources.get(source_id)
        if source is None:
            raise ValueError(f"source manifest row absent for {source_id}")
        provenance = source["provenance"]
        verifier = source["verifier_results"]
        scene = replay_scene(int(provenance["pair_seed"]))
        if scene["pair_id"] != source_id:
            raise ValueError(f"replayed pair_id mismatch for {source_id}")
        if scene["target_label"] != verifier["target_label"]:
            raise ValueError(f"replayed target label mismatch for {source_id}")
        if list(scene["target_a"]) != list(verifier["target_a"]) or list(
            scene["target_b"]
        ) != list(verifier["target_b"]):
            raise ValueError(f"replayed target positions mismatch for {source_id}")
        recorded_swap = bool(
            verifier.get(
                "semantic_side_assignment_swapped",
                provenance.get("semantic_side_assignment_swapped", False),
            )
        )
        if scene["swap"] != recorded_swap:
            raise ValueError(f"replayed side swap mismatch for {source_id}")
        if scene["swap"]:
            scene_member_a, scene_member_b = scene["points_b"], scene["points_a"]
        else:
            scene_member_a, scene_member_b = scene["points_a"], scene["points_b"]
        target_label = scene["target_label"]
        gold_a = str(scene_member_a[target_label][0])
        gold_b = str(scene_member_b[target_label][0])
        if gold_a != str(registry_row["answer_a"]) or gold_b != str(registry_row["answer_b"]):
            raise ValueError(f"replayed golds disagree with frozen registry for {source_id}")
        verified += 1

        values: dict[str, set[str]] = {}

        def add(value: int, role: str) -> None:
            key = str(value)
            values.setdefault(key, set()).add(role)

        add(int(gold_a), "gold_member_a")
        add(int(gold_b), "gold_member_b")
        add(int(gold_a), "twin_member_gold_for_b")
        add(int(gold_b), "twin_member_gold_for_a")
        add(scene_member_a[target_label][1], "same_point_y_member_a")
        add(scene_member_b[target_label][1], "same_point_y_member_b")
        add(nearest_neighbor_x(scene_member_a, target_label), "nearest_neighbor_x_member_a")
        add(nearest_neighbor_x(scene_member_b, target_label), "nearest_neighbor_x_member_b")
        add(most_similar_label_x(scene_member_a, target_label), "most_similar_label_x")
        add(nearest_gridline(int(gold_a)), "nearest_gridline_member_a")
        add(nearest_gridline(int(gold_b)), "nearest_gridline_member_b")

        pair_id = str(registry_row["pair_id"])
        ordered = sorted(values, key=lambda value: _hash_order(pair_id, value))
        candidate_records = [
            {
                "candidate_id": _candidate_id(value),
                "answer": value,
                "answer_signature": answer_signature(value),
                "verbalization": candidate_verbalization(value),
                "negative_types": sorted(values[value]),
            }
            for value in ordered
        ]
        gold_ids = {
            "a": [c["candidate_id"] for c in candidate_records if c["answer"] == gold_a],
            "b": [c["candidate_id"] for c in candidate_records if c["answer"] == gold_b],
        }
        if len(gold_ids["a"]) != 1 or len(gold_ids["b"]) != 1:
            raise AssertionError(f"gold mapping not unique for {pair_id}")
        set_sizes.append(len(candidate_records))
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "pair_id": pair_id,
            "source_pair_id": registry_row.get("source_pair_id"),
            "template_id": TEMPLATE,
            "template_label": registry_row["template_label"],
            "category": registry_row.get("category"),
            "question": registry_row["question"],
            "image_a_path": registry_row["image_a_path"],
            "image_a_sha256": registry_row.get("image_a_sha256"),
            "image_b_path": registry_row["image_b_path"],
            "image_b_sha256": registry_row.get("image_b_sha256"),
            "answer_a": gold_a,
            "answer_b": gold_b,
            "gold_candidate_id_a": gold_ids["a"][0],
            "gold_candidate_id_b": gold_ids["b"][0],
            "candidates": candidate_records,
            "candidate_count": len(candidate_records),
            "candidate_policy": {
                "structured_negative_types": [
                    "same_point_y",
                    "nearest_neighbor_x",
                    "most_similar_label_x",
                    "nearest_gridline",
                    "twin_member_gold",
                ],
                "symmetric_sampling": "every type is computed for both members with the identical deterministic rule; the shared look-alike-label value is member-invariant; set composition never identifies gold",
                "gridline_rule": "gold+1 skipping zero, reflected to gold-1 above +7",
                "selection_uses_model_outputs": False,
                "scene_source": "seeded generator replay verified against recorded pair_id, verifier_results, side swap, and frozen registry answers",
            },
        }
        frozen["candidate_set_sha256"] = sha256_json(candidate_records)
        output_rows.append(frozen)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    report = {
        "schema_version": "blind-gains.x2-hard-negative-build-report.v1",
        "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registry_input": str(args.registry),
        "registry_input_sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
        "pairs": len(output_rows),
        "scene_replays_verified": verified,
        "candidate_set_size_min": min(set_sizes),
        "candidate_set_size_max": max(set_sizes),
        "candidate_set_size_mean": sum(set_sizes) / len(set_sizes),
        "output": str(args.output),
        "output_sha256": digest,
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
