#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def select_templates(config_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    if output_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite selection output: {output_path} / {summary_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    selected: list[dict[str, Any]] = []
    source_records = []
    expected_by_template: Counter[str] = Counter()
    for source in config["sources"]:
        path = Path(source["path"])
        actual_hash = sha256_file(path)
        if actual_hash != source["sha256"]:
            raise ValueError(f"source hash mismatch for {path}: expected {source['sha256']}, found {actual_hash}")
        rows = _read_jsonl(path)
        templates = {str(name): int(count) for name, count in source["templates"].items()}
        source_selected = [row for row in rows if str(row.get("template_id")) in templates]
        counts = Counter(str(row.get("template_id")) for row in source_selected)
        if counts != Counter(templates):
            raise ValueError(f"template counts mismatch for {path}: expected {templates}, found {dict(counts)}")
        selected.extend(source_selected)
        expected_by_template.update(templates)
        source_records.append(
            {
                "path": str(path),
                "sha256": actual_hash,
                "selected_templates": dict(sorted(templates.items())),
            }
        )

    expected_total = int(config["expected_total_pairs"])
    if len(selected) != expected_total:
        raise ValueError(f"expected {expected_total} selected pairs, found {len(selected)}")
    pair_ids = [str(row["pair_id"]) for row in selected]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("duplicate pair ids across selected source manifests")

    selected.sort(key=lambda row: (str(row["template_id"]), str(row["pair_id"])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    summary = {
        "schema_version": config["schema_version"],
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "output_path": str(output_path),
        "output_sha256": sha256_file(output_path),
        "n_pairs": len(selected),
        "template_counts": dict(sorted(expected_by_template.items())),
        "sources": source_records,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    summary = select_templates(Path(args.config), Path(args.output), Path(args.summary))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
