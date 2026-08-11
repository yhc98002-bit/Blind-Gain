"""Build the two-seed planted fixture and print its markdown + key JSON."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = _load(
    "_two_seed_fixture", REPO / "tests/test_m7_r3_readout_two_seed_fixture.py"
)
work = Path(sys.argv[1]).resolve()
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
fixture.build_two_seed_fixture(work)
result = subprocess.run(
    fixture._cli_two_seed(work), capture_output=True, text=True
)
if result.returncode != 0:
    sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)
print((work / "reports/out.md").read_text(encoding="utf-8"))
payload = json.loads((work / "reports/out.json").read_text(encoding="utf-8"))
print("=" * 70)
print("SCHEMA:", payload["schema_version"])
print("CHECKS:", json.dumps(payload["checks"], indent=2, sort_keys=True))
print("SEED_DISPERSION:", json.dumps(payload["seed_dispersion"], indent=2, sort_keys=True)[:4000])
