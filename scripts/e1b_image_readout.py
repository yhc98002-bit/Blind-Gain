#!/usr/bin/env python3
"""E1b with-image column: canonical postprocess + S1/S2 readout.

The vlmevalkit harness emits a .pkl; the project's canonical per-item scoring
comes from scripts/postprocess_vlmeval_predictions.py, which is what produced the
base with-image rows. This runs that same step on every E1b image cell (CPU only,
no GPU), then compares each arm to the base column paired by item index.

S1 (secondary): A2-gray with-image accuracy falls below A1's -- corrosion visible
    beyond R19/geo3k.
S2 (secondary): trained arms >= base with images.

Same contract obligations as the blind readout: MathVista is mixed and is split
into MC and free-form; lenient and strict both reported; CIs are paired item
bootstrap.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RUNS = ROOT / "experiments/runs"
PY = ROOT / "artifacts/envs/vlmevalkit/bin/python"  # has openpyxl; the env the base column used
BASE = {
    "mmstar": RUNS / "vlmevalkit_postprocess_l10_mmstar3b_canonicalv2_final_20260711T132325Z/rows.jsonl",
    "mathvista": RUNS / "vlmevalkit_postprocess_l10_mathvista3b_canonicalv2_final_20260711T132325Z/rows.jsonl",
}
ARMS = ["a1_real", "a2_gray", "a2b_noimage", "a3_caption"]
SEEDS = [1, 2, 3]
RNG = np.random.default_rng(20260728)
REPS = 10000

# ----------------------------- 1. postprocess -------------------------------
postproc_fail = []
for d in sorted(RUNS.glob("vlmevalkit_e1b_*_image_an12_*")):
    rows_out = d / "rows.jsonl"
    if rows_out.is_file():
        continue
    # MMStar cells emit a .pkl, MathVista cells only an .xlsx (their native
    # scorer aborted for want of an OpenAI judge, after inference hadcompleted).
    # Either is fine: postprocess_vlmeval_predictions.py reads the prediction
    # and answer columns and applies canonical-v2 itself -- it never reads a
    # judge column, so both paths score identically to the base column.
    cands = [q for q in sorted(d.glob("work/*/T*/*.xlsx")) + sorted(d.glob("work/*/T*/*.pkl"))
             if "judge" not in q.name]
    if not cands:
        postproc_fail.append(f"{d.name}: no prediction workbook produced")
        continue
    pkls = cands
    cmd = [str(PY), str(ROOT / "scripts/postprocess_vlmeval_predictions.py"),
           "--input", str(pkls[0]),  # cands[0] is the RAW prediction workbook; [-1] would grab _exact_matching_result.pkl
           "--rows-output", str(rows_out),
           "--metrics-output", str(d / "metrics.json")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        postproc_fail.append(f"{d.name}: postprocess rc={r.returncode} :: "
                             f"{(r.stderr or r.stdout).strip().splitlines()[-1][:160]}")

if postproc_fail:
    print("POSTPROCESS FAILURES:")
    for f in postproc_fail:
        print("  -", f)


def load(p):
    return {str(json.loads(l)["index"]): json.loads(l)
            for l in Path(p).read_text().splitlines() if l.strip()}


def subsets(bench, base_rows):
    if bench == "mmstar":
        return {"all items (MC pooled)": sorted(base_rows)}
    mc = sorted(i for i, r in base_rows.items() if (r.get("option_labels") or []))
    ff = sorted(i for i, r in base_rows.items() if not (r.get("option_labels") or []))
    return {"MC pooled": mc, "free-form": ff}


def boot(a, b):
    n = len(a)
    idx = RNG.integers(0, n, size=(REPS, n))
    d = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


out = {"schema_version": "blind-gains.e1b-image.v1",
       "registration": "docs/registered_e1b_external_access_matrix_v1.md",
       "bootstrap": {"reps": REPS, "seed": 20260728, "unit": "item", "paired": True},
       "postprocess_failures": postproc_fail, "rows": [], "notes": []}

for bench, basep in BASE.items():
    if not Path(basep).is_file():
        out["notes"].append(f"{bench}: base with-image rows absent at {basep}")
        continue
    base_rows = load(basep)

    arm_rows = {}
    for arm in ARMS:
        per_seed = []
        for s in SEEDS:
            hits = sorted(RUNS.glob(f"vlmevalkit_e1b_{arm}_seed{s}_{bench}_image_an12_*/rows.jsonl"))
            if not hits:
                out["notes"].append(f"missing cell: {arm} seed{s} {bench}")
                continue
            per_seed.append(load(hits[-1]))
        if per_seed:
            arm_rows[arm] = per_seed
    if not arm_rows:
        continue

    for sub, ids in subsets(bench, base_rows).items():
        ids = [i for i in ids if all(i in ps for a in arm_rows.values() for ps in a)]
        if not ids:
            continue
        for metric in ("acc_final", "acc_strict"):
            bvec = np.array([float(base_rows[i][metric]) for i in ids])
            out["rows"].append({"benchmark": bench, "subset": sub, "metric": metric,
                                "arm": "BASE (frozen)", "n": len(ids),
                                "acc": float(bvec.mean()), "delta_vs_base": 0.0,
                                "ci95": [0.0, 0.0]})
            means = {}
            for arm, per_seed in arm_rows.items():
                vecs = [np.array([float(ps[i][metric]) for i in ids]) for ps in per_seed]
                avec = np.mean(vecs, axis=0)
                means[arm] = avec
                lo, hi = boot(avec, bvec)
                out["rows"].append({
                    "benchmark": bench, "subset": sub, "metric": metric, "arm": arm,
                    "n": len(ids), "seeds": len(vecs), "acc": float(avec.mean()),
                    "acc_per_seed": [float(v.mean()) for v in vecs],
                    "delta_vs_base": float(avec.mean() - bvec.mean()),
                    "ci95": [lo, hi], "excludes_zero": bool(lo > 0 or hi < 0)})
            # S1: A2-gray vs A1, paired on the same items
            if "a1_real" in means and "a2_gray" in means:
                lo, hi = boot(means["a2_gray"], means["a1_real"])
                d = float(means["a2_gray"].mean() - means["a1_real"].mean())
                out["rows"].append({
                    "benchmark": bench, "subset": sub, "metric": metric,
                    "arm": "S1: a2_gray - a1_real", "n": len(ids),
                    "acc": None, "delta_vs_base": d, "ci95": [lo, hi],
                    "excludes_zero": bool(lo > 0 or hi < 0)})

p = ROOT / "reports/e1b_image_readout_v1.json"
p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

print(f"\n{'bench':<10} {'subset':<22} {'metric':<10} {'arm':<24} {'n':>5} "
      f"{'acc':>7} {'Δ':>9} {'95% CI':>21} {'sig':>4}")
for r in out["rows"]:
    ci = "" if r["arm"] == "BASE (frozen)" else f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
    acc = "" if r["acc"] is None else f"{r['acc']:.4f}"
    print(f"{r['benchmark']:<10} {r['subset']:<22} {r['metric']:<10} {r['arm']:<24} "
          f"{r['n']:>5} {acc:>7} {r['delta_vs_base']:>+9.4f} {ci:>21} "
          f"{'yes' if r.get('excludes_zero') else '':>4}")
for n in out["notes"]:
    print("NOTE:", n)
print(f"\nwrote {p.relative_to(ROOT)}")
if postproc_fail:
    sys.exit(1)
