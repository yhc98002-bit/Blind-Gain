from __future__ import annotations

import argparse
import json
import random
import shutil
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageChops

from src.fliptrack.build_mini_a5_train import (
    DEFAULT_EVAL_MANIFESTS,
    _evaluation_identity,
    _render_code_matrix,
    _render_scatter,
    _render_trajectories,
    _save_pair,
)
from src.fliptrack.schema import sha256_file, stable_id, write_jsonl


SCHEMA_VERSION = "blind-gains.mini-a5-catch.v1"
CATCH_TEMPLATE_IDS = (
    "mini_a5_catch_distractor_matrix_v1",
    "mini_a5_catch_distractor_trajectory_v1",
    "mini_a5_catch_distractor_scatter_v1",
)
DEFAULT_TRAIN_MANIFEST = Path("data/mini_a5_train_v1/pairs.jsonl")


def _random_code(rng: random.Random) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(rng.sample(alphabet, 3))


def _region_is_unchanged(
    image_a: Image.Image, image_b: Image.Image, box: tuple[int, int, int, int]
) -> bool:
    return ImageChops.difference(
        image_a.convert("RGB").crop(box), image_b.convert("RGB").crop(box)
    ).getbbox() is None


def _code_matrix_catch(rng: random.Random, index: int) -> dict[str, Any]:
    codes = [[_random_code(rng) for _ in range(5)] for _ in range(5)]
    target_row, target_col = rng.randrange(5), rng.randrange(5)
    answer = codes[target_row][target_col]
    distractors = [
        (row, col)
        for row in range(5)
        for col in range(5)
        if (row, col) != (target_row, target_col)
    ]
    changed_cells = rng.sample(distractors, 4)
    codes_b = [list(row) for row in codes]
    for row, col in changed_cells:
        original = codes_b[row][col]
        replacement = original
        while replacement == original:
            replacement = _random_code(rng)
        codes_b[row][col] = replacement
    image_a = _render_code_matrix(codes)
    image_b = _render_code_matrix(codes_b)
    target_box = (
        115 + target_col * 98,
        105 + target_row * 68,
        115 + (target_col + 1) * 98 + 1,
        105 + (target_row + 1) * 68 + 1,
    )
    if not _region_is_unchanged(image_a, image_b, target_box):
        raise AssertionError("matrix catch changed the queried cell")
    return {
        "index": index,
        "template_id": CATCH_TEMPLATE_IDS[0],
        "category": "document_grid_lookup_catch",
        "question": f"What code is in row R{target_row + 1}, column C{target_col + 1}?",
        "answer": answer,
        "image_a": image_a,
        "image_b": image_b,
        "verifier_results": {
            "target_row": target_row + 1,
            "target_column": target_col + 1,
            "changed_distractor_cells": [
                [row + 1, col + 1] for row, col in changed_cells
            ],
            "target_fact_a": answer,
            "target_fact_b": answer,
            "target_region_xyxy": list(target_box),
            "target_region_pixel_invariant": True,
        },
    }


def _trajectory_catch(rng: random.Random, index: int) -> dict[str, Any]:
    names = [f"S-{number}" for number in rng.sample(range(11, 90), 5)]
    values = [[rng.randrange(2, 19) * 5 for _ in range(7)] for _ in range(5)]
    target_series, target_x = rng.randrange(5), rng.randrange(1, 6)
    answer = values[target_series][target_x]
    image_a = _render_trajectories(names, values)
    target_pixel_x = 80 + target_x * (545 - 80) // 6
    target_pixel_y = 445 - answer * (445 - 95) // 100
    target_box = (
        target_pixel_x - 10,
        target_pixel_y - 10,
        target_pixel_x + 11,
        target_pixel_y + 11,
    )
    for _ in range(256):
        distractor_series = rng.choice(
            [value for value in range(5) if value != target_series]
        )
        distractor_x = rng.randrange(7)
        values_b = [list(series) for series in values]
        original = values_b[distractor_series][distractor_x]
        replacement = original
        while replacement == original:
            replacement = rng.randrange(2, 19) * 5
        values_b[distractor_series][distractor_x] = replacement
        image_b = _render_trajectories(names, values_b)
        if _region_is_unchanged(image_a, image_b, target_box):
            break
    else:
        raise RuntimeError("could not construct a target-invariant trajectory catch")
    return {
        "index": index,
        "template_id": CATCH_TEMPLATE_IDS[1],
        "category": "chart_series_lookup_catch",
        "question": f"What value does sensor {names[target_series]} have at time {target_x + 1}?",
        "answer": str(answer),
        "image_a": image_a,
        "image_b": image_b,
        "verifier_results": {
            "target_series": names[target_series],
            "target_time": target_x + 1,
            "changed_distractor_series": names[distractor_series],
            "changed_distractor_time": distractor_x + 1,
            "target_fact_a": str(answer),
            "target_fact_b": str(answer),
            "target_region_xyxy": list(target_box),
            "target_region_pixel_invariant": True,
        },
    }


