#!/usr/bin/env python3
"""Three-seed Geometry3K summary and pooled equivalence verdict (Track C1).

Reads the three registered four-arm readouts, reproduces each seed's published
numbers verbatim, and reports the pooled picture. The registered FlipTrack
equivalence band is +/-0.05; a pooled mean whose 95% interval lies entirely
inside the band supports equivalence, an interval extending beyond it does not.
Facts and registered statistics only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SEEDS = {
    1: "reports/pilot_4arm_seed1_results_v1.json",
    2: "reports/pilot_4arm_seed2_results_v1.json",
    3: "reports/pilot_4arm_seed3_results_v1.json",
}
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND = ("a2_gray", "a2b_noimage", "a3_caption")
SESOI = 0.05
GEOM = "category:geometry_coordinate_indexing"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()
    for path in (Path(args.json_output), Path(args.markdown_output)):
        if path.exists():
            raise FileExistsError("refusing to overwrite the three-seed summary")

    per_seed: dict[int, Any] = {}
    provenance = []
    for seed, rel in SEEDS.items():
        path = ROOT / rel
        payload = json.loads(path.read_text(encoding="utf-8"))
        if int(payload.get("seed", seed)) != seed:
            raise ValueError(f"seed mismatch in {rel}")
        geo = payload["geo3k"]["arms"]
        rec = payload["geo3k"]["recovery_fractions"]
        flip = payload["fliptrack_r19"]["arms"]
        entry: dict[str, Any] = {"arms": {}, "recovery": {}, "fliptrack_geometry": {}}
        for arm in ARMS:
            block = geo[arm]
            entry["arms"][arm] = {
                "step0": block["acc_final_step0"],
                "step100": block["acc_final_step100"],
                "gain": block["delta_acc_final"]["estimate"],
                "gain_ci95": block["delta_acc_final"]["ci95"],
            }
            cell = flip[arm]["100"][GEOM]
            entry["fliptrack_geometry"][arm] = {
                "step0": cell["pair_accuracy_step0"],
                "step100": cell["pair_accuracy_observed"],
                "delta": cell["pair_accuracy_observed"] - cell["pair_accuracy_step0"],
            }
            if arm in BLIND:
                entry["recovery"][arm] = rec[arm]["estimate"]
        per_seed[seed] = entry
        provenance.append({"seed": seed, "path": rel, "sha256": _sha256(path)})

    pooled: dict[str, Any] = {"geo3k_gain": {}, "recovery": {}, "fliptrack_geometry": {}}
    for arm in ARMS:
        gains = [per_seed[s]["arms"][arm]["gain"] for s in SEEDS]
        pooled["geo3k_gain"][arm] = {
            "per_seed": gains,
            "mean": statistics.fmean(gains),
            "min": min(gains),
            "max": max(gains),
        }
        deltas = [per_seed[s]["fliptrack_geometry"][arm]["delta"] for s in SEEDS]
        mean = statistics.fmean(deltas)
        half = 1.96 * (statistics.stdev(deltas) / len(deltas) ** 0.5) if len(deltas) > 1 else 0.0
        lo, hi = mean - half, mean + half
        pooled["fliptrack_geometry"][arm] = {
            "per_seed": deltas,
            "mean": mean,
            "seed_level_ci95": [lo, hi],
            "within_sesoi_band": abs(lo) <= SESOI and abs(hi) <= SESOI,
            "sesoi": SESOI,
        }
        if arm in BLIND:
            recs = [per_seed[s]["recovery"][arm] for s in SEEDS]
            pooled["recovery"][arm] = {
                "per_seed": recs,
                "mean": statistics.fmean(recs),
                "min": min(recs),
                "max": max(recs),
            }

    a1_flip = pooled["fliptrack_geometry"]["a1_real"]
    verdict = (
        "equivalence_supported_within_registered_band"
        if a1_flip["within_sesoi_band"]
        else "equivalence_not_supported_interval_exceeds_band"
    )
    prereg_falsified = all(
        pooled["recovery"][arm]["max"] < 0.30 for arm in ("a2_gray", "a2b_noimage")
    )
    inversion = {
        seed: (
            per_seed[seed]["arms"]["a3_caption"]["step0"] > per_seed[seed]["arms"]["a1_real"]["step0"]
            and per_seed[seed]["arms"]["a3_caption"]["step100"] < per_seed[seed]["arms"]["a1_real"]["step100"]
        )
        for seed in SEEDS
    }

    result = {
        "schema_version": "blind-gains.three-seed-summary.v1",
        "scope": "Geometry3K four-arm pilot, seeds 1-3, step-100 endpoints; registered FlipTrack equivalence band +/-0.05",
        "per_seed": per_seed,
        "pooled": pooled,
        "a1_fliptrack_geometry_equivalence_verdict": verdict,
        "preregistered_30_70_blind_recovery_falsified_all_seeds": prereg_falsified,
        "caption_inversion_replicates": inversion,
        "provenance": provenance,
    }

    def row(values: list[float], fmt: str = "{:+.4f}") -> str:
        return " | ".join(fmt.format(v) for v in values)

    lines = [
        "# Three-seed Geometry3K summary (Track C1)",
        "",
        "Seeds 1-3, four matched arms, step-100 endpoints, 601 held-out items per",
        "seed. Each seed's numbers are read verbatim from its registered readout.",
        "Scope tags stay attached: Geometry3K corpus, 3B scale, three seeds.",
        "",
        "## Task gain (Acc_final, step 100 minus step 0)",
        "",
        "| arm | seed 1 | seed 2 | seed 3 | mean |",
        "|---|---|---|---|---|",
    ]
    for arm in ARMS:
        block = pooled["geo3k_gain"][arm]
        lines.append(f"| {arm} | {row(block['per_seed'])} | {block['mean']:+.4f} |")
    lines += [
        "",
        "## Recovery of the A1 gain",
        "",
        "| arm | seed 1 | seed 2 | seed 3 | mean |",
        "|---|---|---|---|---|",
    ]
    for arm in BLIND:
        block = pooled["recovery"][arm]
        lines.append(
            f"| {arm} | " + " | ".join(f"{v*100:.1f}%" for v in block["per_seed"]) +
            f" | {block['mean']*100:.1f}% |"
        )
    lines += [
        "",
        "The preregistered 30-70% blind-recovery interval is falsified in every seed"
        f" for gray and no-image: {prereg_falsified}.",
        "",
        "## Registered geometry FlipTrack endpoint (pair accuracy, step 100 minus step 0)",
        "",
        "| arm | seed 1 | seed 2 | seed 3 | mean | seed-level 95% CI | within +/-0.05 |",
        "|---|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        block = pooled["fliptrack_geometry"][arm]
        ci = block["seed_level_ci95"]
        lines.append(
            f"| {arm} | {row(block['per_seed'])} | {block['mean']:+.4f}"
            f" | [{ci[0]:+.4f}, {ci[1]:+.4f}] | {block['within_sesoi_band']} |"
        )
    lines += [
        "",
        f"**A1 equivalence verdict: {verdict}**",
        "",
        "## Caption inversion (A3 starts above A1 and ends below it)",
        "",
        "| seed 1 | seed 2 | seed 3 |",
        "|---|---|---|",
        "| " + " | ".join(str(inversion[s]) for s in SEEDS) + " |",
        "",
        "No interpretation beyond the registered statistics; the pooled verdict uses",
        "the registered +/-0.05 band on seed-level variation with three seeds.",
        "",
    ]

    Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "a1_gain_mean": pooled["geo3k_gain"]["a1_real"]["mean"],
        "verdict": verdict,
        "prereg_falsified": prereg_falsified,
        "inversion": inversion,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
