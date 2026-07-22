#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.finalize_run_manifest import finalize_manifest  # noqa: E402


def run_manifest_job(manifest_path: Path, log_path: Path) -> int:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    command = str(payload["command"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PATH"] = f"{ROOT / '.venv' / 'bin'}{os.pathsep}{environment.get('PATH', '')}"
    environment["PYTHONPATH"] = "."
    environment["PYTHONUNBUFFERED"] = "1"
    with log_path.open("ab", buffering=0) as log:
        try:
            result = subprocess.run(
                command,
                shell=True,
                executable="/bin/bash",
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        except OSError as error:
            exit_code = 126
            message = (
                f"run_manifest_job could not spawn the registered command: "
                f"{type(error).__name__}: {error}\n"
            )
            log.write(message.encode("utf-8", errors="replace"))
            finalize_manifest(
                manifest_path,
                exit_code,
                runner_error={
                    "phase": "spawn_registered_command",
                    "error_type": type(error).__name__,
                    "message": str(error),
                },
            )
            return exit_code
    finalize_manifest(manifest_path, result.returncode)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("log")
    args = parser.parse_args()
    raise SystemExit(run_manifest_job(Path(args.manifest), Path(args.log)))


if __name__ == "__main__":
    main()
