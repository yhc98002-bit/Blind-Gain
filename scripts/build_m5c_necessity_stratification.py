#!/usr/bin/env python3
"""M5c item 5 -- stratify the geo3k step-100 -> step-400 change by VISUAL NECESSITY.

Reuses the Gate 0 stratification definitions verbatim (reports/gate0_stratification_v1.md,
scripts/build_gate0_stratification.py, scripts/build_g02_headroom_control.py). Nothing
about the binning rule is invented here; both rules are reproduced from Gate 0 code and
checked against the numbers Gate 0 published.

Outputs: reports/m5c_necessity_stratification_v1.json / .md
"""
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

from src.eval.blind_solvability import score_greedy_item_pilot  # noqa: E402
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402

SEED = 20260729
BOOT = 10000
PERM = 10000
RNG = np.random.default_rng(SEED)
RNG_ORDER = []  # documented consumption order of the single seeded stream

SUBSTRATE = "reports/m5c_item_substrate_v1.jsonl"

# --- necessity source: Gate 0's own inputs, base model, guarded rescore ------------
NEC = {
    "real": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z/per_item.jsonl",
    "none": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_none_login_20260712T055030Z/per_item.jsonl",
}
# --- step-100 checkpoint under real + blind conditions (for the gap column) --------
STEP100 = {
    "real": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl",
    "none": "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_none_an29_20260712T102011Z/per_item.jsonl",
    "gray": "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_gray_an12_20260712T101335Z/per_item.jsonl",
    "noise": "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_noise_an12_20260712T101335Z/per_item.jsonl",
    "caption": "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_caption_an29_20260712T102011Z/per_item.jsonl",
}
STEP400_REAL_RUN = "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z"


