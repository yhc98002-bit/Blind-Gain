#!/usr/bin/env python3
"""Independent arithmetic re-check of the seed-3 replication JSON."""
import json
from fractions import Fraction

P = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/x3_seed3_corrosion_replication_v1.json"
r = json.load(open(P))
ok = []


def eq(name, a, b, tol=1e-12):
    good = abs(a - b) <= tol
    ok.append((name, good, a, b))


for track in ("lenient", "strict"):
    t = r[track]
    nb = t["base_pair_correct_n"]
    eq(f"{track}.base_acc", t["base_pair_accuracy"], nb / 600)
    for s in ("seed1", "seed2", "seed3"):
        p = t["per_seed"][s]
        eq(f"{track}.{s}.acc", p["a2_pair_accuracy"], p["a2_pair_correct_n"] / 600)
        eq(f"{track}.{s}.delta", p["net_delta_vs_base"], (p["a2_pair_correct_n"] - nb) / 600)
        eq(f"{track}.{s}.delta_boot", p["net_delta_vs_base_paired_bootstrap"]["delta"], p["net_delta_vs_base"])
        # net delta must equal (gained - degraded)/600
        eq(
            f"{track}.{s}.delta_from_sets",
            p["net_delta_vs_base"],
            (p["gained_wrong_to_correct"] - p["degraded_correct_to_wrong"]) / 600,
        )
        tax = p["transition_taxonomy"]
        eq(f"{track}.{s}.taxonomy_sums_to_slots", float(sum(tax.values())), float(p["wrong_member_slots"]))
        md = p["member_direction"]
        eq(
            f"{track}.{s}.direction_sums_to_pairs",
            float(sum(md.values())),
            float(p["degraded_correct_to_wrong"]),
        )
        eq(
            f"{track}.{s}.slots_from_direction",
            float(2 * md.get("both_members", 0) + md.get("member_a_only", 0) + md.get("member_b_only", 0)),
            float(p["wrong_member_slots"]),
        )
        eq(f"{track}.{s}.gridline_count", float(p["nearest_gridline_count"]), float(tax.get("nearest_gridline", 0)))
        eq(
            f"{track}.{s}.gridline_share",
            p["nearest_gridline_share_of_wrong_slots"],
            p["nearest_gridline_count"] / p["wrong_member_slots"],
        )
    for k in ("seed3__seed1", "seed3__seed2", "seed1__seed2"):
        e = t["overlap"][k]
        eq(f"{track}.{k}.jaccard", e["jaccard"], e["intersection"] / e["union"])
        # inclusion-exclusion
        eq(
            f"{track}.{k}.union_ie",
            float(e["union"]),
            float(e["size_a"] + e["size_b"] - e["intersection"]),
        )
        assert e["intersection"] <= min(e["size_a"], e["size_b"]), k
    t3 = t["overlap"]["three_seed"]
    eq(f"{track}.3way.jaccard", t3["jaccard3"], t3["intersection_all_three"] / t3["union_all_three"])
    eq(
        f"{track}.3way.recovery",
        t3["seed3_recovery_rate_of_seed12_intersection"],
        t3["seed3_recovers_of_seed12_intersection"] / t3["seed12_intersection_size"],
    )
    eq(
        f"{track}.3way.inter_matches_seed12",
        float(t3["intersection_all_three"]),
        float(t3["seed3_recovers_of_seed12_intersection"]),
    )
    eq(
        f"{track}.3way.seed12_inter_matches_overlap",
        float(t3["seed12_intersection_size"]),
        float(t["overlap"]["seed1__seed2"]["intersection"]),
    )
    for k, e in t["same_wrong_answer"].items():
        eq(f"{track}.samewrong.{k}", e["rate"], e["same_extracted_wrong_answer"] / e["shared_wrong_member_slots"])
        assert e["same_extracted_wrong_answer"] <= e["shared_wrong_member_slots"]
    for arm, e in t["cross_arm_seed3"].items():
        assert e["wrong_on_three_seed_shared_items"] <= e["three_seed_shared_items"]
        assert e["wrong_on_seed3_degraded_items"] <= e["seed3_degraded_items"]
        assert e["wrong_on_all_base_correct"] <= e["base_correct_items"]

ag = r["frozen_v1_agreement"]
print("frozen agreement:", ag["fields_equal"], "/", ag["fields_checked"], "all_equal =", ag["all_equal"])
bad = [x for x in ok if not x[1]]
print("arithmetic checks:", len(ok) - len(bad), "/", len(ok), "pass")
for b in bad:
    print("  FAIL", b)
# p-value resolution floor
print("p floor at 10000 perms =", 1 / 10001)
