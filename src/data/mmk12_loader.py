from __future__ import annotations

import argparse
import io
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator

import pyarrow.parquet as pq
from PIL import Image, ImageDraw, ImageFont

from src.data.virl39k_loader import answer_type


REQUIRED_COLUMNS = {"id", "question", "answer", "subject", "image"}


def discover_parquet(parquet_dir: str | Path) -> list[Path]:
    paths = sorted(Path(parquet_dir).glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no MMK12 parquet files under {parquet_dir}")
    return paths


def _split_name(path: Path) -> str:
    return "test" if path.name.startswith("test-") else "train"


def iter_examples(parquet_paths: Iterable[str | Path], batch_size: int = 64) -> Iterator[dict[str, Any]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for parquet_path in (Path(path) for path in parquet_paths):
        parquet = pq.ParquetFile(parquet_path)
        missing = REQUIRED_COLUMNS - set(parquet.schema_arrow.names)
        if missing:
            raise ValueError(f"MMK12 parquet missing columns in {parquet_path}: {sorted(missing)}")
        for batch in parquet.iter_batches(batch_size=batch_size, columns=sorted(REQUIRED_COLUMNS)):
            for raw in batch.to_pylist():
                image = raw.get("image") or {}
                yield {
                    "id": str(raw["id"]),
                    "question": str(raw["question"]),
                    "answer": str(raw["answer"]),
                    "subject": str(raw["subject"]),
                    "split": _split_name(parquet_path),
                    "image_bytes": image.get("bytes"),
                    "image_path": image.get("path"),
                }


def _decode_image(example: dict[str, Any]) -> Image.Image:
    payload = example.get("image_bytes")
    if payload:
        return Image.open(io.BytesIO(payload))
    image_path = example.get("image_path")
    if image_path:
        return Image.open(image_path)
    raise FileNotFoundError("example has neither embedded image bytes nor an image path")


def scan_dataset(
    examples: Iterable[dict[str, Any]], seed: int = 20260710, sample_size: int = 16
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if sample_size < 0:
        raise ValueError("sample_size must be non-negative")
    rng = random.Random(seed)
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    subjects: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    answer_types: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    formats: Counter[str] = Counter()
    missing_examples: list[str] = []
    embedded = 0
    path_backed = 0
    readable = 0

    for index, example in enumerate(examples):
        example_id = example["id"]
        if example_id in seen:
            raise ValueError(f"duplicate MMK12 id: {example_id}")
        seen.add(example_id)
        subjects[example["subject"]] += 1
        splits[example["split"]] += 1
        answer_types[answer_type(example["answer"])] += 1
        embedded += int(bool(example.get("image_bytes")))
        path_backed += int(bool(example.get("image_path")))

        try:
            with _decode_image(example) as image:
                image.load()
                dimensions[f"{image.width}x{image.height}"] += 1
                formats[str(image.format or "unknown").upper()] += 1
                readable += 1
        except (OSError, ValueError, FileNotFoundError):
            if len(missing_examples) < 20:
                missing_examples.append(example_id)

        if sample_size:
            retained = {
                key: example[key]
                for key in ("id", "question", "answer", "subject", "split", "image_bytes", "image_path")
            }
            if len(selected) < sample_size:
                selected.append(retained)
            else:
                replacement = rng.randint(0, index)
                if replacement < sample_size:
                    selected[replacement] = retained

    total = len(seen)
    missing_count = total - readable
    return (
        {
            "n_rows": total,
            "n_unique_ids": len(seen),
            "n_readable_images": readable,
            "n_missing_or_unreadable_images": missing_count,
            "missing_image_rate": missing_count / total if total else 0.0,
            "missing_examples": missing_examples,
            "n_embedded_images": embedded,
            "n_path_backed_images": path_backed,
            "split_counts": dict(sorted(splits.items())),
            "subject_counts": dict(sorted(subjects.items())),
            "answer_type_counts": dict(sorted(answer_types.items())),
            "image_format_counts": dict(sorted(formats.items())),
            "n_unique_image_dimensions": len(dimensions),
            "top_image_dimension_counts": dict(dimensions.most_common(100)),
        },
        selected,
    )


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def write_contact_sheet(examples: list[dict[str, Any]], output: str | Path) -> None:
    tile_width, tile_height, columns = 420, 300, 4
    row_count = max(1, (len(examples) + columns - 1) // columns)
    sheet = Image.new("RGB", (tile_width * columns, tile_height * row_count), "white")
    draw = ImageDraw.Draw(sheet)
    for index, example in enumerate(examples):
        x0 = (index % columns) * tile_width
        y0 = (index // columns) * tile_height
        try:
            with _decode_image(example) as opened:
                image = opened.convert("RGB")
                image.thumbnail((390, 205), Image.Resampling.LANCZOS)
            sheet.paste(image, (x0 + (tile_width - image.width) // 2, y0 + 8))
        except (OSError, ValueError, FileNotFoundError):
            draw.rectangle((x0 + 10, y0 + 10, x0 + 410, y0 + 210), outline="red", width=2)
        question = example["question"].replace("<image>", "").replace("\n", " ").strip()
        if len(question) > 75:
            question = question[:72] + "..."
        draw.text((x0 + 10, y0 + 220), f"{example['split']} | {example['subject']}", font=_font(11), fill=(60, 60, 60))
        draw.text((x0 + 10, y0 + 240), question, font=_font(10), fill=(20, 20, 20))
        draw.text((x0 + 10, y0 + 274), str(example["answer"])[:65], font=_font(11), fill=(20, 70, 130))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=False, compress_level=9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet-dir", required=True)
    parser.add_argument("--stats-output", required=True)
    parser.add_argument("--contact-sheet", required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    paths = discover_parquet(args.parquet_dir)
    stats, selected = scan_dataset(iter_examples(paths, batch_size=args.batch_size))
    stats["parquet_files"] = [str(path) for path in paths]
    output = Path(args.stats_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_contact_sheet(selected, args.contact_sheet)
    print(json.dumps({key: stats[key] for key in ("n_rows", "n_readable_images", "missing_image_rate")}))


if __name__ == "__main__":
    main()
