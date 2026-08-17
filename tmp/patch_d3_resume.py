#!/usr/bin/env python3
"""Make the test-time cell orchestrator restart-safe.

The orchestrator died leaving three cells running and one dead, with buffered
stdout lost. Two fixes:
  1. reconcile(): any cell dir whose predictions.jsonl already holds the full
     601 rows is finalized to complete; a dir whose manifest says running but
     whose predictions are absent/short AND whose worker pid is gone is
     finalized to fail. Idempotent, safe to run repeatedly.
  2. completed_cells(): additionally treats a (model, condition) as already
     handled when a run dir for it is still legitimately in flight, so a
     restarted orchestrator never launches a duplicate of a live cell.
"""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/run_d2_testtime_ablation.py"
t = p.read_text()

if "def reconcile(" in t:
    print("already patched")
    sys.exit(0)

old = '''def completed_cells() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    for manifest_path in (ROOT / "experiments/runs").glob("d2_testtime_*/run_manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("job_type") == "d2_testtime_ablation_cell" and payload.get("status") == "complete":
            done.add((str(payload.get("model_key")), str(payload.get("condition"))))
    return done'''

new = '''def reconcile(node: str) -> dict[str, int]:
    """Finalize orphaned cell manifests left by a dead orchestrator."""
    stats = {"completed": 0, "failed": 0}
    for manifest_path in (ROOT / "experiments/runs").glob("d2_testtime_*/run_manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("job_type") != "d2_testtime_ablation_cell":
            continue
        if payload.get("status") != "running":
            continue
        run_dir = manifest_path.parent
        predictions = run_dir / "predictions.jsonl"
        rows = 0
        if predictions.is_file():
            rows = sum(1 for line in predictions.read_text(encoding="utf-8").splitlines() if line.strip())
        if rows >= EXPECTED_ROWS:
            payload.update({
                "status": "complete", "exit_code": 0, "end_time_utc": _now(),
                "artifacts_exist": True, "rows": rows,
                "predictions_sha256": _sha256(predictions),
                "reconciled": "finalized by reconcile() after an orchestrator restart",
            })
            _write(manifest_path, payload)
            stats["completed"] += 1
            continue
        pid_file = run_dir / "logs/pid"
        alive = False
        if pid_file.is_file():
            pid = pid_file.read_text().strip()
            probe = _ssh(node, f"ps -o pid= -p {pid} | wc -l")
            alive = probe.returncode == 0 and int(probe.stdout.strip() or 0) > 0
        if not alive:
            payload.update({
                "status": "fail", "exit_code": 1, "end_time_utc": _now(),
                "rows": rows,
                "failure": "worker exited without complete output; orchestrator was not running to observe it",
            })
            _write(manifest_path, payload)
            stats["failed"] += 1
    return stats


def in_flight_cells(node: str) -> set[tuple[str, str]]:
    """(model, condition) pairs whose cell is still legitimately running."""
    live: set[tuple[str, str]] = set()
    for manifest_path in (ROOT / "experiments/runs").glob("d2_testtime_*/run_manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("job_type") != "d2_testtime_ablation_cell":
            continue
        if payload.get("status") == "running":
            live.add((str(payload.get("model_key")), str(payload.get("condition"))))
    return live


def completed_cells() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    for manifest_path in (ROOT / "experiments/runs").glob("d2_testtime_*/run_manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("job_type") == "d2_testtime_ablation_cell" and payload.get("status") == "complete":
            done.add((str(payload.get("model_key")), str(payload.get("condition"))))
    return done'''

assert t.count(old) == 1, f"anchor count {t.count(old)}"
t = t.replace(old, new)

old_main = '''    done = completed_cells()
    pending = [cell for cell in CELLS if cell not in done]'''
new_main = '''    recon = reconcile(args.node)
    print(json.dumps({"reconciled": recon}))
    done = completed_cells()
    live = in_flight_cells(args.node)
    pending = [cell for cell in CELLS if cell not in done and cell not in live]'''
assert t.count(old_main) == 1, "main anchor"
t = t.replace(old_main, new_main)
p.write_text(t)
print("patched: reconcile() + in-flight skip")
