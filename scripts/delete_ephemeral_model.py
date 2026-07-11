#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from src.data.model_registry import sha256_tree


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_deletion_contract(
    download_manifest: dict[str, Any],
    checkout_manifest: dict[str, Any],
    caption_manifest: dict[str, Any],
    *,
    expected_node: str,
    download_run_reference: str | None = None,
    require_memory_path: bool = True,
) -> Path:
    model_path = Path(str(download_manifest.get("local_path", "")))
    checks = {
        "download_complete": download_manifest.get("status") == "complete",
        "download_node_exact": download_manifest.get("node") == expected_node,
        "checkout_pass": checkout_manifest.get("status") == "pass",
        "checkout_path_exact": checkout_manifest.get("local_path") == str(model_path),
        "caption_complete": caption_manifest.get("status") == "complete",
        "caption_node_exact": caption_manifest.get("node") == expected_node,
        "caption_model_path_exact": caption_manifest.get("model_path") == str(model_path),
        "caption_download_run_exact": caption_manifest.get("model_download_run")
        == (download_run_reference or download_manifest.get("run_id")),
    }
    if require_memory_path:
        checks["model_path_ephemeral"] = str(model_path).startswith(
            "/dev/shm/blind-gains/"
        ) and ".." not in model_path.parts
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError(f"ephemeral model deletion contract failed: {failed}")
    return model_path


def write_json_immutable(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite deletion record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True, choices=("an12", "an29"))
    parser.add_argument("--download-manifest", type=Path, required=True)
    parser.add_argument("--checkout-manifest", type=Path, required=True)
    parser.add_argument("--caption-manifest", type=Path, required=True)
    parser.add_argument("--caption-store", type=Path, required=True)
    parser.add_argument("--predelete-record", type=Path, required=True)
    parser.add_argument("--deletion-record", type=Path, required=True)
    args = parser.parse_args()

    download = json.loads(args.download_manifest.read_text(encoding="utf-8"))
    checkout = json.loads(args.checkout_manifest.read_text(encoding="utf-8"))
    caption = json.loads(args.caption_manifest.read_text(encoding="utf-8"))
    model_path = validate_deletion_contract(
        download,
        checkout,
        caption,
        expected_node=args.node,
        download_run_reference=str(args.download_manifest.parent),
    )
    if not model_path.is_dir():
        raise FileNotFoundError(f"ephemeral model checkout is absent: {model_path}")
    if not args.caption_store.is_file() or args.caption_store.stat().st_size == 0:
        raise FileNotFoundError(f"committed caption store is absent: {args.caption_store}")

    observed_tree_hash = sha256_tree(model_path)
    expected_tree_hash = str(checkout.get("sha256_tree", ""))
    if observed_tree_hash != expected_tree_hash:
        raise ValueError(
            f"ephemeral model tree hash drift: expected {expected_tree_hash}, "
            f"found {observed_tree_hash}"
        )
    total_bytes = sum(path.stat().st_size for path in model_path.rglob("*") if path.is_file())
    if total_bytes != int(checkout.get("total_bytes", -1)):
        raise ValueError("ephemeral model byte count differs from checkout manifest")
    caption_sha256 = _sha256(args.caption_store)
    caption_rows = sum(1 for line in args.caption_store.open(encoding="utf-8") if line.strip())
    if caption_rows <= 0:
        raise ValueError("caption store contains no rows")

    common = {
        "schema_version": "blind-gains.ephemeral-model-deletion.v1",
        "node": args.node,
        "model_path": str(model_path),
        "model_id": checkout.get("model_id"),
        "model_revision": checkout.get("revision"),
        "model_sha256_tree": observed_tree_hash,
        "model_total_bytes": total_bytes,
        "download_manifest": str(args.download_manifest),
        "checkout_manifest": str(args.checkout_manifest),
        "caption_manifest": str(args.caption_manifest),
        "caption_store": str(args.caption_store),
        "caption_store_sha256": caption_sha256,
        "caption_store_rows": caption_rows,
        "deletion_reason": "L9 caption store committed; ephemeral weights are retention-expired and re-derivable.",
    }
    write_json_immutable(
        args.predelete_record,
        {
            **common,
            "status": "deletion-authorized",
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    )
    shutil.rmtree(model_path)
    if model_path.exists():
        raise RuntimeError(f"ephemeral model path remains after deletion: {model_path}")
    write_json_immutable(
        args.deletion_record,
        {
            **common,
            "status": "deleted",
            "deleted_at_utc": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "path_absent_after_deletion": True,
        },
    )
    print(json.dumps({"status": "deleted", "bytes": total_bytes}, sort_keys=True))


if __name__ == "__main__":
    main()
