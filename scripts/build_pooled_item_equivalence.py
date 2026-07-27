#!/usr/bin/env python3
"""Pooled item-level equivalence for the FlipTrack geometry endpoint.

Addresses the plan's P1: the registered +/-0.05 SESOI was evaluated with a
seed-level normal approximation at n=3.  This re-evaluates it on the paired
item-level data (600 pairs x 3 seeds) using a cluster bootstrap over pair_id,
which respects the fact that the same pairs recur in every seed.

Also emits contract validity as a first-class per-arm result and a power
analysis for the equivalence null.
"""
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
GEO = "geometry_coordinate_indexing"
SESOI = 0.05
BOOT = 20000
RNG = np.random.default_rng(20260727)

BASE_SHARDS = ("experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_"
               "an29_20260710T142716Z/shards/*.jsonl")
ARMS = {"a1_real": "a1", "a2_gray": "a2", "a2b_noimage": "a2b", "a3_caption": "a3"}


def load_rows(pattern):
    rows = []
    for f in sorted(glob.glob(str(ROOT / pattern))):
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def geo_index(rows, label):
    """pair_id -> row, restricted to the registered geometry slice."""
    geo = [r for r in rows if r.get("category") == GEO]
    idx = {}
    for r in geo:
        pid = r["pair_id"]
        if pid in idx:
            raise SystemExit(f"FAIL {label}: duplicate pair_id {pid}")
        idx[pid] = r
    if len(idx) != 600:
        raise SystemExit(f"FAIL {label}: {len(idx)} geometry pairs, expected 600")
    return idx


def resolve_arm_runs():
    """arm -> {seed: eval_run_dir}, resolved from the sealed per-seed readouts.

    Fails closed on a missing arm, a non-step100 audit, or a sha256 mismatch --
    a silent seed-2 audit inheritance already reached a committed readout once.
    """
    import hashlib

    out = {a: {} for a in ARMS}
    for seed in (1, 2, 3):
        res = json.loads((ROOT / f"reports/pilot_4arm_seed{seed}_results_v1.json").read_text())
        markers = res["provenance"]["r19_markers"]
        if sorted(markers) != sorted(ARMS):
            raise SystemExit(f"FAIL seed {seed}: r19_markers arms {sorted(markers)}")
        for arm, per_step in markers.items():
            rec = per_step["100"]
            path = rec["path"]
            if "step100" not in path:
                raise SystemExit(f"FAIL {arm} seed {seed}: not a step100 marker ({path})")
            blob = (ROOT / path).read_bytes()
            got = hashlib.sha256(blob).hexdigest()
            if got != rec["sha256"]:
                raise SystemExit(f"FAIL {arm} seed {seed}: sha256 mismatch on {path}")
            out[arm][seed] = json.loads(blob)["evaluation_run"]
    # every one of the 12 cells must be a distinct run directory
    seen = {}
    for arm, per in out.items():
        if sorted(per) != [1, 2, 3]:
            raise SystemExit(f"FAIL: {arm} resolved seeds {sorted(per)}")
        for seed, run in per.items():
            if run in seen:
                raise SystemExit(f"FAIL: {arm}/seed{seed} reuses run of {seen[run]}")
            seen[run] = f"{arm}/seed{seed}"
    return out


def contract_valid(row):
    """Pair-level contract validity; older shards carry only the per-member flags."""
    if "contract_valid" in row:
        return float(row["contract_valid"])
    a, b = row.get("contract_valid_a"), row.get("contract_valid_b")
    if a is None or b is None:
        return None
    return float(bool(a) and bool(b))


def mean_cv(idx, pids):
    vals = [contract_valid(idx[p]) for p in pids]
    return None if any(v is None for v in vals) else float(np.mean(vals))


def cluster_bootstrap(per_pair_delta, pids):
    """Resample pair_ids; each carries its seed-averaged delta."""
    vals = np.array([per_pair_delta[p] for p in pids])
    n = len(vals)
    draws = RNG.integers(0, n, size=(BOOT, n))
    return vals[draws].mean(axis=1)


