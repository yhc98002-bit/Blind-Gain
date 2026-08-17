#!/usr/bin/env python3
"""Adversarial verifier fixture: build a tiny synthetic two-seed M7 input and an
INDEPENDENT reference computation of every registered estimand, written from the
registration text (not from build_m7_r3_readout.py).

Usage: python make_fixture.py <root_dir>
Writes the fixture tree under <root_dir> and prints reference JSON to
<root_dir>/reference.json
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
BLIND = ("a2_gray", "a2b_noimage", "a3_caption")
COND = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
GEO3K = {"a2_gray": 0.0789, "a2b_noimage": 0.1184}

# ---------------------------------------------------------------- strata
# 3 eligible strata of 30 items each, 1 descriptive-small-n stratum of 5.
STRATA = [
    ("srcA", "catX", 30),
    ("srcA", "catY", 30),
    ("srcB", "catX", 30),
    ("srcB", "catY", 5),
]

# arm -> per-stratum constant q_i.  Different rank orders per arm on purpose so
# rho_gain / rho_recovery differ between arms.
QVALS = {
    "a1_real": [0.10, 0.20, 0.30, 0.40],
    "a2_gray": [0.10, 0.30, 0.20, 0.40],
    "a2b_noimage": [0.30, 0.20, 0.10, 0.40],
    "a3_caption": [0.20, 0.10, 0.30, 0.40],
}


def items():
    """(row_index, qid, source, category, stratum_index, position_in_stratum)."""
    out = []
    row = 0
    for s_index, (src, cat, n) in enumerate(STRATA):
        for j in range(n):
            out.append((row, f"q{row:04d}", src, cat, s_index, j))
            row += 1
    return out


ITEMS = items()


def acc0_of(a, s, j):
    return ((j + a) % 4) == 0


def acc100_of(a, s, j, seed):
    base = acc0_of(a, s, j)
    if seed == 1:
        improved = (not base) and ((j + 2 * a + s) % 5 == 0)
        regress = base and ((j + a + 3 * s) % 7 == 0)
    else:
        improved = (not base) and ((j + 2 * a + s) % 4 == 0)
        regress = base and ((j + a + 3 * s) % 9 == 0)
    return (base and not regress) or improved


def build(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    data = root / "data"
    data.mkdir(exist_ok=True)
    # held-out manifest
    lines = []
    for row, qid, src, cat, s_index, j in ITEMS:
        lines.append(
            json.dumps(
                {
                    "qid": qid,
                    "row_index": row,
                    "split": "heldout",
                    "metadata": {"source": src, "category": cat},
                },
                sort_keys=True,
            )
        )
    heldout = data / "fixture_heldout.jsonl"
    heldout.write_text("\n".join(lines) + "\n", encoding="utf-8")

    runs = root / "runs"
    runs.mkdir(exist_ok=True)
    for a, arm in enumerate(ARMS):
        # step 0
        d = runs / f"step0_{arm}"
        d.mkdir(exist_ok=True)
        rows = []
        for row, qid, src, cat, s_index, j in ITEMS:
            base = acc0_of(a, s_index, j)
            q = QVALS[arm][s_index]
            correct_count = 0 if (not base and row % 5 == 0) else (4 if base else 1)
            rows.append(
                json.dumps(
                    {
                        "qid": qid,
                        "row_index": row,
                        "split": "heldout",
                        "condition": COND[arm],
                        "greedy_canonical_correct": bool(base),
                        "sample_count": 16,
                        "sample_correct_count": correct_count,
                        "q_i": q,
                        "p_i_jeffreys": q,
                    },
                    sort_keys=True,
                )
            )
        (d / "per_item.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
        (d / "run_manifest.json").write_text(
            json.dumps(
                {
                    "run_id": f"step0_{arm}",
                    "status": "complete",
                    "condition": COND[arm],
                    "model_path": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
                    "model_revision": "66285546d2b821cf421d4f5eb2576359d3770cd3",
                    "job_type": "eval",
                    "node": "fixture",
                    "git_hash": "0" * 40,
                    "config_hash": "cfg0",
                    "seed": 20260710,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        for seed in (1, 2):
            d = runs / f"step100_{arm}_seed{seed}"
            d.mkdir(exist_ok=True)
            rows = []
            for row, qid, src, cat, s_index, j in ITEMS:
                rows.append(
                    json.dumps(
                        {
                            "qid": qid,
                            "row_index": row,
                            "split": "heldout",
                            "condition": COND[arm],
                            "greedy_canonical_correct": bool(
                                acc100_of(a, s_index, j, seed)
                            ),
                        },
                        sort_keys=True,
                    )
                )
            (d / "per_item.jsonl").write_text(
                "\n".join(rows) + "\n", encoding="utf-8"
            )
            (d / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "run_id": f"step100_{arm}_seed{seed}",
                        "status": "complete",
                        "condition": COND[arm],
                        "model_path": (
                            f"checkpoints/m7/m7_virl_{arm}_seed{seed}/"
                            "global_step_100/actor/huggingface"
                        ),
                        "job_type": "eval",
                        "node": "fixture",
                        "git_hash": "0" * 40,
                        "config_hash": "cfg100",
                        "seed": 20260710,
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    sha = hashlib.sha256(heldout.read_bytes()).hexdigest()
    return sha


# ------------------------------------------------------------------ reference
def rankavg(x):
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(x):
        k = i
        while k + 1 < len(x) and x[order[k + 1]] == x[order[i]]:
            k += 1
        avg = (i + k) / 2.0 + 1.0
        for t in range(i, k + 1):
            ranks[order[t]] = avg
        i = k + 1
    return ranks


def spearman(a, b):
    ra, rb = rankavg(a), rankavg(b)
    if np.all(ra == ra[0]) or np.all(rb == rb[0]):
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def se(v):
    v = np.asarray(v, dtype=float)
    return float(v.std(ddof=1) / math.sqrt(v.size)) if v.size > 1 else 0.0


def reference(seeds):
    """Independent computation from the registration text."""
    # per-arm per-item vectors, in (qid, row_index) sorted order == row order
    acc0 = {}
    accS = {}
    qv = {}
    strat = []
    for row, qid, src, cat, s_index, j in ITEMS:
        strat.append((src, cat))
    for a, arm in enumerate(ARMS):
        acc0[arm] = np.array(
            [acc0_of(a, s, j) for _, _, _, _, s, j in ITEMS], dtype=float
        )
        qv[arm] = np.array([QVALS[arm][s] for _, _, _, _, s, j in ITEMS], dtype=float)
        accS[arm] = {
            sd: np.array(
                [acc100_of(a, s, j, sd) for _, _, _, _, s, j in ITEMS], dtype=float
            )
            for sd in seeds
        }
    # registered estimator: per-item mean across seeds, minus the shared step-0
    gain = {
        arm: np.mean([accS[arm][sd] for sd in seeds], axis=0) - acc0[arm]
        for arm in ARMS
    }
    gain_per_seed = {
        arm: {sd: accS[arm][sd] - acc0[arm] for sd in seeds} for arm in ARMS
    }
    masks = {}
    for s_index, (src, cat, n) in enumerate(STRATA):
        m = np.array([st == (src, cat) for st in strat])
        masks[(src, cat)] = m
    eligible = [
        (src, cat) for (src, cat, n) in STRATA if n >= 30
    ]
    eligible = sorted(eligible)

    out = {"strata": {}, "corpus": {}, "rank": {}, "per_seed": {}}

    # ---- per-stratum
    for (src, cat, n) in STRATA:
        m = masks[(src, cat)]
        row = {"n": int(m.sum()), "eligible": bool(n >= 30)}
        row["q_bar"] = {arm: float(qv[arm][m].mean()) for arm in ARMS}
        row["gain"] = {arm: float(gain[arm][m].mean()) for arm in ARMS}
        row["paired_se"] = {arm: se(gain[arm][m]) for arm in ARMS}
        a1m = float(gain["a1_real"][m].mean())
        a1s = se(gain["a1_real"][m])
        stable = bool(a1m > 0 and a1m >= 2 * a1s)
        row["a1_stable"] = stable
        row["recovery"] = {
            arm: (float(gain[arm][m].mean() / a1m) if stable else None)
            for arm in BLIND
        }
        row["acc_final_step100"] = {
            arm: float(np.mean([accS[arm][sd][m] for sd in seeds]))
            for arm in ARMS
        }
        out["strata"][f"{src}||{cat}"] = row

    # ---- corpus
    a1c = float(gain["a1_real"].mean())
    a1cse = se(gain["a1_real"])
    cstable = bool(a1c > 0 and a1c >= 2 * a1cse)
    out["corpus"] = {
        "gain": {arm: float(gain[arm].mean()) for arm in ARMS},
        "paired_se": {arm: se(gain[arm]) for arm in ARMS},
        "a1_stable": cstable,
        "aggregate_recovery": {
            arm: (float(gain[arm].mean() / a1c) if cstable else None)
            for arm in BLIND
        },
        "acc_final_step0": {arm: float(acc0[arm].mean()) for arm in ARMS},
        "acc_final_step100": {
            arm: float(np.mean([accS[arm][sd] for sd in seeds])) for arm in ARMS
        },
        "q_bar": {arm: float(qv[arm].mean()) for arm in ARMS},
    }
    out["corpus"]["anchor_difference"] = {
        arm: (
            None
            if out["corpus"]["aggregate_recovery"][arm] is None
            else out["corpus"]["aggregate_recovery"][arm] - GEO3K[arm]
        )
        for arm in GEO3K
    }

    # ---- rank statistics over eligible strata
    for arm in BLIND:
        qb = [out["strata"][f"{s}||{c}"]["q_bar"][arm] for (s, c) in eligible]
        gg = [out["strata"][f"{s}||{c}"]["gain"][arm] for (s, c) in eligible]
        flags = [out["strata"][f"{s}||{c}"]["a1_stable"] for (s, c) in eligible]
        rec = [
            out["strata"][f"{s}||{c}"]["recovery"][arm]
            for (s, c), f in zip(eligible, flags)
            if f
        ]
        recq = [q for q, f in zip(qb, flags) if f]
        out["rank"][arm] = {
            "rho_gain": spearman(qb, gg),
            "rho_recovery": spearman(recq, rec) if len(rec) >= 2 else None,
            "n_strata": len(eligible),
            "n_recovery_strata": len(rec),
        }

    # ---- descriptive per-seed
    for sd in seeds:
        g = {arm: gain_per_seed[arm][sd] for arm in ARMS}
        a1m = float(g["a1_real"].mean())
        a1s = se(g["a1_real"])
        st = bool(a1m > 0 and a1m >= 2 * a1s)
        block = {
            "corpus_gain": {arm: float(g[arm].mean()) for arm in ARMS},
            "corpus_paired_se": {arm: se(g[arm]) for arm in ARMS},
            "corpus_acc_final_step100": {
                arm: float(accS[arm][sd].mean()) for arm in ARMS
            },
            "a1_stable": st,
            "aggregate_recovery": {
                arm: (float(g[arm].mean() / a1m) if st else None) for arm in BLIND
            },
            "rank": {},
        }
        a1means = [float(g["a1_real"][masks[e]].mean()) for e in eligible]
        a1ses = [se(g["a1_real"][masks[e]]) for e in eligible]
        flags = [m > 0 and m >= 2 * s for m, s in zip(a1means, a1ses)]
        for arm in BLIND:
            qb = [float(qv[arm][masks[e]].mean()) for e in eligible]
            gg = [float(g[arm][masks[e]].mean()) for e in eligible]
            rec = [x / a for x, a, f in zip(gg, a1means, flags) if f]
            recq = [q for q, f in zip(qb, flags) if f]
            block["rank"][arm] = {
                "rho_gain": spearman(qb, gg) if len(eligible) >= 2 else None,
                "rho_recovery": spearman(recq, rec) if len(rec) >= 2 else None,
                "n_strata": len(eligible),
                "n_recovery_strata": len(rec),
            }
        out["per_seed"][f"seed{sd}"] = block
    return out


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    sha = build(root)
    ref = {
        "heldout_sha256": sha,
        "rows": len(ITEMS),
        "eligible": 3,
        "small_n": 1,
        "two_seed": reference((1, 2)),
        "one_seed": reference((1,)),
    }
    (root / "reference.json").write_text(
        json.dumps(ref, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"sha256": sha, "rows": len(ITEMS)}, sort_keys=True))
