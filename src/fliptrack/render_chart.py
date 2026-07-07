from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.fliptrack.schema import pair_record, stable_id, write_jsonl


WIDTH, HEIGHT = 720, 480
PLOT_LEFT, PLOT_TOP, PLOT_RIGHT, PLOT_BOTTOM = 90, 60, 660, 390
BAR_COLOR = (43, 116, 196)
FLIP_COLOR = (40, 125, 95)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _draw_mask(rect: tuple[int, int, int, int], path: Path) -> None:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(rect, fill=255)
    mask.save(path)


def _draw_chart(labels: list[str], values: list[int], changed_idx: int, out: Path, mask: Path) -> tuple[int, int, int, int]:
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    title_font = _font(26)
    label_font = _font(20)
    tick_font = _font(16)

    draw.text((WIDTH // 2, 25), "Quarterly Units", anchor="mm", fill=(20, 20, 20), font=title_font)
    draw.line((PLOT_LEFT, PLOT_BOTTOM, PLOT_RIGHT, PLOT_BOTTOM), fill=(35, 35, 35), width=3)
    draw.line((PLOT_LEFT, PLOT_TOP, PLOT_LEFT, PLOT_BOTTOM), fill=(35, 35, 35), width=3)

    max_value = max(max(values), 10)
    scale_top = ((max_value + 9) // 10) * 10
    for tick in range(0, scale_top + 1, max(5, scale_top // 5)):
        y = PLOT_BOTTOM - int((tick / scale_top) * (PLOT_BOTTOM - PLOT_TOP))
        draw.line((PLOT_LEFT - 7, y, PLOT_RIGHT, y), fill=(225, 225, 225), width=1)
        draw.text((PLOT_LEFT - 15, y), str(tick), anchor="rm", fill=(70, 70, 70), font=tick_font)

    slot = (PLOT_RIGHT - PLOT_LEFT) / len(labels)
    bar_width = int(slot * 0.56)
    changed_rect = (0, 0, 0, 0)
    for idx, (label, value) in enumerate(zip(labels, values)):
        cx = int(PLOT_LEFT + slot * idx + slot / 2)
        x0 = cx - bar_width // 2
        x1 = cx + bar_width // 2
        y1 = PLOT_BOTTOM - 1
        y0 = PLOT_BOTTOM - int((value / scale_top) * (PLOT_BOTTOM - PLOT_TOP))
        color = FLIP_COLOR if idx == changed_idx else BAR_COLOR
        draw.rectangle((x0, y0, x1, y1), fill=color)
        draw.text((cx, y0 - 14), str(value), anchor="mm", fill=(20, 20, 20), font=tick_font)
        draw.text((cx, PLOT_BOTTOM + 28), label, anchor="mm", fill=(30, 30, 30), font=label_font)
        if idx == changed_idx:
            changed_rect = (x0 - 6, min(y0 - 24, PLOT_BOTTOM - 24), x1 + 6, PLOT_BOTTOM + 8)

    img.save(out)
    _draw_mask(changed_rect, mask)
    return changed_rect


def generate_chart_pairs(out_dir: str | Path, n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out_dir = Path(out_dir)
    img_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    label_pool = [
        ["Q1", "Q2", "Q3", "Q4"],
        ["North", "South", "East", "West"],
        ["Alpha", "Beta", "Gamma", "Delta"],
    ]
    for i in range(n):
        labels = rng.choice(label_pool)
        values_a = [rng.randint(12, 86) for _ in labels]
        changed_idx = rng.randrange(len(labels))
        delta = rng.choice([-18, -13, -9, 9, 13, 18])
        values_b = list(values_a)
        values_b[changed_idx] = max(5, min(95, values_b[changed_idx] + delta))
        if values_b[changed_idx] == values_a[changed_idx]:
            values_b[changed_idx] = values_a[changed_idx] + 7

        pair_id = "chart_" + stable_id(seed, i, labels, values_a, values_b)
        image_a = img_dir / f"{pair_id}_a.png"
        image_b = img_dir / f"{pair_id}_b.png"
        mask_a = mask_dir / f"{pair_id}_a_mask.png"
        mask_b = mask_dir / f"{pair_id}_b_mask.png"
        _draw_chart(labels, values_a, changed_idx, image_a, mask_a)
        _draw_chart(labels, values_b, changed_idx, image_b, mask_b)

        rows.append(
            pair_record(
                pair_id=pair_id,
                image_a_path=str(image_a),
                image_b_path=str(image_b),
                changed_region_mask_a=str(mask_a),
                changed_region_mask_b=str(mask_b),
                question=f"What is the value for {labels[changed_idx]}?",
                answer_a=str(values_a[changed_idx]),
                answer_b=str(values_b[changed_idx]),
                category="chart_value",
                template_id="bar_value_v0",
                provenance={"generator": "src.fliptrack.render_chart", "seed": seed, "index": i},
                verifier_results={"exact_by_construction": True, "changed_index": changed_idx},
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v0/chart")
    parser.add_argument("--manifest", default="data/fliptrack_v0/chart_manifest.jsonl")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    rows = generate_chart_pairs(args.out_dir, args.n, args.seed)
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()

