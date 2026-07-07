from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.fliptrack.schema import pair_record, stable_id, write_jsonl


WIDTH, HEIGHT = 900, 620


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf"] if bold else ["DejaVuSans.ttf", "Arial.ttf"]
    for name in names:
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


def _render_doc(fields: dict[str, str], changed_key: str, out: Path, mask: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), (250, 250, 247))
    draw = ImageDraw.Draw(img)
    title_font = _font(30, True)
    body_font = _font(23)
    small_font = _font(18)

    draw.rectangle((70, 45, WIDTH - 70, HEIGHT - 45), fill="white", outline=(180, 180, 180), width=2)
    draw.text((WIDTH // 2, 90), "Service Visit Summary", anchor="mm", fill=(20, 20, 20), font=title_font)
    draw.line((110, 125, WIDTH - 110, 125), fill=(200, 200, 200), width=2)
    draw.text((115, 160), "Customer", fill=(60, 60, 60), font=small_font)
    draw.text((300, 160), fields["customer"], fill=(20, 20, 20), font=body_font)
    draw.text((115, 205), "Ticket ID", fill=(60, 60, 60), font=small_font)
    draw.text((300, 205), fields["ticket"], fill=(20, 20, 20), font=body_font)

    y = 275
    rect = None
    for key, label in [("room", "Room"), ("time", "Time"), ("technician", "Technician"), ("total", "Total Due")]:
        draw.text((115, y), label, fill=(60, 60, 60), font=small_font)
        draw.rounded_rectangle((292, y - 8, 610, y + 32), radius=4, outline=(230, 230, 230), fill=(248, 250, 252))
        draw.text((310, y), fields[key], fill=(15, 15, 15), font=body_font)
        if key == changed_key:
            rect = (292, y - 8, 610, y + 32)
        y += 52

    draw.text((115, HEIGHT - 95), "Notes: Bring a printed copy to the front desk.", fill=(90, 90, 90), font=small_font)
    img.save(out)
    assert rect is not None
    _draw_mask(rect, mask)


def generate_doc_pairs(out_dir: str | Path, n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out_dir = Path(out_dir)
    img_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    customers = ["Mina Chen", "Ari Singh", "Noah Park", "Lina Zhou"]
    techs = ["T. Rivera", "J. Morgan", "S. Patel", "K. Lin"]
    keys = ["room", "time", "technician", "total"]
    rows = []
    for i in range(n):
        fields_a = {
            "customer": rng.choice(customers),
            "ticket": f"BG-{rng.randint(1000, 9999)}",
            "room": f"{rng.choice(['A', 'B', 'C'])}-{rng.randint(101, 429)}",
            "time": f"{rng.randint(8, 17):02d}:{rng.choice(['00', '15', '30', '45'])}",
            "technician": rng.choice(techs),
            "total": f"${rng.randint(24, 180)}",
        }
        changed_key = rng.choice(keys)
        fields_b = dict(fields_a)
        if changed_key == "room":
            fields_b["room"] = f"{rng.choice(['D', 'E', 'F'])}-{rng.randint(101, 429)}"
        elif changed_key == "time":
            fields_b["time"] = f"{rng.randint(8, 17):02d}:{rng.choice(['05', '20', '35', '50'])}"
        elif changed_key == "technician":
            fields_b["technician"] = rng.choice([t for t in techs if t != fields_a["technician"]])
        else:
            fields_b["total"] = f"${rng.randint(181, 360)}"

        pair_id = "doc_" + stable_id(seed, i, fields_a, fields_b, changed_key)
        image_a = img_dir / f"{pair_id}_a.png"
        image_b = img_dir / f"{pair_id}_b.png"
        mask_a = mask_dir / f"{pair_id}_a_mask.png"
        mask_b = mask_dir / f"{pair_id}_b_mask.png"
        _render_doc(fields_a, changed_key, image_a, mask_a)
        _render_doc(fields_b, changed_key, image_b, mask_b)

        question_key = {"room": "room", "time": "scheduled time", "technician": "technician", "total": "total due"}[changed_key]
        rows.append(
            pair_record(
                pair_id=pair_id,
                image_a_path=str(image_a),
                image_b_path=str(image_b),
                changed_region_mask_a=str(mask_a),
                changed_region_mask_b=str(mask_b),
                question=f"What is the {question_key}?",
                answer_a=fields_a[changed_key],
                answer_b=fields_b[changed_key],
                category="document_ocr",
                template_id="service_summary_v0",
                provenance={"generator": "src.fliptrack.render_doc", "seed": seed, "index": i},
                verifier_results={"exact_by_construction": True, "changed_key": changed_key},
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v0/doc")
    parser.add_argument("--manifest", default="data/fliptrack_v0/doc_manifest.jsonl")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    rows = generate_doc_pairs(args.out_dir, args.n, args.seed)
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()

