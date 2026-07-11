#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"


def inventory_checkout(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not (root / ".git").exists():
        raise ValueError(f"dataset checkout has no git metadata: {root}")
    files = sorted(path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)
    if not files:
        raise ValueError("dataset checkout has no working-tree files")
    digest = hashlib.sha256()
    total_bytes = 0
    unresolved_lfs = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        size = path.stat().st_size
        total_bytes += size
        with path.open("rb") as handle:
            first = handle.read(len(LFS_POINTER_PREFIX))
            if first == LFS_POINTER_PREFIX:
                unresolved_lfs.append(relative)
            digest.update(first)
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "revision": revision,
        "tree_sha256": digest.hexdigest(),
        "file_count": len(files),
        "size_bytes": total_bytes,
        "unresolved_lfs_pointers": unresolved_lfs,
        "status": "pass" if not unresolved_lfs else "fail",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--license", required=True)
    parser.add_argument("--redistribution", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite dataset inventory: {args.output}")
    payload = {
        "schema_version": "blind-gains.dataset-checkout.v1",
        "dataset_id": args.dataset_id,
        "source": "ModelScope direct domestic route",
        "source_url": args.source_url,
        "license": args.license,
        "redistribution": args.redistribution,
        "local_path": str(args.checkout),
        "inventoried_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **inventory_checkout(args.checkout),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
