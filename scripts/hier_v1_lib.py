#!/usr/bin/env python3
"""hier_coord_v1 / hier_chart_v1 mother-item library (P1.1 of the 08-12
dispatch; registered in docs/registered_hier_benchmark_v1.md §1–§6 +
Amendment A1).

Every mother-PAIR derives three layer rows from identical scene data:
  l3  Discover+Ground+Read — no target identity, no cue
  l2  Ground+Read          — target identity given in the question
  l1  Read                 — l2 question + a non-occluding offset cue at the
                             target (the registered ink rule: cue pixels may
                             only replace background/plot-fill pixels)
plus one discovery-probe row (target identity question, L3 oracle level).

Verifier obligations (a)–(e) are computed here at build time and re-checked
from disk by scripts/verify_hier_dev_batch.py:
  (a) L1 cue ink pixel-disjoint from all existing ink (allowed-color rule)
  (b) golds recomputed per layer from serialized scene truth; L2/L1 question
      names the target entity
  (c) L2 and L3 images byte-identical per side
  (d) answers / hard negatives / scene hashes identical across a mother's
      three layers
  (e) hard-negative roles on every L2/L3 row (candidate registries are built
      per cell by the batch CLI via the frozen registry builder)

Renderers: the coordinate family uses the FROZEN
src/fliptrack/build_v02._render_high_entropy_coordinate_register untouched;
the chart family re-implements the chart-v08 drawing locally (same geometry
constants) because it needs 9-series palettes and no star machinery —
extensions are additive, the v08 module is not modified.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image, ImageDraw

from scripts.build_b1_geometry_track_prototype import (
    base_scene,
    hard_negatives,
    spacing_ok,
)
from src.fliptrack.build_v02 import (
    COLORS as _V02_COLORS,
    _answers_distinguishable,
    _font as _v02_font,
    _render_high_entropy_coordinate_register,
)
from src.fliptrack.render_chart_v08 import (
    COLORS as V08_COLORS,
    LABELS as V08_LABELS,
    LINESTYLES as V08_LINESTYLES,
    MARKERS as V08_MARKERS,
    _draw_marker,
    _font,
    _positions,
    adjacent_crossing_count,
    palette_distance_report,
)

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# shared: offset cue (Amendment A1 ink rule)
# ---------------------------------------------------------------------------

CUE_COLOR = (196, 30, 58)
# Diagonal-first: scene points sit on gridline intersections, and a 45-degree
# ray whose axis offsets stay inside one grid cell crosses no gridline.
CUE_DIRECTIONS = (
    (1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (-1, 0), (0, 1), (0, -1),
)
CUE_RADII = ((18, 66), (18, 52), (24, 78))


def _draw_cue(draw: ImageDraw.ImageDraw, target: tuple[int, int],
              direction: tuple[int, int], radii: tuple[int, int]) -> None:
    norm = math.hypot(*direction)
    ux, uy = direction[0] / norm, direction[1] / norm
    near, far = radii
    tip = (round(target[0] + ux * near), round(target[1] + uy * near))
    tail = (round(target[0] + ux * far), round(target[1] + uy * far))
    draw.line((tail, tip), fill=CUE_COLOR, width=3)
    # open arrowhead: two wings back from the tip
    for wing_sign in (1, -1):
        angle = math.atan2(uy, ux) + wing_sign * 0.45
        wing = (
            round(tip[0] + math.cos(angle) * 14),
            round(tip[1] + math.sin(angle) * 14),
        )
        draw.line((tip, wing), fill=CUE_COLOR, width=3)


def add_offset_cue(
    base: Image.Image,
    target_px: tuple[int, int],
    allowed_colors: frozenset[tuple[int, int, int]],
) -> tuple[Image.Image, dict[str, Any]] | None:
    """Return (cued image, cue record) or None if no placement satisfies the
    registered ink rule. Deterministic search order; never force-drawn."""
    base_array = np.asarray(base, dtype=np.uint8)
    for radii in CUE_RADII:
        for direction in CUE_DIRECTIONS:
            candidate = base.copy()
            _draw_cue(ImageDraw.Draw(candidate), target_px, direction, radii)
            cand_array = np.asarray(candidate, dtype=np.uint8)
            changed = np.any(cand_array != base_array, axis=2)
            if not changed.any():
                continue
            replaced = base_array[changed]
            replaced_colors = {tuple(int(v) for v in px) for px in replaced}
            if replaced_colors <= allowed_colors:
                ys, xs = np.nonzero(changed)
                return candidate, {
                    "cue_direction": list(direction),
                    "cue_radii": list(radii),
                    "cue_pixel_count": int(changed.sum()),
                    "cue_bbox": [int(xs.min()), int(ys.min()),
                                 int(xs.max()), int(ys.max())],
                    "cue_ink_disjoint": True,
                }
    return None


def cue_ink_disjoint(l2_image: Image.Image, l1_image: Image.Image,
                     allowed_colors: frozenset[tuple[int, int, int]]) -> bool:
    """From-disk re-check of obligation (a)."""
    a2 = np.asarray(l2_image, dtype=np.uint8)
    a1 = np.asarray(l1_image, dtype=np.uint8)
    changed = np.any(a1 != a2, axis=2)
    if not changed.any():
        return False  # an L1 with no cue at all is a violation, not a pass
    replaced = {tuple(int(v) for v in px) for px in a2[changed]}
    return replaced <= allowed_colors


def sha256_image(image: Image.Image) -> str:
    return hashlib.sha256(image.tobytes()).hexdigest()


# ---------------------------------------------------------------------------
# coordinate family (hier_coord_v1)
# ---------------------------------------------------------------------------

COORD_ALLOWED = frozenset({(250, 250, 248), (255, 255, 255)})
COORD_ORIGIN, COORD_SCALE = (700, 650), 68

EXTREMUM_KINDS = {
    "largest_y": {"axis": 1, "best": max, "read": 0,
                  "phrase": "largest y-coordinate", "read_name": "x"},
    "smallest_y": {"axis": 1, "best": min, "read": 0,
                   "phrase": "smallest y-coordinate", "read_name": "x"},
    "leftmost": {"axis": 0, "best": min, "read": 1,
                 "phrase": "smallest x-coordinate", "read_name": "y"},
    "rightmost": {"axis": 0, "best": max, "read": 1,
                  "phrase": "largest x-coordinate", "read_name": "y"},
}
EXTREMUM_ROTATION = ("largest_y", "rightmost", "smallest_y", "leftmost")
COORD_MARGIN = 1  # extremum-axis gap top1 vs top2, both sides (Amendment A1)


def coord_extremum(points: dict[str, tuple[int, int]], kind: str) -> tuple[str, int]:
    spec = EXTREMUM_KINDS[kind]
    axis, best = spec["axis"], spec["best"]
    ordered = sorted(points.items(), key=lambda kv: kv[1][axis],
                     reverse=(best is max))
    gap = abs(ordered[0][1][axis] - ordered[1][1][axis])
    return ordered[0][0], gap


def coord_questions(kind: str, target: str) -> dict[str, str]:
    spec = EXTREMUM_KINDS[kind]
    return {
        "l3": (f"Consider the point with the {spec['phrase']}. "
               f"What is its {spec['read_name']}-coordinate?"),
        "l2": (f"Point {target} has the {spec['phrase']}. "
               f"What is the {spec['read_name']}-coordinate of point {target}?"),
        "probe": f"Which labeled point has the {spec['phrase']}?",
    }


def coord_read(points: dict[str, tuple[int, int]], label: str, kind: str) -> str:
    return str(points[label][EXTREMUM_KINDS[kind]["read"]])


def _coord_move_candidates(points: dict[str, tuple[int, int]], label: str,
                           predicate) -> list[tuple[int, int]]:
    others = {p for l, p in points.items() if l != label}
    return [
        (x, y)
        for x in range(-7, 8) if x != 0
        for y in [*range(-7, 0), *range(1, 8)]
        if (x, y) != points[label]
        and spacing_ok((x, y), others)
        and predicate((x, y))
    ]


def build_coord_geometry(role: str, kind: str, n_points: int,
                         rng) -> dict[str, Any] | None:
    """One mother-pair's geometry, or None on any constraint rejection."""
    labels, points_a = base_scene(rng, n_points)
    spec = EXTREMUM_KINDS[kind]
    axis, read = spec["axis"], spec["read"]
    target_a, gap_a = coord_extremum(points_a, kind)
    if gap_a < COORD_MARGIN:
        return None
    answer_a = coord_read(points_a, target_a, kind)

    if role == "target_switch":
        ordered = sorted(points_a.items(), key=lambda kv: kv[1][axis],
                         reverse=(spec["best"] is max))
        runner_up = ordered[1][0]

        def becomes_runner_up_extremum(new_pos: tuple[int, int]) -> bool:
            moved = dict(points_a)
            moved[target_a] = new_pos
            new_target, new_gap = coord_extremum(moved, kind)
            return (
                new_target == runner_up
                and new_gap >= COORD_MARGIN
                and _answers_distinguishable(
                    answer_a, coord_read(moved, runner_up, kind))
            )

        candidates = _coord_move_candidates(points_a, target_a,
                                            becomes_runner_up_extremum)
        if not candidates:
            return None
        points_b = dict(points_a)
        points_b[target_a] = candidates[rng.randrange(len(candidates))]
        target_b = runner_up
        moved_label = target_a
    elif role == "target_stable":
        fixed_extremum = points_a[target_a][axis]

        def keeps_extremum_moves_read(new_pos: tuple[int, int]) -> bool:
            if new_pos[axis] != fixed_extremum:
                return False
            moved = dict(points_a)
            moved[target_a] = new_pos
            new_target, new_gap = coord_extremum(moved, kind)
            return (
                new_target == target_a
                and new_gap >= COORD_MARGIN
                and abs(new_pos[read] - points_a[target_a][read]) >= 3
                and _answers_distinguishable(
                    answer_a, str(new_pos[read]))
            )

        candidates = _coord_move_candidates(points_a, target_a,
                                            keeps_extremum_moves_read)
        if not candidates:
            return None
        points_b = dict(points_a)
        points_b[target_a] = candidates[rng.randrange(len(candidates))]
        target_b = target_a
        moved_label = target_a
    elif role == "invariance":
        pool = [l for l in labels if l != target_a]
        rng.shuffle(pool)
        points_b = None
        moved_label = None
        for distractor in pool:
            def preserves_everything(new_pos: tuple[int, int],
                                     _d=distractor) -> bool:
                moved = dict(points_a)
                moved[_d] = new_pos
                new_target, new_gap = coord_extremum(moved, kind)
                return (
                    new_target == target_a
                    and new_gap >= COORD_MARGIN
                    and max(abs(new_pos[0] - points_a[_d][0]),
                            abs(new_pos[1] - points_a[_d][1])) >= 3
                )

            candidates = _coord_move_candidates(points_a, distractor,
                                                preserves_everything)
            if candidates:
                points_b = dict(points_a)
                points_b[distractor] = candidates[rng.randrange(len(candidates))]
                moved_label = distractor
                break
        if points_b is None:
            return None
        target_b = target_a
    else:
        raise AssertionError(f"unknown role {role}")

    answer_b = coord_read(points_b, target_b, kind)
    if role == "invariance":
        if answer_a != answer_b:
            return None
    return {
        "family": "hier_coord_v1",
        "role": role,
        "extremum_kind": kind,
        "n_points": n_points,
        "labels": labels,
        "points_a": points_a,
        "points_b": points_b,
        "target_a": target_a,
        "target_b": target_b,
        "answer_a": answer_a,
        "answer_b": answer_b,
        "moved_label": moved_label,
        "questions": coord_questions(kind, target_a),
        "questions_b_target": coord_questions(kind, target_b),
    }


