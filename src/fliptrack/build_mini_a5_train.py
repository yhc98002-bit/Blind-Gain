from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image, ImageChops, ImageDraw, ImageFont

from src.fliptrack.schema import sha256_file, stable_id, write_jsonl


WIDTH, HEIGHT = 720, 520
SCHEMA_VERSION = "blind-gains.mini-a5-train.v1"
TRAIN_TEMPLATE_IDS = (
    "mini_a5_train_code_matrix_v1",
    "mini_a5_train_named_trajectory_v1",
    "mini_a5_train_labeled_scatter_v1",
)
DEFAULT_EVAL_MANIFESTS = (
    Path("data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"),
    Path("data/fliptrack_r20_source_manifest.jsonl"),
    Path("data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"),
)
PALETTE = (
    (0, 114, 178),
    (213, 94, 0),
    (0, 158, 115),
    (204, 121, 167),
    (230, 159, 0),
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ("DejaVuSans-Bold.ttf", "Arial Bold.ttf") if bold else (
        "DejaVuSans.ttf",
        "Arial.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _exact_diff_mask(image_a: Image.Image, image_b: Image.Image) -> Image.Image:
    difference = ImageChops.difference(image_a.convert("RGB"), image_b.convert("RGB"))
    return difference.convert("L").point(lambda value: 255 if value else 0)


def _save_pair(
    image_a: Image.Image,
    image_b: Image.Image,
    *,
    staging_dir: Path,
    final_dir: Path,
    pair_id: str,
) -> dict[str, str]:
    relative = {
        "image_a_path": Path("images") / f"{pair_id}_a.png",
        "image_b_path": Path("images") / f"{pair_id}_b.png",
        "changed_region_mask_a": Path("masks") / f"{pair_id}_a_mask.png",
        "changed_region_mask_b": Path("masks") / f"{pair_id}_b_mask.png",
    }
    for path in relative.values():
        (staging_dir / path).parent.mkdir(parents=True, exist_ok=True)
    image_a.save(staging_dir / relative["image_a_path"], format="PNG", optimize=False)
    image_b.save(staging_dir / relative["image_b_path"], format="PNG", optimize=False)
    mask = _exact_diff_mask(image_a, image_b)
    if mask.getbbox() is None:
        raise ValueError(f"pair {pair_id} has no changed pixels")
    mask.save(staging_dir / relative["changed_region_mask_a"], format="PNG", optimize=False)
    mask.save(staging_dir / relative["changed_region_mask_b"], format="PNG", optimize=False)
    result = {key: str(final_dir / path) for key, path in relative.items()}
    result["image_a_sha256"] = sha256_file(staging_dir / relative["image_a_path"])
    result["image_b_sha256"] = sha256_file(staging_dir / relative["image_b_path"])
    result["mask_sha256"] = sha256_file(staging_dir / relative["changed_region_mask_a"])
    return result


def _base_canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), (250, 250, 248))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, WIDTH - 24, HEIGHT - 24), fill="white", outline=(170, 170, 170), width=2)
    draw.text((WIDTH // 2, 50), title, anchor="mm", fill=(20, 20, 20), font=_font(25, True))
    return image, draw


def _render_code_matrix(codes: list[list[str]]) -> Image.Image:
    image, draw = _base_canvas("Reference Code Matrix")
    x0, y0, cell_w, cell_h = 115, 105, 98, 68
    for col in range(5):
        draw.text(
            (x0 + col * cell_w + cell_w // 2, y0 - 25),
            f"C{col + 1}",
            anchor="mm",
            fill=(45, 45, 45),
            font=_font(17, True),
        )
    for row in range(5):
        draw.text(
            (x0 - 35, y0 + row * cell_h + cell_h // 2),
            f"R{row + 1}",
            anchor="mm",
            fill=(45, 45, 45),
            font=_font(17, True),
        )
        for col in range(5):
            box = (
                x0 + col * cell_w,
                y0 + row * cell_h,
                x0 + (col + 1) * cell_w,
                y0 + (row + 1) * cell_h,
            )
            draw.rectangle(box, fill=(247, 249, 251), outline=(135, 140, 145), width=2)
            draw.text(
                ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2),
                codes[row][col],
                anchor="mm",
                fill=(15, 15, 15),
                font=_font(21, True),
            )
    return image


def _code_matrix_pair(rng: random.Random, index: int) -> dict[str, Any]:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codes = [
        ["".join(rng.sample(alphabet, 3)) for _ in range(5)] for _ in range(5)
    ]
    row, col = rng.randrange(5), rng.randrange(5)
    answer_a = codes[row][col]
    answer_b = answer_a
    while answer_b == answer_a:
        answer_b = "".join(rng.sample(alphabet, 3))
    codes_b = [list(values) for values in codes]
    codes_b[row][col] = answer_b
    return {
        "index": index,
        "template_id": TRAIN_TEMPLATE_IDS[0],
        "category": "document_grid_lookup",
        "question": f"What code is in row R{row + 1}, column C{col + 1}?",
        "answer_a": answer_a,
        "answer_b": answer_b,
        "image_a": _render_code_matrix(codes),
        "image_b": _render_code_matrix(codes_b),
        "verifier_results": {"target_row": row + 1, "target_column": col + 1},
    }


def _marker(draw: ImageDraw.ImageDraw, x: int, y: int, kind: int, color: tuple[int, int, int]) -> None:
    radius = 5
    if kind % 3 == 0:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    elif kind % 3 == 1:
        draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=color)
    else:
        draw.polygon(((x, y - 7), (x - 7, y + 6), (x + 7, y + 6)), fill=color)


def _render_trajectories(names: list[str], values: list[list[int]]) -> Image.Image:
    image, draw = _base_canvas("Sensor Trajectories")
    left, top, right, bottom = 80, 95, 545, 445
    draw.line((left, bottom, right, bottom), fill=(45, 45, 45), width=2)
    draw.line((left, top, left, bottom), fill=(45, 45, 45), width=2)
    for tick in range(7):
        x = left + tick * (right - left) // 6
        draw.line((x, top, x, bottom), fill=(225, 225, 225), width=1)
        draw.text((x, bottom + 20), str(tick + 1), anchor="mm", fill=(35, 35, 35), font=_font(14))
    for value in range(0, 101, 20):
        y = bottom - value * (bottom - top) // 100
        draw.line((left, y, right, y), fill=(225, 225, 225), width=1)
        draw.text((left - 25, y), str(value), anchor="mm", fill=(35, 35, 35), font=_font(14))
    for series, (name, series_values) in enumerate(zip(names, values, strict=True)):
        color = PALETTE[series]
        points = [
            (left + i * (right - left) // 6, bottom - value * (bottom - top) // 100)
            for i, value in enumerate(series_values)
        ]
        draw.line(points, fill=color, width=3)
        for x, y in points:
            _marker(draw, x, y, series, color)
        legend_y = 120 + series * 58
        draw.line((580, legend_y, 620, legend_y), fill=color, width=3)
        _marker(draw, 600, legend_y, series, color)
        draw.text((630, legend_y), name, anchor="lm", fill=(25, 25, 25), font=_font(16, True))
    return image


def _trajectory_pair(rng: random.Random, index: int) -> dict[str, Any]:
    names = [f"S-{number}" for number in rng.sample(range(11, 90), 5)]
    values = [[rng.randrange(2, 19) * 5 for _ in range(7)] for _ in range(5)]
    target_series, target_x = rng.randrange(5), rng.randrange(1, 6)
    answer_a = values[target_series][target_x]
    alternatives = [value for value in range(10, 96, 5) if value != answer_a]
    answer_b = rng.choice(alternatives)
    values_b = [list(series) for series in values]
    values_b[target_series][target_x] = answer_b
    return {
        "index": index,
        "template_id": TRAIN_TEMPLATE_IDS[1],
        "category": "chart_series_lookup",
        "question": f"What value does sensor {names[target_series]} have at time {target_x + 1}?",
        "answer_a": str(answer_a),
        "answer_b": str(answer_b),
        "image_a": _render_trajectories(names, values),
        "image_b": _render_trajectories(names, values_b),
        "verifier_results": {
            "target_series": names[target_series],
            "target_time": target_x + 1,
            "answer_pointing_cue": False,
        },
    }


def _render_scatter(labels: list[str], coordinates: list[tuple[int, int]]) -> Image.Image:
    image, draw = _base_canvas("Labeled Coordinate Field")
    left, top, right, bottom = 95, 90, 650, 450
    draw.line((left, bottom, right, bottom), fill=(30, 30, 30), width=2)
    draw.line((left, top, left, bottom), fill=(30, 30, 30), width=2)
    for value in range(10):
        x = left + value * (right - left) // 9
        y = bottom - value * (bottom - top) // 9
        draw.line((x, top, x, bottom), fill=(230, 230, 230), width=1)
        draw.line((left, y, right, y), fill=(230, 230, 230), width=1)
        draw.text((x, bottom + 18), str(value), anchor="mm", fill=(40, 40, 40), font=_font(13))
        draw.text((left - 20, y), str(value), anchor="mm", fill=(40, 40, 40), font=_font(13))
    for label, (x_value, y_value) in zip(labels, coordinates, strict=True):
        x = left + x_value * (right - left) // 9
        y = bottom - y_value * (bottom - top) // 9
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(25, 95, 160))
        draw.text((x + 9, y - 9), label, anchor="lm", fill=(15, 15, 15), font=_font(14, True))
    return image


def _scatter_pair(rng: random.Random, index: int) -> dict[str, Any]:
    labels = [f"P{value}" for value in rng.sample(range(10, 99), 12)]
    coordinates = rng.sample([(x, y) for x in range(10) for y in range(10)], len(labels))
    target = rng.randrange(len(labels))
    answer_a = coordinates[target][0]
    occupied_without_target = set(coordinates[:target] + coordinates[target + 1 :])
    candidates = [
        (x, coordinates[target][1])
        for x in range(10)
        if x != answer_a and (x, coordinates[target][1]) not in occupied_without_target
    ]
    if not candidates:
        return _scatter_pair(rng, index)
    replacement = rng.choice(candidates)
    coordinates_b = list(coordinates)
    coordinates_b[target] = replacement
    return {
        "index": index,
        "template_id": TRAIN_TEMPLATE_IDS[2],
        "category": "geometry_coordinate_lookup",
        "question": f"What is the x-coordinate of point {labels[target]}?",
        "answer_a": str(answer_a),
        "answer_b": str(replacement[0]),
        "image_a": _render_scatter(labels, coordinates),
        "image_b": _render_scatter(labels, coordinates_b),
        "verifier_results": {
            "target_label": labels[target],
            "target_y_preserved": True,
            "answer_pointing_cue": False,
        },
    }


PAIR_BUILDERS: tuple[Callable[[random.Random, int], dict[str, Any]], ...] = (
    _code_matrix_pair,
    _trajectory_pair,
    _scatter_pair,
)


def _evaluation_identity(manifests: list[Path]) -> dict[str, set[str]]:
    identity = {"template_ids": set(), "pair_ids": set(), "image_hashes": set()}
    for manifest in manifests:
        if not manifest.is_file():
            raise FileNotFoundError(f"evaluation manifest is absent: {manifest}")
        for row in _jsonl_rows(manifest):
            identity["template_ids"].add(str(row["template_id"]))
            identity["pair_ids"].add(str(row["pair_id"]))
            identity["image_hashes"].update(
                (str(row["image_a_sha256"]), str(row["image_b_sha256"]))
            )
    return identity


def audit_template_disjointness(
    pair_rows: list[dict[str, Any]], eval_identity: dict[str, set[str]]
) -> dict[str, Any]:
    training_templates = {str(row["template_id"]) for row in pair_rows}
    training_pairs = {str(row["pair_group_uid"]) for row in pair_rows}
    training_hashes = {
        value
        for row in pair_rows
        for value in (str(row["image_a_sha256"]), str(row["image_b_sha256"]))
    }
    overlaps = {
        "template_ids": sorted(training_templates & eval_identity["template_ids"]),
        "pair_ids": sorted(training_pairs & eval_identity["pair_ids"]),
        "image_hashes": sorted(training_hashes & eval_identity["image_hashes"]),
    }
    if any(overlaps.values()):
        raise ValueError(f"mini-A5 training/evaluation overlap: {overlaps}")
    return {
        "training_template_ids": sorted(training_templates),
        "evaluation_template_count": len(eval_identity["template_ids"]),
        "template_id_overlap": 0,
        "pair_id_overlap": 0,
        "image_hash_overlap": 0,
    }


def build_corpus(
    output_dir: Path,
    *,
    n_per_template: int,
    seed: int,
    eval_manifests: list[Path],
) -> dict[str, Any]:
    if n_per_template < 1:
        raise ValueError("n_per_template must be positive")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite mini-A5 corpus: {output_dir}")
    staging = output_dir.parent / f".{output_dir.name}.staging-{uuid.uuid4().hex}"
    rng = random.Random(seed)
    pair_rows: list[dict[str, Any]] = []
    try:
        staging.mkdir(parents=True)
        for builder in PAIR_BUILDERS:
            for index in range(n_per_template):
                generated = builder(rng, index)
                answers = (str(generated["answer_a"]), str(generated["answer_b"]))
                swapped = bool(rng.getrandbits(1))
                if swapped:
                    generated["image_a"], generated["image_b"] = (
                        generated["image_b"],
                        generated["image_a"],
                    )
                    answers = (answers[1], answers[0])
                pair_group_uid = "m6_" + stable_id(
                    seed,
                    generated["template_id"],
                    index,
                    generated["question"],
                    answers,
                )
                paths = _save_pair(
                    generated["image_a"],
                    generated["image_b"],
                    staging_dir=staging,
                    final_dir=output_dir,
                    pair_id=pair_group_uid,
                )
                pair_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "pair_group_uid": pair_group_uid,
                        "parent_group_uid": f"{generated['template_id']}:{seed}",
                        "template_id": generated["template_id"],
                        "category": generated["category"],
                        "question": generated["question"],
                        "answer_a": answers[0],
                        "answer_b": answers[1],
                        **paths,
                        "provenance": {
                            "generator": "src.fliptrack.build_mini_a5_train",
                            "seed": seed,
                            "template_index": index,
                            "semantic_side_assignment_swapped": swapped,
                            "answer_pointing_cue": False,
                        },
                        "verifier_results": {
                            **generated["verifier_results"],
                            "exact_by_construction": True,
                            "answers_differ": answers[0] != answers[1],
                            "changed_mask_is_exact_pixel_diff": True,
                        },
                    }
                )

        eval_identity = _evaluation_identity(eval_manifests)
        disjointness = audit_template_disjointness(pair_rows, eval_identity)
        rng.shuffle(pair_rows)
        train_rows: list[dict[str, Any]] = []
        for pair in pair_rows:
            for member in ("a", "b"):
                train_rows.append(
                    {
                        "problem": f"<image>{pair['question']}",
                        "answer": pair[f"answer_{member}"],
                        "images": [pair[f"image_{member}_path"]],
                        "pair_group_uid": pair["pair_group_uid"],
                        "pair_member": member,
                        "template_id": pair["template_id"],
                        "category": pair["category"],
                    }
                )

        write_jsonl(staging / "pairs.jsonl", pair_rows)
        write_jsonl(staging / "train.jsonl", train_rows)
        pq.write_table(
            pa.Table.from_pylist(train_rows),
            staging / "train.parquet",
            compression="zstd",
        )
        source_path = Path(__file__)
        side_counts = Counter(
            (row["template_id"], row["provenance"]["semantic_side_assignment_swapped"])
            for row in pair_rows
        )
        decontamination = {
            "schema_version": "blind-gains.mini-a5-decontamination.v1",
            "status": "pass",
            "seed": seed,
            "n_pairs": len(pair_rows),
            "n_training_rows": len(train_rows),
            "template_counts": dict(sorted(Counter(row["template_id"] for row in pair_rows).items())),
            "parent_group_uids": sorted({row["parent_group_uid"] for row in pair_rows}),
            "semantic_side_assignment_counts": {
                f"{template}:{str(swapped).lower()}": count
                for (template, swapped), count in sorted(side_counts.items())
            },
            "training_pair_adjacency": all(
                train_rows[index]["pair_group_uid"] == train_rows[index + 1]["pair_group_uid"]
                and train_rows[index]["pair_member"] == "a"
                and train_rows[index + 1]["pair_member"] == "b"
                for index in range(0, len(train_rows), 2)
            ),
            "evaluation_manifests": [
                {"path": str(path), "sha256": sha256_file(path)} for path in eval_manifests
            ],
            "disjointness": disjointness,
            "generator_path": str(source_path),
            "generator_sha256": sha256_file(source_path),
            "answer_pointing_cues": 0,
        }
        if not decontamination["training_pair_adjacency"]:
            raise ValueError("training rows lost A/B adjacency")
        (staging / "decontamination.json").write_text(
            json.dumps(decontamination, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staging.rename(output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    artifact = {
        "output_dir": str(output_dir),
        "pairs": str(output_dir / "pairs.jsonl"),
        "train_jsonl": str(output_dir / "train.jsonl"),
        "train_parquet": str(output_dir / "train.parquet"),
        "decontamination": str(output_dir / "decontamination.json"),
        "n_pairs": len(pair_rows),
        "n_training_rows": len(train_rows),
    }
    artifact["hashes"] = {
        key: sha256_file(path)
        for key, path in artifact.items()
        if key in {"pairs", "train_jsonl", "train_parquet", "decontamination"}
    }
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/mini_a5_train_v1"))
    parser.add_argument("--n-per-template", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026071606)
    parser.add_argument("--eval-manifest", action="append", type=Path)
    args = parser.parse_args()
    manifests = args.eval_manifest or list(DEFAULT_EVAL_MANIFESTS)
    artifact = build_corpus(
        args.output_dir,
        n_per_template=args.n_per_template,
        seed=args.seed,
        eval_manifests=manifests,
    )
    print(json.dumps(artifact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
