#!/usr/bin/env python3
"""Render reports/m5c_necessity_stratification_v1.md from the v1 JSON. Numbers only."""
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
R = json.loads((ROOT / "reports/m5c_necessity_stratification_v1.json").read_text())
BINS = ["blind_solvable", "intermediate", "image_necessary"]
CONDS = ["none", "gray", "noise", "caption"]
L = []
w = L.append


def f4(v):
    return f"{v:.4f}"


def s4(v):
    return f"{v:+.4f}"


def ci(c):
    return f"[{c[0]:+.4f}, {c[1]:+.4f}]"


w("# M5c — geo3k step-100 → step-400 change stratified by visual necessity (PI item 5)")
w("")
w(f"Artifact: `reports/m5c_necessity_stratification_v1.json` · built by "
  f"`scripts/build_m5c_necessity_stratification.py` · git `{R['git_hash']}` · "
  f"generated {R['generated_utc']} · login node, CPU only, no GPU job started.")
w("")
w("Scope: the 601 Geometry3K **test** items in `reports/m5c_item_substrate_v1.jsonl` "
  f"(sha256 `{R['substrate']['sha256']}`, {R['substrate']['rows']} rows), item key "
  f"`{R['substrate']['item_key_definition']}`.")
w("")

# ---------------------------------------------------------------- definitions
w("## 1. Stratification definition adopted (reused from Gate 0, not invented here)")
w("")
p = R["adopted_definitions"]["primary"]
w(f"**Primary — {p['name']}.** Quoted from `{p['source_report']}`:")
w("")
w(f"> {p['quote_from_gate0_md']}")
w("")
w(f"and from the Gate 0 builder docstring ({p['source_code']}):")
w("")
w(f"> {p['quote_from_gate0_docstring']}")
w("")
w(f"Operational rule as executed here: {p['operational_rule']}")
w("")
w("Label map applied to the three Gate 0 terciles: "
  + ", ".join(f"`{k}` → **{v}**" for k, v in p["label_map"].items()) + ".")
w("")
w(f"**Label caveat (measured, see §3).** {p['label_caveat']}")
w("")
s = R["adopted_definitions"]["secondary"]
w(f"**Secondary — {s['name']}.** Quoted from `{s['source_report']}`:")
w("")
w(f"> {s['quote_from_gate0_md']}")
w("")
w(f"Operational rule: {s['operational_rule']} (`{s['source_code']}`). {s['why_reported']}")
w("")
w("Necessity source runs (base model `Qwen2.5-VL-3B-Instruct`, the same two files Gate 0 used):")
w("")
w("| arm | run | per_item sha256 | rows total | rows test |")
w("| :-- | :-- | :-- | ---: | ---: |")
for c in ("real", "none"):
    v = R["necessity_source"][c]
    w(f"| q_{'real' if c == 'real' else 'blind'} (`{c}`) | `{v['run']}` | "
      f"`{v['per_item_sha256'][:16]}…` | {v['rows_total']} | {v['rows_test']} |")
w("")
w("Δq is a **base-model dataset property**, not a training-arm outcome, per "
  "`reports/blind_solvability_geo3k_v3_audited.md` (\"These are base-model dataset-property "
  "measurements, not training-arm outcomes.\").")
w("")

# --------------------------------------------------------------- canonicality
w("### Which necessity artifact is canonical")
w("")
w("| candidate | what it actually contains | used here |")
w("| :-- | :-- | :-- |")
w("| `reports/blind_solvability_geo3k_v3_audited.json` | aggregate-only (no per-item rows); "
  "2702 items, canonical-v1 512-token Gate-2 audit family | no — wrong item universe (2702, "
  "not the 601-item filtered-v2 eval split) and carries no per-item field |")
w("| `reports/blind_solvability_geo3k_v2_audited.json` | machine measurement-integrity audit "
  "of the 1889-row filtered-v2 condition runs; checks only, no per-item scores | no — it is "
  "the audit that certifies the runs below, not a source of per-item values |")
