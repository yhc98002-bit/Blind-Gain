#!/usr/bin/env python3
"""M5C: shared per-item substrate for geo3k trajectory + step100->step400 turnover.

Builds reports/m5c_item_substrate_v1.jsonl (one row per geo3k test item, acc_final /
acc_strict at steps 100/150/200/300/400 + transition labels) and
reports/m5c_turnover_v1.json (transition tables, turnover stats, McNemar exact).

Item key: (split, row_index) -- the same unit m5b_trajectory_v1 used.
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
import subprocess
import sys
import time

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from src.eval.blind_solvability import score_greedy_item_pilot  # noqa: E402
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402

RUNS = {
    "100": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
    "150": "experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z",
    "200": "experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z",
    "300": "experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z",
    "400": "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z",
}
STEPS = ["100", "150", "200", "300", "400"]
# m5b_trajectory_v1.md section 2, acc_final column
M5B_ACC_FINAL = {"100": 0.4359, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443}
M5B_ACC_STRICT = {"100": 0.4359, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443}


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mcnemar_exact_p(b01, b10):
    """Two-sided exact McNemar (binomial sign test on discordant pairs)."""
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n))


# ---------------------------------------------------------------------------
# 1. Load, filter to the geo3k test split, key on (split, row_index)
# ---------------------------------------------------------------------------
raw_counts = {}
excluded_breakdown = {}
items = {}          # step -> {key: {"acc_final":int, "acc_strict":int, ...}}
dupes = {}
provenance = {}
recompute_agreement = {}

t0 = time.time()
for step in STEPS:
    run = RUNS[step]
    path = os.path.join(run, "per_item.jsonl")
    rows_all = load_jsonl(path)
    raw_counts[step] = len(rows_all)
    other = collections.Counter(
        (str(r.get("split")), str(r.get("condition")))
        for r in rows_all
        if r.get("split") != "test"
    )
    excluded_breakdown[step] = {f"split={s}|condition={c}": n for (s, c), n in sorted(other.items())}

    rows = [r for r in rows_all if r.get("split") == "test"]
    seen = collections.Counter((str(r["split"]), int(r["row_index"])) for r in rows)
    dupes[step] = sorted([f"{k[0]}:{k[1]}" for k, v in seen.items() if v > 1])

    per = {}
    agree = {"acc_final": 0, "acc_strict": 0, "n": 0}
    for row in rows:
        key = (str(row["split"]), int(row["row_index"]))
        # schema differs: guarded-rescore (step100) vs M5 (150-400)
        acc_final = row.get("acc_final", row.get("greedy_correct"))
        acc_strict = row.get("acc_strict", row.get("greedy_acc_strict"))
        assert acc_final is not None and acc_strict is not None, (step, key)
        out = score_greedy_item_pilot(
            str(row["ground_truth"]),
            str(row["greedy_response"]),
            DEFAULT_PROMPT_CONTRACT,
            format_weight=float(row.get("format_weight", 0.5)),
        )
        agree["n"] += 1
        agree["acc_final"] += int(bool(acc_final) == bool(out["acc_final"]))
        agree["acc_strict"] += int(bool(acc_strict) == bool(out["acc_strict"]))
        per[key] = {
            "acc_final": int(bool(acc_final)),
            "acc_strict": int(bool(acc_strict)),
            "recomputed_acc_final": int(bool(out["acc_final"])),
            "recomputed_acc_strict": int(bool(out["acc_strict"])),
            "ground_truth": str(row.get("ground_truth")),
            "qid": str(row.get("qid")),
            "image_sha256": str(row.get("image_sha256")),
            "problem_sha256": hashlib.sha256(str(row.get("problem")).encode("utf-8")).hexdigest(),
        }
    items[step] = per
    recompute_agreement[step] = agree
    provenance[step] = {
        "run": run,
        "per_item_sha256": sha256_file(path),
        "rows_total": len(rows_all),
        "rows_test": len(rows),
    }
    print(f"  step {step}: {len(rows)}/{len(rows_all)} test rows  ({time.time()-t0:.1f}s)", flush=True)

# ---------------------------------------------------------------------------
# 2. Item-id set identity across all five runs
# ---------------------------------------------------------------------------
keysets = {s: set(items[s]) for s in STEPS}
ref = keysets["100"]
common = set.intersection(*keysets.values())
union = set.union(*keysets.values())
id_check = {
    "n_per_step": {s: len(keysets[s]) for s in STEPS},
    "n_common": len(common),
    "n_union": len(union),
    "all_identical": all(keysets[s] == ref for s in STEPS),
    "missing_vs_step100": {
        s: sorted(f"{k[0]}:{k[1]}" for k in (ref - keysets[s])) for s in STEPS
    },
    "extra_vs_step100": {
        s: sorted(f"{k[0]}:{k[1]}" for k in (keysets[s] - ref)) for s in STEPS
    },
    "duplicate_keys_within_step": dupes,
    "raw_row_counts": raw_counts,
    "non_test_rows_excluded": excluded_breakdown,
}

if not id_check["all_identical"]:
    print("!! ITEM-ID SETS NOT IDENTICAL -- see id_check", flush=True)

ORDER = sorted(common)

# ---------------------------------------------------------------------------
# 3. Joined-field identity on every item (join sanity)
# ---------------------------------------------------------------------------
field_mismatch = {f: 0 for f in ("ground_truth", "qid", "image_sha256", "problem_sha256")}
mismatch_examples = collections.defaultdict(list)
for key in ORDER:
    base = items["100"][key]
    for s in STEPS[1:]:
        cur = items[s][key]
        for f in field_mismatch:
            if base[f] != cur[f]:
                field_mismatch[f] += 1
                if len(mismatch_examples[f]) < 5:
                    mismatch_examples[f].append(
                        {"item": f"{key[0]}:{key[1]}", "at_step": s,
                         "value_step100": base[f], "value_at_step": cur[f]}
                    )

# ---------------------------------------------------------------------------
# 4. Levels, and reproduction of the m5b series
# ---------------------------------------------------------------------------
n = len(ORDER)
levels = {}
for s in STEPS:
    af = sum(items[s][k]["acc_final"] for k in ORDER)
    st = sum(items[s][k]["acc_strict"] for k in ORDER)
    levels[s] = {
        "n": n,
        "acc_final_count": af,
        "acc_final": af / n,
        "acc_strict_count": st,
        "acc_strict": st / n,
        "m5b_acc_final": M5B_ACC_FINAL[s],
        "acc_final_matches_m5b_4dp": round(af / n, 4) == M5B_ACC_FINAL[s],
        "m5b_acc_strict": M5B_ACC_STRICT[s],
        "acc_strict_matches_m5b_4dp": round(st / n, 4) == M5B_ACC_STRICT[s],
        "acc_final_equals_acc_strict_all_items": all(
            items[s][k]["acc_final"] == items[s][k]["acc_strict"] for k in ORDER
        ),
    }

# ---------------------------------------------------------------------------
# 5. Transition tables
# ---------------------------------------------------------------------------
LABELS = {(1, 1): "stable_correct", (0, 1): "gained", (1, 0): "lost", (0, 0): "stable_incorrect"}


def transition(a_step, b_step, metric):
    """a_step -> b_step transition table on `metric`."""
    counts = {"stable_correct": 0, "gained": 0, "lost": 0, "stable_incorrect": 0}
    labels = {}
    for key in ORDER:
        a = items[a_step][key][metric]
        b = items[b_step][key][metric]
        lab = LABELS[(a, b)]
        counts[lab] += 1
        labels[key] = lab
    b01 = counts["gained"]
    b10 = counts["lost"]
    disc = b01 + b10
    net_count = b01 - b10
    net_delta = net_count / n
    acc_a = (counts["stable_correct"] + counts["lost"]) / n
    acc_b = (counts["stable_correct"] + counts["gained"]) / n
    turnover_frac = disc / n
    tbl = {
        "from_step": a_step,
        "to_step": b_step,
        "metric": metric,
        "n": n,
        "counts": counts,
        "acc_from": acc_a,
        "acc_to": acc_b,
        "net_count": net_count,
        "net_delta": net_delta,
        "acc_to_minus_acc_from": acc_b - acc_a,
        "net_delta_matches_level_diff": abs((acc_b - acc_a) - net_delta) < 1e-12,
        "b01_gained": b01,
        "b10_lost": b10,
        "discordant_pairs": disc,
        "turnover_fraction_of_n": turnover_frac,
        "turnover_to_abs_net_ratio": (disc / abs(net_count)) if net_count != 0 else None,
        "abs_net_count": abs(net_count),
        "mcnemar_exact_two_sided_p": mcnemar_exact_p(b01, b10),
        "concordant_pairs": counts["stable_correct"] + counts["stable_incorrect"],
        "agreement_fraction": (counts["stable_correct"] + counts["stable_incorrect"]) / n,
    }
    return tbl, labels


HOPS = [("100", "400"), ("100", "200"), ("200", "400")]
transitions = {}
label_store = {}
for a, b in HOPS:
    for metric in ("acc_final", "acc_strict"):
        tbl, labs = transition(a, b, metric)
        transitions[f"{a}->{b}|{metric}"] = tbl
        label_store[(a, b, metric)] = labs

# consecutive hops as well, for reading the peak-and-reverse shape
for a, b in zip(STEPS[:-1], STEPS[1:]):
    for metric in ("acc_final", "acc_strict"):
        tbl, _ = transition(a, b, metric)
        transitions[f"{a}->{b}|{metric}"] = tbl

# ---------------------------------------------------------------------------
# 6. Per-item substrate JSONL
# ---------------------------------------------------------------------------
os.makedirs("reports", exist_ok=True)
sub_path = "reports/m5c_item_substrate_v1.jsonl"
with open(sub_path, "w", encoding="utf-8") as fh:
    for key in ORDER:
        rec = {
            "schema_version": "blind-gains.m5c-item-substrate.v1",
            "split": key[0],
            "row_index": key[1],
            "item_key": f"{key[0]}:{key[1]}",
            "qid": items["100"][key]["qid"],
            "image_sha256": items["100"][key]["image_sha256"],
            "ground_truth": items["100"][key]["ground_truth"],
        }
        for s in STEPS:
            rec[f"acc_final_step{s}"] = items[s][key]["acc_final"]
        for s in STEPS:
            rec[f"acc_strict_step{s}"] = items[s][key]["acc_strict"]
        rec["transition_100_400_lenient"] = label_store[("100", "400", "acc_final")][key]
        rec["transition_100_400_strict"] = label_store[("100", "400", "acc_strict")][key]
        rec["transition_100_200_lenient"] = label_store[("100", "200", "acc_final")][key]
        rec["transition_100_200_strict"] = label_store[("100", "200", "acc_strict")][key]
        rec["transition_200_400_lenient"] = label_store[("200", "400", "acc_final")][key]
        rec["transition_200_400_strict"] = label_store[("200", "400", "acc_strict")][key]
        rec["n_steps_correct_lenient"] = sum(items[s][key]["acc_final"] for s in STEPS)
        rec["n_steps_correct_strict"] = sum(items[s][key]["acc_strict"] for s in STEPS)
        rec["pattern_lenient"] = "".join(str(items[s][key]["acc_final"]) for s in STEPS)
        rec["pattern_strict"] = "".join(str(items[s][key]["acc_strict"]) for s in STEPS)
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

# ---------------------------------------------------------------------------
# 7. Turnover JSON
# ---------------------------------------------------------------------------
git_hash = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
).stdout.strip()

pattern_counts_len = collections.Counter(
    "".join(str(items[s][k]["acc_final"]) for s in STEPS) for k in ORDER
)
pattern_counts_str = collections.Counter(
    "".join(str(items[s][k]["acc_strict"]) for s in STEPS) for k in ORDER
)
never_correct_len = sum(1 for k in ORDER if all(items[s][k]["acc_final"] == 0 for s in STEPS))
always_correct_len = sum(1 for k in ORDER if all(items[s][k]["acc_final"] == 1 for s in STEPS))
moved_len = n - never_correct_len - always_correct_len

artifact = {
    "schema_version": "blind-gains.m5c-turnover.v1",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "git_hash": git_hash,
    "item_key_definition": "(split, row_index) on the Geometry3K test split",
    "metrics": {
        "acc_final": "lenient (I7)",
        "acc_strict": "contract-strict (I7)",
    },
    "n_items": n,
    "id_check": id_check,
    "joined_field_mismatch_counts": field_mismatch,
    "joined_field_mismatch_examples": {k: v for k, v in mismatch_examples.items()},
    "stored_vs_recomputed_agreement": recompute_agreement,
    "levels": levels,
    "transitions": transitions,
    "multi_step_patterns": {
        "note": "pattern digits are steps 100/150/200/300/400 in order",
        "lenient_pattern_counts": dict(sorted(pattern_counts_len.items(), key=lambda kv: -kv[1])),
        "strict_pattern_counts": dict(sorted(pattern_counts_str.items(), key=lambda kv: -kv[1])),
        "lenient_never_correct_any_step": never_correct_len,
        "lenient_always_correct_all_steps": always_correct_len,
        "lenient_items_that_moved_at_least_once": moved_len,
    },
    "provenance": provenance,
    "substrate_path": sub_path,
    "substrate_sha256": sha256_file(sub_path),
    "substrate_rows": n,
}

tj_path = "reports/m5c_turnover_v1.json"
with open(tj_path, "w", encoding="utf-8") as fh:
    json.dump(artifact, fh, indent=2, ensure_ascii=False, sort_keys=False)
    fh.write("\n")

print(json.dumps({
    "n": n,
    "id_sets_identical": id_check["all_identical"],
    "levels": {s: [levels[s]["acc_final"], levels[s]["acc_final_matches_m5b_4dp"],
                   levels[s]["acc_strict"], levels[s]["acc_strict_matches_m5b_4dp"]] for s in STEPS},
    "recompute_agreement": recompute_agreement,
    "field_mismatch": field_mismatch,
    "main": {k: transitions[k] for k in transitions if k.startswith(("100->400", "100->200", "200->400"))},
    "moved": moved_len,
}, indent=2))
print("wrote", sub_path, tj_path)