def sha256(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


def manifest(run_rel):
    return json.loads((ROOT / run_rel / "run_manifest.json").read_text())


rep = {
    "schema_version": "blind-gains.m5c-necessity-stratification.v1",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_hash": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip(),
    "rng": {"seed": SEED, "bootstrap_draws": BOOT, "permutation_draws": PERM,
            "note": "one numpy default_rng(20260729) stream, consumed in the order "
                    "recorded in rng.consumption_order"},
}

# =====================================================================================
# 1. ADOPTED DEFINITIONS -- quoted from Gate 0, not invented here
# =====================================================================================
rep["adopted_definitions"] = {
    "primary": {
        "name": "delta_q terciles (Gate 0 G0.1)",
        "source_report": "reports/gate0_stratification_v1.md",
        "source_code": "scripts/build_gate0_stratification.py (function `concentration`, n_bins=3)",
        "quote_from_gate0_md": (
            "Δq = q_real − q_blind per item, taken from the registered blind "
            "reward-opportunity audit's own `q_i`. Terciles of Δq, mean per-item "
            "image-present gain in each"),
        "quote_from_gate0_docstring": (
            "Delta-q uses the audit's own per-item q_i, real minus none, on the identical rows."),
        "operational_rule": (
            "q_real = q_i from the guarded-rescore `real` per_item.jsonl; q_blind = q_i from "
            "the guarded-rescore `none` per_item.jsonl (base model, Jeffreys-smoothed). "
            "delta_q = q_real - q_blind. Bin edges = np.quantile(delta_q, [0,1/3,2/3,1]) with "
            "the outer edges opened to +/-inf; bin 0 is delta_q <= e1, bin i>0 is "
            "e_i < delta_q <= e_{i+1}. Identical code path to Gate 0."),
        "label_map": {"bin0_low_delta_q": "blind_solvable", "bin1_mid_delta_q": "intermediate",
                      "bin2_high_delta_q": "image_necessary"},
        "label_caveat": (
            "Gate 0 never attached the words blind-solvable / image-necessary to these "
            "terciles; it called them low/mid/high Δq. The low-Δq bin means 'the image "
            "bought no measured reward opportunity', which is satisfied both by items the base "
            "model solves blind and by items it solves under no condition. q_blind and q_real "
            "are reported per bin so this is visible."),
    },
    "secondary": {
        "name": "blind-answerable split (Gate 0 G0.2 headroom control)",
        "source_report": "reports/gate0_stratification_v1.md",
        "source_code": "scripts/build_g02_headroom_control.py lines 39-42",
        "quote_from_gate0_md": (
            "`q_blind` is Jeffreys-smoothed, so items with no observed blind success sit at "
            "the floor 0.1387. The split is therefore **blind-answerable** (≥1 observed "
            "blind success, n=117) versus **not** (n=484)."),
        "operational_rule": (
            "FLOOR = min(q_blind) over the 601 eval items; blind_answerable = q_blind > FLOOR + 1e-9."),
        "why_reported": (
            "This is Gate 0's only literal 'blind-solvable' definition. It is binary, so it "
            "cannot produce an 'intermediate' bin; it is reported alongside, not merged (I13)."),
    },
}

# =====================================================================================
# 2. LOAD + JOIN
# =====================================================================================
sub_rows = load(SUBSTRATE)
sub = {}
dups = []
for r in sub_rows:
    k = (r["split"], int(r["row_index"]))
    if k in sub:
        dups.append(k)
    sub[k] = r
if dups:
    raise SystemExit(f"duplicate substrate keys: {dups[:5]}")
if any(r["split"] != "test" for r in sub_rows):
    raise SystemExit("substrate contains non-test rows")

nec_rows = {}
for cond, path in NEC.items():
    allrows = load(path)
    test = [r for r in allrows if r["split"] == "test"]
    d = {}
    for r in test:
        k = (r["split"], int(r["row_index"]))
        if k in d:
            raise SystemExit(f"duplicate necessity key {k} in {cond}")
        d[k] = r
    nec_rows[cond] = d
    rep.setdefault("necessity_source", {})[cond] = {
        "run": str(Path(path).parent), "per_item_sha256": sha256(path),
        "rows_total": len(allrows), "rows_test": len(test),
        "rows_excluded_non_test": len(allrows) - len(test),
        "model_revision": manifest(Path(path).parent)["model_revision"],
        "condition_field_values": sorted({r["condition"] for r in allrows}),
        "data_manifest": manifest(Path(path).parent)["data_manifest"],
        "data_manifest_hash": manifest(Path(path).parent)["data_manifest_hash"],
        "rescore_source_run": manifest(Path(path).parent).get("rescore_source_run"),
        "parser_version": manifest(Path(path).parent)["parser_version"],
        "prompt_contract_sha256": manifest(Path(path).parent)["prompt_contract_sha256"],
    }

ITEMS = sorted(sub.keys(), key=lambda k: k[1])
n = len(ITEMS)

join = {"n_substrate": len(sub), "n_necessity_real_test": len(nec_rows["real"]),
        "n_necessity_none_test": len(nec_rows["none"])}
join["n_joined"] = sum(1 for k in ITEMS if k in nec_rows["real"] and k in nec_rows["none"])
join["join_rate"] = join["n_joined"] / n
join["substrate_keys_missing_from_necessity"] = [
    f"{a}:{b}" for (a, b) in ITEMS
    if (a, b) not in nec_rows["real"] or (a, b) not in nec_rows["none"]][:20]
join["necessity_test_keys_missing_from_substrate"] = [
    f"{a}:{b}" for (a, b) in sorted(nec_rows["real"]) if (a, b) not in sub][:20]
# cross-field identity checks on the joined rows
mism = {"image_sha256_sub_vs_real": 0, "image_sha256_sub_vs_none": 0,
        "ground_truth_sub_vs_real": 0, "ground_truth_sub_vs_none": 0,
        "problem_real_vs_none": 0, "image_sha256_real_vs_none": 0}
for k in ITEMS:
    rr, rn, rs = nec_rows["real"][k], nec_rows["none"][k], sub[k]
    if list(rs.get("image_sha256") or []) != list(rr.get("image_sha256") or []):
        mism["image_sha256_sub_vs_real"] += 1
    if list(rs.get("image_sha256") or []) != list(rn.get("image_sha256") or []):
        mism["image_sha256_sub_vs_none"] += 1
    if str(rs["ground_truth"]) != str(rr["ground_truth"]):
        mism["ground_truth_sub_vs_real"] += 1
    if str(rs["ground_truth"]) != str(rn["ground_truth"]):
        mism["ground_truth_sub_vs_none"] += 1
    if rr["problem"] != rn["problem"]:
        mism["problem_real_vs_none"] += 1
    if list(rr.get("image_sha256") or []) != list(rn.get("image_sha256") or []):
        mism["image_sha256_real_vs_none"] += 1
join["cross_field_mismatch_counts"] = mism
join["note_qid"] = ("qid is null on every substrate row and on every necessity row, so a qid "
                    "arm of the identity check is vacuous and is not claimed as a check.")
join["qid_null_counts"] = {
    "substrate": sum(1 for k in ITEMS if sub[k].get("qid") is None),
    "necessity_real": sum(1 for k in ITEMS if nec_rows["real"][k].get("qid") is None),
    "necessity_none": sum(1 for k in ITEMS if nec_rows["none"][k].get("qid") is None),
}
rep["join"] = join

rep["substrate"] = {"path": SUBSTRATE, "sha256": sha256(SUBSTRATE), "rows": len(sub_rows),
                    "item_key_definition": "(split, row_index) on the Geometry3K test split"}

# the two necessity arms were produced under different data_manifest_hash values; item
# identity is therefore asserted from the row fields, not from the manifest hash
rep["join"]["necessity_arm_manifest_hash_differs"] = (
    rep["necessity_source"]["real"]["data_manifest_hash"] !=
    rep["necessity_source"]["none"]["data_manifest_hash"])
rep["join"]["necessity_arm_manifest_hash_note"] = (
    "The real and none guarded-rescore arms carry different data_manifest_hash values. "
    "This is inherited from Gate 0's inputs, which are used unchanged. Item identity across "
    "the two arms is therefore asserted from the row fields directly: problem and "
    "image_sha256 are equal on 601/601 joined test rows (see cross_field_mismatch_counts).")

# =====================================================================================
# 3. BIN
# =====================================================================================
q_real = np.array([float(nec_rows["real"][k]["q_i"]) for k in ITEMS])
q_blind = np.array([float(nec_rows["none"][k]["q_i"]) for k in ITEMS])
dq = q_real - q_blind

# --- Gate 0 `concentration` binning, reproduced exactly -----------------------------
qs = np.quantile(dq, np.linspace(0, 1, 4))
edges_raw = [float(x) for x in qs]
qs[0], qs[-1] = -np.inf, np.inf
masks = []
for i in range(3):
    m = (dq > qs[i]) & (dq <= qs[i + 1]) if i else (dq <= qs[1])
    masks.append(m)

BIN_NAMES = ["blind_solvable", "intermediate", "image_necessary"]
BIN_DESC = ["low delta_q tercile", "mid delta_q tercile", "high delta_q tercile"]

# --- Gate 0 G0.2 blind-answerable, reproduced exactly -------------------------------
FLOOR = float(np.min(q_blind))
answerable = q_blind > FLOOR + 1e-9

rep["stratification"] = {
    "delta_q": {"mean": float(dq.mean()), "min": float(dq.min()), "max": float(dq.max()),
                "q_blind_mean": float(q_blind.mean()), "q_real_mean": float(q_real.mean()),
                "tercile_edges_raw": edges_raw,
                "n_items_with_delta_q_exactly_zero": int((dq == 0).sum())},
    "bins": [],
    "blind_answerable": {"jeffreys_floor": FLOOR, "n_blind_answerable": int(answerable.sum()),
                         "n_not_blind_answerable": int((~answerable).sum())},
}
for i, m in enumerate(masks):
    rep["stratification"]["bins"].append({
        "index": i, "label": BIN_NAMES[i], "gate0_description": BIN_DESC[i],
        "n": int(m.sum()),
        "delta_q_lo": float(qs[i] if i else dq.min()),
        "delta_q_hi": float(qs[i + 1] if i < 2 else dq.max()),
        "delta_q_mean": float(dq[m].mean()),
        "q_real_mean": float(q_real[m].mean()), "q_blind_mean": float(q_blind[m].mean()),
        "n_blind_answerable_in_bin": int(answerable[m].sum()),
    })

# --- provenance check: do these reproduce Gate 0's published bins? ------------------
g0 = json.loads((ROOT / "reports/gate0_stratification_v1.json").read_text())
g0bins = g0["G0_1_a1_gain_by_delta_q"]["bins"]
rep["gate0_reproduction_check"] = {
    "bin_n_here": [int(m.sum()) for m in masks],
    "bin_n_gate0": [b["n"] for b in g0bins],
    "bin_n_match": [int(m.sum()) for m in masks] == [b["n"] for b in g0bins],
    "bin_edges_here": [[float(qs[i] if i else dq.min()),
                        float(qs[i + 1] if i < 2 else dq.max())] for i in range(3)],
    "bin_edges_gate0": [[b["strat_lo"], b["strat_hi"]] for b in g0bins],
    "bin_edges_match": all(
        abs(float(qs[i] if i else dq.min()) - g0bins[i]["strat_lo"]) < 1e-12 and
        abs(float(qs[i + 1] if i < 2 else dq.max()) - g0bins[i]["strat_hi"]) < 1e-12
        for i in range(3)),
    "delta_q_summary_here": {"mean": float(dq.mean()), "min": float(dq.min()),
                             "max": float(dq.max()), "q_blind_mean": float(q_blind.mean())},
    "delta_q_summary_gate0": g0["delta_q"],
    "jeffreys_floor_here": FLOOR,
    "jeffreys_floor_gate0": g0["G0_2_headroom_control"]["jeffreys_floor"],
    "blind_answerable_n_here": [int(answerable.sum()), int((~answerable).sum())],
    "blind_answerable_n_gate0": [g0["G0_2_headroom_control"]["n_blind_answerable"],
                                 g0["G0_2_headroom_control"]["n_not_blind_answerable"]],
}

# =====================================================================================
# 4. PER-BIN 100 -> 400 MOVEMENT
# =====================================================================================
METRICS = ["acc_final", "acc_strict"]
x = {mt: {s: np.array([float(sub[k][f"{mt}_step{s}"]) for k in ITEMS]) for s in (100, 400)}
     for mt in METRICS}


def paired_boot_ci(d, tag):
    RNG_ORDER.append(tag)
    if len(d) == 0:
        return None
    idx = RNG.integers(0, len(d), size=(BOOT, len(d)))
    b = d[idx].mean(axis=1)
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def mcnemar_exact(gained, lost):
    """Two-sided exact binomial test on the discordant pairs, p=0.5."""
    nd = gained + lost
    if nd == 0:
        return 1.0
    k = min(gained, lost)
    tail = sum(math.comb(nd, i) for i in range(0, k + 1)) / (2.0 ** nd)
    return float(min(1.0, 2.0 * tail))


def cell(mask, mt, tag):
    a, b = x[mt][100][mask], x[mt][400][mask]
    d = b - a
    gained = int(((a == 0) & (b == 1)).sum())
    lost = int(((a == 1) & (b == 0)).sum())
    return {
        "n": int(mask.sum()),
        "acc_step100": float(a.mean()), "n_correct_step100": int(a.sum()),
        "acc_step400": float(b.mean()), "n_correct_step400": int(b.sum()),
        "delta": float(d.mean()),
        "delta_ci95_paired_item_bootstrap": paired_boot_ci(d, tag),
        "gained": gained, "lost": lost,
        "stable_correct": int(((a == 1) & (b == 1)).sum()),
        "stable_incorrect": int(((a == 0) & (b == 0)).sum()),
        "n_changed": gained + lost,
        "turnover_rate": (gained + lost) / int(mask.sum()) if mask.sum() else None,
        "mcnemar_exact_p": mcnemar_exact(gained, lost),
    }


# I7 precondition: is acc_final identical to acc_strict on every item at both steps?
rep["i7_lenient_vs_strict"] = {
    "acc_final_equals_acc_strict_per_item": {
        str(s): int((x["acc_final"][s] == x["acc_strict"][s]).sum()) for s in (100, 400)},
    "n": n,
    "note": ("Both metrics are computed, stored and reported separately and are never "
             "collapsed. Where the two tables carry identical point estimates it is because "
             "the underlying per-item vectors are identical, not because one was substituted "
             "for the other. Small differences between the lenient and strict bootstrap CIs "
             "are Monte-Carlo only: identical data, different draws consumed from the single "
             "seeded stream."),
}

# cross-tab of the two Gate 0 stratifications (reported, not merged -- I13)
rep["crosstab_primary_by_secondary"] = {
    BIN_NAMES[i]: {"blind_answerable": int((masks[i] & answerable).sum()),
                   "not_blind_answerable": int((masks[i] & ~answerable).sum())}
    for i in range(3)}

rep["per_bin_100_to_400"] = {"primary_delta_q_terciles": {}, "secondary_blind_answerable": {},
                             "overall_all_items": {}}
for mt in METRICS:
    rep["per_bin_100_to_400"]["overall_all_items"][mt] = cell(
        np.ones(n, bool), mt, f"overall|{mt}")
for i, m in enumerate(masks):
    for mt in METRICS:
        rep["per_bin_100_to_400"]["primary_delta_q_terciles"].setdefault(BIN_NAMES[i], {})[mt] = \
            cell(m, mt, f"primary|{BIN_NAMES[i]}|{mt}")
for nm, m in (("blind_answerable", answerable), ("not_blind_answerable", ~answerable)):
    for mt in METRICS:
        rep["per_bin_100_to_400"]["secondary_blind_answerable"].setdefault(nm, {})[mt] = \
            cell(m, mt, f"secondary|{nm}|{mt}")

# =====================================================================================
# 5. TESTS OF THE PI'S HYPOTHESIS
# =====================================================================================
tests = {"hypothesis_as_stated": (
    "blind-solvable items improve or hold while image-necessary items decline, "
    "cancelling to a flat overall")}

# 5a. between-bin contrast: image_necessary delta minus blind_solvable delta
for mt in METRICS:
    d_lo = (x[mt][400] - x[mt][100])[masks[0]]
    d_hi = (x[mt][400] - x[mt][100])[masks[2]]
    obs = float(d_hi.mean() - d_lo.mean())
    RNG_ORDER.append(f"contrast_boot|{mt}")
    bl = d_lo[RNG.integers(0, len(d_lo), size=(BOOT, len(d_lo)))].mean(axis=1)
    bh = d_hi[RNG.integers(0, len(d_hi), size=(BOOT, len(d_hi)))].mean(axis=1)
    diff = bh - bl
    # permutation: reshuffle bin membership among the union of the two bins
    pool = np.concatenate([d_lo, d_hi])
    RNG_ORDER.append(f"contrast_perm|{mt}")
    cnt = 0
    for _ in range(PERM):
        p = RNG.permutation(pool)
        if abs(p[len(d_lo):].mean() - p[:len(d_lo)].mean()) >= abs(obs) - 1e-12:
            cnt += 1
    tests.setdefault("contrast_image_necessary_minus_blind_solvable", {})[mt] = {
        "delta_blind_solvable": float(d_lo.mean()), "n_blind_solvable": int(len(d_lo)),
        "delta_image_necessary": float(d_hi.mean()), "n_image_necessary": int(len(d_hi)),
        "contrast": obs,
        "contrast_ci95_independent_bin_bootstrap": [float(np.percentile(diff, 2.5)),
                                                    float(np.percentile(diff, 97.5))],
        "permutation_p_two_sided": (cnt + 1) / (PERM + 1),
        "note": ("bins are disjoint item sets, so the bootstrap resamples each bin "
                 "independently; the permutation reshuffles bin membership within their union"),
    }

# 5b. is turnover systematic in delta_q? mean delta_q of gained vs lost items
for mt in METRICS:
    a, b = x[mt][100], x[mt][400]
    g = (a == 0) & (b == 1)
    l = (a == 1) & (b == 0)
    obs = float(dq[g].mean() - dq[l].mean())
    RNG_ORDER.append(f"gained_vs_lost_perm|{mt}")
    pool = np.concatenate([dq[g], dq[l]])
    ng = int(g.sum())
    cnt = 0
    for _ in range(PERM):
        p = RNG.permutation(pool)
        if abs(p[:ng].mean() - p[ng:].mean()) >= abs(obs) - 1e-12:
            cnt += 1
    tests.setdefault("delta_q_of_gained_vs_lost", {})[mt] = {
        "n_gained": ng, "n_lost": int(l.sum()),
        "mean_delta_q_gained": float(dq[g].mean()), "mean_delta_q_lost": float(dq[l].mean()),
        "difference": obs, "permutation_p_two_sided": (cnt + 1) / (PERM + 1),
        "mean_delta_q_stable": float(dq[~(g | l)].mean()),
    }

# 5c. tie-aware Spearman of per-item change against delta_q, permutation p
def avg_rank(v):
    order = np.argsort(v, kind="mergesort")
    r = np.empty(len(v), float)
    sv = v[order]
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and sv[j + 1] == sv[i]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


for mt in METRICS:
    d = x[mt][400] - x[mt][100]
    rd, rq = avg_rank(d), avg_rank(dq)
    rho = float(np.corrcoef(rd, rq)[0, 1])
    RNG_ORDER.append(f"spearman_perm|{mt}")
    cnt = 0
    for _ in range(PERM):
        if abs(np.corrcoef(rd, RNG.permutation(rq))[0, 1]) >= abs(rho) - 1e-15:
            cnt += 1
    tests.setdefault("spearman_change_vs_delta_q", {})[mt] = {
        "spearman_rho_tie_aware": rho, "permutation_p_two_sided": (cnt + 1) / (PERM + 1),
        "note": ("average-rank Spearman; per-item change takes only {-1,0,+1} so ties dominate "
                 "and Gate 0's ordinal-rank helper is not reused here"),
    }
rep["hypothesis_tests"] = tests

# =====================================================================================
# 6. REAL-VS-BLIND GAP PER BIN
# =====================================================================================
gap = {"step_100": {}, "step_400": None,
       "step_400_absence_reason": None, "blind_conditions_scanned": None}

s100 = {}
for cond, path in STEP100.items():
    rows = [r for r in load(path) if r["split"] == "test"]
    d = {}
    for r in rows:
        k = (r["split"], int(r["row_index"]))
        if k in d:
            raise SystemExit(f"dup key {k} in step100 {cond}")
        d[k] = r
    if set(d) != set(ITEMS):
        raise SystemExit(f"step100 {cond}: item set differs from substrate")
    s100[cond] = d

# rescore every step-100 row through the registered scorer so real and blind sit on an
# identical contract (the real arm is a guarded rescore, the blind arms are raw runs)
resc = {}
agree = {}
for cond, d in s100.items():
    af, ast = np.zeros(n), np.zeros(n)
    ok_f = ok_s = 0
    for i, k in enumerate(ITEMS):
        r = d[k]
        sc = score_greedy_item_pilot(str(r["ground_truth"]), r["greedy_response"],
                                     DEFAULT_PROMPT_CONTRACT)
        af[i] = float(sc["acc_final"])
        ast[i] = float(sc["acc_strict"])
        stored_f = bool(r.get("greedy_correct"))
        stored_s = bool(r.get("greedy_acc_strict"))
        ok_f += int(stored_f == bool(sc["acc_final"]))
        ok_s += int(stored_s == bool(sc["acc_strict"]))
    resc[cond] = {"acc_final": af, "acc_strict": ast}
    agree[cond] = {"acc_final_stored_eq_recomputed": ok_f,
                   "acc_strict_stored_eq_recomputed": ok_s, "n": n}

# the real arm must reproduce the substrate's step-100 column exactly
sub_check = {}
for mt in METRICS:
    sub_check[mt] = int((resc["real"][mt] == x[mt][100]).sum())
gap["real_arm_reproduces_substrate_step100"] = {"n": n, **sub_check}
gap["stored_vs_recomputed_agreement"] = agree
gap["field_mapping_note"] = (
    "The step-100 per_item rows carry greedy_correct / greedy_acc_strict; the m5_geo3k "
    "step-150..400 rows carry acc_final / acc_strict. greedy_correct is the field that equals "
    "score_greedy_item_pilot(...)['acc_final'] (601/601). The separate field "
    "greedy_canonical_correct agrees with greedy_correct on only 598/601 rows and is NOT used "
    "here; Gate 0's base-model analysis used greedy_canonical_correct, which is a different "
    "quantity. Neither field feeds the necessity binning, which comes from q_i.")
gap["greedy_correct_eq_greedy_canonical_correct_step100_real"] = int(sum(
    1 for k in ITEMS if bool(s100["real"][k]["greedy_correct"]) ==
    bool(s100["real"][k]["greedy_canonical_correct"])))
gap["runs"] = {cond: {"run": str(Path(p).parent), "per_item_sha256": sha256(p),
                      "model_revision": manifest(Path(p).parent)["model_revision"],
                      "condition": manifest(Path(p).parent)["condition"],
                      "status": manifest(Path(p).parent)["status"],
                      "data_manifest_hash": manifest(Path(p).parent)["data_manifest_hash"],
                      "parser_version": manifest(Path(p).parent)["parser_version"],
                      "prompt_contract_sha256": manifest(Path(p).parent)["prompt_contract_sha256"],
                      "is_guarded_rescore": "guarded_rescore_version" in manifest(Path(p).parent)}
               for cond, p in STEP100.items()}
gap["scoring_parity_note"] = (
    "The real arm is a guarded RESCORE; the four blind arms are raw run outputs. To remove "
    "that asymmetry every greedy response in all five arms was re-scored here through "
    "src.eval.blind_solvability.score_greedy_item_pilot under DEFAULT_PROMPT_CONTRACT, and the "
    "gap is computed from those recomputed values. Stored == recomputed on 601/601 rows for "
    "both metrics in all five arms, so the rescore asymmetry has no effect on these numbers.")
gap["checkpoint_identity"] = {
    "all_step100_runs_share_model_revision": len({
        manifest(Path(p).parent)["model_revision"] for p in STEP100.values()}) == 1,
    "model_revision": manifest(Path(STEP100["real"]).parent)["model_revision"],
}

strata = [("primary_delta_q_terciles", BIN_NAMES[i], masks[i]) for i in range(3)] + \
         [("secondary_blind_answerable", "blind_answerable", answerable),
          ("secondary_blind_answerable", "not_blind_answerable", ~answerable),
          ("overall_all_items", "all", np.ones(n, bool))]
for group, name, m in strata:
    for mt in METRICS:
        real = resc["real"][mt][m]
        entry = {"n": int(m.sum()), "acc_real": float(real.mean()), "blind_conditions": {}}
        for cond in ("none", "gray", "noise", "caption"):
            bl = resc[cond][mt][m]
            dpair = real - bl
            entry["blind_conditions"][cond] = {
                "acc_blind": float(bl.mean()),
                "gap_real_minus_blind": float(dpair.mean()),
                "gap_ci95_paired_item_bootstrap": paired_boot_ci(
                    dpair, f"gap100|{group}|{name}|{mt}|{cond}"),
            }
        gap["step_100"].setdefault(group, {}).setdefault(name, {})[mt] = entry

gap["step_400"] = "NOT COMPUTED -- no artifact exists"
gap["step_400_absence_reason"] = (
    "No Geometry3K evaluation of any M5 step-400 checkpoint under a blind condition exists. "
    "A scan of every experiments/runs/*/run_manifest.json whose manifest mentions 'geo' and "
    "whose condition field is not 'real' returns 100 runs; all of them evaluate either the "
    "frozen base model or a step-60/step-100 pilot checkpoint. The only step-400 blind "
    "evaluations in the repo are m5_r19_step400_gray_an12_20260728T054005Z and "
    "m5_r19_step400_noise_an12_20260728T054005Z, which are R19 grounding probes, not geo3k, "
    "and are not substitutable. The step-400 real-vs-blind column is therefore not reported.")
gap["blind_conditions_scanned"] = {
    "step_100_available": ["none", "gray", "noise", "caption"],
    "step_400_available": [],
    "note": "conditions are kept separate and never pooled (I13)",
}
rep["real_vs_blind_gap"] = gap

rep["step_400_real_run"] = {"run": STEP400_REAL_RUN,
                            "per_item_sha256": sha256(f"{STEP400_REAL_RUN}/per_item.jsonl"),
                            "model_revision": manifest(STEP400_REAL_RUN)["model_revision"],
                            "condition": manifest(STEP400_REAL_RUN)["condition"]}
rep["rng"]["consumption_order"] = RNG_ORDER

(ROOT / "reports/m5c_necessity_stratification_v1.json").write_text(
    json.dumps(rep, indent=2, sort_keys=True) + "\n")
print("wrote reports/m5c_necessity_stratification_v1.json")
print("bins:", [(b["label"], b["n"]) for b in rep["stratification"]["bins"]])
print("gate0 reproduction:", rep["gate0_reproduction_check"]["bin_n_match"],
      rep["gate0_reproduction_check"]["bin_edges_match"])
for i in range(3):
    c = rep["per_bin_100_to_400"]["primary_delta_q_terciles"][BIN_NAMES[i]]["acc_final"]
    print(f"  {BIN_NAMES[i]:16s} n={c['n']:3d} 100={c['acc_step100']:.4f} "
          f"400={c['acc_step400']:.4f} d={c['delta']:+.4f} "
          f"CI[{c['delta_ci95_paired_item_bootstrap'][0]:+.4f},"
          f"{c['delta_ci95_paired_item_bootstrap'][1]:+.4f}] "
          f"g={c['gained']} l={c['lost']}")
