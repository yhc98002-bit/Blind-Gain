from __future__ import annotations

import argparse
import math
import random
import string
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.eval.fliptrack_metrics import match_tier
from src.fliptrack.build_v01 import generate_doc_pairs
from src.fliptrack.schema import pair_record, stable_id, write_jsonl


COLORS = [
    (38, 94, 168),
    (205, 75, 65),
    (49, 139, 87),
    (142, 84, 160),
    (218, 145, 42),
    (32, 145, 153),
    (190, 91, 132),
    (105, 114, 130),
    (113, 92, 52),
    (61, 61, 61),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf"] if bold else ["DejaVuSans.ttf", "Arial.ttf"]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _answers_distinguishable(answer_a: str, answer_b: str) -> bool:
    return match_tier(answer_a, answer_b) == 0 and match_tier(answer_b, answer_a) == 0


def _exact_change_mask(image_a: Image.Image, image_b: Image.Image) -> Image.Image:
    array_a = np.asarray(image_a.convert("RGB"))
    array_b = np.asarray(image_b.convert("RGB"))
    changed = np.any(array_a != array_b, axis=2).astype(np.uint8) * 255
    return Image.fromarray(changed, mode="L")


def _save_rendered_pair(
    *,
    out_dir: Path,
    pair_id: str,
    image_a: Image.Image,
    image_b: Image.Image,
    question: str,
    answer_a: str,
    answer_b: str,
    category: str,
    template_id: str,
    provenance: dict[str, Any],
    verifier_results: dict[str, Any],
    swap_sides: bool = False,
) -> dict[str, Any]:
    if swap_sides:
        image_a, image_b = image_b, image_a
        answer_a, answer_b = answer_b, answer_a
    provenance = dict(provenance)
    provenance["semantic_side_assignment_swapped"] = swap_sides
    verifier_results = dict(verifier_results)
    verifier_results["semantic_side_assignment_swapped"] = swap_sides
    if image_a.size != image_b.size:
        raise ValueError(f"pair dimensions differ for {pair_id}")
    if not _answers_distinguishable(answer_a, answer_b):
        raise ValueError(f"degenerate answers for {pair_id}: {answer_a!r}, {answer_b!r}")
    image_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    image_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    image_a_path = image_dir / f"{pair_id}_a.png"
    image_b_path = image_dir / f"{pair_id}_b.png"
    mask_a_path = mask_dir / f"{pair_id}_a_mask.png"
    mask_b_path = mask_dir / f"{pair_id}_b_mask.png"
    mask = _exact_change_mask(image_a, image_b)
    if not np.any(np.asarray(mask)):
        raise ValueError(f"pair has no pixel change: {pair_id}")
    image_a.save(image_a_path, format="PNG", optimize=False, compress_level=9)
    image_b.save(image_b_path, format="PNG", optimize=False, compress_level=9)
    mask.save(mask_a_path, format="PNG", optimize=False, compress_level=9)
    mask.save(mask_b_path, format="PNG", optimize=False, compress_level=9)
    return pair_record(
        pair_id=pair_id,
        image_a_path=str(image_a_path),
        image_b_path=str(image_b_path),
        changed_region_mask_a=str(mask_a_path),
        changed_region_mask_b=str(mask_b_path),
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        category=category,
        template_id=template_id,
        provenance=provenance,
        verifier_results=verifier_results,
    )


def _procedural_labels(rng: random.Random, count: int) -> list[str]:
    labels: set[str] = set()
    consonants = "BCDFGHJKLMNPRSTVWXYZ"
    vowels = "AEIOU"
    while len(labels) < count:
        label = f"{rng.choice(consonants)}{rng.choice(vowels)}{rng.choice(consonants)}-{rng.randint(10, 99)}{rng.choice(string.ascii_uppercase)}"
        labels.add(label)
    return list(labels)


def _render_chart(labels: list[str], values: list[list[int]], target_series: int, target_x: int) -> Image.Image:
    width, height = 1200, 760
    image = Image.new("RGB", (width, height), (249, 250, 248))
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 90, 78, 820, 650
    draw.text((width // 2, 30), "Multi-Series Calibration Trace", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    draw.rectangle((left, top, right, bottom), fill=(255, 255, 255), outline=(45, 45, 45), width=2)
    for tick in range(0, 101, 10):
        y = bottom - round(tick / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=(232, 232, 232), width=1)
        if tick % 20 == 0:
            draw.text((left - 12, y), str(tick), anchor="rm", font=_font(13), fill=(55, 55, 55))
    x_positions = [left + 55 + index * 128 for index in range(6)]
    for index, x in enumerate(x_positions, start=1):
        draw.line((x, top, x, bottom), fill=(242, 242, 242), width=1)
        draw.text((x, bottom + 24), str(index), anchor="mm", font=_font(14), fill=(55, 55, 55))
    draw.text(((left + right) // 2, bottom + 54), "x", anchor="mm", font=_font(17, True), fill=(40, 40, 40))

    for series_index, series_values in enumerate(values):
        points = [
            (x, bottom - round(value / 100 * (bottom - top)))
            for x, value in zip(x_positions, series_values)
        ]
        color = COLORS[series_index]
        draw.line(points, fill=color, width=3)
        for x, y in points:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color, outline=(255, 255, 255), width=1)
        if series_index == target_series:
            target_point = points[target_x]
            draw.ellipse(
                (target_point[0] - 15, target_point[1] - 15, target_point[0] + 15, target_point[1] + 15),
                fill=(255, 255, 255),
                outline=(0, 0, 0),
                width=2,
            )
            draw.text(target_point, "*", anchor="mm", font=_font(26, True), fill=(0, 0, 0))

    legend_left = 855
    draw.rectangle((legend_left, 74, 1168, 650), fill=(255, 255, 255), outline=(175, 175, 175), width=2)
    draw.text((1010, 100), "Series key", anchor="mm", font=_font(19, True), fill=(25, 25, 25))
    for index, label in enumerate(labels):
        y = 142 + index * 48
        draw.line((legend_left + 28, y, legend_left + 65, y), fill=COLORS[index], width=5)
        draw.ellipse((legend_left + 43, y - 4, legend_left + 51, y + 4), fill=COLORS[index])
        draw.text((legend_left + 82, y), label, anchor="lm", font=_font(16), fill=(20, 20, 20))
        if index == target_series:
            draw.text((legend_left + 16, y), "*", anchor="mm", font=_font(25, True), fill=(0, 0, 0))
    draw.text((90, 714), f"The black star marks the queried point at x = {target_x + 1}.", font=_font(14), fill=(75, 75, 75))
    return image


def generate_chart_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        labels = _procedural_labels(rng, 10)
        values_a = [[rng.randrange(10, 91, 10) for _ in range(6)] for _ in range(10)]
        target_series = rng.randrange(10)
        target_x = rng.randrange(1, 5)
        values_b = [list(series) for series in values_a]
        candidates = [value for value in range(10, 91, 10) if abs(value - values_a[target_series][target_x]) >= 20]
        values_b[target_series][target_x] = rng.choice(candidates)
        answer_a = str(values_a[target_series][target_x])
        answer_b = str(values_b[target_series][target_x])
        pair_id = "v02_chart_" + stable_id(pair_seed, labels, target_series, target_x, answer_a, answer_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_chart(labels, values_a, target_series, target_x),
                image_b=_render_chart(labels, values_b, target_series, target_x),
                question=f"What is the value of the starred series at x = {target_x + 1}?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="chart_two_hop_read",
                template_id="starred_series_value_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "legend_bind_then_coordinate_read",
                    "training_domain_alignment": "medium",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "target_series_index": target_series,
                    "target_x": target_x + 1,
                    "shared_content_seed": pair_seed,
                    "only_semantic_change": "one series value",
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _render_legible_chart(
    labels: list[str], values: list[list[int]], target_series: int, target_x: int
) -> Image.Image:
    width, height = 1400, 900
    image = Image.new("RGB", (width, height), (249, 250, 248))
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 100, 82, 1010, 770
    draw.text(
        (width // 2, 32),
        "Eight-Interval Calibration Trace",
        anchor="mm",
        font=_font(25, True),
        fill=(25, 25, 25),
    )
    draw.rectangle((left, top, right, bottom), fill="white", outline=(45, 45, 45), width=2)
    for tick in range(0, 101, 10):
        y = bottom - round(tick / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=(226, 229, 232), width=1)
        draw.text((left - 14, y), str(tick), anchor="rm", font=_font(15), fill=(50, 50, 50))
    x_positions = [left + 55 + index * 114 for index in range(8)]
    for index, x in enumerate(x_positions, start=1):
        draw.line((x, top, x, bottom), fill=(240, 242, 244), width=1)
        draw.text((x, bottom + 27), str(index), anchor="mm", font=_font(16), fill=(50, 50, 50))
    target_column_x = x_positions[target_x]
    for y in range(top + 4, bottom, 18):
        draw.line((target_column_x, y, target_column_x, min(y + 8, bottom)), fill=(120, 120, 120), width=2)
    draw.text(((left + right) // 2, bottom + 59), "x", anchor="mm", font=_font(18, True), fill=(40, 40, 40))

    for series_index, series_values in enumerate(values):
        points = [
            (x, bottom - round(value / 100 * (bottom - top)))
            for x, value in zip(x_positions, series_values)
        ]
        color = COLORS[series_index]
        draw.line(points, fill=color, width=5 if series_index == target_series else 3)
        for x, y in points:
            radius = 6 if series_index == target_series else 4
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline="white", width=2)
        if series_index == target_series:
            x, y = points[target_x]
            draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(15, 15, 15), width=3)

    legend_left = 1040
    draw.rectangle((legend_left, 82, 1370, 500), fill="white", outline=(165, 165, 165), width=2)
    draw.text((1205, 112), "Series key", anchor="mm", font=_font(20, True), fill=(25, 25, 25))
    for index, label in enumerate(labels):
        y = 160 + index * 54
        draw.line(
            (legend_left + 40, y, legend_left + 92, y),
            fill=COLORS[index],
            width=6 if index == target_series else 4,
        )
        draw.ellipse((legend_left + 61, y - 5, legend_left + 71, y + 5), fill=COLORS[index])
        draw.text((legend_left + 110, y), label, anchor="lm", font=_font(18, True), fill=(20, 20, 20))
        if index == target_series:
            draw.text((legend_left + 20, y), "*", anchor="mm", font=_font(27, True), fill=(0, 0, 0))
    draw.multiline_text(
        (1040, 548),
        "The dashed guide marks x.\nThe star selects the series.",
        font=_font(16),
        fill=(70, 70, 70),
        spacing=8,
    )
    return image


def generate_legible_chart_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        labels = _procedural_labels(rng, 6)
        values_a = [[rng.randrange(10, 91, 10) for _ in range(8)] for _ in range(6)]
        target_series = rng.randrange(6)
        target_x = rng.randrange(1, 7)
        values_b = [list(series) for series in values_a]
        current = values_a[target_series][target_x]
        candidates = [value for value in range(10, 91, 10) if abs(value - current) >= 20]
        values_b[target_series][target_x] = rng.choice(candidates)
        answer_a = str(current)
        answer_b = str(values_b[target_series][target_x])
        pair_id = "v02_chart6x8_" + stable_id(
            pair_seed, labels, target_series, target_x, answer_a, answer_b
        )
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_legible_chart(labels, values_a, target_series, target_x),
                image_b=_render_legible_chart(labels, values_b, target_series, target_x),
                question=f"What is the value of the starred series at x = {target_x + 1}?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="chart_two_hop_read",
                template_id="starred_series_value_legible_v03",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "legend_bind_then_guided_coordinate_read",
                    "training_domain_alignment": "medium",
                    "caption_failure_targeted": "forty_eight_question_blind_series_value_bindings",
                    "render_variant": "six_series_eight_intervals_large_plot_r11",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "series_count": len(labels),
                    "x_count": 8,
                    "target_series_index": target_series,
                    "target_x": target_x + 1,
                    "shared_content_seed": pair_seed,
                    "only_semantic_change": "one series value",
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


SYMBOLS = ("A", "H", "K", "M", "2", "4", "7", "9")


def _draw_symbol(draw: ImageDraw.ImageDraw, symbol: str, center: tuple[int, int], size: int = 14) -> None:
    x, y = center
    ink = (27, 55, 82)
    if symbol not in SYMBOLS:
        raise ValueError(symbol)
    draw.text((x, y), symbol, anchor="mm", font=_font(size * 2, True), fill=ink)


def _render_grid(grid: list[list[str]], row_labels: list[str], col_labels: list[str]) -> Image.Image:
    width, height = 1260, 1230
    image = Image.new("RGB", (width, height), (252, 252, 250))
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 36), "Indexed Symbol Matrix", anchor="mm", font=_font(24, True), fill=(20, 20, 20))
    left, top, cell = 130, 108, 86
    for column, label in enumerate(col_labels):
        draw.text((left + column * cell + cell // 2, top - 26), label, anchor="mm", font=_font(14, True), fill=(35, 35, 35))
    for row, label in enumerate(row_labels):
        draw.text((left - 32, top + row * cell + cell // 2), label, anchor="mm", font=_font(14, True), fill=(35, 35, 35))
        for column, symbol in enumerate(grid[row]):
            x0 = left + column * cell
            y0 = top + row * cell
            fill = (255, 255, 255) if (row + column) % 2 == 0 else (245, 247, 249)
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=fill, outline=(165, 165, 165), width=1)
            _draw_symbol(draw, symbol, (x0 + cell // 2, y0 + cell // 2), size=17)
    draw.text((left, 1182), "Use the row and column headers; no cell is highlighted.", font=_font(16), fill=(78, 78, 78))
    return image


def generate_grid_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        row_labels = [f"{rng.choice('GHJKLMNPQRSTVWXYZ')}{rng.randint(2, 9)}" for _ in range(12)]
        while len(set(row_labels)) < 12:
            row_labels = [f"{rng.choice('GHJKLMNPQRSTVWXYZ')}{rng.randint(2, 9)}" for _ in range(12)]
        col_labels = [f"{value:02d}" for value in rng.sample(range(11, 90), 12)]
        grid_a = [[rng.choice(SYMBOLS) for _ in range(12)] for _ in range(12)]
        target_row = rng.randrange(12)
        target_col = rng.randrange(12)
        grid_b = [list(row) for row in grid_a]
        grid_b[target_row][target_col] = rng.choice([symbol for symbol in SYMBOLS if symbol != grid_a[target_row][target_col]])
        answer_a = grid_a[target_row][target_col]
        answer_b = grid_b[target_row][target_col]
        pair_id = "v02_grid_" + stable_id(pair_seed, row_labels, col_labels, target_row, target_col, answer_a, answer_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_grid(grid_a, row_labels, col_labels),
                image_b=_render_grid(grid_b, row_labels, col_labels),
                question=f"Which symbol is at row {row_labels[target_row]} and column {col_labels[target_col]}?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="spatial_indexing",
                template_id="indexed_symbol_grid_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "row_column_indexing",
                    "training_domain_alignment": "low",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "target_row": target_row,
                    "target_column": target_col,
                    "shared_content_seed": pair_seed,
                    "highlight_present": False,
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _triangle_apex(left_angle: int, right_angle: int) -> tuple[float, float]:
    base = 620.0
    left_radians = math.radians(left_angle)
    right_radians = math.radians(right_angle)
    distance = base / (math.cos(left_radians) + math.sin(left_radians) * math.cos(right_radians) / math.sin(right_radians))
    return 180 + distance * math.cos(left_radians), 590 - distance * math.sin(left_radians)


def _render_triangle(left_angle: int, right_angle: int) -> Image.Image:
    width, height = 980, 720
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left = (180, 590)
    right = (800, 590)
    apex = _triangle_apex(left_angle, right_angle)
    draw.text((width // 2, 38), "Triangle Angle Check", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    draw.line((left, apex, right, left), fill=(34, 62, 91), width=5, joint="curve")
    draw.arc((left[0] - 5, left[1] - 90, left[0] + 105, left[1] + 20), 270, 360, fill=(175, 70, 65), width=3)
    draw.arc((right[0] - 105, right[1] - 90, right[0] + 5, right[1] + 20), 180, 270, fill=(175, 70, 65), width=3)
    draw.text((left[0] + 75, left[1] - 40), f"{left_angle}°", anchor="mm", font=_font(20, True), fill=(120, 35, 35))
    draw.text((right[0] - 75, right[1] - 40), f"{right_angle}°", anchor="mm", font=_font(20, True), fill=(120, 35, 35))
    draw.text((apex[0], apex[1] + 48), "x°", anchor="mm", font=_font(22, True), fill=(32, 95, 66))
    draw.text((left[0] - 20, left[1] + 27), "Q", anchor="mm", font=_font(18, True), fill=(25, 25, 25))
    draw.text((right[0] + 20, right[1] + 27), "R", anchor="mm", font=_font(18, True), fill=(25, 25, 25))
    draw.text((apex[0], apex[1] - 25), "P", anchor="mm", font=_font(18, True), fill=(25, 25, 25))
    draw.text((180, 660), "Diagram rendered from the displayed base angles.", font=_font(14), fill=(80, 80, 80))
    return image


def generate_triangle_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        right_angle = rng.randint(42, 68)
        left_a = rng.randint(42, 68)
        valid = [value for value in range(38, 73) if value != left_a and 35 <= 180 - value - right_angle <= 95]
        left_b = rng.choice(valid)
        answer_a = str(180 - left_a - right_angle)
        answer_b = str(180 - left_b - right_angle)
        if not _answers_distinguishable(answer_a, answer_b):
            raise AssertionError("triangle answer sampler emitted cross-matching answers")
        pair_id = "v02_triangle_" + stable_id(pair_seed, left_a, left_b, right_angle)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_triangle(left_a, right_angle),
                image_b=_render_triangle(left_b, right_angle),
                question="What is the measure of angle P in degrees?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_angle",
                template_id="triangle_missing_angle_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "angle_label_and_geometry_change",
                    "training_domain_alignment": "high",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "right_angle": right_angle,
                    "left_angle_a": left_a,
                    "left_angle_b": left_b,
                    "triangle_sum_a": left_a + right_angle + int(answer_a),
                    "triangle_sum_b": left_b + right_angle + int(answer_b),
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _render_parallel_angles(theta: int, query_relation: str) -> Image.Image:
    width, height = 980, 720
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    top_y, bottom_y = 220, 510
    top_x = 380
    delta_x = (bottom_y - top_y) / math.tan(math.radians(theta))
    bottom_x = top_x + delta_x
    draw.text((width // 2, 38), "Parallel-Line Angle Diagram", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    draw.line((90, top_y, 890, top_y), fill=(35, 68, 103), width=5)
    draw.line((90, bottom_y, 890, bottom_y), fill=(35, 68, 103), width=5)
    extension = 120
    dx = delta_x / (bottom_y - top_y) * extension
    draw.line((top_x - dx, top_y - extension, bottom_x + dx, bottom_y + extension), fill=(145, 65, 55), width=5)
    for x, y in ((210, top_y), (210, bottom_y)):
        draw.line((x - 10, y - 8, x, y), fill=(35, 68, 103), width=3)
        draw.line((x, y, x + 10, y - 8), fill=(35, 68, 103), width=3)
    draw.text((112, top_y - 24), "l", font=_font(18, True), fill=(25, 25, 25))
    draw.text((112, bottom_y - 24), "m", font=_font(18, True), fill=(25, 25, 25))
    draw.text((top_x + 70, top_y + 42), f"{theta}°", anchor="mm", font=_font(21, True), fill=(120, 35, 35))
    draw.arc((top_x - 5, top_y - 5, top_x + 115, top_y + 115), 180, 270, fill=(120, 35, 35), width=3)
    if query_relation == "alternate":
        label_x, label_y = bottom_x - 66, bottom_y - 42
        arc_box = (bottom_x - 115, bottom_y - 115, bottom_x + 5, bottom_y + 5)
        arc_angles = (0, 90)
    elif query_relation == "same_side":
        label_x, label_y = bottom_x + 66, bottom_y - 42
        arc_box = (bottom_x - 5, bottom_y - 115, bottom_x + 115, bottom_y + 5)
        arc_angles = (90, 180)
    else:
        raise ValueError(query_relation)
    draw.ellipse(
        (label_x - 42, label_y - 30, label_x + 42, label_y + 30),
        fill=(226, 246, 232),
        outline=(35, 110, 72),
        width=2,
    )
    draw.arc(arc_box, *arc_angles, fill=(35, 110, 72), width=4)
    draw.text((label_x, label_y), "x°", anchor="mm", font=_font(22, True), fill=(35, 110, 72))
    draw.text((150, 650), "Matching arrow marks indicate l ∥ m.", font=_font(15), fill=(75, 75, 75))
    return image


def generate_parallel_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        theta = rng.randint(32, 78)
        answer_a = str(theta)
        answer_b = str(180 - theta)
        pair_id = "v02_parallel_" + stable_id(pair_seed, theta)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_parallel_angles(theta, "alternate"),
                image_b=_render_parallel_angles(theta, "same_side"),
                question="Lines l and m are parallel. What is x in degrees?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_parallel_lines",
                template_id="parallel_angle_marker_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "queried_angle_marker_relocation",
                    "training_domain_alignment": "high",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "given_angle": theta,
                    "relation_a": "alternate_interior",
                    "relation_b": "same_side_interior",
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _format_fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _render_coordinate_line(point_p: tuple[int, int], point_q: tuple[int, int]) -> Image.Image:
    width, height = 820, 820
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 34), "Coordinate Plane", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    origin = (410, 430)
    scale = 52

    def pixel(point: tuple[int, int]) -> tuple[int, int]:
        return origin[0] + point[0] * scale, origin[1] - point[1] * scale

    for value in range(-6, 7):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, origin[1] - 6 * scale, x, origin[1] + 6 * scale), fill=(230, 232, 235), width=1)
        draw.line((origin[0] - 6 * scale, y, origin[0] + 6 * scale, y), fill=(230, 232, 235), width=1)
        if value:
            draw.text((x, origin[1] + 18), str(value), anchor="mm", font=_font(12), fill=(75, 75, 75))
            draw.text((origin[0] - 18, y), str(value), anchor="mm", font=_font(12), fill=(75, 75, 75))
    draw.line((origin[0] - 6 * scale, origin[1], origin[0] + 6 * scale, origin[1]), fill=(45, 45, 45), width=3)
    draw.line((origin[0], origin[1] - 6 * scale, origin[0], origin[1] + 6 * scale), fill=(45, 45, 45), width=3)
    p_pixel, q_pixel = pixel(point_p), pixel(point_q)
    draw.line((p_pixel, q_pixel), fill=(38, 94, 168), width=5)
    corner = (q_pixel[0], p_pixel[1])
    draw.line((p_pixel, corner), fill=(72, 130, 82), width=3)
    draw.line((corner, q_pixel), fill=(72, 130, 82), width=3)
    for label, location, offset in (("P", p_pixel, (-16, -22)), ("Q", q_pixel, (16, -22))):
        draw.ellipse((location[0] - 8, location[1] - 8, location[0] + 8, location[1] + 8), fill=(185, 55, 55), outline="white", width=2)
        draw.text((location[0] + offset[0], location[1] + offset[1]), label, anchor="mm", font=_font(18, True), fill=(25, 25, 25))
    draw.text((96, 770), "Read each point from the grid before computing rise over run.", font=_font(14), fill=(75, 75, 75))
    return image


def generate_coordinate_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        while True:
            point_p = (rng.randint(-5, -1), rng.randint(-5, 4))
            point_q_a = (rng.randint(1, 5), rng.randint(-4, 5))
            point_q_b = (rng.randint(1, 5), rng.randint(-4, 5))
            if point_q_a == point_q_b or point_p[0] in {point_q_a[0], point_q_b[0]}:
                continue
            slope_a = Fraction(point_q_a[1] - point_p[1], point_q_a[0] - point_p[0])
            slope_b = Fraction(point_q_b[1] - point_p[1], point_q_b[0] - point_p[0])
            answer_a = _format_fraction(slope_a)
            answer_b = _format_fraction(slope_b)
            if slope_a != slope_b and _answers_distinguishable(answer_a, answer_b):
                break
        pair_id = "v02_coordinate_" + stable_id(pair_seed, point_p, point_q_a, point_q_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_coordinate_line(point_p, point_q_a),
                image_b=_render_coordinate_line(point_p, point_q_b),
                question="What is the slope of line PQ? Give an integer or reduced fraction.",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_coordinate",
                template_id="coordinate_slope_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "point_relocation_then_slope",
                    "training_domain_alignment": "high",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "point_p": point_p,
                    "point_q_a": point_q_a,
                    "point_q_b": point_q_b,
                    "slope_a": answer_a,
                    "slope_b": answer_b,
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _render_coordinate_point(points: dict[str, tuple[int, int]]) -> Image.Image:
    width, height = 900, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 34), "Coordinate Point Register", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    origin = (450, 470)
    scale = 57

    def pixel(point: tuple[int, int]) -> tuple[int, int]:
        return origin[0] + point[0] * scale, origin[1] - point[1] * scale

    for value in range(-6, 7):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, origin[1] - 6 * scale, x, origin[1] + 6 * scale), fill=(224, 228, 232), width=1)
        draw.line((origin[0] - 6 * scale, y, origin[0] + 6 * scale, y), fill=(224, 228, 232), width=1)
        if value:
            draw.text((x, origin[1] + 20), str(value), anchor="mm", font=_font(13), fill=(65, 65, 65))
            draw.text((origin[0] - 22, y), str(value), anchor="mm", font=_font(13), fill=(65, 65, 65))
    draw.line((origin[0] - 6 * scale, origin[1], origin[0] + 6 * scale, origin[1]), fill=(35, 35, 35), width=3)
    draw.line((origin[0], origin[1] - 6 * scale, origin[0], origin[1] + 6 * scale), fill=(35, 35, 35), width=3)
    styles = {
        "P": ((45, 108, 176), "circle"),
        "Q": ((190, 55, 55), "square"),
        "R": ((45, 145, 87), "diamond"),
        "S": ((135, 80, 160), "circle"),
    }
    for label, point in points.items():
        x, y = pixel(point)
        color, shape = styles[label]
        if shape == "square":
            draw.rectangle((x - 10, y - 10, x + 10, y + 10), fill=color, outline="white", width=2)
        elif shape == "diamond":
            draw.polygon(((x, y - 12), (x - 12, y), (x, y + 12), (x + 12, y)), fill=color)
        else:
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color, outline="white", width=2)
        draw.text((x + 20, y - 20), label, anchor="mm", font=_font(19, True), fill=(20, 20, 20))
    draw.text((108, 850), "Read coordinates from the numbered axes; point labels do not contain coordinates.", font=_font(14), fill=(75, 75, 75))
    return image


def generate_coordinate_point_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        while True:
            shared = {label: (rng.randint(-5, 5), rng.randint(-5, 5)) for label in ("P", "R", "S")}
            q_a = (rng.randint(-5, 5), rng.randint(-5, 5))
            q_b = (rng.randint(-5, 5), rng.randint(-5, 5))
            if q_a != q_b and q_a not in shared.values() and q_b not in shared.values() and len(set(shared.values())) == 3:
                break
        points_a = {**shared, "Q": q_a}
        points_b = {**shared, "Q": q_b}
        answer_a = f"({q_a[0]}, {q_a[1]})"
        answer_b = f"({q_b[0]}, {q_b[1]})"
        pair_id = "v02_point_" + stable_id(pair_seed, shared, q_a, q_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_coordinate_point(points_a),
                image_b=_render_coordinate_point(points_b),
                question="What are the coordinates of point Q? Answer as (x, y).",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_coordinate_read",
                template_id="coordinate_point_read_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "point_localization_then_coordinate_read",
                    "training_domain_alignment": "high",
                },
                verifier_results={"exact_by_construction": True, "shared_points": shared, "q_a": q_a, "q_b": q_b},
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _render_coordinate_register(
    points: dict[str, tuple[int, int]], *, scale: int = 65, point_radius: int = 8, label_size: int = 16
) -> Image.Image:
    width, height = 1080, 960
    image = Image.new("RGB", (width, height), (250, 250, 248))
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 35), "Coordinate Survey Register", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    origin = (540, 500)

    def pixel(point: tuple[int, int]) -> tuple[int, int]:
        return origin[0] + point[0] * scale, origin[1] - point[1] * scale

    plot_left = origin[0] - 6 * scale
    plot_right = origin[0] + 6 * scale
    plot_top = origin[1] - 6 * scale
    plot_bottom = origin[1] + 6 * scale
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), fill="white", outline=(75, 75, 75), width=2)
    for value in range(-6, 7):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, plot_top, x, plot_bottom), fill=(224, 228, 232), width=1)
        draw.line((plot_left, y, plot_right, y), fill=(224, 228, 232), width=1)
        if value:
            draw.text((x, origin[1] + 17), str(value), anchor="mm", font=_font(12), fill=(70, 70, 70))
            draw.text((origin[0] - 18, y), str(value), anchor="mm", font=_font(12), fill=(70, 70, 70))
    draw.line((plot_left, origin[1], plot_right, origin[1]), fill=(40, 40, 40), width=3)
    draw.line((origin[0], plot_top, origin[0], plot_bottom), fill=(40, 40, 40), width=3)

    for index, (label, point) in enumerate(points.items()):
        x, y = pixel(point)
        color = COLORS[index % len(COLORS)]
        draw.ellipse(
            (x - point_radius, y - point_radius, x + point_radius, y + point_radius),
            fill=color,
            outline="white",
            width=2,
        )
        label_offset = point_radius + 11
        label_x = x + (label_offset if x <= origin[0] else -label_offset)
        label_y = y - point_radius - 9
        anchor = "lm" if x <= origin[0] else "rm"
        draw.text((label_x, label_y), label, anchor=anchor, font=_font(label_size, True), fill=(18, 18, 18))
    return image


def _spaced_coordinate(rng: random.Random, occupied: set[tuple[int, int]]) -> tuple[int, int]:
    candidates = [
        (x, y)
        for x in range(-5, 6)
        for y in range(-5, 6)
        if all(abs(x - ox) + abs(y - oy) >= 2 for ox, oy in occupied)
    ]
    if not candidates:
        raise ValueError("unable to sample a spaced coordinate")
    return rng.choice(candidates)


def _generate_coordinate_register_pairs(
    out_dir: Path,
    n: int,
    seed: int,
    *,
    render_variant: str,
    scale: int,
    point_radius: int,
    label_size: int,
    point_count: int,
    template_id: str,
) -> list[dict[str, Any]]:
    rows = []
    alphabet = "BCDFGHJKLMNPRSTVWXYZ"
    label_pool = [left + right for left in alphabet for right in alphabet if left != right]
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        labels = rng.sample(label_pool, point_count)
        target_label = rng.choice(labels)
        points_a: dict[str, tuple[int, int]] = {}
        occupied: set[tuple[int, int]] = set()
        for label in labels:
            point = _spaced_coordinate(rng, occupied)
            points_a[label] = point
            occupied.add(point)
        shared_occupied = {point for label, point in points_a.items() if label != target_label}
        target_b = _spaced_coordinate(rng, shared_occupied | {points_a[target_label]})
        points_b = dict(points_a)
        points_b[target_label] = target_b
        answer_a = f"({points_a[target_label][0]}, {points_a[target_label][1]})"
        answer_b = f"({target_b[0]}, {target_b[1]})"
        id_parts = (pair_seed, labels, target_label, answer_a, answer_b)
        if render_variant != "base_r4_r5":
            id_parts += (render_variant,)
        pair_prefix = "v02_register8_" if point_count == 8 else "v02_register_"
        pair_id = pair_prefix + stable_id(*id_parts)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_coordinate_register(
                    points_a, scale=scale, point_radius=point_radius, label_size=label_size
                ),
                image_b=_render_coordinate_register(
                    points_b, scale=scale, point_radius=point_radius, label_size=label_size
                ),
                question=f"What are the coordinates of point {target_label}? Answer as (x, y).",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_coordinate_indexing",
                template_id=template_id,
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "random_label_localization_then_coordinate_read",
                    "training_domain_alignment": "high",
                    "caption_failure_targeted": "fixed_target_label_and_sparse_point_register",
                    "render_variant": render_variant,
                },
                verifier_results={
                    "exact_by_construction": True,
                    "point_count": len(labels),
                    "target_label": target_label,
                    "target_a": points_a[target_label],
                    "target_b": target_b,
                    "all_labels_randomized": True,
                    "render_scale": scale,
                    "point_radius": point_radius,
                    "label_size": label_size,
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def generate_coordinate_register_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    return _generate_coordinate_register_pairs(
        out_dir,
        n,
        seed,
        render_variant="base_r4_r5",
        scale=65,
        point_radius=8,
        label_size=16,
        point_count=12,
        template_id="coordinate_register_random_target_v02",
    )


def generate_coordinate_register_legible_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    return _generate_coordinate_register_pairs(
        out_dir,
        n,
        seed,
        render_variant="legibility_r6_scale70_radius10_label18",
        scale=70,
        point_radius=10,
        label_size=18,
        point_count=12,
        template_id="coordinate_register_random_target_v02",
    )


def generate_coordinate_register_eight_point_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    return _generate_coordinate_register_pairs(
        out_dir,
        n,
        seed,
        render_variant="eight_point_r7_scale72_radius11_label19",
        scale=72,
        point_radius=11,
        label_size=19,
        point_count=8,
        template_id="coordinate_register_eight_point_v02",
    )


def _render_high_entropy_coordinate_register(points: dict[str, tuple[int, int]]) -> Image.Image:
    width, height = 1400, 1240
    image = Image.new("RGB", (width, height), (250, 250, 248))
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 38), "Coordinate Survey Register", anchor="mm", font=_font(26, True), fill=(25, 25, 25))
    origin = (700, 650)
    scale = 68
    plot_left = origin[0] - 7 * scale
    plot_right = origin[0] + 7 * scale
    plot_top = origin[1] - 7 * scale
    plot_bottom = origin[1] + 7 * scale
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), fill="white", outline=(75, 75, 75), width=2)
    for value in range(-7, 8):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, plot_top, x, plot_bottom), fill=(224, 228, 232), width=1)
        draw.line((plot_left, y, plot_right, y), fill=(224, 228, 232), width=1)
        if value:
            draw.text((x, origin[1] + 19), str(value), anchor="mm", font=_font(13), fill=(65, 65, 65))
            draw.text((origin[0] - 20, y), str(value), anchor="mm", font=_font(13), fill=(65, 65, 65))
    draw.line((plot_left, origin[1], plot_right, origin[1]), fill=(40, 40, 40), width=3)
    draw.line((origin[0], plot_top, origin[0], plot_bottom), fill=(40, 40, 40), width=3)

    for index, (label, point) in enumerate(points.items()):
        x = origin[0] + point[0] * scale
        y = origin[1] - point[1] * scale
        color = COLORS[index % len(COLORS)]
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color, outline="white", width=2)
        label_x = x + (17 if point[0] <= 0 else -17)
        label_y = y - 16
        draw.text(
            (label_x, label_y),
            label,
            anchor="lm" if point[0] <= 0 else "rm",
            font=_font(19, True),
            fill=(18, 18, 18),
            stroke_width=2,
            stroke_fill="white",
        )
    draw.text(
        (plot_left, 1186),
        "Locate the requested label, then read its coordinate from the numbered axes.",
        font=_font(15),
        fill=(70, 70, 70),
    )
    return image


