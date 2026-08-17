#!/usr/bin/env python3
"""Relax watcher-completion gating in seed-3 queue and M5-after-A2 lifecycle.

Rationale: watch_pilot_checkpoints.py holds its manifest at status=running until
step-60 evaluation markers exist, but the seed-3 eval lifecycle runs post-cohort
(seed-2 registered procedure). Node capacity release must therefore gate on the
artifact truth (training complete + step-100 merged index + RAW_STATE_RELOCATED)
rather than on watcher manifest completion. Watcher terminal failures still fail
closed in both pollers.
"""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

PATCHES = [
    (
        ROOT / "scripts/run_pilot_seed3_queue_v2.py",
        '''    if watcher_status != "complete":
        return False, "waiting_checkpoint_watcher_completion"
    if watcher.get("exit_code") != 0 or watcher.get("artifacts_exist") is not True:
        raise RuntimeError("checkpoint watcher completion is not artifact-verified")
    checkpoint_root = Path(str(training["checkpoint_path"]))
    final_index = checkpoint_root / "global_step_100/actor/huggingface/model.safetensors.index.json"
    final_raw_marker = checkpoint_root / "global_step_100/actor/RAW_STATE_RELOCATED.json"
    if not final_index.is_file() or not final_raw_marker.is_file():
        return False, "waiting_step100_merge_and_retention"
    return True, "training_and_step100_retention_complete"
''',
        '''    checkpoint_root = Path(str(training["checkpoint_path"]))
    final_index = checkpoint_root / "global_step_100/actor/huggingface/model.safetensors.index.json"
    final_raw_marker = checkpoint_root / "global_step_100/actor/RAW_STATE_RELOCATED.json"
    if not final_index.is_file() or not final_raw_marker.is_file():
        return False, "waiting_step100_merge_and_retention"
    if watcher_status == "complete":
        if watcher.get("exit_code") != 0 or watcher.get("artifacts_exist") is not True:
            raise RuntimeError("checkpoint watcher completion is not artifact-verified")
        return True, "training_and_step100_retention_complete"
    # Watcher stays running until step-60 eval markers exist; those evals run
    # post-cohort under the registered lifecycle, so capacity release keys on
    # the on-disk step-100 artifacts verified above.
    return True, "training_and_step100_artifacts_complete_step60_retention_deferred_to_eval_lifecycle"
''',
    ),
    (
        ROOT / "scripts/run_m5_after_seed3_a2_queue.py",
        '''    if training_status in TERMINAL_FAILURES or watcher_status in TERMINAL_FAILURES:
        return "fail", evidence
    if training_status != "complete" or watcher_status != "complete":
        return "waiting", evidence
    completion_checks = {
        "training_exit_zero": training.get("exit_code") == 0,
        "training_artifacts_verified": training.get("artifacts_exist") is True,
        "watcher_exit_zero": watcher.get("exit_code") == 0,
        "watcher_artifacts_verified": watcher.get("artifacts_exist") is True,
    }
''',
        '''    if training_status in TERMINAL_FAILURES or watcher_status in TERMINAL_FAILURES:
        return "fail", evidence
    if training_status != "complete":
        return "waiting", evidence
    completion_checks = {
        "training_exit_zero": training.get("exit_code") == 0,
        "training_artifacts_verified": training.get("artifacts_exist") is True,
        "watcher_nonterminal": watcher_status in {"running", "complete"},
    }
    if watcher_status == "complete":
        completion_checks["watcher_exit_zero"] = watcher.get("exit_code") == 0
        completion_checks["watcher_artifacts_verified"] = (
            watcher.get("artifacts_exist") is True
        )
''',
    ),
]


def main() -> int:
    for path, old, new in PATCHES:
        text = path.read_text(encoding="utf-8")
        if new in text:
            print(f"already patched: {path.name}")
            continue
        count = text.count(old)
        if count != 1:
            print(f"ABORT: expected exactly 1 match in {path.name}, found {count}")
            return 1
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched: {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