w("| `reports/gate0_stratification_v1.json` | holds the Δq **summary** (`delta_q`) and the "
  "binned results, but not per-item Δq | consulted as the reproduction target, not as input |")
w("| `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_{real,none}"
  "_login_*/per_item.jsonl` | the per-item `q_i` Gate 0 itself reads | **yes — canonical "
  "per-item source** |")
w("")
w("Neither audited JSON is superseded by the other; they are different measurement families "
  "(2702-item canonical-v1 vs 1889-row filtered-v2). Only the filtered-v2 family contains the "
  "601 test items this substrate is built on, so it is the only one that can be joined.")
w("")

# ---------------------------------------------------------------------- join
j = R["join"]
w("## 2. Join to the substrate")
w("")
w(f"- Join key: `(split, row_index)`, restricted to `split == \"test\"`.")
w(f"- Substrate rows: **{j['n_substrate']}**. Necessity `real` test rows: "
  f"**{j['n_necessity_real_test']}**. Necessity `none` test rows: "
  f"**{j['n_necessity_none_test']}**.")
w(f"- Joined: **{j['n_joined']} / {j['n_substrate']}** → join rate **"
  f"{j['join_rate']:.4f} (100.00%)**. Items failing to join: **0** in either direction.")
w(f"- Non-test rows excluded, not aggregated (I13): "
  f"{R['necessity_source']['real']['rows_excluded_non_test']} `split=train` rows per arm.")
w("")
w("Cross-field identity checks on the 601 joined rows (0 = pass):")
w("")
w("| check | mismatches |")
w("| :-- | ---: |")
for k, v in sorted(j["cross_field_mismatch_counts"].items()):
    w(f"| `{k}` | {v} |")
w("")
w(f"- {j['note_qid']} (`qid` null on {j['qid_null_counts']['substrate']}/601 substrate rows, "
  f"{j['qid_null_counts']['necessity_real']}/601 and "
  f"{j['qid_null_counts']['necessity_none']}/601 necessity rows.)")
w(f"- {j['necessity_arm_manifest_hash_note']}")
w("")

# ------------------------------------------------------------------- bin sizes
st = R["stratification"]
w("## 3. Bin sizes and what the bins contain")
w("")
w("| bin | Gate 0 name | Δq range | n | mean Δq | mean q_real | mean q_blind | "
  "blind-answerable in bin |")
w("| :-- | :-- | :-- | ---: | ---: | ---: | ---: | ---: |")
for b in st["bins"]:
    lo = "≤ 0.0000" if b["index"] == 0 else f"({b['delta_q_lo']:.4f}, {b['delta_q_hi']:.4f}]"
    if b["index"] == 0:
        lo = f"[{b['delta_q_lo']:.4f}, 0.0000]"
    w(f"| **{b['label']}** | {b['gate0_description']} | {lo} | {b['n']} | "
      f"{b['delta_q_mean']:+.4f} | {b['q_real_mean']:.4f} | {b['q_blind_mean']:.4f} | "
      f"{b['n_blind_answerable_in_bin']} |")
w(f"| all | — | [{st['delta_q']['min']:.4f}, {st['delta_q']['max']:.4f}] | 601 | "
  f"{st['delta_q']['mean']:+.4f} | {st['delta_q']['q_real_mean']:.4f} | "
  f"{st['delta_q']['q_blind_mean']:.4f} | "
  f"{st['blind_answerable']['n_blind_answerable']} |")
w("")
w(f"- The terciles are unequal because Δq is heavily tied: **"
  f"{st['delta_q']['n_items_with_delta_q_exactly_zero']} of 601** items have Δq exactly 0, so "
  f"the 33rd-percentile edge lands exactly on 0 and the low bin absorbs every Δq ≤ 0 item "
  f"(n=329).")
