#!/usr/bin/env python3
"""Pre-flight verification for Task B: reproduce the prior agent's 0.2133 reference
figure from the step-100 sampled run, and confirm the greedy labels in the sampled
runs agree with the m5c substrate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

GUARDED = ROOT / "experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/per_item.jsonl"
RESCORE = ROOT / "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl"
SUBSTRATE = ROOT / "reports/m5c_item_substrate_v1.jsonl"


def load_test(path: Path) -> dict[str, dict]:
    out = {}
    for line in path.open():
        d = json.loads(line)
        if d.get("split") != "test":
            continue
        out[f'{d["split"]}:{d["row_index"]}'] = d
    return out


def main() -> None:
    g = load_test(GUARDED)
    r = load_test(RESCORE)
    sub = {}
    for line in SUBSTRATE.open():
        d = json.loads(line)
        sub[d["item_key"]] = d
    print("n test guarded", len(g), "rescore", len(r), "substrate", len(sub))
    assert set(g) == set(r) == set(sub)
    keys = sorted(sub, key=lambda k: int(k.split(":")[1]))

    # reference figure reproduction: p_i from step-100 sampled, applied at BOTH ends
    ps_raw = [r[k]["sample_correct_count"] / r[k]["sample_count"] for k in keys]
    ps_field = [r[k]["p_sample"] for k in keys]
    assert ps_raw == ps_field
    exp_same = sum(2 * p * (1 - p) for p in ps_raw) / len(ps_raw)
    print("mean p_i (rescore, lenient)      =", sum(ps_raw) / len(ps_raw))
    print("E[disc] p100 at both ends        =", exp_same, " (prior figure 0.21327735024958402)")
    print("count                            =", exp_same * len(ps_raw))

    # guarded (pre-rescore) version
    ps_g = [g[k]["sample_correct_count"] / g[k]["sample_count"] for k in keys]
    print("mean p_i (guarded, lenient)      =", sum(ps_g) / len(ps_g))
    print("guarded==rescore sample_correct  =",
          sum(1 for k in keys if g[k]["sample_correct"] == r[k]["sample_correct"]), "/", len(keys))

    # greedy label agreement with substrate
    ag_len = sum(1 for k in keys if bool(r[k]["greedy_correct"]) == bool(sub[k]["acc_final_step100"]))
    ag_str = sum(1 for k in keys if bool(r[k]["greedy_acc_strict"]) == bool(sub[k]["acc_strict_step100"]))
    print("rescore greedy_correct == substrate acc_final_step100 :", ag_len, "/", len(keys))
    print("rescore greedy_acc_strict == substrate acc_strict_100 :", ag_str, "/", len(keys))
    print("step100 greedy acc_final count   =", sum(1 for k in keys if sub[k]["acc_final_step100"]))
    print("step400 greedy acc_final count   =", sum(1 for k in keys if sub[k]["acc_final_step400"]))
    disc = sum(1 for k in keys if sub[k]["acc_final_step100"] != sub[k]["acc_final_step400"])
    print("observed greedy discordance      =", disc, "/", len(keys), "=", disc / len(keys))

    # strict sampled analogue availability
    n_bad = 0
    for k in keys:
        cv = r[k]["sampled_contract_valid"]
        sc = r[k]["sample_correct"]
        n_bad += sum(1 for a, b in zip(cv, sc) if b and not a)
    print("sampled rows correct-but-not-contract-valid (strict<lenient):", n_bad)


if __name__ == "__main__":
    main()
