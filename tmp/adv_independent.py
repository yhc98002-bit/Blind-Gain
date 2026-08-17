"""ADVERSARIAL: independent re-implementation of the registered two-seed R3
estimator, computed from the raw fixture per_item.jsonl files, compared against
the instrument's own JSON output.

Also computes the WRONG estimators the registration forbids, and asserts the
instrument does NOT match them:
  W1 pool items across seeds (2N item vector)
  W2 mean of per-seed recovery ratios (instead of ratio of two-seed means)
  W3 mean of per-seed rho values (instead of rho on two-seed gains)
  W4 seed-1 only
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy import stats  # independent tie-corrected Spearman

REPO = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

import test_m7_r3_readout_two_seed_fixture as fx  # noqa: E402

ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND = ("a2_gray", "a2b_noimage", "a3_caption")


def read_rows(path: Path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[(row["qid"], row["row_index"])] = row
    return out


def spearman(x, y):
    if len(x) < 2:
        return None
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return float(stats.spearmanr(x, y).statistic)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="adv_twoseed_"))
    fx.build_two_seed_fixture(tmp)
    args = fx._cli_two_seed(tmp)
    res = subprocess.run(args, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    payload = json.loads((tmp / "reports/out.json").read_text(encoding="utf-8"))

    # ---- independent load of the raw fixture -----------------------------
    heldout = [
        json.loads(line)
        for line in (tmp / "data/heldout.jsonl").read_text().splitlines()
        if line.strip()
    ]
    keys = sorted((r["qid"], r["row_index"]) for r in heldout)
    stratum_of = {
        (r["qid"], r["row_index"]): (r["metadata"]["source"], r["metadata"]["category"])
        for r in heldout
    }
    strata = sorted(set(stratum_of.values()))
    items_by_stratum = {
        s: sorted(k for k in keys if stratum_of[k] == s) for s in strata
    }
    eligible = [s for s in strata if len(items_by_stratum[s]) >= 30]

    step0 = {a: read_rows(tmp / f"runs/{a}_step0/per_item.jsonl") for a in ARMS}
    s100 = {
        a: {
            sd: read_rows(tmp / f"runs/{a}_step100_seed{sd}/per_item.jsonl")
            for sd in (1, 2)
        }
        for a in ARMS
    }

    def acc0(a, ks):
        return np.array(
            [float(step0[a][k]["greedy_canonical_correct"]) for k in ks]
        )

    def acc100(a, sd, ks):
        return np.array(
            [float(s100[a][sd][k]["greedy_canonical_correct"]) for k in ks]
        )

    def gain_two_seed(a, ks):
        """REGISTERED: per-item mean over seeds of (acc100_seed - acc0)."""
        g1 = acc100(a, 1, ks) - acc0(a, ks)
        g2 = acc100(a, 2, ks) - acc0(a, ks)
        return (g1 + g2) / 2.0

    def gain_seed(a, sd, ks):
        return acc100(a, sd, ks) - acc0(a, ks)

    def qbar(a, ks):
        return float(np.mean([float(step0[a][k]["q_i"]) for k in ks]))

    def paired_se(v):
        return float(v.std(ddof=1) / np.sqrt(v.size)) if v.size > 1 else 0.0

    problems: list[str] = []
    checks = 0

    def chk(name, got, want, tol=1e-12):
        nonlocal checks
        checks += 1
        if want is None or got is None:
            ok = got is want or got == want
        else:
            ok = abs(float(got) - float(want)) <= tol
        if not ok:
            problems.append(f"MISMATCH {name}: instrument={got!r} independent={want!r}")

    # ---- corpus gains ----------------------------------------------------
    for a in ARMS:
        want = float(gain_two_seed(a, keys).mean())
        got = payload["corpus"]["arms"][a]["gain"]["estimate"]
        chk(f"corpus.gain[{a}]", got, want)
        # W1: pooling items across seeds would give the same MEAN but a
        # different paired SE on a 2N vector -- check the SE discriminates.
        want_se = paired_se(gain_two_seed(a, keys))
        pooled = np.concatenate([gain_seed(a, 1, keys), gain_seed(a, 2, keys)])
        chk(f"corpus.gain[{a}].paired_se", payload["corpus"]["arms"][a]["gain"]["paired_se"], want_se)
        if abs(paired_se(pooled) - want_se) > 1e-9:
            got_se = payload["corpus"]["arms"][a]["gain"]["paired_se"]
            if abs(got_se - paired_se(pooled)) < 1e-12:
                problems.append(
                    f"W1 POOLED-ACROSS-SEEDS SE detected for {a}: "
                    f"{got_se} == pooled-2N SE {paired_se(pooled)}"
                )

    # ---- corpus aggregate recovery: ratio of two-seed means --------------
    a1 = gain_two_seed("a1_real", keys)
    a1_mean, a1_se = float(a1.mean()), paired_se(gain_two_seed("a1_real", keys))
    a1_stable = a1_mean > 0 and a1_mean >= 2 * a1_se
    chk("corpus.a1_denominator.estimate", payload["corpus"]["a1_denominator"]["estimate"], a1_mean)
    chk("corpus.a1_denominator.paired_se", payload["corpus"]["a1_denominator"]["paired_se"], a1_se)
    if payload["corpus"]["a1_denominator"]["stable"] != bool(a1_stable):
        problems.append("MISMATCH corpus.a1_denominator.stable")
    checks += 1
    for a in BLIND:
        want = float(gain_two_seed(a, keys).mean() / a1_mean)
        got = payload["corpus"]["aggregate_recovery"][a]["estimate"]
        chk(f"corpus.aggregate_recovery[{a}]", got, want)
        # W2: mean of per-seed ratios
        w2 = float(
            np.mean(
                [
                    gain_seed(a, sd, keys).mean() / gain_seed("a1_real", sd, keys).mean()
                    for sd in (1, 2)
                ]
            )
        )
        if abs(w2 - want) > 1e-9 and got is not None and abs(got - w2) < 1e-12:
            problems.append(
                f"W2 MEAN-OF-PER-SEED-RATIOS detected for {a}: {got} == {w2}"
            )

    # ---- stratum table ---------------------------------------------------
    rows = {(r["source"], r["category"]): r for r in payload["stratum_table"]}
    if set(rows) != set(strata):
        problems.append(f"stratum set mismatch: {set(rows) ^ set(strata)}")
    checks += 1
    for s in strata:
        ks = items_by_stratum[s]
        r = rows[s]
        chk(f"stratum{s}.n", r["n"], len(ks))
        for a in ARMS:
            chk(f"stratum{s}.q_bar[{a}]", r["q_bar"][a], qbar(a, ks))
            chk(f"stratum{s}.gain[{a}]", r["gain"][a]["estimate"], float(gain_two_seed(a, ks).mean()))
            chk(
                f"stratum{s}.gain[{a}].paired_se",
                r["gain"][a]["paired_se"],
                paired_se(gain_two_seed(a, ks)),
            )
        g = gain_two_seed("a1_real", ks)
        m, se = float(g.mean()), paired_se(g)
        stable = bool(m > 0 and m >= 2 * se)
        if r["a1_denominator"]["stable"] != stable:
            problems.append(f"MISMATCH stratum{s}.a1_denominator.stable")
        checks += 1
        if r["recovery"] is not None:
            for a in BLIND:
                cell = r["recovery"][a]
                if stable:
                    chk(
                        f"stratum{s}.recovery[{a}]",
                        cell["estimate"],
                        float(gain_two_seed(a, ks).mean() / m),
                    )
                elif cell.get("status") != "undefined-unstable-denominator":
                    problems.append(
                        f"stratum{s}.recovery[{a}] should be "
                        f"undefined-unstable-denominator, got {cell.get('status')}"
                    )
                    checks += 1

    # ---- rank statistics -------------------------------------------------
    for a in BLIND:
        q = [qbar(a, items_by_stratum[s]) for s in eligible]
        g = [float(gain_two_seed(a, items_by_stratum[s]).mean()) for s in eligible]
        ga1 = [gain_two_seed("a1_real", items_by_stratum[s]) for s in eligible]
        m = [float(v.mean()) for v in ga1]
        se = [paired_se(v) for v in ga1]
        flags = [mm > 0 and mm >= 2 * ss for mm, ss in zip(m, se)]
        want_rg = spearman(q, g)
        got_rg = payload["rank_statistics"][a]["rho_gain"]["estimate"]
        chk(f"rho_gain[{a}]", got_rg, want_rg, tol=1e-9)
        rq = [x for x, f in zip(q, flags) if f]
        rv = [gg / mm for gg, mm, f in zip(g, m, flags) if f]
        want_rr = spearman(rq, rv)
        got_rr = payload["rank_statistics"][a]["rho_recovery"]["estimate"]
        chk(f"rho_recovery[{a}]", got_rr, want_rr, tol=1e-9)
        # W3: mean of per-seed rho values; W4: seed-1 only
        per_seed_rho = []
        for sd in (1, 2):
            gs = [float(gain_seed(a, sd, items_by_stratum[s]).mean()) for s in eligible]
            per_seed_rho.append(spearman(q, gs))
        w3 = (
            float(np.mean([r for r in per_seed_rho]))
            if all(r is not None for r in per_seed_rho)
            else None
        )
        w4 = per_seed_rho[0]
        if got_rg is not None:
            if w3 is not None and abs(w3 - want_rg) > 1e-9 and abs(got_rg - w3) < 1e-12:
                problems.append(f"W3 MEAN-OF-PER-SEED-RHO detected for {a}")
            if w4 is not None and abs(w4 - want_rg) > 1e-9 and abs(got_rg - w4) < 1e-12:
                problems.append(f"W4 SEED-1-ONLY rho detected for {a}")
        print(
            f"  {a}: rho_gain two-seed={want_rg} instrument={got_rg} "
            f"| per-seed={per_seed_rho} mean-of-rho={w3}"
        )

    # ---- seed dispersion per-seed values ---------------------------------
    disp = payload["seed_dispersion"]
    for sd in (1, 2):
        blk = disp["per_seed"][f"seed{sd}"]
        for a in ARMS:
            chk(
                f"dispersion.seed{sd}.corpus.gain[{a}]",
                blk["corpus"][a]["gain"],
                float(gain_seed(a, sd, keys).mean()),
            )
        for a in BLIND:
            d = gain_seed("a1_real", sd, keys)
            dm, dse = float(d.mean()), paired_se(d)
            if dm > 0 and dm >= 2 * dse:
                chk(
                    f"dispersion.seed{sd}.aggregate_recovery[{a}]",
                    blk["aggregate_recovery"][a]["estimate"],
                    float(gain_seed(a, sd, keys).mean() / dm),
                )
        if blk.get("scope_tag") != f"one seed (seed {sd})":
            problems.append(f"per-seed block {sd} scope_tag = {blk.get('scope_tag')!r}")
        checks += 1

    print(f"\nindependent checks run: {checks}")
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
        raise SystemExit(1)
    print("INDEPENDENT VERDICT: instrument matches the registered two-seed estimator")
    print("and matches NONE of the forbidden alternatives (W1-W4).")


if __name__ == "__main__":
    main()
