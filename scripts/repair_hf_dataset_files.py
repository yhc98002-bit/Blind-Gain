#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lfs_pointer_oid(path: Path) -> str | None:
    if not path.is_file() or path.stat().st_size > 1024:
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "version https://git-lfs.github.com/spec/v1":
        return None
    for line in lines[1:]:
        if line.startswith("oid sha256:"):
            return line.removeprefix("oid sha256:")
    return None


def install_verified_file(source_url: str, destination: Path, expected_sha256: str, expected_bytes: int) -> str:
    if destination.is_file() and sha256_file(destination) == expected_sha256:
        return "already_verified"
    pointer_oid = lfs_pointer_oid(destination)
    if pointer_oid != expected_sha256:
        raise ValueError(
            f"refusing to replace {destination}: expected unresolved pointer {expected_sha256}, found {pointer_oid}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f".{destination.name}.partial.{os.getpid()}")
    if partial.exists():
        raise FileExistsError(f"partial download already exists: {partial}")
    try:
        digest = hashlib.sha256()
        written = 0
        with urllib.request.urlopen(source_url, timeout=120) as response, partial.open("xb") as handle:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                handle.write(chunk)
                digest.update(chunk)
                written += len(chunk)
        actual_sha256 = digest.hexdigest()
        if written != expected_bytes or actual_sha256 != expected_sha256:
            raise ValueError(
                f"download verification failed for {destination}: "
                f"bytes={written}/{expected_bytes} sha256={actual_sha256}/{expected_sha256}"
            )
        os.replace(partial, destination)
    finally:
        partial.unlink(missing_ok=True)
    return "installed"


def repair(spec_path: Path, checkout: Path) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    required = {"repo_id", "revision", "files"}
    missing = required - set(spec)
    if missing:
        raise ValueError(f"repair spec missing fields: {sorted(missing)}")
    if not checkout.is_dir():
        raise FileNotFoundError(checkout)

    results = []
    for record in spec["files"]:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe repair path: {relative}")
        encoded_path = "/".join(urllib.parse.quote(part) for part in relative.parts)
        source_url = (
            f"https://huggingface.co/datasets/{spec['repo_id']}/resolve/"
            f"{spec['revision']}/{encoded_path}"
        )
        destination = checkout / relative
        action = install_verified_file(
            source_url,
            destination,
            str(record["sha256"]),
            int(record["bytes"]),
        )
        results.append(
            {
                "path": str(relative),
                "source_url": source_url,
                "sha256": sha256_file(destination),
                "bytes": destination.stat().st_size,
                "action": action,
            }
        )
    return {
        "schema_version": "blind-gains.hf-file-repair.v1",
        "status": "pass",
        "repo_id": spec["repo_id"],
        "revision": spec["revision"],
        "checkout": str(checkout),
        "files": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite repair report: {args.output}")
    payload = repair(args.spec, args.checkout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "files": len(payload["files"])}))


if __name__ == "__main__":
    main()
