#!/usr/bin/env python3
"""Gate 0 — G0.1 to G0.4, from cached predictions only (EXPERIMENT_TODO 2A).

G0.1  Do A1's per-item gains concentrate on high-Delta-q items?
G0.2  Does A2b's image-present gain concentrate on low blind-solvability items?
      (this one freezes Paper 1's title claim)
G0.3  Overlap of the A1 / A2b newly-correct sets (Jaccard + permutation null)
G0.4  Answer-gain vs format-gain split of A2b's image-present gain

Base per-item comes from the guarded-rescore runs the seed readouts name as
geo_baselines; those reproduce the registered step-0 values exactly
(acc_final 0.1747, strict 0.0599, contract 0.4393). Delta-q uses the audit's
own per-item q_i, real minus none, on the identical rows.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
BOOT, PERM = 10000, 10000

GUARDED = {
    "real": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z/per_item.jsonl",
    "none": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_none_login_20260712T055030Z/per_item.jsonl",
}
ARMS = ("a1_real", "a2b_noimage", "a2_gray", "a3_caption")


def load(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


def key(r):
    return (r["problem"], tuple(r.get("image_sha256") or []))


def resolve_arm_runs():
    """arm -> {seed: per_item.jsonl}, sha256-verified, distinct runs, fail closed."""
    out = {a: {} for a in ARMS}
    for seed in (1, 2, 3):
        res = json.loads((ROOT / f"reports/pilot_4arm_seed{seed}_results_v1.json").read_text())
        audits = res["provenance"]["geo_audits"]
        if sorted(audits) != sorted(ARMS):
            raise SystemExit(f"seed {seed}: geo_audits arms {sorted(audits)}")
        for arm, rec in audits.items():
            blob = (ROOT / rec["path"]).read_bytes()
            if hashlib.sha256(blob).hexdigest() != rec["sha256"]:
                raise SystemExit(f"{arm} seed {seed}: audit sha256 mismatch")
            out[arm][seed] = json.loads(blob)["output"]
    seen = {}
    for arm, per in out.items():
        if sorted(per) != [1, 2, 3]:
            raise SystemExit(f"{arm}: seeds {sorted(per)}")
        for s, p in per.items():
            if p in seen:
                raise SystemExit(f"{arm}/s{s} reuses run of {seen[p]}")
            seen[p] = f"{arm}/s{s}"
    return out


base_real = {key(r): r for r in load(GUARDED["real"])}
base_none = {key(r): r for r in load(GUARDED["none"])}
arm_runs = resolve_arm_runs()

# item universe = the 601-row eval split, taken from any arm cell and verified
# identical across all twelve
ref = [key(r) for r in load(Path(arm_runs["a1_real"][1]).relative_to(ROOT).as_posix())]
ITEMS = list(ref)
if len(set(ITEMS)) != len(ITEMS):
    raise SystemExit("duplicate items in reference cell")

arm_items = {}
for arm, per in arm_runs.items():
    for seed, path in per.items():
        rows = {key(r): r for r in load(Path(path).relative_to(ROOT).as_posix())}
        if set(rows) != set(ITEMS):
            raise SystemExit(f"{arm} s{seed}: item set differs from reference")
        arm_items[(arm, seed)] = rows

# Image-present (crossed) cells from D3. Each arm's own geo_audit is its MATCHED
# condition -- A2b's is `none`, A2's is `gray` -- so a matched cell cannot answer
# "does the image-present gain concentrate on ...". Those questions require the
# arm evaluated under `real`, which is exactly the D3 crossed cell.
CROSSED = {
    ("a1_real", 1): "d2_testtime_a1_seed1_step100_real_an12_gpu4_20260726T143942Z",
    ("a1_real", 2): "d2_testtime_a1_seed2_step100_real_an12_gpu7_20260726T144048Z",
    ("a1_real", 3): "d2_testtime_a1_seed3_step100_real_an12_gpu4_20260727T082313Z",
    ("a2b_noimage", 1): "d2_testtime_a2b_seed1_step100_real_an12_gpu6_20260726T145754Z",
    ("a2b_noimage", 2): "d2_testtime_a2b_seed2_step100_real_an12_gpu7_20260726T145815Z",
    ("a2b_noimage", 3): "d2_testtime_a2b_seed3_step100_real_an12_gpu7_20260727T082419Z",
    ("a2_gray", 1): "d2_testtime_a2_seed1_step100_real_an12_gpu4_20260727T085251Z",
    ("a2_gray", 2): "d2_testtime_a2_seed2_step100_real_an12_gpu7_20260727T085358Z",
    ("a2_gray", 3): "d2_testtime_a2_seed3_step100_real_an12_gpu4_20260727T091106Z",
    ("a3_caption", 1): "d2_testtime_a3_seed1_step100_real_an12_gpu5_20260727T094941Z",
    ("a3_caption", 2): "d2_testtime_a3_seed2_step100_real_an12_gpu4_20260727T095814Z",
    ("a3_caption", 3): "d2_testtime_a3_seed3_step100_real_an12_gpu4_20260727T102811Z",
}
crossed_items = {}
for (arm, seed), run in CROSSED.items():
    man = json.loads((ROOT / f"experiments/runs/{run}/run_manifest.json").read_text())
    if man.get("status") != "complete":
        raise SystemExit(f"crossed {arm} s{seed}: status {man.get('status')}")
    rows = {key(r): r for r in load(f"experiments/runs/{run}/predictions.jsonl")}
    if set(rows) != set(ITEMS):
        raise SystemExit(f"crossed {arm} s{seed}: item set differs from reference")
    conds = {r["condition"] for r in rows.values()}
    if conds != {"real"}:
        raise SystemExit(f"crossed {arm} s{seed}: conditions {conds}")
    crossed_items[(arm, seed)] = rows
report_crossed = {f"{a}|s{s}": r for (a, s), r in CROSSED.items()}

missing = [k for k in ITEMS if k not in base_real or k not in base_none]
if missing:
    raise SystemExit(f"{len(missing)} items missing from guarded rescore")

# --- base and delta-q vectors -------------------------------------------------
b_final = np.array([float(bool(base_real[k]["greedy_canonical_correct"])) for k in ITEMS])
b_strict = np.array([float(bool(base_real[k]["greedy_acc_strict"])) for k in ITEMS])
b_contract = np.array([float(bool(base_real[k]["greedy_contract_valid"])) for k in ITEMS])
q_real = np.array([float(base_real[k]["q_i"]) for k in ITEMS])
q_blind = np.array([float(base_none[k]["q_i"]) for k in ITEMS])
dq = q_real - q_blind

report = {
    "schema_version": 1,
    "n_items": len(ITEMS),
    "base_check": {
        "acc_final": float(b_final.mean()), "acc_strict": float(b_strict.mean()),
        "contract_valid": float(b_contract.mean()),
        "registered": {"acc_final": 0.1747, "acc_strict": 0.0599, "contract_valid": 0.4393},
    },
    "delta_q": {"mean": float(dq.mean()), "min": float(dq.min()), "max": float(dq.max()),
                "q_blind_mean": float(q_blind.mean())},
    "arm_runs": {a: {str(s): p for s, p in per.items()} for a, per in arm_runs.items()},
}


def arm_final(arm, seed, crossed=False):
    rows = (crossed_items if crossed else arm_items)[(arm, seed)]
    return np.array([float(bool(rows[k]["acc_final"])) for k in ITEMS])


def arm_field(arm, seed, field, crossed=False):
    rows = (crossed_items if crossed else arm_items)[(arm, seed)]
    return np.array([float(bool(rows[k][field])) for k in ITEMS])


def boot_mean_ci(v):
    d = RNG.integers(0, len(v), size=(BOOT, len(v)))
    b = v[d].mean(axis=1)
    return float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def concentration(gain, strat, label, n_bins=3):
    """Mean per-item gain within strata of `strat`, plus a rank correlation."""
    qs = np.quantile(strat, np.linspace(0, 1, n_bins + 1))
    qs[0], qs[-1] = -np.inf, np.inf
    bins = []
    for i in range(n_bins):
        m = (strat > qs[i]) & (strat <= qs[i + 1]) if i else (strat <= qs[1])
        if m.sum() == 0:
            bins.append(None)
            continue
        mean, lo, hi = boot_mean_ci(gain[m])
        bins.append({"n": int(m.sum()), "strat_lo": float(qs[i] if i else strat.min()),
                     "strat_hi": float(qs[i + 1] if i < n_bins - 1 else strat.max()),
                     "mean_gain": mean, "ci95": [lo, hi]})
    # Spearman without scipy
    def rank(x):
        o = np.argsort(np.argsort(x, kind="mergesort"), kind="mergesort").astype(float)
        return o
    rg, rs = rank(gain), rank(strat)
    rho = float(np.corrcoef(rg, rs)[0, 1])
    # permutation p for rho
    cnt = 0
    for _ in range(2000):
        if abs(np.corrcoef(rg, RNG.permutation(rs))[0, 1]) >= abs(rho):
            cnt += 1
    return {"label": label, "bins": bins, "spearman_rho": rho,
            "spearman_perm_p": (cnt + 1) / 2001}


# --- G0.1 / G0.2 --------------------------------------------------------------
gains, matched_gains = {}, {}
for arm in ARMS:
    gm = np.mean([arm_final(arm, s) - b_final for s in (1, 2, 3)], axis=0)
    gc = np.mean([arm_final(arm, s, crossed=True) - b_final for s in (1, 2, 3)], axis=0)
    matched_gains[arm], gains[arm] = gm, gc
    m, lo, hi = boot_mean_ci(gc)
    report.setdefault("mean_gain_image_present", {})[arm] = {"mean": m, "ci95": [lo, hi]}
    m2, lo2, hi2 = boot_mean_ci(gm)
    report.setdefault("mean_gain_matched_condition", {})[arm] = {
        "mean": m2, "ci95": [lo2, hi2],
        "note": "arm evaluated in its own training condition; differenced against base real",
    }
report["crossed_runs"] = report_crossed

report["G0_1_a1_gain_by_delta_q"] = concentration(gains["a1_real"], dq, "A1 image-present gain vs delta-q")
report["G0_1_a2b_gain_by_delta_q"] = concentration(gains["a2b_noimage"], dq, "A2b image-present gain vs delta-q")
report["G0_2_a2b_gain_by_blind_solvability"] = concentration(
    gains["a2b_noimage"], q_blind, "A2b image-present gain vs blind solvability")
report["G0_2_a1_gain_by_blind_solvability"] = concentration(
    gains["a1_real"], q_blind, "A1 image-present gain vs blind solvability (comparator)")

# --- G0.3 newly-correct overlap ----------------------------------------------
g03 = {"per_seed": [], "note": "newly correct = base wrong and arm right, on acc_final"}
for seed in (1, 2, 3):
    a1 = (arm_final("a1_real", seed, crossed=True) > 0) & (b_final == 0)
    a2b = (arm_final("a2b_noimage", seed, crossed=True) > 0) & (b_final == 0)
    inter = int((a1 & a2b).sum())
    union = int((a1 | a2b).sum())
    jac = inter / union if union else float("nan")
    # permutation null: shuffle a2b membership among base-wrong items
    pool = np.where(b_final == 0)[0]
    a1_idx = set(np.where(a1)[0])
    k = int(a2b.sum())
    null = []
    for _ in range(PERM):
        pick = set(RNG.choice(pool, size=k, replace=False).tolist())
        i2 = len(a1_idx & pick)
        u2 = len(a1_idx | pick)
        null.append(i2 / u2 if u2 else 0.0)
    null = np.array(null)
    g03["per_seed"].append({
        "seed": seed, "n_a1_new": int(a1.sum()), "n_a2b_new": k,
        "intersection": inter, "union": union, "jaccard": jac,
        "null_mean": float(null.mean()),
        "p_ge": float(((null >= jac).sum() + 1) / (PERM + 1)),
    })
report["G0_3_newly_correct_overlap"] = g03

# --- G0.4 answer vs format split ---------------------------------------------
g04 = {"note": "AnswerGain = delta acc_final; StrictGain = delta acc_strict; "
               "G_format = StrictGain - AnswerGain", "per_arm": {}}
for arm in ARMS:
    rows = []
    for seed in (1, 2, 3):
        af = float((arm_final(arm, seed, crossed=True) - b_final).mean())
        st = float((arm_field(arm, seed, "acc_strict", crossed=True) - b_strict).mean())
        cv = float((arm_field(arm, seed, "contract_valid", crossed=True) - b_contract).mean())
        rows.append({"seed": seed, "answer_gain": af, "strict_gain": st,
                     "format_gain": st - af, "contract_valid_gain": cv})
    g04["per_arm"][arm] = {
        "per_seed": rows,
        "mean_answer_gain": float(np.mean([r["answer_gain"] for r in rows])),
        "mean_strict_gain": float(np.mean([r["strict_gain"] for r in rows])),
        "mean_format_gain": float(np.mean([r["format_gain"] for r in rows])),
        "mean_contract_valid_gain": float(np.mean([r["contract_valid_gain"] for r in rows])),
    }
report["G0_4_answer_vs_format"] = g04

(ROOT / "reports/gate0_stratification_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

print(f"n={len(ITEMS)}  base acc_final={b_final.mean():.4f} (reg 0.1747) "
      f"strict={b_strict.mean():.4f} (reg 0.0599) contract={b_contract.mean():.4f} (reg 0.4393)")
print(f"delta-q mean={dq.mean():.4f}  q_blind mean={q_blind.mean():.4f}")
for arm in ARMS:
    v = report["mean_gain_image_present"][arm]
    w = report["mean_gain_matched_condition"][arm]
    print(f"  {arm:14s} image-present {v['mean']:+.4f} [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
          f"   matched {w['mean']:+.4f}")
for name in ("G0_1_a1_gain_by_delta_q", "G0_2_a2b_gain_by_blind_solvability"):
    r = report[name]
    cells = " | ".join(f"n={b['n']} gain={b['mean_gain']:+.3f}" for b in r["bins"] if b)
    print(f"{name}: {cells}  rho={r['spearman_rho']:+.3f} p={r['spearman_perm_p']:.4f}")
for s in g03["per_seed"]:
    print(f"G0.3 seed{s['seed']}: jaccard={s['jaccard']:.3f} null={s['null_mean']:.3f} p={s['p_ge']:.4f}")
print("wrote reports/gate0_stratification_v1.json")
