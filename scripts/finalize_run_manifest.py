#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path


def finalize_manifest(
    path: Path,
    exit_code: int,
    *,
    runner_error: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = [Path(item) for item in payload.get("expected_artifacts", [])]
    artifacts_exist = all(item.exists() for item in expected)
    payload.update(
        {
            "end_time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "exit_code": exit_code,
            "artifacts_exist": artifacts_exist,
            "status": "complete" if exit_code == 0 and artifacts_exist else "fail",
        }
    )
    if runner_error is not None:
        payload["runner_error"] = runner_error
    temporary = path.with_name(f".{path.name}.finalize.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("exit_code", type=int)
    args = parser.parse_args()
    path = Path(args.manifest)
    finalize_manifest(path, args.exit_code)


if __name__ == "__main__":
    main()
