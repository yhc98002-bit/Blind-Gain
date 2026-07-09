from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.fliptrack.schema import pair_record, stable_id, write_jsonl


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf"] if bold else ["DejaVuSans.ttf", "Arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _mask(size: tuple[int, int], rect: tuple[int, int, int, int], path: Path) -> None:
    img = Image.new("L", size, 0)
    ImageDraw.Draw(img).rectangle(rect, fill=255)
    img.save(path)


def _save_pair(
    *,
    pair_id: str,
    image_a: Path,
    image_b: Path,
    mask_a: Path,
    mask_b: Path,
    question: str,
    answer_a: str,
    answer_b: str,
    category: str,
    template_id: str,
    provenance: dict[str, Any],
    verifier_results: dict[str, Any],
    catch_twin_id: str | None = None,
) -> dict[str, Any]:
    return pair_record(
        pair_id=pair_id,
        image_a_path=str(image_a),
        image_b_path=str(image_b),
        changed_region_mask_a=str(mask_a),
        changed_region_mask_b=str(mask_b),
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        category=category,
        template_id=template_id,
        provenance=provenance,
        verifier_results=verifier_results,
        artifact_gate_score=None,
        catch_twin_id=catch_twin_id,
    )


def _chart_image(labels: dict[str, str], target: str, out: Path, mask_path: Path) -> None:
    width, height = 900, 560
    img = Image.new("RGB", (width, height), (252, 252, 250))
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = 70, 70, 555, 430
    draw.text((width // 2, 35), "Regional Mix Dashboard", anchor="mm", font=_font(24, True), fill=(25, 25, 25))
    draw.rectangle((left, top, right, bottom), outline=(45, 45, 45), width=2)
    for tick in range(0, 101, 20):
        y = bottom - int((tick / 100.0) * (bottom - top))
        draw.line((left, y, right, y), fill=(225, 225, 225), width=1)
        draw.text((left - 12, y), str(tick), anchor="rm", font=_font(13), fill=(70, 70, 70))

    rng = random.Random(stable_id(labels, target))
    colors = {
        "amber": (214, 139, 38),
        "blue": (53, 101, 190),
        "green": (68, 145, 87),
        "purple": (126, 82, 160),
        "red": (202, 70, 70),
        "teal": (45, 148, 151),
        "gray": (115, 125, 138),
        "pink": (206, 94, 142),
    }
    series = list(labels)
    xs = [left + 35 + idx * 58 for idx in range(8)]
    for color_name, color in colors.items():
        points = []
        base = rng.randint(20, 72)
        for idx, x in enumerate(xs):
            val = max(8, min(96, base + rng.randint(-16, 16) + idx * rng.choice([-2, -1, 1, 2])))
            y = bottom - int((val / 100.0) * (bottom - top))
            points.append((x, y))
        draw.line(points, fill=color, width=3)
        for point in points:
            draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=color)

    legend_x, legend_y = 600, 88
    draw.rectangle((585, 65, 850, 448), fill=(255, 255, 255), outline=(190, 190, 190), width=2)
    draw.text((718, 84), "Legend", anchor="mm", font=_font(20, True), fill=(25, 25, 25))
    target_rect = (0, 0, 0, 0)
    for idx, color_name in enumerate(series):
        row = idx
        y = legend_y + 35 + row * 40
        draw.rectangle((legend_x, y - 12, legend_x + 30, y + 12), fill=colors[color_name], outline=(40, 40, 40))
        if color_name == target:
            target_rect = (legend_x - 18, y - 18, legend_x + 190, y + 18)
            draw.text((legend_x - 8, y), "*", anchor="mm", font=_font(26, True), fill=(0, 0, 0))
        draw.text((legend_x + 44, y), labels[color_name], anchor="lm", font=_font(18), fill=(15, 15, 15))
    draw.text((70, height - 62), "The black star marks the queried legend entry; read that entry's label.", font=_font(15), fill=(70, 70, 70))
    img.save(out)
    _mask((width, height), target_rect, mask_path)


def generate_chart_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    img_dir, mask_dir = out_dir / "images", out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    colors = ["amber", "blue", "green", "purple", "red", "teal", "gray", "pink"]
    label_pool = [
        "Atlas-14",
        "Boreal-22",
        "Cedar-31",
        "Delta-37",
        "Ember-46",
        "Fjord-52",
        "Grove-68",
        "Harbor-73",
        "Ion-85",
        "Juno-91",
        "Kite-26",
        "Lumen-44",
    ]
    for i in range(n):
        chosen = rng.sample(label_pool, len(colors))
        labels_a = dict(zip(colors, chosen))
        target = rng.choice(colors)
        labels_b = dict(labels_a)
        replacement = rng.choice([label for label in label_pool if label not in labels_a.values()])
        labels_b[target] = replacement
        pair_id = "v01_chart_" + stable_id(seed, i, labels_a, labels_b, target)
        image_a, image_b = img_dir / f"{pair_id}_a.png", img_dir / f"{pair_id}_b.png"
        mask_a, mask_b = mask_dir / f"{pair_id}_a_mask.png", mask_dir / f"{pair_id}_b_mask.png"
        _chart_image(labels_a, target, image_a, mask_a)
        _chart_image(labels_b, target, image_b, mask_b)
        rows.append(
            _save_pair(
                pair_id=pair_id,
                image_a=image_a,
                image_b=image_b,
                mask_a=mask_a,
                mask_b=mask_b,
                question=f"What label is next to the black-starred {target} legend entry?",
                answer_a=labels_a[target],
                answer_b=labels_b[target],
                category="chart_legend_lookup",
                template_id="starred_legend_label_v01",
                provenance={"generator": "src.fliptrack.build_v01", "seed": seed, "index": i, "family": "chart"},
                verifier_results={"exact_by_construction": True, "target": target, "labels_a": labels_a, "labels_b": labels_b},
            )
        )
    return rows


def _doc_image(table: list[list[str]], row_label: str, col_label: str, out: Path, mask_path: Path) -> None:
    width, height = 980, 680
    img = Image.new("RGB", (width, height), (248, 248, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle((55, 45, width - 55, height - 45), fill="white", outline=(190, 190, 190), width=2)
    draw.text((width // 2, 82), "Warehouse Exception Sheet", anchor="mm", font=_font(25, True), fill=(20, 20, 20))
    left, top = 120, 145
    cell_w, cell_h = 126, 48
    cols = ["A1", "B2", "C3", "D4", "E5", "F6"]
    rows = ["Gate-11", "Gate-13", "Gate-17", "Gate-19", "Gate-23", "Gate-29"]
    for c, label in enumerate([""] + cols):
        x = left + c * cell_w
        draw.rectangle((x, top, x + cell_w, top + cell_h), fill=(235, 238, 242), outline=(120, 120, 120))
        draw.text((x + cell_w / 2, top + cell_h / 2), label, anchor="mm", font=_font(17, True), fill=(35, 35, 35))
    target_rect = (0, 0, 0, 0)
    for r, rlabel in enumerate(rows):
        y = top + (r + 1) * cell_h
        draw.rectangle((left, y, left + cell_w, y + cell_h), fill=(235, 238, 242), outline=(120, 120, 120))
        draw.text((left + cell_w / 2, y + cell_h / 2), rlabel, anchor="mm", font=_font(16, True), fill=(35, 35, 35))
        for c, value in enumerate(table[r]):
            x = left + (c + 1) * cell_w
            fill = (255, 255, 255)
            if rlabel == row_label and cols[c] == col_label:
                fill = (255, 252, 220)
                target_rect = (x, y, x + cell_w, y + cell_h)
            draw.rectangle((x, y, x + cell_w, y + cell_h), fill=fill, outline=(150, 150, 150))
            draw.text((x + cell_w / 2, y + cell_h / 2), value, anchor="mm", font=_font(20), fill=(10, 10, 10))
    draw.text((left, height - 90), "Rows and columns repeat across sheets; read the intersecting cell only.", font=_font(15), fill=(70, 70, 70))
    img.save(out)
    _mask((width, height), target_rect, mask_path)


def generate_doc_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    img_dir, mask_dir = out_dir / "images", out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    rows = ["Gate-11", "Gate-13", "Gate-17", "Gate-19", "Gate-23", "Gate-29"]
    cols = ["A1", "B2", "C3", "D4", "E5", "F6"]
    out_rows = []
    for i in range(n):
        table_a = [["".join(rng.choice(chars) for _ in range(3)) for _ in cols] for _ in rows]
        row_label, col_label = rng.choice(rows), rng.choice(cols)
        r_idx, c_idx = rows.index(row_label), cols.index(col_label)
        table_b = [list(row) for row in table_a]
        replacement = table_a[r_idx][c_idx]
        while replacement == table_a[r_idx][c_idx]:
            replacement = "".join(rng.choice(chars) for _ in range(3))
        table_b[r_idx][c_idx] = replacement
        pair_id = "v01_doc_" + stable_id(seed, i, table_a, table_b, row_label, col_label)
        image_a, image_b = img_dir / f"{pair_id}_a.png", img_dir / f"{pair_id}_b.png"
        mask_a, mask_b = mask_dir / f"{pair_id}_a_mask.png", mask_dir / f"{pair_id}_b_mask.png"
        _doc_image(table_a, row_label, col_label, image_a, mask_a)
        _doc_image(table_b, row_label, col_label, image_b, mask_b)
        out_rows.append(
            _save_pair(
                pair_id=pair_id,
                image_a=image_a,
                image_b=image_b,
                mask_a=mask_a,
                mask_b=mask_b,
                question=f"What is the 3-character code at row {row_label} and column {col_label}?",
                answer_a=table_a[r_idx][c_idx],
                answer_b=table_b[r_idx][c_idx],
                category="document_table_lookup",
                template_id="dense_table_code_v01",
                provenance={"generator": "src.fliptrack.build_v01", "seed": seed, "index": i, "family": "doc"},
                verifier_results={"exact_by_construction": True, "row": row_label, "column": col_label},
            )
        )
    return out_rows


def _geometry_image(grid: list[list[str]], row_name: str, col_num: int, out: Path, mask_path: Path) -> None:
    width, height = 760, 620
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((width // 2, 42), "Inspection Grid", anchor="mm", font=_font(25, True), fill=(20, 20, 20))
    left, top, cell = 110, 100, 72
    row_names = ["A", "B", "C", "D", "E", "F"]
    for c in range(1, 7):
        draw.text((left + (c - 0.5) * cell, top - 26), str(c), anchor="mm", font=_font(18, True), fill=(40, 40, 40))
    target_rect = (0, 0, 0, 0)
    colors = {"plus": (207, 70, 70), "minus": (50, 105, 190), "star": (58, 145, 92), "dot": (130, 80, 165)}
    for r, rn in enumerate(row_names):
        draw.text((left - 30, top + (r + 0.5) * cell), rn, anchor="mm", font=_font(18, True), fill=(40, 40, 40))
        for c in range(6):
            x0, y0 = left + c * cell, top + r * cell
            rect = (x0, y0, x0 + cell, y0 + cell)
            fill = (252, 252, 252) if (r + c) % 2 == 0 else (245, 247, 250)
            if rn == row_name and c + 1 == col_num:
                fill = (255, 252, 222)
                target_rect = rect
            draw.rectangle(rect, fill=fill, outline=(150, 150, 150), width=1)
            sym = grid[r][c]
            cx, cy = x0 + cell // 2, y0 + cell // 2
            if sym == "plus":
                draw.line((cx - 15, cy, cx + 15, cy), fill=colors[sym], width=5)
                draw.line((cx, cy - 15, cx, cy + 15), fill=colors[sym], width=5)
            elif sym == "minus":
                draw.line((cx - 17, cy, cx + 17, cy), fill=colors[sym], width=6)
            elif sym == "star":
                draw.text((cx, cy), "*", anchor="mm", font=_font(38, True), fill=colors[sym])
            else:
                draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=colors[sym])
    draw.text((left, height - 70), "Answer only the symbol in the highlighted indexed cell.", font=_font(15), fill=(70, 70, 70))
    img.save(out)
    _mask((width, height), target_rect, mask_path)


def generate_geometry_pairs(out_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    img_dir, mask_dir = out_dir / "images", out_dir / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    row_names = ["A", "B", "C", "D", "E", "F"]
    symbols = ["plus", "minus", "star", "dot"]
    out_rows = []
    for i in range(n):
        grid_a = [[rng.choice(symbols) for _ in range(6)] for _ in range(6)]
        row_name, col_num = rng.choice(row_names), rng.randint(1, 6)
        r_idx, c_idx = row_names.index(row_name), col_num - 1
        grid_b = [list(row) for row in grid_a]
        choices = [s for s in symbols if s != grid_a[r_idx][c_idx]]
        grid_b[r_idx][c_idx] = rng.choice(choices)
        pair_id = "v01_geometry_" + stable_id(seed, i, grid_a, grid_b, row_name, col_num)
        image_a, image_b = img_dir / f"{pair_id}_a.png", img_dir / f"{pair_id}_b.png"
        mask_a, mask_b = mask_dir / f"{pair_id}_a_mask.png", mask_dir / f"{pair_id}_b_mask.png"
        _geometry_image(grid_a, row_name, col_num, image_a, mask_a)
        _geometry_image(grid_b, row_name, col_num, image_b, mask_b)
        out_rows.append(
            _save_pair(
                pair_id=pair_id,
                image_a=image_a,
                image_b=image_b,
                mask_a=mask_a,
                mask_b=mask_b,
                question=f"Which symbol is in row {row_name}, column {col_num}: plus, minus, star, or dot?",
                answer_a=grid_a[r_idx][c_idx],
                answer_b=grid_b[r_idx][c_idx],
                category="geometry_grid_lookup",
                template_id="symbol_grid_v01",
                provenance={"generator": "src.fliptrack.build_v01", "seed": seed, "index": i, "family": "geometry"},
                verifier_results={"exact_by_construction": True, "row": row_name, "column": col_num},
            )
        )
    return out_rows


def build(out_dir: str | Path, n_per_family: int, seed: int) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    rows: list[dict[str, Any]] = []
    rows.extend(generate_chart_pairs(out_dir / "chart", n_per_family, seed + 101))
    rows.extend(generate_doc_pairs(out_dir / "doc", n_per_family, seed + 202))
    rows.extend(generate_geometry_pairs(out_dir / "geometry", n_per_family, seed + 303))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/fliptrack_v01/renderable")
    parser.add_argument("--manifest", default="data/fliptrack_v01_manifest.jsonl")
    parser.add_argument("--n-per-family", type=int, default=100)
    parser.add_argument("--seed", type=int, default=101)
    args = parser.parse_args()
    rows = build(args.out_dir, args.n_per_family, args.seed)
    write_jsonl(args.manifest, rows)
    print(args.manifest)


if __name__ == "__main__":
    main()