# ---------------------------------------------------------------------------
# Registered in-image text (pre-freeze cleanup amendment, 2026-08-17): exactly
# one title + one LAYER-NEUTRAL encoding footer per family. In-image text must
# never state task procedure or name targets — the v1 coordinate footer stated
# the L2 two-step ("Locate the requested label, then read its coordinate...")
# inside every layer's image, contradicting the L3/probe capability contract.
# ---------------------------------------------------------------------------

COORD_TITLE = "Coordinate Survey Register"
COORD_FOOTER = "Each point is identified by its printed label."
CHART_TITLE = "Multi-Series Measurement Trace"
CHART_FOOTER = ("Each series is identified by its legend entry "
                "(color, line style, marker).")
REGISTERED_TEXT = {
    "hier_coord_v1": {"title": COORD_TITLE, "footer": COORD_FOOTER},
    "hier_chart_v1": {"title": CHART_TITLE, "footer": CHART_FOOTER},
    # v2 renders with the same renderer and therefore the same registered text
    "hier_chart_v2": {"title": CHART_TITLE, "footer": CHART_FOOTER},
}
# Any of these substrings in drawn text marks a task-procedure instruction.
PROCEDURE_TOKENS = ("locate", "requested", "then read", "first find")
# The frozen renderer's footer strip; the hier-owned renderer may differ from
# the frozen one ONLY inside this box (pinned by fixture).
COORD_FOOTER_BOX = (0, 1160, 1400, 1240)


