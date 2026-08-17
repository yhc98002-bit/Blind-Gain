#!/usr/bin/env python3
"""Compare the instrument's fixture output against the independent reference."""
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
ref = json.loads((root / "reference.json").read_text())
two = json.loads((root / "out_two" / "r.json").read_text())
one = json.loads((root / "out_one" / "r.json").read_text())
dup = json.loads((root / "out_dup" / "r.json").read_text())

fails = []
checks = 0
TOL = 1e-12


def eq(label, got, want):
    global checks
    checks += 1
    if got is None and want is None:
        return
    if got is None or want is None:
        fails.append(f"{label}: got {got!r} want {want!r}")
        return
    if isinstance(got, bool) or isinstance(want, bool):
        if bool(got) != bool(want):
            fails.append(f"{label}: got {got!r} want {want!r}")
        return
    if isinstance(got, (int, float)) and isinstance(want, (int, float)):
        if not math.isclose(float(got), float(want), rel_tol=0, abs_tol=TOL):
            fails.append(f"{label}: got {got!r} want {want!r} (d={got-want:.3e})")
        return
    if got != want:
        fails.append(f"{label}: got {got!r} want {want!r}")


def check_mode(payload, R, tag):
    ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
    BLIND = ("a2_gray", "a2b_noimage", "a3_caption")
    # corpus
    for arm in ARMS:
        e = payload["corpus"]["arms"][arm]
        eq(f"{tag} corpus.gain[{arm}]", e["gain"]["estimate"], R["corpus"]["gain"][arm])
        eq(
            f"{tag} corpus.paired_se[{arm}]",
            e["gain"]["paired_se"],
            R["corpus"]["paired_se"][arm],
        )
        eq(f"{tag} corpus.qbar[{arm}]", e["q_bar"], R["corpus"]["q_bar"][arm])
        eq(
            f"{tag} corpus.acc0[{arm}]",
            e["acc_final_step0"],
            R["corpus"]["acc_final_step0"][arm],
        )
        eq(
            f"{tag} corpus.acc100[{arm}]",
            e["acc_final_step100"],
            R["corpus"]["acc_final_step100"][arm],
        )
    eq(
        f"{tag} corpus.a1_stable",
        payload["corpus"]["a1_denominator"]["stable"],
        R["corpus"]["a1_stable"],
    )
    for arm in BLIND:
        eq(
            f"{tag} corpus.aggregate_recovery[{arm}]",
            payload["corpus"]["aggregate_recovery"][arm]["estimate"],
            R["corpus"]["aggregate_recovery"][arm],
        )
    for arm, d in R["corpus"]["anchor_difference"].items():
        eq(
            f"{tag} anchor.difference[{arm}]",
            payload["corpus"]["geometry3k_anchor_comparison"][arm][
                "difference_from_anchor"
            ],
            d,
        )
    # strata
    for row in payload["stratum_table"]:
        key = f"{row['source']}||{row['category']}"
        Rr = R["strata"][key]
        eq(f"{tag} {key}.n", row["n"], Rr["n"])
        eq(f"{tag} {key}.eligible", row["eligible"], Rr["eligible"])
        for arm in ARMS:
            eq(f"{tag} {key}.qbar[{arm}]", row["q_bar"][arm], Rr["q_bar"][arm])
            eq(
                f"{tag} {key}.gain[{arm}]",
                row["gain"][arm]["estimate"],
                Rr["gain"][arm],
            )
            eq(
                f"{tag} {key}.se[{arm}]",
                row["gain"][arm]["paired_se"],
                Rr["paired_se"][arm],
            )
            eq(
                f"{tag} {key}.acc100[{arm}]",
                row["acc_final_step100"][arm],
                Rr["acc_final_step100"][arm],
            )
        eq(f"{tag} {key}.a1_stable", row["a1_denominator"]["stable"], Rr["a1_stable"])
        if row["eligible"]:
            for arm in BLIND:
                got = row["recovery"][arm].get("estimate")
                eq(f"{tag} {key}.recovery[{arm}]", got, Rr["recovery"][arm])
    # rank statistics
    for arm in BLIND:
        eq(
            f"{tag} rho_gain[{arm}]",
            payload["rank_statistics"][arm]["rho_gain"]["estimate"],
            R["rank"][arm]["rho_gain"],
        )
        eq(
            f"{tag} rho_recovery[{arm}]",
            payload["rank_statistics"][arm]["rho_recovery"]["estimate"],
            R["rank"][arm]["rho_recovery"],
        )
        eq(
            f"{tag} n_recovery_strata[{arm}]",
            payload["rank_statistics"][arm]["rho_recovery"]["n_recovery_strata"],
            R["rank"][arm]["n_recovery_strata"],
        )


check_mode(two, ref["two_seed"], "TWO")
check_mode(one, ref["one_seed"], "ONE")