def main():
    base_rows = load_rows(BASE_SHARDS)
    base = geo_index(base_rows, "base")
    pids = sorted(base)
    arm_runs = resolve_arm_runs()

    report = {"schema_version": 1, "sesoi": SESOI, "n_pairs": len(pids),
              "n_seeds": 3, "bootstrap_draws": BOOT,
              "method": ("cluster bootstrap over pair_id on the seed-averaged "
                         "paired delta; 600 clusters, 3 seeds each"),
              "base_shards": BASE_SHARDS, "arms": {}, "contract_validity": {},
              "arm_runs": {a: dict(s) for a, s in arm_runs.items()}}

    base_cv = mean_cv(base, pids)
    report["contract_validity"]["base"] = {"mean": base_cv}

    for arm, per_seed in arm_runs.items():
        d_final, d_strict, cv = {p: [] for p in pids}, {p: [] for p in pids}, []
        seed_means = []
        for seed in (1, 2, 3):
            rows = load_rows(f"{per_seed[seed]}/shards/*.jsonl")
            idx = geo_index(rows, f"{arm} seed{seed}")
            if sorted(idx) != pids:
                raise SystemExit(f"FAIL {arm} seed{seed}: pair_id set differs from base")
            for p in pids:
                d_final[p].append(float(idx[p]["pair_correct"]) - float(base[p]["pair_correct"]))
                d_strict[p].append(float(idx[p]["strict_pair_correct"])
                                   - float(base[p]["strict_pair_correct"]))
            seed_means.append(float(np.mean([d_final[p][-1] for p in pids])))
            cv.append(mean_cv(idx, pids))

        entry = {"per_seed_delta_final": seed_means}
        for name, dd in (("final", d_final), ("strict", d_strict)):
            avg = {p: float(np.mean(dd[p])) for p in pids}
            boots = cluster_bootstrap(avg, pids)
            mean = float(np.mean(list(avg.values())))
            lo95, hi95 = np.percentile(boots, [2.5, 97.5])
            lo90, hi90 = np.percentile(boots, [5.0, 95.0])
            se = float(np.std(boots, ddof=1))
            # bootstrap TOST: both one-sided nulls must be rejected
            p_upper = float(np.mean(boots >= SESOI))
            p_lower = float(np.mean(boots <= -SESOI))
            entry[name] = {
                "pooled_mean_delta": mean,
                "ci95": [float(lo95), float(hi95)],
                "ci90_tost": [float(lo90), float(hi90)],
                "bootstrap_se": se,
                "tost_p_upper": p_upper, "tost_p_lower": p_lower,
                "equivalence_established": bool(lo90 > -SESOI and hi90 < SESOI),
                "ci95_excludes_zero": bool(lo95 > 0 or hi95 < 0),
                # power to reject a true |delta| = SESOI at 80%, two-sided a=.05
                "min_detectable_effect_80pct_power": float(2.802 * se),
            }
        entry["contract_valid_per_seed"] = cv
        ok = all(v is not None for v in cv)
        entry["contract_valid_mean"] = float(np.mean(cv)) if ok else None
        entry["contract_valid_delta_vs_base"] = (
            float(np.mean(cv) - base_cv) if ok and base_cv is not None else None)
        report["arms"][arm] = entry
        report["contract_validity"][arm] = {
            "mean": entry["contract_valid_mean"],
            "per_seed": cv,
            "delta_vs_base": entry["contract_valid_delta_vs_base"],
        }

    out = ROOT / "reports/pooled_item_equivalence_v1.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}")
    for arm, e in report["arms"].items():
        f = e["final"]
        print(f"{arm:14s} pooled={f['pooled_mean_delta']:+.4f} "
              f"ci95=[{f['ci95'][0]:+.4f},{f['ci95'][1]:+.4f}] "
              f"tost90=[{f['ci90_tost'][0]:+.4f},{f['ci90_tost'][1]:+.4f}] "
              f"equiv={f['equivalence_established']} "
              f"cv={e['contract_valid_mean']}")
    print(f"base contract_valid={base_cv}")


if __name__ == "__main__":
    main()
