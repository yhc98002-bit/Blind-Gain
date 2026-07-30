#!/usr/bin/env python3
"""Derive an eval-harness-schema manifest from the frozen M7 held-out split.

WHY THIS EXISTS
---------------
data/virl39k_m7_heldout_v3.jsonl is written by scripts/build_m7_split_manifest_v3.py
in the *training* schema ("blind-gains.virl39k-filtered-training.v1"), where
`images` is a list of path STRINGS and the per-image digests live in
`metadata.image_sha256`.

The blind-solvability eval harness requires the *blind-sample* schema, where
`images` is a list of {"path", "sha256"} mappings:
  - src/eval/conditioned_inputs.py::build_conditioned_messages reads
    image["path"] (real/gray/noise) and image["sha256"] (caption);
  - scripts/run_blind_solvability_v2.py writes
    "image_sha256": [image["sha256"] for image in row.get("images", [])]
    for EVERY condition, including "none".

Feeding the training-schema file straight to the harness raises
`TypeError: string indices must be integers`.

This script performs a lossless, mechanical re-shape: every field is carried
through byte-for-byte except `images` (re-shaped) and `schema_version`. Row
order, row_index, qid, problem, answer and metadata are untouched, so any join
back to the frozen held-out set on qid or row_index is exact.

Every image digest is re-verified against the bytes on disk before it is
written, so the emitted sha256 values are genuine file digests (this is what the
caption store is keyed on).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

SOURCE_SCHEMA = "blind-gains.virl39k-filtered-training.v1"
EVAL_SCHEMA = "blind-gains.virl39k-m7-heldout-eval.v1"
SPEC_SCHEMA = "blind-gains.virl39k-m7-heldout-sample.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(path: Path) -> str:
    return sha256_file(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/virl39k_m7_heldout_v3.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/virl39k_m7_heldout_v3_eval.jsonl"))
    parser.add_argument("--spec", type=Path, default=Path("reports/virl39k_m7_heldout_v3_sample.json"))
    parser.add_argument("--expected-source-sha256", default=None)
    args = parser.parse_args()

    source_sha = sha256_bytes(args.source)
    if args.expected_source_sha256 and source_sha != args.expected_source_sha256:
        raise SystemExit(
            f"source manifest sha256 mismatch: expected {args.expected_source_sha256}, found {source_sha}"
        )

    rows = []
    with args.source.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if not rows:
        raise SystemExit("source manifest is empty")

    split_counts: collections.Counter[str] = collections.Counter()
    image_count_counts: collections.Counter[int] = collections.Counter()
    answer_type_counts: collections.Counter[str] = collections.Counter()
    category_counts: collections.Counter[str] = collections.Counter()
    source_counts: collections.Counter[str] = collections.Counter()
    unique_images: set[str] = set()
    image_references = 0
    verified_digests = 0

    out_rows = []
    for row in rows:
        if row.get("schema_version") != SOURCE_SCHEMA:
            raise SystemExit(f"unexpected source schema_version: {row.get('schema_version')!r}")
        paths = list(row.get("images", []))
        digests = list(row.get("metadata", {}).get("image_sha256", []))
        if len(paths) != len(digests):
            raise SystemExit(f"row {row['row_index']}: {len(paths)} paths vs {len(digests)} digests")
        images = []
        for path_value, recorded in zip(paths, digests):
            path = Path(str(path_value))
            if not path.exists():
                raise SystemExit(f"row {row['row_index']}: image is absent on disk: {path}")
            observed = sha256_file(path)
            if observed != recorded:
                raise SystemExit(
                    f"row {row['row_index']}: image digest mismatch for {path}: "
                    f"recorded {recorded}, on disk {observed}"
                )
            verified_digests += 1
            images.append({"path": str(path_value), "sha256": str(recorded)})
            unique_images.add(str(recorded))
            image_references += 1

        new_row = dict(row)
        new_row["images"] = images
        new_row["schema_version"] = EVAL_SCHEMA
        out_rows.append(new_row)

        split_counts[str(row["split"])] += 1
        image_count_counts[len(images)] += 1
        metadata = row.get("metadata", {})
        answer_type_counts[str(metadata.get("answer_type"))] += 1
        category_counts[str(metadata.get("category"))] += 1
        source_counts[str(metadata.get("source"))] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    output_sha = sha256_bytes(args.output)
    max_images = max(image_count_counts)

    spec = {
        "schema_version": SPEC_SCHEMA,
        "purpose": (
            "Sample spec for the M7 step-0 base evaluation over the frozen held-out split. "
            "Consumed by scripts/launch_virl39k_blind_v1_condition.sh via VIRL_SAMPLE_SPEC "
            "(.sample_size and .max_images_per_item)."
        ),
        "sample_size": len(out_rows),
        "max_images_per_item": max_images,
        "image_references": image_references,
        "unique_images": len(unique_images),
        "split_counts": dict(sorted(split_counts.items())),
        "image_count_counts": {str(k): v for k, v in sorted(image_count_counts.items())},
        "answer_type_counts": dict(sorted(answer_type_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "eval_manifest": str(args.output),
        "eval_manifest_sha256": output_sha,
        "eval_manifest_schema_version": EVAL_SCHEMA,
        "source_manifest": str(args.source),
        "source_manifest_sha256": source_sha,
        "source_manifest_schema_version": SOURCE_SCHEMA,
        "derivation": (
            "Lossless re-shape of `images` from list[str] to list[{path, sha256}] using "
            "metadata.image_sha256; every digest re-verified against the bytes on disk. "
            "All other fields, and row order, are unchanged."
        ),
        "verified_image_digests": verified_digests,
    }
    args.spec.parent.mkdir(parents=True, exist_ok=True)
    args.spec.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "rows": len(out_rows),
        "source_manifest_sha256": source_sha,
        "eval_manifest_sha256": output_sha,
        "max_images_per_item": max_images,
        "unique_images": len(unique_images),
        "verified_image_digests": verified_digests,
        "split_counts": dict(split_counts),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