def _render_hier_coordinate_register(points: dict[str, tuple[int, int]]) -> Image.Image:
    """Hier-owned copy of the FROZEN
    src.fliptrack.build_v02._render_high_entropy_coordinate_register,
    differing ONLY in the footer string (COORD_FOOTER, layer-neutral). The
    frozen module stays untouched for R19/premise lineage reproducibility;
    tests/test_hier_footer_text_policy.py pins that renders differ only
    inside COORD_FOOTER_BOX."""
    width, height = 1400, 1240
    image = Image.new("RGB", (width, height), (250, 250, 248))
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 38), COORD_TITLE, anchor="mm",
              font=_v02_font(26, True), fill=(25, 25, 25))
    origin = (700, 650)
    scale = 68
    plot_left = origin[0] - 7 * scale
    plot_right = origin[0] + 7 * scale
    plot_top = origin[1] - 7 * scale
    plot_bottom = origin[1] + 7 * scale
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom),
                   fill="white", outline=(75, 75, 75), width=2)
    for value in range(-7, 8):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, plot_top, x, plot_bottom), fill=(224, 228, 232), width=1)
        draw.line((plot_left, y, plot_right, y), fill=(224, 228, 232), width=1)
        if value:
            draw.text((x, origin[1] + 19), str(value), anchor="mm",
                      font=_v02_font(13), fill=(65, 65, 65))
            draw.text((origin[0] - 20, y), str(value), anchor="mm",
                      font=_v02_font(13), fill=(65, 65, 65))
    draw.line((plot_left, origin[1], plot_right, origin[1]), fill=(40, 40, 40), width=3)
    draw.line((origin[0], plot_top, origin[0], plot_bottom), fill=(40, 40, 40), width=3)

    for index, (label, point) in enumerate(points.items()):
        x = origin[0] + point[0] * scale
        y = origin[1] - point[1] * scale
        color = _V02_COLORS[index % len(_V02_COLORS)]
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color,
                     outline="white", width=2)
        label_x = x + (17 if point[0] <= 0 else -17)
        label_y = y - 16
        draw.text(
            (label_x, label_y),
            label,
            anchor="lm" if point[0] <= 0 else "rm",
            font=_v02_font(19, True),
            fill=(18, 18, 18),
            stroke_width=2,
            stroke_fill="white",
        )
    draw.text(
        (plot_left, 1186),
        COORD_FOOTER,
        font=_v02_font(15),
        fill=(70, 70, 70),
    )
    return image


