#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


OPTION_MARKER = re.compile(r"(?:^|,\s+)([A-D]):\s*")
PAREN_OPTION_MARKER = re.compile(r"(?m)^\(([A-D])\)\s*")


def allow_large_csv_fields() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_question_options(question: str) -> tuple[str, dict[str, str]]:
    if "\nOptions:" in question:
        stem, option_text = question.rsplit("\nOptions:", 1)
        option_text = option_text.strip()
        matches = list(OPTION_MARKER.finditer(option_text))
    else:
        matches = list(PAREN_OPTION_MARKER.finditer(question))
        if not matches:
            raise ValueError("question has no recognized option block")
        stem = question[: matches[0].start()].rstrip()
        stem = re.sub(r"\nChoices:\s*$", "", stem).rstrip()
        option_text = question
    labels = [match.group(1) for match in matches]
    expected = list("ABCD"[: len(labels)])
    if len(labels) < 2 or labels != expected:
        raise ValueError(f"expected contiguous options starting at A, found {labels}")
    options = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(option_text)
        value = option_text[match.end() : end].strip().rstrip(",").strip()
        if not value:
            raise ValueError(f"empty option {match.group(1)}")
        options[match.group(1)] = value
    return stem.strip(), options


def normalize_tsv(input_path: Path, output_path: Path, metadata_path: Path) -> dict[str, Any]:
    if output_path.exists() or metadata_path.exists():
        raise FileExistsError(f"refusing to overwrite MMStar adapter output: {output_path} / {metadata_path}")
    allow_large_csv_fields()
    expected = {"index", "question", "answer", "category", "l2_category", "bench", "image"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    rows = 0
    option_counts: Counter[int] = Counter()
    try:
        with input_path.open("r", encoding="utf-8", newline="") as source, temporary.open(
            "w", encoding="utf-8", newline=""
        ) as target:
            reader = csv.DictReader(source, delimiter="\t")
            missing = expected - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"MMStar source missing columns: {sorted(missing)}")
            fields = ["index", "question", "answer", "category", "l2_category", "bench", "A", "B", "C", "D", "image"]
            writer = csv.DictWriter(target, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for row_number, row in enumerate(reader, start=1):
                try:
                    stem, options = parse_question_options(str(row["question"]))
                except ValueError as error:
                    raise ValueError(f"row {row_number}: {error}") from error
                answer = str(row["answer"]).strip()
                if answer not in options:
                    raise ValueError(f"row {row_number}: answer is not among parsed options: {answer!r}")
                writer.writerow(
                    {
                        "index": row["index"],
                        "question": stem,
                        "answer": answer,
                        "category": row["category"],
                        "l2_category": row["l2_category"],
                        "bench": row["bench"],
                        **options,
                        "image": row["image"],
                    }
                )
                rows += 1
                option_counts[len(options)] += 1
        if rows != 1500:
            raise ValueError(f"expected 1500 MMStar rows, found {rows}")
        os.replace(temporary, output_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    payload = {
        "status": "pass",
        "source": str(input_path),
        "source_sha256": sha256_file(input_path),
        "output": str(output_path),
        "output_sha256": sha256_file(output_path),
        "n_rows": rows,
        "option_count_distribution": {str(key): value for key, value in sorted(option_counts.items())},
        "transform": "split final question Options block into A-D columns; preserve image bytes and labels",
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--expected-source-sha256", required=True)
    args = parser.parse_args()
    actual = sha256_file(args.input)
    if actual != args.expected_source_sha256:
        raise ValueError(f"MMStar source hash mismatch: expected {args.expected_source_sha256}, found {actual}")
    print(json.dumps(normalize_tsv(args.input, args.output, args.metadata), sort_keys=True))


if __name__ == "__main__":
    main()
