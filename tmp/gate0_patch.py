#!/usr/bin/env python3
"""Patch Gate 0 to use the D3 crossed real-condition cells for image-present gains."""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/build_gate0_stratification.py")
t = p.read_text()

old_universe = '''arm_items = {}
for arm, per in arm_runs.items():
    for seed, path in per.items():
        rows = {key(r): r for r in load(Path(path).relative_to(ROOT).as_posix())}
        if set(rows) != set(ITEMS):
            raise SystemExit(f"{arm} s{seed}: item set differs from reference")
        arm_items[(arm, seed)] = rows'''

new_universe = '''arm_items = {}
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
    ("a1_real", 1): "d2_testtime_a1_seed1_step100_real_an12_gpu4_20260726T143831Z",
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
report_crossed = {f"{a}|s{s}": r for (a, s), r in CROSSED.items()}'''

assert t.count(old_universe) == 1
t = t.replace(old_universe, new_universe, 1)

old_helpers = '''def arm_final(arm, seed):
    rows = arm_items[(arm, seed)]
    return np.array([float(bool(rows[k]["acc_final"])) for k in ITEMS])


def arm_field(arm, seed, field):
    rows = arm_items[(arm, seed)]
    return np.array([float(bool(rows[k][field])) for k in ITEMS])'''

new_helpers = '''def arm_final(arm, seed, crossed=False):
    rows = (crossed_items if crossed else arm_items)[(arm, seed)]
    return np.array([float(bool(rows[k]["acc_final"])) for k in ITEMS])


def arm_field(arm, seed, field, crossed=False):
    rows = (crossed_items if crossed else arm_items)[(arm, seed)]
    return np.array([float(bool(rows[k][field])) for k in ITEMS])'''

assert t.count(old_helpers) == 1
t = t.replace(old_helpers, new_helpers, 1)

# gains: keep matched for reference, add crossed (image-present) as the Gate-0 basis
old_gain = '''gains = {}
for arm in ARMS:
    g = np.mean([arm_final(arm, s) - b_final for s in (1, 2, 3)], axis=0)
    gains[arm] = g
    m, lo, hi = boot_mean_ci(g)
    report.setdefault("mean_gain", {})[arm] = {"mean": m, "ci95": [lo, hi]}

report["G0_1_a1_gain_by_delta_q"] = concentration(gains["a1_real"], dq, "A1 gain vs delta-q")
report["G0_1_a2b_gain_by_delta_q"] = concentration(gains["a2b_noimage"], dq, "A2b gain vs delta-q")
report["G0_2_a2b_gain_by_blind_solvability"] = concentration(
    gains["a2b_noimage"], q_blind, "A2b image-present gain vs blind solvability")
report["G0_2_a1_gain_by_blind_solvability"] = concentration(
    gains["a1_real"], q_blind, "A1 gain vs blind solvability (comparator)")'''

new_gain = '''gains, matched_gains = {}, {}
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
    gains["a1_real"], q_blind, "A1 image-present gain vs blind solvability (comparator)")'''

assert t.count(old_gain) == 1
t = t.replace(old_gain, new_gain, 1)

t = t.replace('''    a1 = (arm_final("a1_real", seed) > 0) & (b_final == 0)
    a2b = (arm_final("a2b_noimage", seed) > 0) & (b_final == 0)''',
              '''    a1 = (arm_final("a1_real", seed, crossed=True) > 0) & (b_final == 0)
    a2b = (arm_final("a2b_noimage", seed, crossed=True) > 0) & (b_final == 0)''')

t = t.replace('''        af = float((arm_final(arm, seed) - b_final).mean())
        st = float((arm_field(arm, seed, "acc_strict") - b_strict).mean())
        cv = float((arm_field(arm, seed, "contract_valid") - b_contract).mean())''',
              '''        af = float((arm_final(arm, seed, crossed=True) - b_final).mean())
        st = float((arm_field(arm, seed, "acc_strict", crossed=True) - b_strict).mean())
        cv = float((arm_field(arm, seed, "contract_valid", crossed=True) - b_contract).mean())''')

t = t.replace('''    v = report["mean_gain"][arm]
    print(f"  {arm:14s} mean gain {v['mean']:+.4f} [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]")''',
              '''    v = report["mean_gain_image_present"][arm]
    w = report["mean_gain_matched_condition"][arm]
    print(f"  {arm:14s} image-present {v['mean']:+.4f} [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
          f"   matched {w['mean']:+.4f}")''')

p.write_text(t)
print("patched build_gate0_stratification.py")
