#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("exit_code", type=int)
    args = parser.parse_args()
    path = Path(args.manifest)
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = [Path(item) for item in payload.get("expected_artifacts", [])]
    artifacts_exist = all(item.exists() for item in expected)
    payload.update(
        {
            "end_time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "exit_code": args.exit_code,
            "artifacts_exist": artifacts_exist,
            "status": "complete" if args.exit_code == 0 and artifacts_exist else "fail",
        }
    )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
