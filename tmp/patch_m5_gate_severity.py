#!/usr/bin/env python3
"""Fix severity of step-100 artifact checks in the M5-after-A2 release gate.

The previous patch evaluated artifact checks as soon as training completed,
but the checkpoint watcher produces the step-100 merged index and relocation
marker minutes later; the transient absence must be 'waiting' while the
watcher is alive, and 'fail' only once the watcher has completed without
producing them. Hard training/watcher identity failures stay terminal.
"""
from pathlib import Path
import sys

PATH = Path(
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/run_m5_after_seed3_a2_queue.py"
)

OLD = """    evidence["completion_checks"] = completion_checks
    return ("ready" if all(completion_checks.values()) else "fail"), evidence
"""

NEW = """    evidence["completion_checks"] = completion_checks
    hard_keys = (
        "training_exit_zero",
        "training_artifacts_verified",
        "watcher_nonterminal",
        "watcher_exit_zero",
        "watcher_artifacts_verified",
    )
    if not all(
        completion_checks[key] for key in hard_keys if key in completion_checks
    ):
        return "fail", evidence
    artifact_keys = (
        "step100_index",
        "step100_raw_marker",
        "tracker_step100",
        "raw_marker_status",
    )
    if all(completion_checks[key] for key in artifact_keys):
        return "ready", evidence
    if watcher_status == "complete":
        return "fail", evidence
    # The watcher is alive and has not yet merged/relocated step 100; the
    # artifacts are expected to appear, so this state is a wait, not a failure.
    evidence["waiting_reason"] = "step100_merge_and_retention_in_progress"
    return "waiting", evidence
"""

text = PATH.read_text(encoding="utf-8")
if NEW in text:
    print("already patched")
    sys.exit(0)
if text.count(OLD) != 1:
    print(f"ABORT: expected exactly 1 match, found {text.count(OLD)}")
    sys.exit(1)
PATH.write_text(text.replace(OLD, NEW), encoding="utf-8")
print("patched: run_m5_after_seed3_a2_queue.py (severity-aware release gate)")