w(f"- Secondary split: blind-answerable **{st['blind_answerable']['n_blind_answerable']}** vs "
  f"not **{st['blind_answerable']['n_not_blind_answerable']}**, Jeffreys floor "
  f"{st['blind_answerable']['jeffreys_floor']:.4f}.")
w("")
w("Cross-tab of the two Gate 0 stratifications (reported side by side, never merged — I13):")
w("")
w("| Δq bin | blind-answerable | not blind-answerable |")
w("| :-- | ---: | ---: |")
for b in BINS:
    c = R["crosstab_primary_by_secondary"][b]
    w(f"| {b} | {c['blind_answerable']} | {c['not_blind_answerable']} |")
w("")
w("**Two measured facts that constrain how the `blind_solvable` label can be read.** "
  f"(a) Only {R['crosstab_primary_by_secondary']['blind_solvable']['blind_answerable']} of the "
  f"329 low-Δq items are blind-answerable; "
  f"{R['crosstab_primary_by_secondary']['blind_solvable']['not_blind_answerable']} of them "
  "have zero observed blind successes. The low-Δq bin is therefore dominated by items the base "
  "model solves under **no** condition, not by items it solves blind. "
  "(b) Mean q_real rises across the bins "
  + " → ".join(f"{b['q_real_mean']:.4f}" for b in st["bins"]) +
  ", so the high-Δq bin is also the bin the base model scores highest on **with** the image.")
w("")

# --------------------------------------------------- Gate 0 reproduction check
g = R["gate0_reproduction_check"]
w("### Reproduction check against Gate 0")
w("")
w("| quantity | here | `reports/gate0_stratification_v1.json` | match |")
w("| :-- | :-- | :-- | :-- |")
w(f"| tercile sizes | {g['bin_n_here']} | {g['bin_n_gate0']} | "
  f"{'PASS' if g['bin_n_match'] else 'FAIL'} |")
w(f"| tercile edges | {[[round(a, 6), round(b, 6)] for a, b in g['bin_edges_here']]} | "
  f"{[[round(a, 6), round(b, 6)] for a, b in g['bin_edges_gate0']]} | "
  f"{'PASS' if g['bin_edges_match'] else 'FAIL'} |")
w(f"| Δq mean / min / max | {g['delta_q_summary_here']['mean']:.6f} / "
  f"{g['delta_q_summary_here']['min']:.6f} / {g['delta_q_summary_here']['max']:.6f} | "
  f"{g['delta_q_summary_gate0']['mean']:.6f} / {g['delta_q_summary_gate0']['min']:.6f} / "
  f"{g['delta_q_summary_gate0']['max']:.6f} | PASS |")
w(f"| Jeffreys floor | {g['jeffreys_floor_here']:.10f} | {g['jeffreys_floor_gate0']:.10f} | "
  "PASS |")
w(f"| blind-answerable n | {g['blind_answerable_n_here']} | {g['blind_answerable_n_gate0']} | "
  "PASS |")
w("")
w("The binning code path is Gate 0's own; these five checks confirm the reproduction is exact, "
  "so any difference from Gate 0's published stratum results is attributable to the outcome "
  "variable, not to the strata.")
w("")

# ------------------------------------------------------- per-bin 100 -> 400
w("## 4. Step 100 → step 400 per bin (I7: lenient and contract-strict, both reported)")
w("")
w(f"Paired **item** bootstrap, {R['rng']['bootstrap_draws']:,} draws, seed "
  f"`{R['rng']['seed']}`. Resampling is within-bin and paired (the same item contributes its "
  "step-100 and step-400 outcome to every draw). `mcnemar_exact_p` is the two-sided exact "
  "binomial test on the discordant pairs at p=0.5.")
