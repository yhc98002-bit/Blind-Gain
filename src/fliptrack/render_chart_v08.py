from __future__ import annotations

import argparse
import hashlib
import math
import random
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.fliptrack.schema import pair_record, stable_id, write_jsonl


WIDTH, HEIGHT = 1400, 900
PLOT = (100, 82, 1010, 770)
LEGEND = (1040, 82, 1370, 530)
COLORS = (
    (0, 114, 178),
    (213, 94, 0),
    (0, 158, 115),
    (204, 121, 167),
    (230, 159, 0),
    (86, 180, 233),
)
LINESTYLES = ("solid", "dash", "dot", "dashdot", "longdash", "shortdash")
MARKERS = ("square", "triangle", "diamond", "plus", "x", "circle")
LABELS = ("Aster", "Birch", "Cobalt", "Delta", "Ember", "Fjord")
RENDERER_VERSION = "chart-v08-renderer-v2"
DIAGNOSTIC_CONTRACT_VERSION = "chart-v08-necessity-v2"

# Machado et al. severity-100 matrices, applied in linear RGB. The palette is
# also dual-coded, so these checks are a lower bound rather than the sole cue.
CVD_MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


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


def _srgb_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055


def rgb_to_lab(color: tuple[int, int, int]) -> tuple[float, float, float]:
    red, green, blue = (_srgb_channel(value / 255.0) for value in color)
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = 0.2126729 * red + 0.7151522 * green + 0.0721750 * blue
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883

    def transform(value: float) -> float:
        delta = 6 / 29
        return value ** (1 / 3) if value > delta**3 else value / (3 * delta**2) + 4 / 29

    fx, fy, fz = transform(x), transform(y), transform(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def minimum_palette_distance(colors: tuple[tuple[int, int, int], ...] = COLORS) -> float:
    labs = [rgb_to_lab(color) for color in colors]
    return min(
        math.sqrt(sum((left[channel] - right[channel]) ** 2 for channel in range(3)))
        for index, left in enumerate(labs)
        for right in labs[index + 1 :]
    )


def simulate_cvd(
    color: tuple[int, int, int], mode: str
) -> tuple[int, int, int]:
    if mode not in CVD_MATRICES:
        raise ValueError(f"unsupported color-vision mode: {mode}")
    linear = tuple(_srgb_channel(value / 255.0) for value in color)
    matrix = CVD_MATRICES[mode]
    transformed = tuple(
        sum(matrix[row][column] * linear[column] for column in range(3))
        for row in range(3)
    )
    return tuple(round(_linear_to_srgb(value) * 255) for value in transformed)


def palette_distance_report(
    colors: tuple[tuple[int, int, int], ...] = COLORS,
) -> dict[str, float]:
    report = {"normal": minimum_palette_distance(colors)}
    for mode in CVD_MATRICES:
        report[mode] = minimum_palette_distance(
            tuple(simulate_cvd(color, mode) for color in colors)
        )
    return report


def adjacent_crossing_count(values: list[list[int]], target_x: int) -> int:
    if not values or not 0 < target_x < len(values[0]) - 1:
        raise ValueError("target_x must have an adjacent segment on both sides")
    crossings = 0
    for left_series in range(len(values)):
        for right_series in range(left_series + 1, len(values)):
            for left_x, right_x in ((target_x - 1, target_x), (target_x, target_x + 1)):
                left_delta = values[left_series][left_x] - values[right_series][left_x]
                right_delta = values[left_series][right_x] - values[right_series][right_x]
                if (
                    left_delta == 0
                    or right_delta == 0
                    or (left_delta < 0 < right_delta)
                    or (left_delta > 0 > right_delta)
                ):
                    crossings += 1
    return crossings


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _draw_styled_segment(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: tuple[int, int, int],
    width: int,
    style: str,
) -> None:
    patterns = {
        "solid": (10_000, 0),
        "dash": (16, 9),
        "dot": (3, 7),
        "dashdot": (14, 7),
        "longdash": (24, 10),
        "shortdash": (9, 6),
    }
    on, off = patterns[style]
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    cursor = 0.0
    while cursor < length:
        stop = min(length, cursor + on)
        p0 = (round(start[0] + dx * cursor / length), round(start[1] + dy * cursor / length))
        p1 = (round(start[0] + dx * stop / length), round(start[1] + dy * stop / length))
        draw.line((p0, p1), fill=fill, width=width)
        cursor = stop + off


def _draw_marker(
    draw: ImageDraw.ImageDraw,
    point: tuple[int, int],
    marker: str,
    color: tuple[int, int, int],
    radius: int = 6,
) -> None:
    x, y = point
    if marker == "square":
        draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=color)
    elif marker == "triangle":
        draw.polygon(((x, y - radius - 1), (x - radius, y + radius), (x + radius, y + radius)), fill=color)
    elif marker == "diamond":
        draw.polygon(((x, y - radius - 1), (x - radius, y), (x, y + radius + 1), (x + radius, y)), fill=color)
    elif marker == "plus":
        draw.line((x - radius, y, x + radius, y), fill=color, width=3)
        draw.line((x, y - radius, x, y + radius), fill=color, width=3)
    elif marker == "x":
        draw.line((x - radius, y - radius, x + radius, y + radius), fill=color, width=3)
        draw.line((x - radius, y + radius, x + radius, y - radius), fill=color, width=3)
    elif marker == "circle":
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    else:
        raise ValueError(f"unsupported marker: {marker}")


