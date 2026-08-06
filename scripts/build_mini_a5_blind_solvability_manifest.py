#!/usr/bin/env python3
"""Convert the frozen Mini-A5 training corpus into the geometry-manifest
schema consumed by the registered blind-solvability harness.

Registered by docs/registered_mini_a5_gate1_completion_v1.md section 2 R2
(prework ledger T2). data/mini_a5_train_v1/train.jsonl (6,000 member rows)
is converted row-for-row into the schema load_geometry_rows /
scripts/run_blind_solvability.py consume:

    {"split": "train", "row_index": <0..5999 in frozen order>,
     "qid": "<pair_group_uid>:<pair_member>", "problem": ..., "answer": ...,
     "images": [{"path": ..., "sha256": <recomputed per-image sha256>}],
     "metadata": {...provenance...}, "schema_version": ...}

Output (refuses to overwrite):
- data/mini_a5_train_blind_solvability_manifest_v1.jsonl
- reports/mini_a5_blind_solvability_manifest_build_v1.json (byte-correspondence audit)

The byte-correspondence audit checks every manifest row against the frozen
train.jsonl row at the same index (problem/answer/image path identical), the
per-image sha256 against BOTH a fresh hash of the image file and the frozen
pairs.jsonl record for the right member, row_index contiguity, qid
uniqueness, and the single-split invariant.

Adversarial fixture (I10): tests/test_build_mini_a5_blind_solvability_manifest_fixture.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "blind-gains.mini-a5-blind-solvability-manifest.v1"
SPLIT = "train"
PINNED_SOURCE_HASHES = {
    "train.jsonl": "07d785ee6ae4a3b5325e12595f7830c5924e31c49565554f1e88b2abffc5fa5c",
    "pairs.jsonl": "c592d8560cf3f5544fea36a12b3b52642d0faf0056c4ef9fddc0dde1f75f34bd",
}
DEFAULT_SOURCE_DIR = Path("data/mini_a5_train_v1")
DEFAULT_OUTPUT = Path("data/mini_a5_train_blind_solvability_manifest_v1.jsonl")
DEFAULT_REPORT = Path("reports/mini_a5_blind_solvability_manifest_build_v1.json")
EXPECTED_ROWS = 6000


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def convert_rows(
    source_rows: list[dict[str, Any]], corpus_root: Path
) -> list[dict[str, Any]]:
    """Deterministic frozen-order conversion; hashes every image file."""
    manifest_rows = []
    for row_index, row in enumerate(source_rows):
        images = []
        for path in row["images"]:
            file_path = corpus_root / str(path)
            if not file_path.is_file():
                raise FileNotFoundError(f"row {row_index}: image missing: {path}")
            images.append({"path": str(path), "sha256": sha256_file(file_path)})
        manifest_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "split": SPLIT,
                "row_index": row_index,
                "qid": f"{row['pair_group_uid']}:{row['pair_member']}",
                "problem": str(row["problem"]),
                "answer": str(row["answer"]),
                "images": images,
                "metadata": {
                    "pair_group_uid": str(row["pair_group_uid"]),
                    "pair_member": str(row["pair_member"]),
                    "template_id": str(row["template_id"]),
                    "category": str(row["category"]),
                    "source_corpus": "data/mini_a5_train_v1/train.jsonl",
                },
            }
        )
    return manifest_rows


def audit_manifest(
    source_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    pairs_rows: list[dict[str, Any]],
    corpus_root: Path,
    *,
    verify_image_hashes: bool = True,
) -> dict[str, Any]:
    """Byte-correspondence audit: manifest row i <-> frozen train.jsonl row i."""
    errors: list[str] = []
    checks: dict[str, bool] = {}

    pair_sha = {}
    for pair in pairs_rows:
        uid = str(pair["pair_group_uid"])
        pair_sha[(uid, "a")] = (str(pair["image_a_path"]), str(pair["image_a_sha256"]))
        pair_sha[(uid, "b")] = (str(pair["image_b_path"]), str(pair["image_b_sha256"]))

    checks["row_count_matches_source"] = len(manifest_rows) == len(source_rows)
    if not checks["row_count_matches_source"]:
        errors.append(
            f"manifest has {len(manifest_rows)} rows, source has {len(source_rows)}"
        )

    index_ok = all(
        int(row.get("row_index", -1)) == index for index, row in enumerate(manifest_rows)
    )
    checks["row_index_contiguous_in_frozen_order"] = index_ok
    if not index_ok:
        errors.append("row_index is not the contiguous frozen order")

    checks["single_train_split"] = all(
        str(row.get("split")) == SPLIT for row in manifest_rows
    )
    if not checks["single_train_split"]:
        errors.append("at least one row is not in the train split")

    qids = [str(row.get("qid")) for row in manifest_rows]
    checks["qid_unique_and_derived"] = len(set(qids)) == len(qids)
    if not checks["qid_unique_and_derived"]:
        errors.append("qids are not unique")

    correspondence_ok = True
    for index in range(min(len(manifest_rows), len(source_rows))):
        manifest_row, source_row = manifest_rows[index], source_rows[index]
        expected_qid = f"{source_row['pair_group_uid']}:{source_row['pair_member']}"
        if (
            str(manifest_row.get("problem")) != str(source_row["problem"])
            or str(manifest_row.get("answer")) != str(source_row["answer"])
            or str(manifest_row.get("qid")) != expected_qid
        ):
            correspondence_ok = False
            errors.append(f"row {index}: problem/answer/qid deviates from frozen row")
            break
        manifest_paths = [str(image.get("path")) for image in manifest_row.get("images", [])]
        if manifest_paths != [str(path) for path in source_row["images"]]:
            correspondence_ok = False
            errors.append(f"row {index}: image paths deviate from frozen row")
            break
    checks["byte_correspondence_with_frozen_rows"] = correspondence_ok

    if verify_image_hashes:
        hash_ok = True
        for index in range(min(len(manifest_rows), len(source_rows))):
            manifest_row, source_row = manifest_rows[index], source_rows[index]
            key = (str(source_row["pair_group_uid"]), str(source_row["pair_member"]))
            expected = pair_sha.get(key)
            for image in manifest_row.get("images", []):
                path, recorded = str(image.get("path")), str(image.get("sha256"))
                file_path = corpus_root / path
                if not file_path.is_file():
                    hash_ok = False
                    errors.append(f"row {index}: image file missing: {path}")
                    break
                fresh = sha256_file(file_path)
                if recorded != fresh:
                    hash_ok = False
                    errors.append(f"row {index}: manifest sha256 != file bytes for {path}")
                    break
                if expected is None or path != expected[0] or recorded != expected[1]:
                    hash_ok = False
                    errors.append(
                        f"row {index}: sha256/path does not match the frozen pairs.jsonl "
                        f"record for member {key[1]}"
                    )
                    break
            if not hash_ok:
                break
        checks["image_sha256_matches_file_and_pairs_record"] = hash_ok
    else:
        checks["image_sha256_matches_file_and_pairs_record"] = False
        errors.append("image hash verification skipped")

    checks["status_pass"] = all(checks.values())
    return {"checks": checks, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    source_dir = ROOT / args.source_dir
    output_path = ROOT / args.output
    report_path = ROOT / args.report
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing manifest: {output_path}")
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {report_path}")

    source_hashes = {
        name: sha256_file(source_dir / name) for name in PINNED_SOURCE_HASHES
    }
    for name, expected in PINNED_SOURCE_HASHES.items():
        if source_hashes[name] != expected:
            raise ValueError(
                f"frozen input {name} drifted: {source_hashes[name]} != registered {expected}"
            )

    source_rows = load_jsonl(source_dir / "train.jsonl")
    pairs_rows = load_jsonl(source_dir / "pairs.jsonl")
    if len(source_rows) != EXPECTED_ROWS:
        raise ValueError(f"frozen corpus has {len(source_rows)} rows, expected {EXPECTED_ROWS}")

    manifest_rows = convert_rows(source_rows, ROOT)
    audit = audit_manifest(source_rows, manifest_rows, pairs_rows, ROOT)
    if not audit["checks"]["status_pass"]:
        raise RuntimeError(f"manifest audit failed: {audit['errors'][:5]}")

    with output_path.open("w", encoding="utf-8") as handle:
        for row in manifest_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    report = {
        "schema_version": SCHEMA_VERSION + ".build-report",
        "registration": "docs/registered_mini_a5_gate1_completion_v1.md#2-R2",
        "builder": "scripts/build_mini_a5_blind_solvability_manifest.py",
        "source_dir": str(args.source_dir),
        "source_sha256": source_hashes,
        "output": str(args.output),
        "output_sha256": sha256_file(output_path),
        "rows": len(manifest_rows),
        "split": SPLIT,
        "byte_correspondence_audit": audit,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "rows": len(manifest_rows),
                "manifest_sha256": report["output_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
