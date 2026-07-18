#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.caption_image_store_vllm import discover_image_roots
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


def audit_caption_store(
    *,
    run_manifest_path: Path,
    caption_store_path: Path,
    input_dirs: list[Path],
) -> dict[str, Any]:
    manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    expected_items = discover_image_roots(input_dirs)
    expected_by_hash = {item["image_sha256"]: item for item in expected_items}

    raw_lines = caption_store_path.read_text(encoding="utf-8").splitlines()
    if any(not line.strip() for line in raw_lines):
        raise ValueError("caption store contains blank rows")
    rows = [json.loads(line) for line in raw_lines]
    found_by_hash: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("caption-store row is not an object")
        validate_caption_row(row)
        digest = str(row["image_sha256"])
        if digest in found_by_hash:
            raise ValueError(f"duplicate caption row for image hash {digest}")
        found_by_hash[digest] = row

    if set(found_by_hash) != set(expected_by_hash):
        missing = sorted(set(expected_by_hash) - set(found_by_hash))
        extra = sorted(set(found_by_hash) - set(expected_by_hash))
        raise ValueError(
            f"caption image coverage mismatch: missing={len(missing)} extra={len(extra)}"
        )

    source_roots_sha256 = hashlib.sha256(
        "\n".join(str(path) for path in input_dirs).encode("utf-8")
    ).hexdigest()
    for digest, expected in expected_by_hash.items():
        row = found_by_hash[digest]
        for key in ("image_path", "duplicate_paths"):
            if row.get(key) != expected[key]:
                raise ValueError(f"caption source mismatch for {digest}: {key}")
        source_path = Path(str(row["image_path"]))
        if not source_path.is_file() or sha256_file(source_path) != digest:
            raise ValueError(f"caption source bytes mismatch for {digest}")
        if row.get("source_roots_sha256") != source_roots_sha256:
            raise ValueError(f"source-root contract mismatch for {digest}")
        expected_contract = {
            "caption_model_path": manifest.get("model_id"),
            "caption_model_revision": manifest.get("model_revision"),
            "max_new_tokens": manifest.get("max_new_tokens"),
            "tensor_parallel_width": manifest.get("tensor_parallel_width"),
        }
        for key, value in expected_contract.items():
            if row.get(key) != value:
                raise ValueError(
                    f"caption contract mismatch for {digest}: {key}={row.get(key)!r}"
                )

    checks = {
        "run_complete": manifest.get("status") == "complete",
        "run_exit_zero": manifest.get("exit_code") == 0,
        "performance_values_unopened": manifest.get("performance_values_opened") is False,
        "row_count_exact": len(rows) == manifest.get("expected_unique_image_count"),
        "image_hashes_unique": len(found_by_hash) == len(rows),
        "image_coverage_exact": set(found_by_hash) == set(expected_by_hash),
        "source_bytes_match": True,
        "question_blind_contract_valid": True,
        "no_empty_captions": all(str(row["caption"]).strip() for row in rows),
        "model_revision_uniform": len(
            {(row["caption_model_path"], row["caption_model_revision"]) for row in rows}
        )
        == 1,
    }
    return {
        "schema_version": "blind-gains.caption-store-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "run_id": manifest.get("run_id"),
        "run_manifest": str(run_manifest_path),
        "run_manifest_sha256": sha256_file(run_manifest_path),
        "caption_store": str(caption_store_path),
        "caption_store_sha256": sha256_file(caption_store_path),
        "rows": len(rows),
        "expected_rows": len(expected_items),
        "input_dirs": [str(path) for path in input_dirs],
        "input_image_hashes_sha256": hashlib.sha256(
            "\n".join(sorted(expected_by_hash)).encode("utf-8")
        ).hexdigest(),
        "model_id": manifest.get("model_id"),
        "model_revision": manifest.get("model_revision"),
        "tensor_parallel_width": manifest.get("tensor_parallel_width"),
        "max_new_tokens": manifest.get("max_new_tokens"),
        "decoding": manifest.get("decoding"),
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, action="append")
    parser.add_argument("--shards", type=Path, nargs="+")
    parser.add_argument("--expected-model")
    parser.add_argument("--expected-revision")
    parser.add_argument("--expected-tp", type=int)
    parser.add_argument("--run-manifest", type=Path)
    parser.add_argument("--caption-store", type=Path)
    parser.add_argument("--input-dir", type=Path, action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite caption audit: {args.output}")

    legacy_supplied = args.manifest is not None or args.shards is not None
    run_supplied = any(
        value is not None
        for value in (args.run_manifest, args.caption_store, args.input_dir)
    )
    if legacy_supplied == run_supplied:
        raise ValueError("select exactly one audit mode: manifest/shards or run-manifest/store/input-dir")

    if run_supplied:
        if args.run_manifest is None or args.caption_store is None or not args.input_dir:
            raise ValueError("run-manifest mode requires --run-manifest, --caption-store, and --input-dir")
        payload = audit_caption_store(
            run_manifest_path=args.run_manifest,
            caption_store_path=args.caption_store,
            input_dirs=args.input_dir,
        )
        _atomic_write_json(args.output, payload)
        print(json.dumps({"status": payload["status"], "n_images": payload["rows"]}, sort_keys=True))
        raise SystemExit(0 if payload["status"] == "pass" else 1)

    if not args.manifest or not args.shards:
        raise ValueError("legacy mode requires --manifest and --shards")
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
    _atomic_write_json(args.output, payload)
    print(json.dumps({"status": payload["status"], "n_images": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