def _sample_high_entropy_points(rng: random.Random, count: int) -> list[tuple[int, int]]:
    candidates = [(x, y) for x in range(-7, 8) for y in range(-7, 8) if x != 0 and y != 0]
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    for candidate in candidates:
        if all(max(abs(candidate[0] - x), abs(candidate[1] - y)) >= 2 for x, y in selected):
            selected.append(candidate)
            if len(selected) == count:
                return selected
    raise ValueError(f"unable to place {count} high-entropy coordinate labels")


def generate_coordinate_register_high_entropy_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    label_pool = [f"{letter}{digit}" for letter in "BCDFGHJKLMNPRSTVWXYZ" for digit in "23456789"]
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        labels = rng.sample(label_pool, 20)
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
        if not candidates_by_label:
            raise ValueError(f"no horizontal counterfactual targets for seed {pair_seed}")
        target_label = rng.choice(list(candidates_by_label))
        target_a = points_a[target_label]
        target_candidates = candidates_by_label[target_label]
        target_b = rng.choice(target_candidates)
        points_b = dict(points_a)
        points_b[target_label] = target_b
        answer_a = str(target_a[0])
        answer_b = str(target_b[0])
        pair_id = "v02_register20x_" + stable_id(pair_seed, labels, target_label, target_a, target_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_high_entropy_coordinate_register(points_a),
                image_b=_render_high_entropy_coordinate_register(points_b),
                question=f"What is the x-coordinate of point {target_label}?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="geometry_coordinate_indexing",
                template_id="coordinate_register_twenty_point_x_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "random_label_localization_then_x_coordinate_read",
                    "training_domain_alignment": "high",
                    "caption_failure_targeted": "twenty_question_blind_label_coordinate_bindings",
                    "render_variant": "twenty_point_x_r10_scale68_radius10_label19",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "point_count": len(labels),
                    "target_label": target_label,
                    "target_a": target_a,
                    "target_b": target_b,
                    "target_y_preserved": target_a[1] == target_b[1],
                    "all_labels_randomized": True,
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


def _render_header_cued_table(
    table: list[list[str]],
    row_labels: list[str],
    col_labels: list[str],
    target_row: int,
    target_col: int,
) -> Image.Image:
    width, height = 1120, 800
    image = Image.new("RGB", (width, height), (247, 248, 246))
    draw = ImageDraw.Draw(image)
    draw.rectangle((45, 42, width - 45, height - 42), fill="white", outline=(185, 185, 185), width=2)
    draw.text((width // 2, 78), "Repeated Field Verification Form", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    left, top = 102, 132
    row_header_width, cell_width, cell_height = 160, 130, 62
    draw.rectangle((left, top, left + row_header_width, top + cell_height), fill=(231, 235, 239), outline=(125, 125, 125))
    for column, label in enumerate(col_labels):
        x0 = left + row_header_width + column * cell_width
        outline = (36, 102, 165) if column == target_col else (125, 125, 125)
        width_line = 4 if column == target_col else 1
        draw.rectangle((x0, top, x0 + cell_width, top + cell_height), fill=(231, 235, 239), outline=outline, width=width_line)
        draw.text((x0 + cell_width // 2, top + cell_height // 2), label, anchor="mm", font=_font(17, True), fill=(32, 32, 32))
    for row, label in enumerate(row_labels):
        y0 = top + (row + 1) * cell_height
        outline = (36, 102, 165) if row == target_row else (125, 125, 125)
        width_line = 4 if row == target_row else 1
        draw.rectangle((left, y0, left + row_header_width, y0 + cell_height), fill=(231, 235, 239), outline=outline, width=width_line)
        draw.text((left + row_header_width // 2, y0 + cell_height // 2), label, anchor="mm", font=_font(15, True), fill=(32, 32, 32))
        for column, value in enumerate(table[row]):
            x0 = left + row_header_width + column * cell_width
            fill = (255, 255, 255) if (row + column) % 2 == 0 else (248, 249, 250)
            draw.rectangle((x0, y0, x0 + cell_width, y0 + cell_height), fill=fill, outline=(155, 155, 155), width=1)
            draw.text((x0 + cell_width // 2, y0 + cell_height // 2), value, anchor="mm", font=_font(21), fill=(15, 15, 15))
    draw.text((102, 724), "Blue outlines cue only the requested row header and column header; the cell is not highlighted.", font=_font(14), fill=(70, 70, 70))
    return image


def generate_header_table_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rows = []
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    col_labels = ["F2", "G4", "H7", "J9", "K3", "L8"]
    for index in range(n):
        pair_seed = seed + index * 104729
        rng = random.Random(pair_seed)
        row_labels = [f"Case-{value:03d}" for value in rng.sample(range(101, 999), 8)]
        table_a = [["".join(rng.choice(chars) for _ in range(2)) for _ in col_labels] for _ in row_labels]
        target_row = rng.randrange(len(row_labels))
        target_col = rng.randrange(len(col_labels))
        table_b = [list(row) for row in table_a]
        replacement = table_a[target_row][target_col]
        while replacement == table_a[target_row][target_col]:
            replacement = "".join(rng.choice(chars) for _ in range(2))
        table_b[target_row][target_col] = replacement
        answer_a = table_a[target_row][target_col]
        answer_b = table_b[target_row][target_col]
        pair_id = "v02_headertable_" + stable_id(pair_seed, row_labels, target_row, target_col, answer_a, answer_b)
        rows.append(
            _save_rendered_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=_render_header_cued_table(table_a, row_labels, col_labels, target_row, target_col),
                image_b=_render_header_cued_table(table_b, row_labels, col_labels, target_row, target_col),
                question=f"What is the 2-character code at row {row_labels[target_row]} and column {col_labels[target_col]}?",
                answer_a=answer_a,
                answer_b=answer_b,
                category="document_header_indexing",
                template_id="header_cued_table_code_v02",
                provenance={
                    "generator": "src.fliptrack.build_v02",
                    "pair_seed": pair_seed,
                    "visual_operation": "header_cued_row_column_indexing",
                    "training_domain_alignment": "low",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "target_row": target_row,
                    "target_column": target_col,
                    "target_cell_highlighted": False,
                },
                swap_sides=rng.random() < 0.5,
            )
        )
    return rows


GENERATORS: list[tuple[str, Callable[[Path, int, int], list[dict[str, Any]]]]] = [
    ("chart", generate_chart_pairs),
    ("grid", generate_grid_pairs),
    ("triangle", generate_triangle_pairs),
    ("parallel", generate_parallel_pairs),
    ("coordinate", generate_coordinate_pairs),
]

EXPERIMENTAL_GENERATORS: list[tuple[str, Callable[[Path, int, int], list[dict[str, Any]]]]] = [
    ("chart_legible", generate_legible_chart_pairs),
    ("coordinate_point", generate_coordinate_point_pairs),
    ("coordinate_register", generate_coordinate_register_pairs),
    ("coordinate_register_legible", generate_coordinate_register_legible_pairs),
    ("coordinate_register_eight", generate_coordinate_register_eight_point_pairs),
    ("coordinate_register_high_entropy", generate_coordinate_register_high_entropy_pairs),
    ("header_table", generate_header_table_pairs),
]


def _add_dense_table_metadata(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["provenance"].update(
            {
                "visual_operation": "highlighted_table_cell_read",
                "training_domain_alignment": "low",
                "contrast_role": "pop_out_reading",
            }
        )


def _randomize_dense_table_sides(rows: list[dict[str, Any]], seed: int) -> None:
    rng = random.Random(seed)
    for row in rows:
        swapped = rng.random() < 0.5
        row["provenance"]["semantic_side_assignment_swapped"] = swapped
        row["verifier_results"]["semantic_side_assignment_swapped"] = swapped
        if not swapped:
            continue
        for stem in ("image", "changed_region_mask", "answer"):
            key_a = f"{stem}_a" if stem == "answer" else f"{stem}_a_path" if stem == "image" else f"{stem}_a"
            key_b = f"{stem}_b" if stem == "answer" else f"{stem}_b_path" if stem == "image" else f"{stem}_b"
            row[key_a], row[key_b] = row[key_b], row[key_a]
        row["image_a_sha256"], row["image_b_sha256"] = row["image_b_sha256"], row["image_a_sha256"]


def build(
    out_dir: str | Path,
    n_per_template: int,
    seed: int,
    families: set[str] | None = None,
) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    rows: list[dict[str, Any]] = []
    available = GENERATORS + EXPERIMENTAL_GENERATORS
    selected = ({name for name, _ in GENERATORS} | {"dense_table"}) if families is None else families
    unknown = selected - ({name for name, _ in available} | {"dense_table"})
    if unknown:
        raise ValueError(f"unknown FlipTrack families: {sorted(unknown)}")
    for offset, (name, generator) in enumerate(available, start=1):
        if name not in selected:
            continue
        rows.extend(generator(out_dir / name, n_per_template, seed + offset * 1009))
    if "dense_table" in selected:
        dense_rows = generate_doc_pairs(out_dir / "dense_table", n_per_template, seed + 6007)
        _add_dense_table_metadata(dense_rows)
        _randomize_dense_table_sides(dense_rows, seed + 7001)
        rows.extend(dense_rows)
    return rows


def write_contact_sheets(rows: list[dict[str, Any]], output_dir: str | Path, n_per_template: int = 20) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    by_template: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_template.setdefault(str(row["template_id"]), []).append(row)
    outputs = []
    for template_id, template_rows in sorted(by_template.items()):
        selected = template_rows[:n_per_template]
        tile_w, tile_h = 470, 250
        columns = 4
        rows_count = math.ceil(len(selected) / columns)
        sheet = Image.new("RGB", (tile_w * columns, tile_h * rows_count), (238, 238, 238))
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(selected):
            x0 = (index % columns) * tile_w
            y0 = (index // columns) * tile_h
            draw.rectangle((x0 + 2, y0 + 2, x0 + tile_w - 2, y0 + tile_h - 2), fill="white", outline=(160, 160, 160))
            for side_index, side in enumerate(("a", "b")):
                with Image.open(row[f"image_{side}_path"]) as source:
                    thumb = source.convert("RGB")
                    thumb.thumbnail((220, 178), Image.Resampling.LANCZOS)
                x = x0 + 8 + side_index * 230 + (220 - thumb.width) // 2
                y = y0 + 8 + (178 - thumb.height) // 2
                sheet.paste(thumb, (x, y))
                draw.text((x0 + 118 + side_index * 230, y0 + 191), f"{side.upper()}: {row[f'answer_{side}']}", anchor="mm", font=_font(13, True), fill=(20, 20, 20))
            question = str(row["question"])
            if len(question) > 70:
                question = question[:67] + "..."
            draw.text((x0 + 10, y0 + 214), question, font=_font(11), fill=(35, 35, 35))
            draw.text((x0 + 10, y0 + 232), str(row["pair_id"]), font=_font(9), fill=(100, 100, 100))
        output = output_dir / f"{template_id}.png"
        sheet.save(output, format="PNG", optimize=False, compress_level=9)
        outputs.append(output)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v02_source/renderable")
    parser.add_argument("--manifest", default="data/fliptrack_v02_source_manifest.jsonl")
    parser.add_argument("--contact-sheet-dir", default="reports/contact_sheets/fliptrack_v02")
    parser.add_argument("--n-per-template", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--families", help="Comma-separated family names; default is all base families")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    manifest = Path(args.manifest)
    if manifest.exists() or (out_dir.exists() and any(out_dir.iterdir())):
        raise FileExistsError(f"refusing to overwrite existing V0.2 build: {manifest} / {out_dir}")
    families = {item.strip() for item in args.families.split(",") if item.strip()} if args.families else None
    rows = build(args.out_dir, args.n_per_template, args.seed, families=families)
    write_jsonl(args.manifest, rows)
    sheets = write_contact_sheets(rows, args.contact_sheet_dir)
    print(f"manifest={args.manifest} pairs={len(rows)} contact_sheets={len(sheets)}")


if __name__ == "__main__":
    main()
