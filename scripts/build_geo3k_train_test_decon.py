#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.decon.core import enrich_records, load_geometry3k_records, sha256_file, write_jsonl


def build_records(
    manifest: Path, train_output: Path, test_output: Path, summary_output: Path
) -> dict[str, object]:
    for output in (train_output, test_output, summary_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite decontamination artifact: {output}")
    train = enrich_records(load_geometry3k_records(manifest, split="train"))
    test = enrich_records(load_geometry3k_records(manifest, split="test"))
    if not train or not test:
        raise ValueError("Geometry3K train/test decontamination requires both nonempty splits")
    train_ids = {row["record_id"] for row in train}
    test_ids = {row["record_id"] for row in test}
    if train_ids & test_ids:
        raise ValueError("Geometry3K train and test record identities overlap")
    write_jsonl(train, train_output)
    write_jsonl(test, test_output)
    payload: dict[str, object] = {
        "schema_version": "blind-gains.geo3k-train-test-records.v1",
        "source_manifest": str(manifest),
        "source_manifest_sha256": sha256_file(manifest),
        "train_output": str(train_output),
        "train_sha256": sha256_file(train_output),
        "test_output": str(test_output),
        "test_sha256": sha256_file(test_output),
        "n_train_records": len(train),
        "n_test_records": len(test),
        "record_ids_disjoint": True,
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--train-output", type=Path, required=True)
    parser.add_argument("--test-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            build_records(args.manifest, args.train_output, args.test_output, args.summary_output),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
