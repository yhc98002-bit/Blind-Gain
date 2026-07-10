#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from src.captioning.qa_pairs import build_caption_qa_rows


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _publish(
    rows: list[dict[str, Any]], summary: dict[str, Any], output: Path, summary_path: Path
) -> None:
    for final_path in (output, summary_path):
        final_path.parent.mkdir(parents=True, exist_ok=True)
        if final_path.exists():
            raise FileExistsError(f"refusing to overwrite caption-QA artifact: {final_path}")
    output_partial = Path(f"{output}.partial")
    summary_partial = Path(f"{summary_path}.partial")
    for partial_path in (output_partial, summary_partial):
        if partial_path.exists():
            raise FileExistsError(f"stale caption-QA partial requires inspection: {partial_path}")

    published_output = False
    try:
        with output_partial.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
        summary_partial.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(output_partial, output)
        published_output = True
        os.replace(summary_partial, summary_path)
    except BaseException:
        output_partial.unlink(missing_ok=True)
        summary_partial.unlink(missing_ok=True)
        if published_output:
            output.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--caption-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    rows = build_caption_qa_rows(
        _read_jsonl(args.release_manifest),
        _read_jsonl(args.key_file),
        _read_jsonl(args.caption_store),
        args.release_manifest.parent,
    )
    template_counts: dict[str, int] = {}
    for row in rows:
        template = str(row["template_id"])
        template_counts[template] = template_counts.get(template, 0) + 1
    summary = {
        "schema_version": "blind-gains.fliptrack-caption-qa-input-summary.v1",
        "n_pairs": len(rows),
        "n_images": len(rows) * 2,
        "template_counts": template_counts,
        "release_manifest": str(args.release_manifest),
        "key_file": str(args.key_file),
        "caption_store": str(args.caption_store),
    }
    _publish(rows, summary, args.output, args.summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
