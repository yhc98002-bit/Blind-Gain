# HB freeze record v1 — coordinate family + chart-v08 (2026-08-17)

Freeze under `docs/registered_hier_benchmark_v1.md` HB.8 + Amendments A3–A5.
Every number below is scored with **matcher v3** (`match-tier-v3-sign-aware`);
the superseded containment-scored values are in
`reports/matcher_v3_rescore_v1.{json,md}`. Nothing here is self-certified: the
human audit is recorded as passed by the PI on 2026-08-17.

## 1. What is frozen

| component | tier | status |
|---|---|---|
| `hier_coord_v1` @ r2 render, cells **n8, n12** | training + development instrument | **FROZEN** |
| `hier_coord_v1` @ r2, cell **n20** | exploratory hard tier | **FROZEN** (reported, never pooled into a confirmatory claim) |
| chart-v08 calibration family | calibration instrument | **FROZEN** (no-zoom audit passed by the PI 2026-08-17) |
| `hier_chart_v2` (9-series cells) | confirmatory instrument | pending its one-shot acceptance battery (Amendment A4) |
| `hier_chart_v1` | — | superseded, retained as the failed-acceptance archive |

The coordinate family is frozen as the **training/development instrument, not
the confirmatory one** — see §3.

## 2. HB.8 evidence (coordinate family, r2 render)

| requirement | result |
|---|---|
| human audit | **PASSED** — PI, 2026-08-17, on the 27-item r2 audit page (`reports/review_packages/hier_coord_r2_human_audit_20260817.html`) |
| informativeness (HB.7, base 3B, stable+invariance) | n8 **0.685 / 0.605 / 0.330** (L1/L2/L3) and n12 **0.655 / 0.605 / 0.260** pass every gate (monotone; L1∈[0.60,0.95]; L2∈[0.20,0.80]; L3≥0.05). n20 **0.520 / 0.480 / 0.245** fails the L1 band only → exploratory tier |
| blind floor | L3 gray **0.067 / 0.040 / 0.067** (n8/n12/n20), no_image identical to 4 dp; every discovery probe 0.0000 |
| attacker checks (4 attackers incl. permanent file_size) | pooled clean at **0.5144–0.5159** across three seeds; the single per-template marginal **moves across seeds** (n12 0.5569 → none → n20 0.5646) and one seed passes outright → CV-fold noise at the 0.55 line, family **clean** |
| caption stress (A5 ceiling) | n8 **0.265** vs 0.167 FAIL · n12 **0.150** vs 0.140 FAIL (marginal) · n20 **0.075** vs 0.167 PASS |
| verifier-operand audit | pass (hier gates added 2026-08-17; hier rows previously asserted nothing) |
| mother-item matching, program-level split | pass — from-disk verification 0 problems; 1,500/1,500 rows byte-identical to v1 outside image/provenance fields |

## 3. Why coord is not the confirmatory instrument

Caption leakage falls monotonically with scene density — **0.265 → 0.150 →
0.075** for n8 → n12 → n20 — while the L1 readout band fails in exactly the
densest cell. Expressed as caption recovery fraction (A5's secondary):
n8 **0.75**, n12 **0.50**, n20 **0.05**. So the coordinate cells that are
informative are transcribable, and the cell that resists transcription is not
informative: legibility and caption-resistance trade off along the coord
density knob. No coord cell is simultaneously informative and
caption-resistant, so none is confirmatory-eligible under A5.

This is why §6 of the registration reserved the confirmatory role for the
9-series chart cells "for caption resistance" — chart caption stress measures
**0.0413** against a **0.0000** blind floor (unaffected by the matcher fix:
one lenient credit in 800 members, `85` inside `85-90`). `hier_chart_v2`
inherits that property and carries the confirmatory tier once its battery
passes.

## 4. Consequences for downstream work

- **ST3-7B training split**: coord n8 + n12 training bucket (n20 excluded per
  PART 6; caption leakage does not disqualify *training* data, and it affects
  both arms identically), plus the accepted chart-v2 cells.
- **ST3 confirmatory endpoint**: the chart-v2 9-series confirmatory bucket;
  coord contributes development-tier L2/L3 readouts as a secondary.
- **Paper 2**: the density/caption-resistance trade-off is a reportable
  property of the coordinate construction, not a defect to hide.

## 5. Provenance

Frozen tree `data/hier_v1_dev_r2/` (render_rev `r2-footer-neutral`);
`reports/hier_coord_r2_rerender_v1.json`, `hier_r2_gate_readout_v1.*`,
`hier_r2_p23_readout_v1.*`, `hier_r2_ranking_readout_v1.*`,
`hier_r2_caption_stress_readout_v1.*`,
`hier_r2_attacker_gate_hier_coord_v1{,_seed20260818,_seed20260819}.json`,
`matcher_v3_rescore_v1.*`, `generator_census_v4.*`,
`hier_v1_prefreeze_cleanup_v1.md`.