def coord_target_px(points: dict[str, tuple[int, int]], label: str) -> tuple[int, int]:
    x, y = points[label]
    return (COORD_ORIGIN[0] + x * COORD_SCALE, COORD_ORIGIN[1] - y * COORD_SCALE)


def render_coord_layers(points: dict[str, tuple[int, int]],
                        target: str) -> tuple[Image.Image, Image.Image, dict] | None:
    """(l2==l3 image, l1 image, cue record) or None if no legal cue placement."""
    base = _render_hier_coordinate_register(points)
    cued = add_offset_cue(base, coord_target_px(points, target), COORD_ALLOWED)
    if cued is None:
        return None
    l1, record = cued
    return base, l1, record


# ---------------------------------------------------------------------------
# chart family (hier_chart_v1)
# ---------------------------------------------------------------------------

CHART_WIDTH, CHART_HEIGHT = 1400, 900
CHART_PLOT = (100, 82, 1010, 770)
CHART_LEGEND = (1040, 82, 1370, 530)
CHART_CANVAS = (246, 248, 247)
CHART_ALLOWED = frozenset({CHART_CANVAS, (255, 255, 255)})

# Additive 9-series extension (the v08 6-tuples are imported untouched).
EXTRA_COLORS = ((0, 0, 0), (117, 81, 39), (64, 44, 155))
EXTRA_LINESTYLES = ("altdash", "altdot", "altdashdot")
EXTRA_MARKERS = ("tri_down", "hexagon", "star")
EXTRA_LABELS = ("Grove", "Harbor", "Iris")
HIER_COLORS = V08_COLORS + EXTRA_COLORS
HIER_LINESTYLES = V08_LINESTYLES + EXTRA_LINESTYLES
HIER_MARKERS = V08_MARKERS + EXTRA_MARKERS
HIER_LABELS = V08_LABELS + EXTRA_LABELS

_SEGMENT_PATTERNS = {
    "solid": (10_000, 0), "dash": (16, 9), "dot": (3, 7), "dashdot": (14, 7),
    "longdash": (24, 10), "shortdash": (9, 6),
    "altdash": (20, 4), "altdot": (5, 5), "altdashdot": (11, 11),
}

X_COUNT = 7
CHART_GRANULARITY = 5
CROSSING_BANDS = {"low": (0.0, 0.25), "high": (0.50, 1.0)}  # Amendment A1


def _draw_segment(draw, start, end, *, fill, width, style) -> None:
    on, off = _SEGMENT_PATTERNS[style]
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