def _scatter_catch(rng: random.Random, index: int) -> dict[str, Any]:
    labels = [f"P{value}" for value in rng.sample(range(10, 99), 12)]
    coordinates = rng.sample([(x, y) for x in range(10) for y in range(10)], len(labels))
    target = rng.randrange(len(labels))
    answer = coordinates[target][0]
    image_a = _render_scatter(labels, coordinates)
    target_pixel_x = 95 + coordinates[target][0] * (650 - 95) // 9
    target_pixel_y = 450 - coordinates[target][1] * (450 - 90) // 9
    target_box = (
        max(0, target_pixel_x - 12),
        max(0, target_pixel_y - 24),
        min(720, target_pixel_x + 58),
        min(520, target_pixel_y + 13),
    )
    for _ in range(256):
        distractor = rng.choice(
            [value for value in range(len(labels)) if value != target]
        )
        occupied_without_distractor = set(
            coordinates[:distractor] + coordinates[distractor + 1 :]
        )
        replacements = [
            point
            for point in ((x, y) for x in range(10) for y in range(10))
            if point not in occupied_without_distractor
            and point != coordinates[distractor]
        ]
        replacement = rng.choice(replacements)
        coordinates_b = list(coordinates)
        coordinates_b[distractor] = replacement
        image_b = _render_scatter(labels, coordinates_b)
        if _region_is_unchanged(image_a, image_b, target_box):
            break
    else:
        raise RuntimeError("could not construct a target-invariant scatter catch")
    return {
        "index": index,
        "template_id": CATCH_TEMPLATE_IDS[2],
        "category": "geometry_coordinate_lookup_catch",
        "question": f"What is the x-coordinate of point {labels[target]}?",
        "answer": str(answer),
        "image_a": image_a,
        "image_b": image_b,
        "verifier_results": {
            "target_label": labels[target],
            "changed_distractor_label": labels[distractor],
            "target_fact_a": str(answer),
            "target_fact_b": str(answer),
            "target_region_xyxy": list(target_box),
            "target_region_pixel_invariant": True,
        },
    }


CATCH_BUILDERS: tuple[Callable[[random.Random, int], dict[str, Any]], ...] = (
    _code_matrix_catch,
    _trajectory_catch,
    _scatter_catch,
)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _identity(rows: list[dict[str, Any]], id_key: str) -> dict[str, set[str]]:
    return {
        "template_ids": {str(row["template_id"]) for row in rows},
        "pair_ids": {str(row[id_key]) for row in rows},
        "image_hashes": {
            str(value)
            for row in rows
            for value in (row["image_a_sha256"], row["image_b_sha256"])
        },
    }


def _overlap(left: dict[str, set[str]], right: dict[str, set[str]]) -> dict[str, list[str]]:
    return {key: sorted(left[key] & right[key]) for key in left}


