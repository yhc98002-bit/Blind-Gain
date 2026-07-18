#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.caption_image_store_vllm import discover_image_roots
from src.captioning.store import validate_caption_row


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--caption-store", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {args.output}")
    result = audit_caption_store(
        run_manifest_path=args.run_manifest,
        caption_store_path=args.caption_store,
        input_dirs=args.input_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