def _draw_marker_ext(draw, point, marker, color, radius: int = 6) -> None:
    x, y = point
    if marker == "tri_down":
        draw.polygon(((x, y + radius + 1), (x - radius, y - radius),
                      (x + radius, y - radius)), fill=color)
    elif marker == "hexagon":
        half = radius
        draw.polygon(((x - half, y), (x - half // 2, y - half),
                      (x + half // 2, y - half), (x + half, y),
                      (x + half // 2, y + half), (x - half // 2, y + half)),
                     fill=color)
    elif marker == "star":
        for angle_index in range(5):
            angle = -math.pi / 2 + angle_index * 2 * math.pi / 5
            tip = (round(x + math.cos(angle) * (radius + 2)),
                   round(y + math.sin(angle) * (radius + 2)))
            draw.line(((x, y), tip), fill=color, width=3)
    else:
        _draw_marker(draw, point, marker, color, radius)


def render_hier_chart(values: list[list[int]], series_count: int) -> Image.Image:
    """9-series-capable chart, no star machinery, v08 geometry constants."""
    image = Image.new("RGB", (CHART_WIDTH, CHART_HEIGHT), CHART_CANVAS)
    draw = ImageDraw.Draw(image)
    x_positions, left, top, right, bottom = _positions(X_COUNT)
    draw.text((CHART_WIDTH // 2, 34), "Multi-Series Measurement Trace",
              anchor="mm", font=_font(25, True), fill=(25, 25, 25))
    draw.rectangle(CHART_PLOT, fill="white", outline=(40, 40, 40), width=2)
    for tick in range(0, 101, 10):
        y = bottom - round(tick / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=(224, 228, 230), width=1)
        draw.text((left - 14, y), str(tick), anchor="rm", font=_font(15), fill=(45, 45, 45))
    for index, x in enumerate(x_positions, start=1):
        draw.line((x, top, x, bottom), fill=(239, 241, 242), width=1)
        draw.text((x, bottom + 27), str(index), anchor="mm", font=_font(16), fill=(45, 45, 45))
    draw.text(((left + right) // 2, bottom + 58), "x", anchor="mm",
              font=_font(18, True), fill=(35, 35, 35))
    for series in range(series_count):
        points = [
            (x, bottom - round(value / 100 * (bottom - top)))
            for x, value in zip(x_positions, values[series])
        ]
        for p0, p1 in zip(points, points[1:]):
            _draw_segment(draw, p0, p1, fill=HIER_COLORS[series], width=4,
                          style=HIER_LINESTYLES[series])
        for point in points:
            _draw_marker_ext(draw, point, HIER_MARKERS[series], HIER_COLORS[series])
    draw.rectangle(CHART_LEGEND, fill="white", outline=(150, 150, 150), width=2)
    draw.text((1205, 108), "Series key", anchor="mm", font=_font(20, True), fill=(25, 25, 25))
    row_step = 56 if series_count <= 6 else 40
    for index in range(series_count):
        y = 148 + index * row_step
        _draw_segment(draw, (1088, y), (1142, y), fill=HIER_COLORS[index],
                      width=5, style=HIER_LINESTYLES[index])
        _draw_marker_ext(draw, (1115, y), HIER_MARKERS[index], HIER_COLORS[index])
        draw.text((1162, y), HIER_LABELS[index], anchor="lm", font=_font(18), fill=(20, 20, 20))
    draw.text((100, 855),
              "Each series is identified by its legend entry (color, line style, marker).",
              font=_font(16), fill=(60, 60, 60))
    return image


def chart_value_px(values: list[list[int]], series: int, x_index: int) -> tuple[int, int]:
    x_positions, left, top, right, bottom = _positions(X_COUNT)
    return (x_positions[x_index],
            bottom - round(values[series][x_index] / 100 * (bottom - top)))


def chart_questions(series_name: str, xa: int, xr: int) -> dict[str, str]:
    return {
        "l3": (f"Consider the series with the highest value at x = {xa}. "
               f"What value does that series have at x = {xr}?"),
        "l2": (f"The series {series_name} has the highest value at x = {xa}. "
               f"What value does {series_name} have at x = {xr}?"),
        "probe": f"Which series has the highest value at x = {xa}?",
    }


def chart_argmax(values: list[list[int]], series_count: int, x_index: int) -> tuple[int, int]:
    column = [(values[s][x_index], s) for s in range(series_count)]
    ordered = sorted(column, reverse=True)
    return ordered[0][1], ordered[0][0] - ordered[1][0]


def crossing_fraction(values: list[list[int]], series_count: int, x_index: int) -> float:
    count = adjacent_crossing_count([row[:] for row in values[:series_count]], x_index)
    slots = math.comb(series_count, 2) * 2
    return count / slots


def build_chart_geometry(role: str, series_count: int, density: str,
                         rng) -> dict[str, Any] | None:
    xa = rng.randrange(1, X_COUNT - 1)          # interior, 0-based
    xr = rng.choice([x for x in range(1, X_COUNT - 1) if x != xa])
    center = rng.randrange(30, 71)
    values = []
    if density == "low":
        # Banded proposal: at 9 series a random-values proposal essentially
        # never lands in the registered low-crossing band (72 slots), so low
        # cells propose separated value bands with small jitter. The
        # registered band filter below is UNCHANGED and still decides
        # acceptance (A1: scenes outside the band are resampled).
        grid = list(range(15, 91, CHART_GRANULARITY))
        idxs = [round(i * (len(grid) - 1) / (series_count - 1))
                for i in range(series_count)]
        centers = [grid[i] for i in idxs]
        rng.shuffle(centers)
        for series in range(series_count):
            row = []
            for _ in range(X_COUNT):
                jitter = rng.choice((0, 0, 0, -CHART_GRANULARITY, CHART_GRANULARITY))
                row.append(min(90, max(15, centers[series] + jitter)))
            values.append(row)
    else:
        for _ in range(series_count):
            row = [rng.randrange(15, 91, CHART_GRANULARITY) for _ in range(X_COUNT)]
            for x in (xr - 1, xr, xr + 1):
                pulled = center + rng.randrange(-10, 11, CHART_GRANULARITY)
                row[x] = min(90, max(15, pulled))
            values.append(row)
    low, high = CROSSING_BANDS[density]
    if not (low <= crossing_fraction(values, series_count, xr) <= high):
        return None
    target_a, gap = chart_argmax(values, series_count, xa)
    if gap < CHART_GRANULARITY:
        return None
    answer_a = str(values[target_a][xr])

    values_b = [row[:] for row in values]
    if role == "target_switch":
        ordered = sorted(((values[s][xa], s) for s in range(series_count)), reverse=True)
        runner_up = ordered[1][1]
        new_value = ordered[1][0] - CHART_GRANULARITY * rng.randrange(1, 4)
        if new_value < 15:
            return None
        values_b[target_a][xa] = new_value
        new_target, new_gap = chart_argmax(values_b, series_count, xa)
        if new_target != runner_up or new_gap < CHART_GRANULARITY:
            return None
        target_b = runner_up
        answer_b = str(values_b[target_b][xr])
        if not _answers_distinguishable(answer_a, answer_b):
            return None
        changed = ("value", target_a, xa)
    elif role == "target_stable":
        options = [v for v in range(15, 91, CHART_GRANULARITY)
                   if v != values[target_a][xr]
                   and _answers_distinguishable(answer_a, str(v))]
        if not options:
            return None
        values_b[target_a][xr] = options[rng.randrange(len(options))]
        if xr == xa:  # never true (xa != xr) — belt and braces
            return None
        target_b = target_a
        answer_b = str(values_b[target_b][xr])
        changed = ("value", target_a, xr)
    elif role == "invariance":
        distractors = [s for s in range(series_count) if s != target_a]
        rng.shuffle(distractors)
        xs = [x for x in range(X_COUNT) if x != xa]
        rng.shuffle(xs)
        changed = None
        for series in distractors:
            for x in xs:
                options = [v for v in range(15, 91, CHART_GRANULARITY)
                           if abs(v - values[series][x]) >= CHART_GRANULARITY * 2]
                if not options:
                    continue
                values_b[series][x] = options[rng.randrange(len(options))]
                new_target, new_gap = chart_argmax(values_b, series_count, xa)
                if new_target == target_a and new_gap >= CHART_GRANULARITY:
                    changed = ("value", series, x)
                    break
                values_b[series][x] = values[series][x]
            if changed:
                break
        if changed is None:
            return None
        target_b = target_a
        answer_b = str(values_b[target_b][xr])
        if answer_a != answer_b:
            return None
    else:
        raise AssertionError(f"unknown role {role}")

    return {
        "family": "hier_chart_v1",
        "role": role,
        "series_count": series_count,
        "density": density,
        "xa": xa + 1,   # 1-based, question-facing
        "xr": xr + 1,
        "values_a": values,
        "values_b": values_b,
        "target_a": target_a,
        "target_b": target_b,
        "target_a_name": HIER_LABELS[target_a],
        "target_b_name": HIER_LABELS[target_b],
        "answer_a": answer_a,
        "answer_b": answer_b,
        "changed": list(changed),
        "questions": chart_questions(HIER_LABELS[target_a], xa + 1, xr + 1),
        "questions_b_target": chart_questions(HIER_LABELS[target_b], xa + 1, xr + 1),
        "crossing_fraction_a": crossing_fraction(values, series_count, xr),
    }


def render_chart_layers(values: list[list[int]], series_count: int,
                        target_series: int,
                        xr_zero_based: int) -> tuple[Image.Image, Image.Image, dict] | None:
    base = render_hier_chart(values, series_count)
    cued = add_offset_cue(
        base, chart_value_px(values, target_series, xr_zero_based), CHART_ALLOWED
    )
    if cued is None:
        return None
    l1, record = cued
    return base, l1, record


def chart_hard_negatives(geometry: dict[str, Any]) -> list[dict[str, Any]]:
    """Structured roles per Amendment A1 / HB.5 for the chart family."""
    values_a, values_b = geometry["values_a"], geometry["values_b"]
    series_count = geometry["series_count"]
    xa, xr = geometry["xa"] - 1, geometry["xr"] - 1
    negatives: dict[str, set[str]] = {}

    def add(value: Any, role: str) -> None:
        negatives.setdefault(str(value), set()).add(role)

    add(geometry["answer_a"], "gold_member_a")
    add(geometry["answer_b"], "gold_member_b")
    add(geometry["answer_b"], "twin_member_gold_for_a")
    add(geometry["answer_a"], "twin_member_gold_for_b")
    for tag, values, target in (("member_a", values_a, geometry["target_a"]),
                                ("member_b", values_b, geometry["target_b"])):
        add(values[target][xa], f"anchor_x_value_{tag}")          # other-axis analog
        for series in range(series_count):
            if series != target:
                add(values[series][xr], f"other_series_at_read_x_{tag}")
        for neighbor in (xr - 1, xr + 1):
            if 0 <= neighbor < X_COUNT:
                add(values[target][neighbor], f"neighbor_x_value_{tag}")
    return [
        {"answer": value, "negative_types": sorted(roles)}
        for value, roles in sorted(negatives.items())
    ]


def coord_hard_negatives(geometry: dict[str, Any]) -> list[dict[str, Any]]:
    return hard_negatives(
        geometry["points_a"], geometry["points_b"], geometry["target_a"],
        geometry["answer_a"], geometry["answer_b"],
    )


def hier_palette_report() -> dict[str, float]:
    return palette_distance_report(HIER_COLORS)


# ---------------------------------------------------------------------------
# chart family v2 (hier_chart_v2) — Amendment A4, 2026-08-17
#
# v1 failed the artifact-attacker gate structurally, not statistically: every
# causal edit ADDED ink to exactly one side (switch lowered the winner in
# 200/200 pairs; in low-crossing cells the edited PNG was larger in 198/200),
# so dinov2/frequency/metadata could all read "which side was edited" without
# reading the task. Symmetrising the direction cannot fix that — an edit in
# either direction still breaks the band and adds ink to the side it lands on.
#
# v2 therefore makes every causal edit a TRANSPOSITION WITHIN A COLUMN: two
# series exchange their values at one x. The column's value multiset — and
# hence the global ink budget, the compression profile and the file size — is
# identical on both sides by construction, and neither side is structurally
# "the edited one". This satisfies the ratified "symmetrized switch edit" with
# no direction bookkeeping (a swap has no direction) and the ratified
# "band-preserving low-cell edits" exactly (a swap cannot leave the band).
# ---------------------------------------------------------------------------


def _column_multiset(values: list[list[int]], series_count: int, x: int) -> list[int]:
    return sorted(values[s][x] for s in range(series_count))


def build_chart_v2_geometry(role: str, series_count: int, density: str,
                            rng) -> dict[str, Any] | None:
    """hier_chart_v2 geometry: identical scene proposal and registered band
    filter as v1, but all three roles edit by column transposition, and the
    crossing band is now verified on BOTH sides (v1 checked side A only)."""
    xa = rng.randrange(1, X_COUNT - 1)
    xr = rng.choice([x for x in range(1, X_COUNT - 1) if x != xa])
    center = rng.randrange(30, 71)
    values: list[list[int]] = []
    if density == "low":
        grid = list(range(15, 91, CHART_GRANULARITY))
        idxs = [round(i * (len(grid) - 1) / (series_count - 1))
                for i in range(series_count)]
        centers = [grid[i] for i in idxs]
        rng.shuffle(centers)
        for series in range(series_count):
            row = []
            for _ in range(X_COUNT):
                jitter = rng.choice((0, 0, 0, -CHART_GRANULARITY, CHART_GRANULARITY))
                row.append(min(90, max(15, centers[series] + jitter)))
            values.append(row)
    else:
        for _ in range(series_count):
            row = [rng.randrange(15, 91, CHART_GRANULARITY) for _ in range(X_COUNT)]
            for x in (xr - 1, xr, xr + 1):
                pulled = center + rng.randrange(-10, 11, CHART_GRANULARITY)
                row[x] = min(90, max(15, pulled))
            values.append(row)

    low, high = CROSSING_BANDS[density]
    if not (low <= crossing_fraction(values, series_count, xr) <= high):
        return None
    target_a, gap = chart_argmax(values, series_count, xa)
    if gap < CHART_GRANULARITY:
        return None
    answer_a = str(values[target_a][xr])

    values_b = [row[:] for row in values]
    if role == "target_switch":
        # Swap the top-2 values at the ANCHOR x. The argmax becomes the
        # runner-up with the identical margin, both read-x values are
        # untouched, and the anchor column's multiset is unchanged.
        ordered = sorted(((values[s][xa], s) for s in range(series_count)), reverse=True)
        runner_up = ordered[1][1]
        if ordered[0][0] == ordered[1][0]:
            return None
        values_b[target_a][xa], values_b[runner_up][xa] = (
            values[runner_up][xa], values[target_a][xa])
        new_target, new_gap = chart_argmax(values_b, series_count, xa)
        if new_target != runner_up or new_gap < CHART_GRANULARITY:
            return None
        target_b = runner_up
        answer_b = str(values_b[target_b][xr])
        if not _answers_distinguishable(answer_a, answer_b):
            return None
        changed = ("swap", target_a, runner_up, xa)
    elif role == "target_stable":
        # Swap the target's value at the READ x with a non-target's value
        # there: the answer moves, the target identity does not, and the read
        # column's multiset is unchanged. The anchor column is untouched, so
        # the argmax cannot move.
        partners = [s for s in range(series_count)
                    if s != target_a and values[s][xr] != values[target_a][xr]
                    and _answers_distinguishable(answer_a, str(values[s][xr]))]
        if not partners:
            return None
        partner = partners[rng.randrange(len(partners))]
        values_b[target_a][xr], values_b[partner][xr] = (
            values[partner][xr], values[target_a][xr])
        target_b = target_a
        answer_b = str(values_b[target_b][xr])
        if not _answers_distinguishable(answer_a, answer_b):
            return None
        changed = ("swap", target_a, partner, xr)
    elif role == "invariance":
        # Swap two NON-target values at some x: the answer is untouched on both
        # sides, and the argmax at the anchor is preserved because the target's
        # own value never moves and the column multiset is unchanged.
        candidates = []
        for x in range(X_COUNT):
            others = [s for s in range(series_count) if s != target_a]
            for i, s in enumerate(others):
                for t in others[i + 1:]:
                    if values[s][x] != values[t][x]:
                        candidates.append((x, s, t))
        if not candidates:
            return None
        rng.shuffle(candidates)
        changed = None
        for x, s, t in candidates:
            values_b = [row[:] for row in values]
            values_b[s][x], values_b[t][x] = values[t][x], values[s][x]
            new_target, new_gap = chart_argmax(values_b, series_count, xa)
            if new_target == target_a and new_gap >= CHART_GRANULARITY:
                changed = ("swap", s, t, x)
                break
        if changed is None:
            return None
        target_b = target_a
        answer_b = str(values_b[target_b][xr])
        if answer_a != answer_b:
            return None
    else:
        raise AssertionError(f"unknown role {role}")

    # Both-side band filter (v1 checked side A only, which let the edited side
    # leave the registered band unobserved).
    crossing_b = crossing_fraction(values_b, series_count, xr)
    if not (low <= crossing_b <= high):
        return None
    # Multiset invariance: the defining property of the v2 construction.
    for x in range(X_COUNT):
        if _column_multiset(values, series_count, x) != _column_multiset(
                values_b, series_count, x):
            return None

    return {
        "family": "hier_chart_v2",
        "role": role,
        "series_count": series_count,
        "density": density,
        "xa": xa + 1,
        "xr": xr + 1,
        "values_a": values,
        "values_b": values_b,
        "target_a": target_a,
        "target_b": target_b,
        "target_a_name": HIER_LABELS[target_a],
        "target_b_name": HIER_LABELS[target_b],
        "answer_a": answer_a,
        "answer_b": answer_b,
        "changed": list(changed),
        "questions": chart_questions(HIER_LABELS[target_a], xa + 1, xr + 1),
        "questions_b_target": chart_questions(HIER_LABELS[target_b], xa + 1, xr + 1),
        "crossing_fraction_a": crossing_fraction(values, series_count, xr),
        "crossing_fraction_b": crossing_b,
        "edit_kind": "column_transposition",
    }
