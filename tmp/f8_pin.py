import hashlib, json
from pathlib import Path
ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p = ROOT / "reports" / "mini_a5_f8_run_provenance_v1.json"
d = json.loads(p.read_text())
d["tooling_sha256"] = {
    "tmp/f8_driver.sh": sh(ROOT / "tmp/f8_driver.sh"),
    "tmp/f8_verify.py": sh(ROOT / "tmp/f8_verify.py"),
    "tmp/f8_provenance.py": sh(ROOT / "tmp/f8_provenance.py"),
}
d["artifact_storage_note"] = (
    "experiments/runs/ and logs/ are gitignored, so the six run directories, their shard "
    "predictions, per-shard metrics, worker logs and the driver state dir exist only on cluster "
    "storage. This reports/ file plus reports/mini_a5_f8_cell_verification_v1.json are the "
    "committed record."
)
d["verification_report"] = "reports/mini_a5_f8_cell_verification_v1.json"
p.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
print("pinned")
