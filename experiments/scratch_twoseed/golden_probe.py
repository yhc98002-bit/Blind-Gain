"""Print sha256 of the seed-1 planted-fixture outputs for a given readout script.

Usage: python -m scripts_scratch.golden_probe <script_path> <workdir>
Reuses tests/test_m7_r3_readout_fixture.py's own builders so the golden is
produced by exactly the fixture bytes the committed test suite uses.
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    script = Path(sys.argv[1]).resolve()
    workdir = Path(sys.argv[2]).resolve()
    repo = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else ROOT
    fixture = _load(
        "_seed1_fixture", repo / "tests/test_m7_r3_readout_fixture.py"
    )
    fixture.SCRIPT = script
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    fixture._build_planted(workdir)
    args = fixture._cli(
        workdir, expected_eligible=5, expected_small_n=1, expected_rows=179
    )
    result = fixture._run(args)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"probe run failed: {result.returncode}")

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    print(f"script                 {script}")
    print(f"script_sha256          {sha(script)}")
    print(f"out.json sha256        {sha(workdir / 'reports/out.json')}")
    print(f"out.md   sha256        {sha(workdir / 'reports/out.md')}")
    print(f"out.json bytes         {(workdir / 'reports/out.json').stat().st_size}")
    print(f"out.md   bytes         {(workdir / 'reports/out.md').stat().st_size}")


if __name__ == "__main__":
    main()
