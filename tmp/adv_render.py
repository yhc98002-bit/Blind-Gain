"""Emit the two-seed fixture markdown + key JSON blocks for adversarial text review."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

REPO = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "tests"))
import test_m7_r3_readout_two_seed_fixture as fx  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/adv_render")
out.mkdir(parents=True, exist_ok=True)
tmp = Path(tempfile.mkdtemp(prefix="adv_render_"))
fx.build_two_seed_fixture(tmp)
res = subprocess.run(fx._cli_two_seed(tmp), capture_output=True, text=True)
assert res.returncode == 0, res.stderr
(out / "two_seed.md").write_text((tmp / "reports/out.md").read_text())
payload = json.loads((tmp / "reports/out.json").read_text())
(out / "two_seed.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
print("schema_version:", payload["schema_version"])
print("artifact files:", sorted(p.name for p in (tmp / "reports/artifacts").iterdir()))
print("md bytes:", len((tmp / "reports/out.md").read_text()))

# seed-1 mode on the SAME fixture, for tag/schema comparison
res2 = subprocess.run(
    fx._cli_two_seed(
        tmp, seed2_arms=(), json_name="one.json", md_name="one.md",
        artifact_dir="reports/artifacts_one",
    ),
    capture_output=True, text=True,
)
assert res2.returncode == 0, res2.stderr
one = json.loads((tmp / "reports/one.json").read_text())
(out / "one_seed.md").write_text((tmp / "reports/one.md").read_text())
print("one-seed schema_version:", one["schema_version"])
print("one-seed artifacts:", sorted(p.name for p in (tmp / "reports/artifacts_one").iterdir()))
print("one-seed has seed_dispersion key:", "seed_dispersion" in one)
