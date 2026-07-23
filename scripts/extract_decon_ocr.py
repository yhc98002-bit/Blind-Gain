#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from rapidocr_onnxruntime import RapidOCR

from src.decon.ocr_text import normalize_ocr_text


def _reading_key(line: list[Any]) -> tuple[float, float]:
    box = line[0]
    return (min(float(point[1]) for point in box), min(float(point[0]) for point in box))


def _entities(paths: list[Path]) -> list[tuple[str, str]]:
    by_hash: dict[str, str] = {}
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("image_applicable", True):
                    by_hash.setdefault(str(row["image_sha256"]), str(row["image_path"]))
    return sorted(by_hash.items())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--ocr-config", type=Path, default=None)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite OCR output: {args.output}")
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard specification")

    entities = _entities(args.inputs)
    selected = entities[args.shard_index :: args.num_shards]
    engine = RapidOCR(config_path=str(args.ocr_config)) if args.ocr_config else RapidOCR()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with args.output.open("w", encoding="utf-8") as handle:
        for position, (digest, image_path) in enumerate(selected, start=1):
            row: dict[str, Any] = {
                "schema_version": "blind-gains.decon-ocr.v1",
                "image_sha256": digest,
                "image_path": image_path,
                "text": "",
                "normalized_text": "",
                "line_count": 0,
                "mean_confidence": None,
                "elapsed_seconds": None,
                "error": None,
            }
            item_start = time.monotonic()
            try:
                result, _ = engine(image_path)
                lines = sorted(result or [], key=_reading_key)
                texts = [str(line[1]).strip() for line in lines if str(line[1]).strip()]
                scores = [float(line[2]) for line in lines if str(line[1]).strip()]
                row.update(
                    {
                        "text": "\n".join(texts),
                        "normalized_text": normalize_ocr_text(" ".join(texts)),
                        "line_count": len(texts),
                        "mean_confidence": sum(scores) / len(scores) if scores else None,
                    }
                )
            except Exception as exc:  # preserve per-image failures for the coverage audit
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["elapsed_seconds"] = time.monotonic() - item_start
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
            if position % 100 == 0:
                print(
                    json.dumps(
                        {
                            "processed": position,
                            "selected": len(selected),
                            "elapsed_seconds": time.monotonic() - started,
                            "shard_index": args.shard_index,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    main()
