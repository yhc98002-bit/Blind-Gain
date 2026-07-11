#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_ssh_command(node: str, remote_proxy_port: int, manifest: Path, log: Path) -> list[str]:
    if node not in {"an12", "an29"}:
        raise ValueError("reverse-proxy jobs must target an12 or an29")
    if not 1 <= remote_proxy_port <= 65535:
        raise ValueError("remote proxy port must be in [1, 65535]")
    remote_command = (
        f"cd {shlex.quote(str(ROOT))} && "
        f"{shlex.quote(str(ROOT / '.venv' / 'bin' / 'python'))} "
        f"scripts/run_manifest_job.py {shlex.quote(str(manifest))} "
        f"{shlex.quote(str(log))}"
    )
    return [
        "ssh",
        "-o",
        "ExitOnForwardFailure=yes",
        "-R",
        f"{remote_proxy_port}:127.0.0.1:7890",
        node,
        remote_command,
    ]


def run_reverse_proxy_job(
    node: str,
    remote_proxy_port: int,
    manifest: Path,
    log: Path,
    wrapper_log: Path,
) -> int:
    wrapper_log.parent.mkdir(parents=True, exist_ok=True)
    command = build_ssh_command(node, remote_proxy_port, manifest, log)
    with wrapper_log.open("ab", buffering=0) as handle:
        result = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=False)

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("status") == "running":
        exit_code = result.returncode if result.returncode else 70
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "finalize_run_manifest.py"),
                str(manifest),
                str(exit_code),
            ],
            cwd=ROOT,
            check=True,
        )
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--remote-proxy-port", type=int, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--wrapper-log", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(
        run_reverse_proxy_job(
            args.node,
            args.remote_proxy_port,
            args.manifest,
            args.log,
            args.wrapper_log,
        )
    )


if __name__ == "__main__":
    main()
