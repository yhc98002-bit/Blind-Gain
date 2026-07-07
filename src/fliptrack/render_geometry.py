from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.fliptrack.schema import pair_record, stable_id, write_jsonl


WIDTH, HEIGHT = 640, 480


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


def _render_relation(answer: str, out: Path, mask: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    font = _font(24)
    draw.text((WIDTH // 2, 40), "Diagram", anchor="mm", fill=(20, 20, 20), font=font)
    draw.line((80, 390, 560, 390), fill=(210, 210, 210), width=2)

    red_rect = (310, 190, 410, 290)
    blue_rect = (170, 205, 250, 285) if answer == "left" else (470, 205, 550, 285)
    draw.rectangle(red_rect, fill=(206, 62, 62), outline=(120, 20, 20), width=3)
    draw.ellipse(blue_rect, fill=(55, 117, 201), outline=(20, 60, 130), width=3)
    draw.text(((red_rect[0] + red_rect[2]) // 2, red_rect[3] + 26), "red square", anchor="mm", fill=(20, 20, 20), font=_font(18))
    draw.text(((blue_rect[0] + blue_rect[2]) // 2, blue_rect[3] + 26), "blue circle", anchor="mm", fill=(20, 20, 20), font=_font(18))

    img.save(out)
    _draw_mask((blue_rect[0] - 6, blue_rect[1] - 6, blue_rect[2] + 6, blue_rect[3] + 6), mask)


def generate_geometry_pairs(out_dir: str | Path, n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out_dir = Path(out_dir)
    img_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(n):
        first = rng.choice(["left", "right"])
        second = "right" if first == "left" else "left"
        pair_id = "geometry_" + stable_id(seed, i, first)
        image_a = img_dir / f"{pair_id}_a.png"
        image_b = img_dir / f"{pair_id}_b.png"
        mask_a = mask_dir / f"{pair_id}_a_mask.png"
        mask_b = mask_dir / f"{pair_id}_b_mask.png"
        _render_relation(first, image_a, mask_a)
        _render_relation(second, image_b, mask_b)
        rows.append(
            pair_record(
                pair_id=pair_id,
                image_a_path=str(image_a),
                image_b_path=str(image_b),
                changed_region_mask_a=str(mask_a),
                changed_region_mask_b=str(mask_b),
                question="Is the blue circle to the left or to the right of the red square?",
                answer_a=first,
                answer_b=second,
                category="geometry_spatial_relation",
                template_id="circle_square_relation_v0",
                provenance={"generator": "src.fliptrack.render_geometry", "seed": seed, "index": i},
                verifier_results={"exact_by_construction": True},
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v0/geometry")
    parser.add_argument("--manifest", default="data/fliptrack_v0/geometry_manifest.jsonl")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=19)
    args = parser.parse_args()
    rows = generate_geometry_pairs(args.out_dir, args.n, args.seed)
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()

