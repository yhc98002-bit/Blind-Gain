#!/usr/bin/env python3
"""Generate the sixteen seed-3 evaluation endpoint configurations.

Clones each frozen seed-2 endpoint configuration
(configs/eval/m3_seed2_{arm}_step{60,100}_{r19,geo3k}_queue_v1.json), swapping
only seed, training run, checkpoint root, marker paths, and the cohort-release
run. Arm training runs are read from the live v2 remaining-queue state so the
identities match the actual seed-3 cohort exactly; the builder refuses to run
until every arm (including a3_caption) has a recorded training run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
QUEUE_STATE = ROOT / "experiments/runs/pilot_seed3_remaining_an29_queue_login_20260724T033648Z/queue_state.json"
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
STEPS = (60, 100)
KINDS = ("r19", "geo3k")
CKPT_ROOTS = {
    "a1_real": "checkpoints/pilot/mech_a1_real_seed3",
    "a2_gray": "checkpoints/pilot/mech_a2_gray_seed3",
    "a2b_noimage": "checkpoints/pilot/mech_a2b_noimage_seed3",
    "a3_caption": "checkpoints/pilot/mech_a3_caption_seed3",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    state = json.loads(QUEUE_STATE.read_text(encoding="utf-8"))
    training_runs: dict[str, str] = {}
    for arm in ARMS:
        run = state["arms"][arm].get("training_run")
        if not run:
            raise SystemExit(f"BLOCKED: no training run recorded yet for {arm}")
        manifest = ROOT / run / "run_manifest.json"
        if not manifest.is_file():
            raise SystemExit(f"BLOCKED: training manifest absent for {arm}: {run}")
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("arm") not in (arm, None) and payload.get("job_type") != "m3_mechanical_pilot_arm":
            raise SystemExit(f"identity mismatch for {arm}: {run}")
        training_runs[arm] = run

    a3_run = training_runs["a3_caption"]
    written = []
    for arm in ARMS:
        for step in STEPS:
            for kind in KINDS:
                src = ROOT / f"configs/eval/m3_seed2_{arm}_step{step}_{kind}_queue_v1.json"
                dst = ROOT / f"configs/eval/m3_seed3_{arm}_step{step}_{kind}_queue_v1.json"
                config = json.loads(src.read_text(encoding="utf-8"))
                if int(config["seed"]) != 2 or config["arm"] != arm or int(config["global_step"]) != step:
                    raise SystemExit(f"unexpected source identity in {src.name}")
                config["seed"] = 3
                config["training_run"] = training_runs[arm]
                config["checkpoint_path"] = (
                    f"{CKPT_ROOTS[arm]}/global_step_{step}/actor/huggingface"
                )
                if kind == "r19":
                    config["cohort_release_training_run"] = a3_run
                    config["marker"] = f"{training_runs[arm]}/step{step}_fliptrack_complete.json"
                else:
                    config["r19_marker"] = f"{training_runs[arm]}/step{step}_fliptrack_complete.json"
                text = json.dumps(config, indent=2, sort_keys=True) + "\n"
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                written.append({"file": dst.name, "sha256_16": digest})
                if not args.dry_run:
                    if dst.exists():
                        raise SystemExit(f"refusing to overwrite {dst}")
                    dst.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "mode": "dry-run" if args.dry_run else "written",
                "configs": len(written),
                "training_runs": training_runs,
                "files": written,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
