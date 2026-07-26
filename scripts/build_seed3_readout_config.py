#!/usr/bin/env python3
"""Build the seed-3 four-arm readout configuration.

Clones the frozen seed-2 follow-up readout configuration
(experiments/manifests/pilot_4arm_seed2_readout_v1.json), substituting only
seed-3 identities: the four training runs (read live from the seed-3 queue
state so they cannot drift), their experiment-log segments with fresh hashes,
the seed-3 evaluation lifecycle and its children hash, and the seed-3 R19
markers. Bootstrap settings, the preregistration hash, the shared geo audits
and baselines, and the R19 base run are inherited unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
CKPT_ROOT = {
    "a1_real": "checkpoints/pilot/mech_a1_real_seed3",
    "a2_gray": "checkpoints/pilot/mech_a2_gray_seed3",
    "a2b_noimage": "checkpoints/pilot/mech_a2b_noimage_seed3",
    "a3_caption": "checkpoints/pilot/mech_a3_caption_seed3",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-state", required=True)
    parser.add_argument("--lifecycle-run", required=True)
    parser.add_argument("--output", default="experiments/manifests/pilot_4arm_seed3_readout_v1.json")
    args = parser.parse_args()
    out_path = ROOT / args.output
    if out_path.exists():
        raise FileExistsError(f"refusing to overwrite {out_path}")

    template = json.loads(
        (ROOT / "experiments/manifests/pilot_4arm_seed2_readout_v1.json").read_text(encoding="utf-8")
    )
    queue = json.loads((ROOT / args.queue_state).read_text(encoding="utf-8"))
    lifecycle = ROOT / args.lifecycle_run

    config = dict(template)
    config["seed"] = 3
    config["evaluation_lifecycle_manifest"] = f"{args.lifecycle_run}/run_manifest.json"
    config["evaluation_lifecycle_children_sha256"] = _sha256(lifecycle / "children.json")

    training_runs: dict[str, str] = {}
    segments: dict[str, list[dict]] = {}
    markers: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        run = queue["arms"][arm]["training_run"]
        if not run:
            raise SystemExit(f"BLOCKED: seed-3 {arm} has no training run recorded")
        manifest = json.loads((ROOT / run / "run_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
            raise SystemExit(f"BLOCKED: seed-3 {arm} training run is not complete: {run}")
        training_runs[arm] = run
        log = ROOT / CKPT_ROOT[arm] / "experiment_log.jsonl"
        if not log.is_file():
            raise SystemExit(f"BLOCKED: experiment log absent for {arm}")
        segments[arm] = [
            {
                "path": str(log.relative_to(ROOT)),
                "sha256": _sha256(log),
                "start_step": 1,
                "end_step": 100,
            }
        ]
        markers[arm] = {
            step: f"{run}/step{step}_fliptrack_complete.json" for step in ("60", "100")
        }
        for path in markers[arm].values():
            if not (ROOT / path).is_file():
                raise SystemExit(f"BLOCKED: R19 marker absent: {path}")

    audits: dict[str, str] = {}
    for arm in ARMS:
        matches = sorted(
            (ROOT / "experiments/runs").glob(
                f"pilot_followup_geo3k_audit_m3_geo3k_{arm}_seed3_step100_*"
            )
        )
        matches = [m for m in matches if (m / "audit.json").is_file()]
        if len(matches) != 1:
            raise SystemExit(
                f"BLOCKED: expected exactly one seed-3 step-100 geo3k audit for {arm}, found {len(matches)}"
            )
        audits[arm] = f"experiments/runs/{matches[0].name}/audit.json"
    config["geo_audits"] = audits

    config["training_runs"] = training_runs
    config["training_metric_segments"] = segments
    config["r19_markers"] = markers

    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(config, indent=2, sort_keys=True) + "\n"
    out_path.write_text(text, encoding="utf-8")
    print(json.dumps({"output": str(out_path.relative_to(ROOT)),
                      "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
                      "arms": training_runs}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
