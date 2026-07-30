#!/usr/bin/env python3
"""Mini-A5 secondary endpoint 1 analysis: free-generation vs candidate-ranking.

Reads:
  - the two Mini-A5 candidate-ranking cells launched for this endpoint
  - the two completed F8 primary R19 free-generation cells (already scored,
    both contracts, by the FlipTrack harness)

Reports, per R19 template id and NEVER pooled across templates (I13, because the
three templates hold three distinct scientific roles per
docs/registered_mini_a5_endpoint_readout_v1.md section 3):

  ranking layer      lenient severity  pair_success        (both gold-vs-twin margins > 0)
                     strict severity   candidate_pair_top1 (gold beats all candidates, ties lose)
  generation layer   lenient contract  pair_correct
                     strict contract   strict_pair_correct

Intervals are paired item bootstrap on pair_id, 10,000 draws, percentile
2.5/97.5, both arms resampled on the same indices per replicate. They quantify
evaluation uncertainty on a fixed pair set; they do NOT estimate run-to-run RL
variance, and each arm is a single run.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TS = "20260730T011842Z"

RANKING = {
    "cp": ROOT / f"experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_{TS}/scores.jsonl",
    "member": ROOT / f"experiments/runs/mini_a5_s1_ranking_member_step120_real_an29_gpu5_{TS}/scores.jsonl",
}
GENERATION = {
    "cp": ROOT / "experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z/shards",
    "member": ROOT / "experiments/runs/mini_a5_f8_r19_member_step120_real_an29_20260730T004031Z/shards",
}

BASE_SEED = 20260729
N_BOOT = 10000
# Deterministic, disclosed seed derivation from the pinned base seed 20260729.
# indicator_index fixes the metric, template_index fixes the template (sorted).
INDICATORS = [
    ("ranking_pair_success", "ranking", "lenient"),
    ("ranking_candidate_pair_top1", "ranking", "strict"),
    ("generation_pair_correct", "generation", "lenient"),
    ("generation_strict_pair_correct", "generation", "strict"),
]


def resolve_seed(indicator_index: int, template_index: int) -> int:
    return BASE_SEED + 1000 * indicator_index + 10 * template_index


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_ranking(path: Path) -> dict[str, dict]:
    out = {}
    for row in jsonl(path):
        out[str(row["pair_id"])] = {
            "template_id": str(row["template_id"]),
            "ranking_pair_success": bool(row["pair_success"]),
            "ranking_candidate_pair_top1": bool(row["candidate_pair_top1"]),
            "paired_margin": float(row["paired_margin"]),
        }
    return out


def load_generation(shard_dir: Path) -> dict[str, dict]:
    out = {}
    for shard in sorted(shard_dir.glob("shard_*.jsonl")):
        for row in jsonl(shard):
            pid = str(row["pair_id"])
            if pid in out:
                raise ValueError(f"duplicate generation pair_id {pid}")
            out[pid] = {
                "template_id": str(row["template_id"]),
                "generation_pair_correct": bool(row["pair_correct"]),
                "generation_strict_pair_correct": bool(row["strict_pair_correct"]),
            }
    return out


def mcnemar_exact_bool(a: list[bool], b: list[bool]) -> dict:
    """Two-sided exact McNemar on paired indicators (a = arm/layer 1, b = 2)."""
    b01 = sum((not x) and y for x, y in zip(a, b))
    b10 = sum(x and (not y) for x, y in zip(a, b))
    n = b01 + b10
    if n == 0:
        p = 1.0
    else:
        k = min(b01, b10)
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {"b01": b01, "b10": b10, "n_discordant": n, "p_value": p}


def paired_bootstrap_diff(x: list[float], y: list[float], seed: int) -> dict:
    """Percentile CI for mean(x) - mean(y), resampling the same indices for both."""
    ax = np.asarray(x, dtype=np.float64)
    ay = np.asarray(y, dtype=np.float64)
    if ax.shape != ay.shape or ax.size == 0:
        raise ValueError("paired bootstrap needs equal nonempty vectors")
    rng = np.random.default_rng(seed)
    n = ax.size
    diffs = np.empty(N_BOOT, dtype=np.float64)
    filled = 0
    while filled < N_BOOT:
        block = min(1024, N_BOOT - filled)
        idx = rng.integers(0, n, size=(block, n))
        diffs[filled:filled + block] = ax[idx].mean(axis=1) - ay[idx].mean(axis=1)
        filled += block
    diffs.sort()
    lo = float(diffs[max(0, math.floor(0.025 * N_BOOT))])
    hi = float(diffs[min(N_BOOT - 1, math.ceil(0.975 * N_BOOT) - 1)])
    return {
        "point": float(ax.mean() - ay.mean()),
        "ci95_low": lo,
        "ci95_high": hi,
        "excludes_zero": bool(lo > 0.0 or hi < 0.0),
        "bootstrap_seed": seed,
        "resamples": N_BOOT,
    }


def main() -> None:
    rank = {arm: load_ranking(p) for arm, p in RANKING.items()}
    gen = {arm: load_generation(p) for arm, p in GENERATION.items()}

    # --- coverage / join integrity -------------------------------------------
    checks = {}
    id_sets = {f"ranking_{a}": set(rank[a]) for a in rank}
    id_sets.update({f"generation_{a}": set(gen[a]) for a in gen})
    reference = id_sets["ranking_cp"]
    checks["pair_counts"] = {k: len(v) for k, v in id_sets.items()}
    checks["all_four_cells_share_one_pair_id_set"] = all(v == reference for v in id_sets.values())
    if not checks["all_four_cells_share_one_pair_id_set"]:
        checks["set_differences"] = {
            k: {"only_here": sorted(v - reference)[:5], "missing_here": sorted(reference - v)[:5]}
            for k, v in id_sets.items() if v != reference
        }
    tmpl_consistent = all(
        rank["cp"][pid]["template_id"] == src[pid]["template_id"]
        for pid in reference
        for src in (rank["member"], gen["cp"], gen["member"])
        if pid in src
    )
    checks["template_id_agrees_across_cells"] = tmpl_consistent

    templates = sorted({rank["cp"][pid]["template_id"] for pid in reference})
    checks["templates"] = templates
    checks["template_pair_counts"] = {
        t: sum(1 for pid in reference if rank["cp"][pid]["template_id"] == t) for t in templates
    }

    merged = {}
    for pid in reference:
        row = {"pair_id": pid, "template_id": rank["cp"][pid]["template_id"]}
        for arm in ("cp", "member"):
            row[f"{arm}_ranking_pair_success"] = rank[arm][pid]["ranking_pair_success"]
            row[f"{arm}_ranking_candidate_pair_top1"] = rank[arm][pid]["ranking_candidate_pair_top1"]
            row[f"{arm}_paired_margin"] = rank[arm][pid]["paired_margin"]
            row[f"{arm}_generation_pair_correct"] = gen[arm][pid]["generation_pair_correct"]
            row[f"{arm}_generation_strict_pair_correct"] = gen[arm][pid]["generation_strict_pair_correct"]
        merged[pid] = row

    results = {
        "schema_version": "blind-gains.mini-a5-secondary1-ranking-vs-generation.v1",
        "endpoint": "Mini-A5 secondary 1 (addendum section 6.1): free-generation vs candidate-ranking",
        "aggregation_rule": "per R19 template id only; never pooled across templates (I13)",
        "interval_note": (
            "Paired item bootstrap on pair_id, 10,000 draws, percentile 2.5/97.5, both "
            "arms/layers resampled on identical indices per replicate. Quantifies "
            "evaluation uncertainty on a fixed pair set only; does not estimate "
            "run-to-run RL variance. Each arm is one run."
        ),
        "seed_derivation": "seed = 20260729 + 1000*indicator_index + 10*template_index",
        "checks": checks,
        "per_template": {},
    }

    for t_idx, template in enumerate(templates):
        pids = sorted(pid for pid in reference if merged[pid]["template_id"] == template)
        block = {"n_pairs": len(pids), "arm_rates": {}, "cp_minus_member": {}, "ranking_minus_generation": {}}

        for arm in ("cp", "member"):
            block["arm_rates"][arm] = {
                "ranking_pair_success": float(np.mean([merged[p][f"{arm}_ranking_pair_success"] for p in pids])),
                "ranking_candidate_pair_top1": float(np.mean([merged[p][f"{arm}_ranking_candidate_pair_top1"] for p in pids])),
                "generation_pair_correct": float(np.mean([merged[p][f"{arm}_generation_pair_correct"] for p in pids])),
                "generation_strict_pair_correct": float(np.mean([merged[p][f"{arm}_generation_strict_pair_correct"] for p in pids])),
                "mean_paired_margin": float(np.mean([merged[p][f"{arm}_paired_margin"] for p in pids])),
            }

        # (1) CP minus member, within each layer and severity.
        for i_idx, (indicator, layer, severity) in enumerate(INDICATORS):
            cp_vals = [bool(merged[p][f"cp_{indicator}"]) for p in pids]
            mb_vals = [bool(merged[p][f"member_{indicator}"]) for p in pids]
            entry = paired_bootstrap_diff(
                [float(v) for v in cp_vals], [float(v) for v in mb_vals],
                resolve_seed(i_idx, t_idx),
            )
            entry["mcnemar_exact_two_sided"] = mcnemar_exact_bool(cp_vals, mb_vals)
            entry["layer"] = layer
            entry["severity"] = severity
            block["cp_minus_member"][indicator] = entry

        # (2) The endpoint contrast itself: ranking minus generation, within arm.
        for arm in ("cp", "member"):
            for sev, r_key, g_key, off in (
                ("lenient", "ranking_pair_success", "generation_pair_correct", 4),
                ("strict", "ranking_candidate_pair_top1", "generation_strict_pair_correct", 5),
            ):
                r_vals = [bool(merged[p][f"{arm}_{r_key}"]) for p in pids]
                g_vals = [bool(merged[p][f"{arm}_{g_key}"]) for p in pids]
                entry = paired_bootstrap_diff(
                    [float(v) for v in r_vals], [float(v) for v in g_vals],
                    resolve_seed(off, t_idx),
                )
                entry["mcnemar_exact_two_sided"] = mcnemar_exact_bool(r_vals, g_vals)
                entry["ranking_metric"] = r_key
                entry["generation_metric"] = g_key
                block["ranking_minus_generation"][f"{arm}_{sev}"] = entry

        results["per_template"][template] = block

    out_path = ROOT / "reports/mini_a5_s1_ranking_vs_generation_v1.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results["checks"], indent=2, sort_keys=True))
    print(f"\nwrote {out_path}")
    for template, block in results["per_template"].items():
        print(f"\n=== {template}  (n={block['n_pairs']})")
        for arm, rates in block["arm_rates"].items():
            print(f"  {arm:<7} " + "  ".join(f"{k}={v:.4f}" for k, v in rates.items()))
        for ind, e in block["cp_minus_member"].items():
            print(f"  CP-member {ind:<32} {e['point']:+.4f} [{e['ci95_low']:+.4f},{e['ci95_high']:+.4f}] "
                  f"excl0={e['excludes_zero']} mcnemar_p={e['mcnemar_exact_two_sided']['p_value']:.4g}")
        for key, e in block["ranking_minus_generation"].items():
            print(f"  rank-gen  {key:<32} {e['point']:+.4f} [{e['ci95_low']:+.4f},{e['ci95_high']:+.4f}] "
                  f"excl0={e['excludes_zero']} mcnemar_p={e['mcnemar_exact_two_sided']['p_value']:.4g}")


if __name__ == "__main__":
    sys.exit(main())
