from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "source_image_path",
    "edited_image_path",
    "question",
    "answer_a",
    "answer_b",
    "category",
    "provenance",
}


def validate_candidate(row: dict[str, Any]) -> list[str]:
    errors = []
    missing = REQUIRED_FIELDS - row.keys()
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    for key in ["source_image_path", "edited_image_path"]:
        if key in row and not Path(row[key]).exists():
            errors.append(f"{key} not found: {row[key]}")
    if row.get("answer_a") == row.get("answer_b"):
        errors.append("answers must differ")
    return errors


def audit_manifest(input_jsonl: str | Path, output_jsonl: str | Path) -> None:
    output_jsonl = Path(output_jsonl)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with Path(input_jsonl).open("r", encoding="utf-8") as src, output_jsonl.open("w", encoding="utf-8") as dst:
        for line in src:
            row = json.loads(line)
            row["pipeline_audit_errors"] = validate_candidate(row)
            row["pipeline_audit_pass"] = not row["pipeline_audit_errors"]
            dst.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-jsonl", required=True)
    args = parser.parse_args()
    audit_manifest(args.input_jsonl, args.output_jsonl)
    print(args.output_jsonl)


if __name__ == "__main__":
    main()