# seed dispersion block vs independent per-seed reference
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND = ("a2_gray", "a2b_noimage", "a3_caption")
disp = two["seed_dispersion"]
for sd in ("seed1", "seed2"):
    Rb = ref["two_seed"]["per_seed"][sd]
    blk = disp["per_seed"][sd]
    for arm in ARMS:
        eq(f"DISP {sd}.gain[{arm}]", blk["corpus"][arm]["gain"], Rb["corpus_gain"][arm])
        eq(
            f"DISP {sd}.se[{arm}]",
            blk["corpus"][arm]["paired_se"],
            Rb["corpus_paired_se"][arm],
        )
        eq(
            f"DISP {sd}.acc100[{arm}]",
            blk["corpus"][arm]["acc_final_step100"],
            Rb["corpus_acc_final_step100"][arm],
        )
    eq(f"DISP {sd}.a1_stable", blk["corpus_a1_denominator"]["stable"], Rb["a1_stable"])
    for arm in BLIND:
        eq(
            f"DISP {sd}.aggrec[{arm}]",
            blk["aggregate_recovery"][arm]["estimate"],
            Rb["aggregate_recovery"][arm],
        )
        eq(
            f"DISP {sd}.rho_gain[{arm}]",
            blk["rank_statistics"][arm]["rho_gain"],
            Rb["rank"][arm]["rho_gain"],
        )
        eq(
            f"DISP {sd}.rho_recovery[{arm}]",
            blk["rank_statistics"][arm]["rho_recovery"],
            Rb["rank"][arm]["rho_recovery"],
        )
        eq(
            f"DISP {sd}.n_rec[{arm}]",
            blk["rank_statistics"][arm]["n_recovery_strata"],
            Rb["rank"][arm]["n_recovery_strata"],
        )
# differences
for arm in ARMS:
    eq(
        f"DISP diff.corpus_gain[{arm}]",
        disp["differences"]["corpus_gain"][arm],
        ref["two_seed"]["per_seed"]["seed1"]["corpus_gain"][arm]
        - ref["two_seed"]["per_seed"]["seed2"]["corpus_gain"][arm],
    )

# ---- one-seed identity: seed1 dispersion block must equal the one-seed payload
for arm in ARMS:
    eq(
        f"IDENT seed1-block gain[{arm}] == one-seed corpus gain",
        disp["per_seed"]["seed1"]["corpus"][arm]["gain"],
        one["corpus"]["arms"][arm]["gain"]["estimate"],
    )
for arm in BLIND:
    eq(
        f"IDENT seed1-block rho_gain[{arm}] == one-seed rho_gain",
        disp["per_seed"]["seed1"]["rank_statistics"][arm]["rho_gain"],
        one["rank_statistics"][arm]["rho_gain"]["estimate"],
    )
    eq(
        f"IDENT seed1-block aggrec[{arm}] == one-seed aggrec",
        disp["per_seed"]["seed1"]["aggregate_recovery"][arm]["estimate"],
        one["corpus"]["aggregate_recovery"][arm]["estimate"],
    )

# ---- duplicate-seed invariance: two-seed mode fed identical data as both seeds
#      must reproduce the one-seed numbers AND intervals exactly.
def strip(payload):
    """numeric skeleton for comparison"""
    out = {}
    for arm in ARMS:
        e = payload["corpus"]["arms"][arm]["gain"]
        out[f"gain:{arm}"] = (e["estimate"], e["paired_se"], tuple(e["ci95"]))
    for arm in BLIND:
        r = payload["corpus"]["aggregate_recovery"][arm]
        out[f"aggrec:{arm}"] = (
            r["estimate"],
            tuple(r["bootstrap"]["ci95"]),
            r["bootstrap"]["undefined_draw_count"],
        )
        for k in ("rho_gain", "rho_recovery"):
            s = payload["rank_statistics"][arm][k]
            out[f"{k}:{arm}"] = (
                s["estimate"],
                tuple(s["bootstrap"]["ci95"]) if s.get("bootstrap") else None,
                s["bootstrap"]["undefined_draw_count"] if s.get("bootstrap") else None,
            )
    for row in payload["stratum_table"]:
        key = f"{row['source']}||{row['category']}"
        for arm in ARMS:
            g = row["gain"][arm]
            out[f"strat:{key}:{arm}"] = (
                g["estimate"],
                g["paired_se"],
                tuple(g["ci95"]),
            )
    return out


sd_one, sd_dup = strip(one), strip(dup)
for k in sorted(sd_one):
    checks += 1
    if sd_one[k] != sd_dup[k]:
        fails.append(f"DUP-INVARIANCE {k}: one={sd_one[k]} dup={sd_dup[k]}")

print(json.dumps({"checks": checks, "failures": fails}, indent=2))