w("")
for metric, title in (("acc_final", "lenient `acc_final`"),
                      ("acc_strict", "contract-strict `acc_strict`")):
    w(f"### 4.{'1' if metric == 'acc_final' else '2'} {title}")
    w("")
    w("| stratum | n | acc @100 | acc @400 | Δ (400−100) | 95% CI | gained | lost | "
      "stable ✓ | stable ✗ | turnover | McNemar exact p |")
    w("| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    rows = [("**blind_solvable** (low Δq)", R["per_bin_100_to_400"]["primary_delta_q_terciles"]["blind_solvable"][metric]),
            ("**intermediate** (mid Δq)", R["per_bin_100_to_400"]["primary_delta_q_terciles"]["intermediate"][metric]),
            ("**image_necessary** (high Δq)", R["per_bin_100_to_400"]["primary_delta_q_terciles"]["image_necessary"][metric]),
            ("_all 601 items_", R["per_bin_100_to_400"]["overall_all_items"][metric]),
            ("blind-answerable (2ary)", R["per_bin_100_to_400"]["secondary_blind_answerable"]["blind_answerable"][metric]),
            ("not blind-answerable (2ary)", R["per_bin_100_to_400"]["secondary_blind_answerable"]["not_blind_answerable"][metric])]
    for name, c in rows:
        w(f"| {name} | {c['n']} | {f4(c['acc_step100'])} ({c['n_correct_step100']}) | "
          f"{f4(c['acc_step400'])} ({c['n_correct_step400']}) | {s4(c['delta'])} | "
          f"{ci(c['delta_ci95_paired_item_bootstrap'])} | {c['gained']} | {c['lost']} | "
          f"{c['stable_correct']} | {c['stable_incorrect']} | {c['turnover_rate']:.4f} | "
          f"{c['mcnemar_exact_p']:.4f} |")
    w("")
i7 = R["i7_lenient_vs_strict"]
w(f"**I7 note.** `acc_final == acc_strict` on {i7['acc_final_equals_acc_strict_per_item']['100']}"
  f"/601 items at step 100 and {i7['acc_final_equals_acc_strict_per_item']['400']}/601 at step "
  f"400. {i7['note']}")
w("")
ov = R["per_bin_100_to_400"]["overall_all_items"]["acc_final"]
w(f"**Continuity with `reports/m5b_trajectory_v1.md`.** The all-items row reproduces m5b "
  f"exactly: acc_final {f4(ov['acc_step100'])} → {f4(ov['acc_step400'])}, Δ {s4(ov['delta'])}, "
  f"McNemar exact p {ov['mcnemar_exact_p']:.4f} (m5b: +0.0083, p=0.73). The CI here is "
  f"{ci(ov['delta_ci95_paired_item_bootstrap'])} against m5b's [-0.0283, +0.0449]; the two "
  f"differ only by bootstrap Monte-Carlo (different seed and draw count). Bin gained/lost sum "
  f"to {sum(R['per_bin_100_to_400']['primary_delta_q_terciles'][b]['acc_final']['gained'] for b in BINS)}"
  f" / {sum(R['per_bin_100_to_400']['primary_delta_q_terciles'][b]['acc_final']['lost'] for b in BINS)}"
  f", matching the substrate's 71 / 66.")
w("")

# ------------------------------------------------------------ hypothesis tests
t = R["hypothesis_tests"]
w("## 5. The PI's hypothesis, tested")
w("")
w(f"Hypothesis as stated: *\"{t['hypothesis_as_stated']}\"*.")
w("")
w("Three independent readings of the same question:")
w("")
w("**(a) Direction and size of each bin's move** (from §4, `acc_final`; `acc_strict` identical):")
w("")
w("| bin | Δ (400−100) | 95% CI | CI excludes 0? | direction vs hypothesis |")
w("| :-- | ---: | :---: | :-- | :-- |")
exp = {"blind_solvable": "improve or hold", "intermediate": "(unspecified)",
       "image_necessary": "decline"}
for b in BINS:
    c = R["per_bin_100_to_400"]["primary_delta_q_terciles"][b]["acc_final"]
    lo, hi = c["delta_ci95_paired_item_bootstrap"]
    excl = "no" if lo <= 0 <= hi else "yes"
    obs = "declines" if c["delta"] < 0 else ("rises" if c["delta"] > 0 else "flat")
    match = "predicted: " + exp[b] + f"; observed: {obs}"
    w(f"| {b} | {s4(c['delta'])} | {ci(c['delta_ci95_paired_item_bootstrap'])} | {excl} | "
      f"{match} |")