def _positions(x_count: int) -> tuple[list[int], int, int, int, int]:
    left, top, right, bottom = PLOT
    x_positions = [
        left + 55 + round(index * (right - left - 110) / (x_count - 1))
        for index in range(x_count)
    ]
    return x_positions, left, top, right, bottom


def _render(
    values: list[list[int]],
    target_series: int | None,
    target_x: int,
    *,
    series_count: int,
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (246, 248, 247))
    draw = ImageDraw.Draw(image)
    x_positions, left, top, right, bottom = _positions(len(values[0]))
    draw.text((WIDTH // 2, 34), "Multi-Series Measurement Trace", anchor="mm", font=_font(25, True), fill=(25, 25, 25))
    draw.rectangle(PLOT, fill="white", outline=(40, 40, 40), width=2)
    for tick in range(0, 101, 10):
        y = bottom - round(tick / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=(224, 228, 230), width=1)
        draw.text((left - 14, y), str(tick), anchor="rm", font=_font(15), fill=(45, 45, 45))
    for index, x in enumerate(x_positions, start=1):
        draw.line((x, top, x, bottom), fill=(239, 241, 242), width=1)
        draw.text((x, bottom + 27), str(index), anchor="mm", font=_font(16), fill=(45, 45, 45))
    draw.text(((left + right) // 2, bottom + 58), "x", anchor="mm", font=_font(18, True), fill=(35, 35, 35))

    for series_index in range(series_count):
        points = [
            (x, bottom - round(value / 100 * (bottom - top)))
            for x, value in zip(x_positions, values[series_index])
        ]
        for p0, p1 in zip(points, points[1:]):
            _draw_styled_segment(
                draw,
                p0,
                p1,
                fill=COLORS[series_index],
                width=4,
                style=LINESTYLES[series_index],
            )
        for point in points:
            _draw_marker(draw, point, MARKERS[series_index], COLORS[series_index])

    draw.rectangle(LEGEND, fill="white", outline=(150, 150, 150), width=2)
    draw.text((1205, 112), "Series key", anchor="mm", font=_font(20, True), fill=(25, 25, 25))
    for index in range(series_count):
        y = 158 + index * 56
        _draw_styled_segment(
            draw,
            (1088, y),
            (1142, y),
            fill=COLORS[index],
            width=5,
            style=LINESTYLES[index],
        )
        _draw_marker(draw, (1115, y), MARKERS[index], COLORS[index])
        draw.text((1162, y), LABELS[index], anchor="lm", font=_font(18), fill=(20, 20, 20))
        if index == target_series:
            draw.text((1062, y), "*", anchor="mm", font=_font(28, True), fill=(0, 0, 0))
    draw.text(
        (100, 855),
        "The black star identifies the target series in the legend.",
        font=_font(16),
        fill=(60, 60, 60),
    )
    draw.text((right, 855), f"Read its value at x = {target_x + 1}.", anchor="ra", font=_font(16), fill=(60, 60, 60))
    return image


def _exact_mask(image_a: Image.Image, image_b: Image.Image) -> Image.Image:
    changed = np.any(
        np.asarray(image_a, dtype=np.uint8) != np.asarray(image_b, dtype=np.uint8),
        axis=2,
    )
    return Image.fromarray(changed.astype(np.uint8) * 255, mode="L")


def _save_pair(
    *,
    out_dir: Path,
    pair_id: str,
    image_a: Image.Image,
    image_b: Image.Image,
    question: str,
    answer_a: int,
    answer_b: int,
    category: str,
    template_id: str,
    provenance: dict[str, Any],
    verifier: dict[str, Any],
    diagnostic_no_star_a: Image.Image,
    diagnostic_no_star_b: Image.Image,
    diagnostic_random_star_a: Image.Image,
    diagnostic_random_star_b: Image.Image,
    diagnostic_random_target_a: int,
    diagnostic_random_target_b: int,
    diagnostic_random_answer_a: int,
    diagnostic_random_answer_b: int,
) -> dict[str, Any]:
    if answer_a == answer_b:
        raise ValueError("pair answers must differ")
    image_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    diagnostic_dir = out_dir / "diagnostics"
    for directory in (image_dir, mask_dir, diagnostic_dir):
        directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "image_a": image_dir / f"{pair_id}_a.png",
        "image_b": image_dir / f"{pair_id}_b.png",
        "mask_a": mask_dir / f"{pair_id}_a_mask.png",
        "mask_b": mask_dir / f"{pair_id}_b_mask.png",
        "no_star_a": diagnostic_dir / f"{pair_id}_a_no_star.png",
        "no_star_b": diagnostic_dir / f"{pair_id}_b_no_star.png",
        "random_star_a": diagnostic_dir / f"{pair_id}_a_random_star.png",
        "random_star_b": diagnostic_dir / f"{pair_id}_b_random_star.png",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite chart-v08 artifact: "
            + ", ".join(str(path) for path in existing)
        )
    image_a.save(paths["image_a"], compress_level=9)
    image_b.save(paths["image_b"], compress_level=9)
    mask = _exact_mask(image_a, image_b)
    if not np.any(np.asarray(mask)):
        raise ValueError("pair images must differ")
    mask.save(paths["mask_a"], compress_level=9)
    mask.save(paths["mask_b"], compress_level=9)
    diagnostic_no_star_a.save(paths["no_star_a"], compress_level=9)
    diagnostic_no_star_b.save(paths["no_star_b"], compress_level=9)
    diagnostic_random_star_a.save(paths["random_star_a"], compress_level=9)
    diagnostic_random_star_b.save(paths["random_star_b"], compress_level=9)
    palette_distances = palette_distance_report()
    verifier = dict(verifier)
    verifier.update(
        {
            "exact_by_construction": True,
            "answer_pointing_cue": False,
            "target_point_circled": False,
            "target_point_highlighted": False,
            "target_point_arrowed": False,
            "dual_coding": True,
            "target_point_annotation_circle": False,
            "minimum_palette_cie76": round(palette_distances["normal"], 4),
            "palette_cie76_by_vision_mode": {
                mode: round(distance, 4)
                for mode, distance in palette_distances.items()
            },
            "diagnostic_contract_version": DIAGNOSTIC_CONTRACT_VERSION,
            "diagnostic_scoring_rule": "score_each_intervention_against_original_member_answer",
            "diagnostic_no_star_a_path": str(paths["no_star_a"]),
            "diagnostic_no_star_b_path": str(paths["no_star_b"]),
            "diagnostic_random_star_a_path": str(paths["random_star_a"]),
            "diagnostic_random_star_b_path": str(paths["random_star_b"]),
            "diagnostic_no_star_a_sha256": _sha256(paths["no_star_a"]),
            "diagnostic_no_star_b_sha256": _sha256(paths["no_star_b"]),
            "diagnostic_random_star_a_sha256": _sha256(paths["random_star_a"]),
            "diagnostic_random_star_b_sha256": _sha256(paths["random_star_b"]),
            "diagnostic_random_target_a": diagnostic_random_target_a,
            "diagnostic_random_target_b": diagnostic_random_target_b,
            "diagnostic_random_implied_answer_a": diagnostic_random_answer_a,
            "diagnostic_random_implied_answer_b": diagnostic_random_answer_b,
        }
    )
    return pair_record(
        pair_id=pair_id,
        image_a_path=str(paths["image_a"]),
        image_b_path=str(paths["image_b"]),
        changed_region_mask_a=str(paths["mask_a"]),
        changed_region_mask_b=str(paths["mask_b"]),
        question=question,
        answer_a=str(answer_a),
        answer_b=str(answer_b),
        category=category,
        template_id=template_id,
        provenance=provenance,
        verifier_results=verifier,
    )


def _base_values(rng: random.Random, series_count: int, x_count: int, target_x: int, granularity: int) -> list[list[int]]:
    values: list[list[int]] = []
    center = rng.randrange(35, 66, granularity)
    for _ in range(series_count):
        series = [rng.randrange(15, 91, granularity) for _ in range(x_count)]
        for x_index in range(max(0, target_x - 1), min(x_count, target_x + 2)):
            jitter = rng.choice((-2, -1, 0, 1, 2)) * granularity
            series[x_index] = max(10, min(90, center + jitter))
        values.append(series)
    return values


def _discordant_series(
    values: list[list[int]],
    target_series: int,
    target_x: int,
    rng: random.Random,
) -> int:
    target_answer = values[target_series][target_x]
    candidates = [
        index
        for index, series in enumerate(values)
        if index != target_series and series[target_x] != target_answer
    ]
    if not candidates:
        raise ValueError("necessity diagnostic has no answer-discordant target")
    return rng.choice(candidates)


def generate_chart_v08_pairs(
    out_dir: str | Path,
    *,
    n_per_subfamily: int,
    seed: int,
) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty chart-v08 directory: {out_dir}")
    rows: list[dict[str, Any]] = []
    for subfamily_index, subfamily in enumerate(("legend_target", "point_value")):
        for index in range(n_per_subfamily):
            pair_seed = seed + subfamily_index * 10_000_019 + index * 104_729
            rng = random.Random(pair_seed)
            series_count = rng.choice((5, 6))
            x_count = 7
            target_x = rng.randrange(1, x_count - 1)
            granularity = rng.choice((5, 10))
            values_a = _base_values(rng, series_count, x_count, target_x, granularity)
            values_b = [list(series) for series in values_a]
            target_a = rng.randrange(series_count)
            candidates = [
                candidate
                for candidate in range(series_count)
                if candidate != target_a
                and values_a[candidate][target_x] != values_a[target_a][target_x]
            ]
            while not candidates:
                values_a = _base_values(rng, series_count, x_count, target_x, granularity)
                values_b = [list(series) for series in values_a]
                candidates = [
                    candidate
                    for candidate in range(series_count)
                    if candidate != target_a
                    and values_a[candidate][target_x] != values_a[target_a][target_x]
                ]

            if subfamily == "legend_target":
                target_b = rng.choice(candidates)
                answer_a = values_a[target_a][target_x]
                answer_b = values_b[target_b][target_x]
                image_a = _render(values_a, target_a, target_x, series_count=series_count)
                image_b = _render(values_b, target_b, target_x, series_count=series_count)
                random_target_a = _discordant_series(values_a, target_a, target_x, rng)
                random_target_b = _discordant_series(values_b, target_b, target_x, rng)
                crossing_count = adjacent_crossing_count(values_a, target_x)
                crossing_slots = math.comb(series_count, 2) * 2
                row = _save_pair(
                    out_dir=out_dir / subfamily,
                    pair_id="chart_v08_legend_" + stable_id(pair_seed, target_a, target_b, target_x),
                    image_a=image_a,
                    image_b=image_b,
                    question=f"What value does the starred series have at x = {target_x + 1}?",
                    answer_a=answer_a,
                    answer_b=answer_b,
                    category="chart_legend_to_series_localization",
                    template_id="chart_v08_legend_target_flip",
                    provenance={
                        "generator": "src.fliptrack.render_chart_v08",
                        "renderer_version": RENDERER_VERSION,
                        "pair_seed": pair_seed,
                        "subfamily": subfamily,
                        "difficulty_controls": ["crossing_density", "value_grid_granularity"],
                    },
                    verifier={
                        "series_count": series_count,
                        "x_count": x_count,
                        "target_x": target_x + 1,
                        "target_series_a": target_a,
                        "target_series_b": target_b,
                        "curves_identical_across_pair": values_a == values_b,
                        "only_semantic_change": "starred_legend_entry",
                        "mask_semantics": "star_region",
                        "value_grid_granularity": granularity,
                        "adjacent_crossing_count_a": crossing_count,
                        "adjacent_crossing_count_b": crossing_count,
                        "adjacent_crossing_fraction_a": round(crossing_count / crossing_slots, 6),
                        "adjacent_crossing_fraction_b": round(crossing_count / crossing_slots, 6),
                        "values_a": values_a,
                        "values_b": values_b,
                    },
                    diagnostic_no_star_a=_render(values_a, None, target_x, series_count=series_count),
                    diagnostic_no_star_b=_render(values_b, None, target_x, series_count=series_count),
                    diagnostic_random_star_a=_render(values_a, random_target_a, target_x, series_count=series_count),
                    diagnostic_random_star_b=_render(values_b, random_target_b, target_x, series_count=series_count),
                    diagnostic_random_target_a=random_target_a,
                    diagnostic_random_target_b=random_target_b,
                    diagnostic_random_answer_a=values_a[random_target_a][target_x],
                    diagnostic_random_answer_b=values_b[random_target_b][target_x],
                )
            else:
                target_b = target_a
                current = values_a[target_a][target_x]
                replacements = [
                    value
                    for value in range(10, 91, granularity)
                    if value != current and abs(value - current) >= granularity
                    and any(
                        series_index != target_a
                        and values_a[series_index][target_x] != value
                        for series_index in range(series_count)
                    )
                ]
                values_b[target_a][target_x] = rng.choice(replacements)
                answer_a = current
                answer_b = values_b[target_a][target_x]
                random_target_a = _discordant_series(values_a, target_a, target_x, rng)
                random_target_b = _discordant_series(values_b, target_b, target_x, rng)
                crossing_count_a = adjacent_crossing_count(values_a, target_x)
                crossing_count_b = adjacent_crossing_count(values_b, target_x)
                crossing_slots = math.comb(series_count, 2) * 2
                row = _save_pair(
                    out_dir=out_dir / subfamily,
                    pair_id="chart_v08_value_" + stable_id(pair_seed, target_a, target_x, answer_a, answer_b),
                    image_a=_render(values_a, target_a, target_x, series_count=series_count),
                    image_b=_render(values_b, target_b, target_x, series_count=series_count),
                    question=f"What value does the starred series have at x = {target_x + 1}?",
                    answer_a=answer_a,
                    answer_b=answer_b,
                    category="chart_legend_to_series_value_reading",
                    template_id="chart_v08_point_value_flip",
                    provenance={
                        "generator": "src.fliptrack.render_chart_v08",
                        "renderer_version": RENDERER_VERSION,
                        "pair_seed": pair_seed,
                        "subfamily": subfamily,
                        "difficulty_controls": ["crossing_density", "value_grid_granularity"],
                    },
                    verifier={
                        "series_count": series_count,
                        "x_count": x_count,
                        "target_x": target_x + 1,
                        "target_series_a": target_a,
                        "target_series_b": target_b,
                        "starred_legend_entry_fixed": True,
                        "changed_value_count": 1,
                        "only_semantic_change": "one_target_series_value",
                        "mask_semantics": "marker_and_affected_segments",
                        "value_grid_granularity": granularity,
                        "adjacent_crossing_count_a": crossing_count_a,
                        "adjacent_crossing_count_b": crossing_count_b,
                        "adjacent_crossing_fraction_a": round(crossing_count_a / crossing_slots, 6),
                        "adjacent_crossing_fraction_b": round(crossing_count_b / crossing_slots, 6),
                        "values_a": values_a,
                        "values_b": values_b,
                    },
                    diagnostic_no_star_a=_render(values_a, None, target_x, series_count=series_count),
                    diagnostic_no_star_b=_render(values_b, None, target_x, series_count=series_count),
                    diagnostic_random_star_a=_render(values_a, random_target_a, target_x, series_count=series_count),
                    diagnostic_random_star_b=_render(values_b, random_target_b, target_x, series_count=series_count),
                    diagnostic_random_target_a=random_target_a,
                    diagnostic_random_target_b=random_target_b,
                    diagnostic_random_answer_a=values_a[random_target_a][target_x],
                    diagnostic_random_answer_b=values_b[random_target_b][target_x],
                )
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--n-per-subfamily", type=int, default=50)
    parser.add_argument("--seed", type=int, default=2026071208)
    args = parser.parse_args()
    if args.manifest.exists():
        raise FileExistsError(f"refusing to overwrite manifest: {args.manifest}")
    rows = generate_chart_v08_pairs(
        args.out_dir,
        n_per_subfamily=args.n_per_subfamily,
        seed=args.seed,
    )
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()
