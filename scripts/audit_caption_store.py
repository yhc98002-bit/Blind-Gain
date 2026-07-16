#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

from src.captioning.store import merge_caption_rows, sha256_file, validate_caption_row


def expected_hashes_from_manifest(path: Path) -> set[str]:
    expected: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            images = row.get("images")
            hash_field = "sha256"
            if not isinstance(images, list):
                images = row.get("members")
                hash_field = "image_sha256"
            if not isinstance(images, list):
                raise ValueError(f"manifest line {line_number} has no images or members list")
            if images and all(isinstance(image, str) for image in images):
                metadata = row.get("metadata")
                digests = metadata.get("image_sha256") if isinstance(metadata, dict) else None
                if not isinstance(digests, list) or len(digests) != len(images):
                    raise ValueError(
                        f"manifest line {line_number} string image paths lack one SHA256 per image"
                    )
            else:
                digests = [
                    image.get(hash_field, "") if isinstance(image, dict) else ""
                    for image in images
                ]
            for digest_value in digests:
                digest = str(digest_value)
                if not digest:
                    raise ValueError(f"manifest line {line_number} has an image without SHA256")
                expected.add(digest)
    if not expected:
        raise ValueError("manifest contains no image hashes")
    return expected


def expected_hashes_from_manifests(
    paths: list[Path],
) -> tuple[set[str], dict[str, list[str]]]:
    combined: set[str] = set()
    owners: dict[str, list[str]] = {}
    for path in paths:
        hashes = expected_hashes_from_manifest(path)
        for digest in hashes:
            owners.setdefault(digest, []).append(str(path))
        combined.update(hashes)
    overlaps = {
        digest: sources for digest, sources in owners.items() if len(sources) > 1
    }
    return combined, overlaps


def audit_raw_caption_rows(
    shard_paths: list[Path],
    *,
    expected_model: str | None,
    expected_revision: str | None,
    expected_tp: int | None,
) -> dict[str, object]:
    row_count = 0
    hash_counts: dict[str, int] = {}
    model_paths: set[str] = set()
    revisions: set[str] = set()
    tp_widths: set[int] = set()
    image_hash_mismatches: list[str] = []
    for shard in shard_paths:
        for line_number, line in enumerate(
            shard.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                raise ValueError(f"blank caption row at {shard}:{line_number}")
            row = json.loads(line)
            validate_caption_row(row)
            row_count += 1
            digest = str(row["image_sha256"])
            hash_counts[digest] = hash_counts.get(digest, 0) + 1
            model_paths.add(str(row.get("caption_model_path", "")))
            revisions.add(str(row.get("caption_model_revision", "")))
            try:
                tp_widths.add(int(row.get("tensor_parallel_width")))
            except (TypeError, ValueError):
                tp_widths.add(-1)
            image_path = Path(str(row.get("image_path", "")))
            if not image_path.is_file() or sha256_file(image_path) != digest:
                image_hash_mismatches.append(digest)
    duplicate_hashes = sorted(
        digest for digest, count in hash_counts.items() if count != 1
    )
    checks = {
        "one_row_per_image_hash": not duplicate_hashes,
        "caption_image_files_match_hashes": not image_hash_mismatches,
        "expected_model_exact": expected_model is None
        or model_paths == {expected_model},
        "expected_revision_exact": expected_revision is None
        or revisions == {expected_revision},
        "expected_tensor_parallel_width_exact": expected_tp is None
        or tp_widths == {expected_tp},
    }
    return {
        "checks": checks,
        "row_count": row_count,
        "unique_image_hashes": len(hash_counts),
        "duplicate_image_hashes": duplicate_hashes,
        "image_hash_mismatch_count": len(image_hash_mismatches),
        "model_paths": sorted(model_paths),
        "model_revisions": sorted(revisions),
        "tensor_parallel_widths": sorted(tp_widths),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--shards", type=Path, nargs="+", required=True)
    parser.add_argument("--expected-model")
    parser.add_argument("--expected-revision")
    parser.add_argument("--expected-tp", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite caption audit: {args.output}")

    expected, overlaps = expected_hashes_from_manifests(args.manifest)
    rows, contract = merge_caption_rows(args.shards, expected)
    raw_audit = audit_raw_caption_rows(
        args.shards,
        expected_model=args.expected_model,
        expected_revision=args.expected_revision,
        expected_tp=args.expected_tp,
    )
    checks = {
        "schema_prompt_decoding_budget_valid": True,
        "source_manifests_disjoint": not overlaps,
        "single_caption_contract": raw_audit["row_count"] == len(rows)
        and raw_audit["unique_image_hashes"] == len(rows)
        and raw_audit["checks"]["one_row_per_image_hash"],
        "exact_manifest_image_coverage": contract["coverage_complete"]
        and len(rows) == len(expected),
        **raw_audit["checks"],
    }
    payload = {
        "schema_version": "blind-gains.caption-store-audit.v2",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "audited_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": str(args.manifest[0]) if len(args.manifest) == 1 else None,
        "manifest_sha256": sha256_file(args.manifest[0])
        if len(args.manifest) == 1
        else None,
        "manifests": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in args.manifest
        ],
        "cross_manifest_overlap_count": len(overlaps),
        "cross_manifest_overlaps": overlaps,
        "shards": [
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in args.shards
        ],
        "contract": contract,
        "raw_row_audit": raw_audit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps({"status": payload["status"], "n_images": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