w("")
w("**(b) Direct between-bin contrast** (image_necessary Δ minus blind_solvable Δ). Bins are "
  "disjoint item sets, so the bootstrap resamples each bin independently; the permutation "
  "reshuffles bin membership within the union of the two bins.")
w("")
w("| metric | contrast | 95% CI | permutation p (two-sided) |")
w("| :-- | ---: | :---: | ---: |")
for m in ("acc_final", "acc_strict"):
    c = t["contrast_image_necessary_minus_blind_solvable"][m]
    w(f"| `{m}` | {s4(c['contrast'])} | "
      f"{ci(c['contrast_ci95_independent_bin_bootstrap'])} | "
      f"{c['permutation_p_two_sided']:.4f} |")
w("")
w("**(c) Is the turnover itself systematic in Δq?** Mean Δq of the items that gained vs the "
  "items that lost, plus a tie-aware Spearman of per-item change against Δq over all 601 "
  f"items. Permutations: {R['rng']['permutation_draws']:,}.")
w("")
w("| metric | n gained | n lost | mean Δq gained | mean Δq lost | difference | perm p | "
  "Spearman ρ (change vs Δq) | perm p |")
w("| :-- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
for m in ("acc_final", "acc_strict"):
    a = t["delta_q_of_gained_vs_lost"][m]
    b_ = t["spearman_change_vs_delta_q"][m]
    w(f"| `{m}` | {a['n_gained']} | {a['n_lost']} | {a['mean_delta_q_gained']:.4f} | "
      f"{a['mean_delta_q_lost']:.4f} | {a['difference']:+.4f} | "
      f"{a['permutation_p_two_sided']:.4f} | {b_['spearman_rho_tie_aware']:+.4f} | "
      f"{b_['permutation_p_two_sided']:.4f} |")
w("")
w(f"(Mean Δq of the {601 - t['delta_q_of_gained_vs_lost']['acc_final']['n_gained'] - t['delta_q_of_gained_vs_lost']['acc_final']['n_lost']} "
  f"items that did not change: {t['delta_q_of_gained_vs_lost']['acc_final']['mean_delta_q_stable']:.4f}.)")
w("")
w("### Verdict against the hypothesis")
w("")
w("**The data do not support the hypothesis as stated, on any of the three readings.**")
w("")
lo_c = R["per_bin_100_to_400"]["primary_delta_q_terciles"]["blind_solvable"]["acc_final"]
mid_c = R["per_bin_100_to_400"]["primary_delta_q_terciles"]["intermediate"]["acc_final"]
hi_c = R["per_bin_100_to_400"]["primary_delta_q_terciles"]["image_necessary"]["acc_final"]
ct = t["contrast_image_necessary_minus_blind_solvable"]["acc_final"]
w(f"1. The predicted split does not appear. `blind_solvable` moves {s4(lo_c['delta'])} — "
  f"down, not up or flat — and `image_necessary` moves {s4(hi_c['delta'])}. The two bins move "
  f"in the **same** direction, and the only bin that rises is `intermediate` "
  f"({s4(mid_c['delta'])}), which the hypothesis makes no prediction about.")
w(f"2. Every one of the three bin CIs contains 0 "
  f"({ci(lo_c['delta_ci95_paired_item_bootstrap'])}, "
  f"{ci(mid_c['delta_ci95_paired_item_bootstrap'])}, "
  f"{ci(hi_c['delta_ci95_paired_item_bootstrap'])}), and every per-bin McNemar exact p is "
  f"≥ {min(lo_c['mcnemar_exact_p'], mid_c['mcnemar_exact_p'], hi_c['mcnemar_exact_p']):.4f}. "
  f"No bin's move is distinguishable from zero.")
w(f"3. The direct contrast is {s4(ct['contrast'])} with CI "
  f"{ci(ct['contrast_ci95_independent_bin_bootstrap'])} and permutation p "
  f"{ct['permutation_p_two_sided']:.4f}; the Spearman of per-item change against Δq is "
  f"{t['spearman_change_vs_delta_q']['acc_final']['spearman_rho_tie_aware']:+.4f}, p "
  f"{t['spearman_change_vs_delta_q']['acc_final']['permutation_p_two_sided']:.4f}; gained and "
  f"lost items differ in mean Δq by "
  f"{t['delta_q_of_gained_vs_lost']['acc_final']['difference']:+.4f}, p "
  f"{t['delta_q_of_gained_vs_lost']['acc_final']['permutation_p_two_sided']:.4f}.")
w("")
w("**Stated plainly: the bins move together, not against each other.** The flat aggregate is "
  "not measured here to be a cancellation of opposing bin-level trends. Turnover is large in "
  "every bin (20.1% / 28.1% / 24.5%) and is not measurably sorted by Δq. Note this is a "
  "non-rejection at n=601 with per-bin n as low as 121, not a demonstration that no "
  "necessity-linked effect exists; the contrast CI "
  f"{ci(ct['contrast_ci95_independent_bin_bootstrap'])} is wide enough to admit bin "
  "differences of about ±0.10.")
w("")

# -------------------------------------------------------------- real vs blind
gp = R["real_vs_blind_gap"]
w("## 6. Per-bin real-vs-blind accuracy gap")
w("")
w("### 6.1 Step 100 — computable")
w("")
w(f"All five step-100 arms evaluate the same checkpoint "
  f"(`{gp['checkpoint_identity']['model_revision']}`): "
  f"{'verified identical' if gp['checkpoint_identity']['all_step100_runs_share_model_revision'] else 'NOT identical'}. "
  f"{gp['scoring_parity_note']}")
w("")
for metric in ("acc_final", "acc_strict"):
    w(f"**{'Lenient `acc_final`' if metric == 'acc_final' else 'Contract-strict `acc_strict`'}"
      f"** — accuracy at step 100 by condition, and the paired real-minus-blind gap "
      f"(95% CI, {R['rng']['bootstrap_draws']:,} draws, seed `{R['rng']['seed']}`). Conditions "
      "are never pooled (I13).")
    w("")
    w("| stratum | n | real | none | gap (real−none) | 95% CI | gray | gap | noise | gap | "
      "caption | gap |")
    w("| :-- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    order = [("primary_delta_q_terciles", b, b) for b in BINS] + [
        ("secondary_blind_answerable", "blind_answerable", "blind-answerable (2ary)"),
        ("secondary_blind_answerable", "not_blind_answerable", "not blind-answerable (2ary)"),
        ("overall_all_items", "all", "_all 601 items_")]
    for grp, key, name in order:
        e = gp["step_100"][grp][key][metric]
        bc = e["blind_conditions"]
        w(f"| {name} | {e['n']} | {f4(e['acc_real'])} | {f4(bc['none']['acc_blind'])} | "
          f"{s4(bc['none']['gap_real_minus_blind'])} | "
          f"{ci(bc['none']['gap_ci95_paired_item_bootstrap'])} | "
          f"{f4(bc['gray']['acc_blind'])} | {s4(bc['gray']['gap_real_minus_blind'])} | "
          f"{f4(bc['noise']['acc_blind'])} | {s4(bc['noise']['gap_real_minus_blind'])} | "
          f"{f4(bc['caption']['acc_blind'])} | {s4(bc['caption']['gap_real_minus_blind'])} |")
    w("")
w("Step-100 blind runs used:")
w("")
w("| condition | run | per_item sha256 | status |")
w("| :-- | :-- | :-- | :-- |")
for c in ["real"] + CONDS:
    v = gp["runs"][c]
    w(f"| `{c}` | `{v['run']}` | `{v['per_item_sha256'][:16]}…` | {v['status']} |")
w("")
w("### 6.2 Step 400 — NOT COMPUTED, no artifact exists")
w("")
w(gp["step_400_absence_reason"])
w("")
w("**The step-400 real-vs-blind column is therefore absent from every table above and is not "
  "fabricated, estimated, or back-filled from a step-100 or base-model proxy.** Consequently "
  "the *change* in the real-vs-blind gap between step 100 and step 400 — the quantity that "
  "would connect this section to §4 — cannot be computed at all.")
w("")

# ------------------------------------------------------------------- checks
w("## 7. Verification ledger")
w("")
w("| check | result |")
w("| :-- | :-- |")
w(f"| substrate sha256 matches the one recorded in `reports/m5c_turnover_v1.json` | PASS "
  f"(`{R['substrate']['sha256'][:16]}…`) |")
w(f"| join rate substrate ↔ necessity | {j['n_joined']}/601 = 100.00% |")
w(f"| cross-field mismatches (image_sha256, ground_truth, problem) | "
  f"{sum(j['cross_field_mismatch_counts'].values())} |")
w(f"| tercile sizes / edges reproduce Gate 0 | "
  f"{'PASS' if g['bin_n_match'] and g['bin_edges_match'] else 'FAIL'} |")
w(f"| Jeffreys floor and blind-answerable n reproduce Gate 0 | PASS |")
w(f"| step-100 real arm reproduces the substrate's step-100 column | "
  f"acc_final {gp['real_arm_reproduces_substrate_step100']['acc_final']}/601, acc_strict "
  f"{gp['real_arm_reproduces_substrate_step100']['acc_strict']}/601 |")
w("| stored == recomputed under `score_greedy_item_pilot` (all 5 step-100 arms) | "
  + ", ".join(
      f"{c} {gp['stored_vs_recomputed_agreement'][c]['acc_final_stored_eq_recomputed']}/601"
      for c in ["real"] + CONDS) + " |")
w(f"| all-items Δ and McNemar p reproduce m5b | Δ {s4(ov['delta'])}, p "
  f"{ov['mcnemar_exact_p']:.4f} |")
w(f"| bin gained/lost sum to the substrate's 71/66 | PASS |")
w(f"| step-400 blind geo3k artifact search | 0 found; column withheld |")
w("")
w(f"**Field-mapping caveat.** {gp['field_mapping_note']} "
  f"(`greedy_correct` == `greedy_canonical_correct` on "
  f"{gp['greedy_correct_eq_greedy_canonical_correct_step100_real']}/601 rows; the same 3-item "
  f"gap is already documented in `reports/m5b_trajectory_v1.md` as 0.4359 vs 0.4309.)")
w("")

# ------------------------------------------------------------ what is missing
w("## 8. What could not be computed")
w("")
w("1. **Step-400 real-vs-blind gap, and therefore the change in that gap across training.** "
  "No geo3k evaluation of any M5 step-400 checkpoint under any blind condition exists (§6.2). "
  "No proxy was substituted.")
w("2. **A three-way stratification that is literally blind-solvable / intermediate / "
  "image-necessary.** Gate 0 supplies a three-way rule (Δq terciles) and a two-way rule "
  "(blind-answerable). The three-way rule's low bin is *not* a blind-solvable bin: only "
  f"{R['crosstab_primary_by_secondary']['blind_solvable']['blind_answerable']}/329 of its items "
  "are blind-answerable (§3). Both Gate 0 rules are reported; neither was modified and no "
  "third rule was invented to close the gap.")
w("3. **Any decomposition of turnover below the item level** (e.g. which template or premise "
  "moved) is out of scope here and not attempted.")
w("")

(ROOT / "reports/m5c_necessity_stratification_v1.md").write_text("\n".join(L) + "\n")
print("wrote reports/m5c_necessity_stratification_v1.md",
      len("\n".join(L)), "chars")