def build_catch_set(
    output_dir: Path,
    *,
    n_per_template: int,
    seed: int,
    train_manifest: Path,
    eval_manifests: list[Path],
) -> dict[str, Any]:
    if n_per_template < 1:
        raise ValueError("n_per_template must be positive")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite mini-A5 catch set: {output_dir}")
    staging = output_dir.parent / f".{output_dir.name}.staging-{uuid.uuid4().hex}"
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    try:
        staging.mkdir(parents=True)
        for builder in CATCH_BUILDERS:
            for index in range(n_per_template):
                generated = builder(rng, index)
                catch_id = "m6catch_" + stable_id(
                    seed,
                    generated["template_id"],
                    index,
                    generated["question"],
                    generated["answer"],
                )
                swapped = bool(rng.getrandbits(1))
                image_a: Image.Image = generated["image_a"]
                image_b: Image.Image = generated["image_b"]
                if swapped:
                    image_a, image_b = image_b, image_a
                paths = _save_pair(
                    image_a,
                    image_b,
                    staging_dir=staging,
                    final_dir=output_dir,
                    pair_id=catch_id,
                )
                rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "pair_group_uid": catch_id,
                        "catch_twin_id": catch_id,
                        "parent_group_uid": f"{generated['template_id']}:{seed}",
                        "template_id": generated["template_id"],
                        "category": generated["category"],
                        "question": generated["question"],
                        "answer_a": generated["answer"],
                        "answer_b": generated["answer"],
                        **paths,
                        "provenance": {
                            "generator": "src.fliptrack.build_mini_a5_catch",
                            "seed": seed,
                            "template_index": index,
                            "nuisance_side_assignment_swapped": swapped,
                            "answer_pointing_cue": False,
                            "selection_on_model_performance": False,
                        },
                        "verifier_results": {
                            **generated["verifier_results"],
                            "exact_by_construction": True,
                            "answer_preserved": True,
                            "target_fact_preserved": generated["verifier_results"][
                                "target_fact_a"
                            ]
                            == generated["verifier_results"]["target_fact_b"],
                            "changed_mask_is_exact_pixel_diff": True,
                        },
                    }
                )

        catch_identity = _identity(rows, "pair_group_uid")
        training_identity = _identity(_jsonl(train_manifest), "pair_group_uid")
        eval_identity = _evaluation_identity(eval_manifests)
        train_overlap = _overlap(catch_identity, training_identity)
        eval_overlap = _overlap(catch_identity, eval_identity)
        if any(train_overlap.values()) or any(eval_overlap.values()):
            raise ValueError(
                f"catch/train/evaluation overlap: train={train_overlap}, eval={eval_overlap}"
            )

        rng.shuffle(rows)
        write_jsonl(staging / "pairs.jsonl", rows)
        decontamination = {
            "schema_version": "blind-gains.mini-a5-catch-decontamination.v1",
            "status": "pass",
            "training_manifest": {
                "path": str(train_manifest),
                "sha256": sha256_file(train_manifest),
            },
            "generator_path": "src/fliptrack/build_mini_a5_catch.py",
            "generator_sha256": sha256_file(
                Path("src/fliptrack/build_mini_a5_catch.py")
            ),
            "evaluation_manifests": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in eval_manifests
            ],
            "catch_template_ids": sorted(CATCH_TEMPLATE_IDS),
            "training_overlap": {key: len(value) for key, value in train_overlap.items()},
            "evaluation_overlap": {key: len(value) for key, value in eval_overlap.items()},
            "selection_on_model_performance": False,
            "template_counts": dict(Counter(str(row["template_id"]) for row in rows)),
        }
        (staging / "decontamination.json").write_text(
            json.dumps(decontamination, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staging.rename(output_dir)
        return {
            "status": "pass",
            "pairs": len(rows),
            "template_counts": decontamination["template_counts"],
            "pairs_sha256": sha256_file(output_dir / "pairs.jsonl"),
            "decontamination_sha256": sha256_file(output_dir / "decontamination.json"),
        }
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/mini_a5_catch_v1"))
    parser.add_argument("--n-per-template", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026071611)
    parser.add_argument("--train-manifest", type=Path, default=DEFAULT_TRAIN_MANIFEST)
    parser.add_argument(
        "--eval-manifest", action="append", type=Path, dest="eval_manifests"
    )
    args = parser.parse_args()
    payload = build_catch_set(
        args.output_dir,
        n_per_template=args.n_per_template,
        seed=args.seed,
        train_manifest=args.train_manifest,
        eval_manifests=args.eval_manifests or list(DEFAULT_EVAL_MANIFESTS),
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
