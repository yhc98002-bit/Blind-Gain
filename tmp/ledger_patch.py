#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()

subs = [
    ("| D3b | TrainShare estimand + paired item-level CIs | pending | PAPER1 §8 branches. Must be labeled a declared post-hoc recomputation — all 36 cells were read under the ratio-based D3 registration. |",
     "| D3b | TrainShare estimand + paired item-level CIs | pass | Pooled 0.487 / 0.528 / 0.718, every CI entirely above 0.35 → **headline at full strength**. Labeled a declared post-hoc recomputation (does not satisfy I9). `reports/d3_trainshare_v1.*`. |"),
    ("| F2d | Template decomposition of overall R19 movement | pending | Cached predictions, no new inference. |",
     "| F2d | Template decomposition of overall R19 movement | pass | Movement concentrates on the oracle-localized readout control (70% of A1's overall); primary anchor flat (CI spans zero). **Correction: the header table is not saturated at 1.000 — base 0.8667, contributes 18.7%.** Blind arms decline on the anchor while rising on the cued control. `reports/f2d_template_decomposition_v1.*`. |"),
    ("| G0.1 | A1 gains vs Δq concentration | pending | Δq source = blind-solvability audit (real vs none, 2,702 items). Base step-0 geo3k eval running to supply per-item base under the arm harness. |",
     "| G0.1 | A1 gains vs Δq concentration | pass | Monotone across Δq terciles for **both** A1 and A2b (ρ +0.198 / +0.192, perm p ≤ 0.0005). H1 supported; C1 necessity sampling earns its place. |"),
    ("| G0.2 | A2b image-present gain vs blind solvability | pending | **Freezes Paper 1's title claim.** |",
     "| G0.2 | A2b image-present gain vs blind solvability | pass | **Opposite of the hypothesis**: concentrates on blind-*answerable* items — 84% of A1's gain there vs 42% where no blind success was observed (91% vs 61% base-wrong control). Title claim survives with a scope qualifier; direct support for H1. |"),
    ("| G0.3 | A1/A2b newly-correct overlap (Jaccard + permutation null) | pending | |",
     "| G0.3 | A1/A2b newly-correct overlap (Jaccard + permutation null) | pass | Jaccard 0.363–0.423 vs null 0.157–0.177, p ≤ 0.004 all seeds. Overlapping policies, ~60% of the union arm-specific. |"),
    ("| G0.4 | Answer-gain vs format-gain split of A2b's gain | pending | Per-arm `strict_gain_accounting` already carries AnswerGain / G_format with `identity_exact`. |",
     "| G0.4 | Answer-gain vs format-gain split of A2b's gain | pass | Format gain **exactly +0.1148 for all four arms** by identity (every trained arm has acc_strict == acc_final, so it collapses to base_final − base_strict). The access matrix is format-free by construction. |"),
]
for old, new in subs:
    if old not in t:
        raise SystemExit(f"anchor missing: {old[:60]}")
    t = t.replace(old, new, 1)

t = t.replace("Updated 2026-07-27.",
              "Updated 2026-07-27 (Gate 0 and Phase 0 P0.1/P0.2 complete; F2d and TrainShare landed).")
p.write_text(t)
print("ledger updated")
