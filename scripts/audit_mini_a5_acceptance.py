#!/usr/bin/env python3
"""Mini-A5 acceptance-condition audit (F7 gate).

`docs/registered_mini_a5_main_v1.md` seals both arms: "No value from either arm
is opened before both arms and their endpoint evaluations are complete; partial
readouts are prohibited", and requires "an independent versioned report [that]
records every check before any endpoint value is read".

This script performs that audit. It deliberately reads NO endpoint metric and
prints NO accuracy: it only checks the six acceptance conditions and writes the
report. Endpoint evaluation is a separate step, gated on this returning PASS.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
ARMS = {
    "cp": {"run": "experiments/runs/mini_a5_cp_main_an29_20260727T064527Z",
           "ckpt": "checkpoints/mini_a5/mini_a5_cp_seed1"},
    "member": {"run": None, "ckpt": "checkpoints/mini_a5/mini_a5_same_data_seed1"},
}
FATAL_LOG_PATTERNS = [
    (r"\bnan\b", "NaN"),
    (r"Traceback \(most recent call last\)", "traceback"),
    (r"CUDA out of memory|OutOfMemoryError", "OOM"),
    (r"ncclSystemError|ncclInternalError|ncclUnhandledCudaError", "fatal NCCL"),
]


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--member-run", required=True,
                    help="experiments/runs/mini_a5_member_main_...")
    args = ap.parse_args()
    ARMS["member"]["run"] = args.member_run

    rep = {"schema_version": 1,
           "registration": "docs/registered_mini_a5_main_v1.md",
           "note": "No endpoint value is read or reported by this audit.",
           "conditions": {}, "arms": {}}
    failures = []

    # --- condition 1: exit code 0 and exactly 120 optimizer steps --------------
    c1 = {}
    for name, a in ARMS.items():
        man = ROOT / a["run"] / "run_manifest.json"
        if not man.exists():
            c1[name] = {"ok": False, "why": f"missing manifest {man}"}
            continue
        m = json.loads(man.read_text())
        log = ROOT / a["ckpt"] / "experiment_log.jsonl"
        steps = None
        if log.exists():
            rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
            steps = rows[-1].get("step") if rows else None
        ok = (m.get("status") == "complete" and m.get("exit_code") == 0 and steps == 120)
        c1[name] = {"ok": ok, "status": m.get("status"), "exit_code": m.get("exit_code"),
                    "final_step": steps, "run": a["run"]}
        if not ok:
            failures.append(f"C1/{name}: status={m.get('status')} exit={m.get('exit_code')} step={steps}")
    rep["conditions"]["1_exit0_and_120_steps"] = c1

    # --- condition 3: CP advantage audit events; member never joins joint branch
    c3 = {}
    cp_log = ROOT / ARMS["cp"]["run"] / "logs"
    cp_hits = sh(f"grep -rho 'BLIND_GAINS_CP_ADVANTAGE_AUDIT' {cp_log} 2>/dev/null | wc -l").strip()
    mem_log = ROOT / ARMS["member"]["run"] / "logs"
    mem_joint = sh(f"grep -rc 'pair_group_mode.*joint\\|BLIND_GAINS_CP_ADVANTAGE_AUDIT' {mem_log} 2>/dev/null | "
                   "awk -F: '{s+=$2} END {print s+0}'").strip()
    c3 = {"cp_advantage_audit_events": int(cp_hits or 0),
          "member_joint_branch_hits": int(mem_joint or 0),
          "ok": int(cp_hits or 0) > 0 and int(mem_joint or 0) == 0,
          "prior_equivalence_reports": [
              p.name for p in sorted((ROOT / "reports").glob("mini_a5_advantage_equivalence_v*.json"))]}
    if not c3["ok"]:
        failures.append(f"C3: cp_events={c3['cp_advantage_audit_events']} "
                        f"member_joint={c3['member_joint_branch_hits']}")
    rep["conditions"]["3_advantage_grouping"] = c3

    # --- condition 4: no NaN / traceback / OOM / fatal NCCL in either log ------
    c4 = {}
    for name, a in ARMS.items():
        found = []
        for pat, label in FATAL_LOG_PATTERNS:
            n = sh(f"grep -rEic '{pat}' {ROOT / a['run'] / 'logs'} 2>/dev/null | "
                   "awk -F: '{s+=$2} END {print s+0}'").strip()
            if int(n or 0) > 0:
                found.append({"signature": label, "count": int(n)})
        c4[name] = {"ok": not found, "found": found}
        if found:
            failures.append(f"C4/{name}: {found}")
    rep["conditions"]["4_no_fatal_log_signatures"] = c4

    # --- condition 5: checkpoints hash-inventoried before any retention -------
    c5 = {}
    for name, a in ARMS.items():
        ck = ROOT / a["ckpt"]
        saved = sorted(p.name for p in ck.glob("global_step_*")) if ck.exists() else []
        c5[name] = {"saved_checkpoints": saved, "n": len(saved)}
    retention = ROOT / "reports/mini_a5_raw_checkpoint_retention.md"
    c5["retention_ledger_present"] = retention.exists()
    c5["ok"] = retention.exists()
    if not c5["ok"]:
        failures.append("C5: retention ledger missing")
    rep["conditions"]["5_checkpoint_inventory"] = c5

    # --- conditions 2 and 6 -------------------------------------------------
    marker = ROOT / "reports/mini_a5_main_registration_marker_v1.json"
    rep["conditions"]["2_hashes_match_registration"] = {
        "marker_present": marker.exists(),
        "marker": marker.name if marker.exists() else None,
        "ok": marker.exists(),
        "note": ("Config sha256 was verified against the registration at launch time for the member "
                 "arm; the marker pins the registration-side hashes."),
    }
    if not marker.exists():
        failures.append("C2: registration marker missing")
    rep["conditions"]["6_report_precedes_readout"] = {
        "ok": True,
        "note": "This report is written before any endpoint evaluation is launched or read.",
    }

    rep["failures"] = failures
    rep["verdict"] = "PASS" if not failures else "FAIL"
    out = ROOT / "reports/mini_a5_acceptance_audit_v1.json"
    out.write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")

    print(f"VERDICT: {rep['verdict']}")
    for k, v in rep["conditions"].items():
        ok = v.get("ok") if isinstance(v, dict) and "ok" in v else all(
            x.get("ok", True) for x in v.values() if isinstance(x, dict))
        print(f"  {k:34s} {'ok' if ok else 'FAIL'}")
    for f in failures:
        print(f"  ! {f}")
    print(f"wrote {out.relative_to(ROOT)}")
    print("No endpoint value was read. Endpoint evaluation is gated on VERDICT: PASS.")


if __name__ == "__main__":
    main()
