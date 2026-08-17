# Hierarchical benchmark — pre-freeze cleanup report (2026-08-17)

*Response to the PI review directive: make the benchmark consistent with the
intended capability hierarchy (L1 readout — target location given; L2
grounding — identity given, model finds it; L3 discovery — model determines
which target is relevant), fix in-image instructions, audit layer labels by
required capability, keep the pair-role designs, add guards. Registration:
Amendment A3 in `docs/registered_hier_benchmark_v1.md`. No redesign beyond
the mandate; no training launched.*

## 1. What was wrong

1. **The coordinate footer stated the L2 task procedure inside every layer's
   image.** Every `hier_coord_v1` image (all layers, both sides) carried the
   frozen-renderer footer *"Locate the requested label, then read its
   coordinate from the numbered axes."* (`src/fliptrack/build_v02.py:1189` —
   an inline literal, inherited because `hier_v1_lib.py` reused the frozen
   coordinate-register renderer untouched). That is the L3→L2 decomposition
   handed over in-image: "the requested label" presupposes an
   identity-given question, which is exactly what L3 and the discovery probe
   withhold. Because L2/L3 images are byte-identical by design, the footer
   could not be layer-varied — it had to become layer-neutral. The chart
   footer ("Each series is identified by its legend entry (color, line
   style, marker).") was already encoding-only and is unchanged.
2. **Census stage labels were assigned by filename substring, and a
   shadowing bug mislabeled every hier chart variant.**
   `build_generator_census.py` matched template-id substrings
   first-match-wins; the generic `("chart", "L1")` needle preceded
   `("hier_chart", "L1/L2/L3")`, so all `hier_chart_v1_*` variants were
   staged **L1** with a doc attribution belonging to the flat chart-v08
   family (census v3 rows 101–149), while coord variants (which contain no
   generic needle) got L1/L2/L3. Stages were also per-template, never
   per-layer manifest.
3. **No automated check covered this class.** Layer checks were
   question-string-only; nothing anywhere inspected in-image text; and the
   standing question-operand audit's three gates all key on field names hier
   rows do not carry (`target_label`/`target_x` vs hier's
   `target_label_a/b`) — every hier row fell silently into its
   "no checkable operands" bucket, so the audit asserted **nothing** for the
   very families it was most needed on.

## 2. Layer-label audit (by capability actually required)

The item-level layer assignments are **correct** against the intended
hierarchy — the census column and the footer are what made variants look
misclassified:

| layer | coord question | chart question | capability |
|---|---|---|---|
| L3 | "Consider the point with the smallest y-coordinate. What is its x-coordinate?" | "Consider the series with the highest value at x = 5. What value does that series have at x = 3?" | discovery (identity withheld) |
| L2 | "Point V6 has the smallest y-coordinate. What is the x-coordinate of point V6?" | "The series Harbor has the highest value at x = 5. What value does Harbor have at x = 3?" | grounding (identity given, must be found among 8–20 labeled points / 5–9 styled lines) |
| L1 | = L2 question + non-occluding arrow cue | = L2 question + cue | readout (the cue marks the answer-bearing location: the coord target point; the chart target series' point at the READ x) |
| probe | "Which labeled point has the smallest y-coordinate?" | "Which series has the highest value at x = 5?" | the L3 selection step isolated (gold = identity) |

Pair roles, documented per the directive (registration A3): **target-switch**
is the L3 counterfactual discovery diagnostic and is deliberately not paired
at L1/L2 — a switch pair admits no single truthful identity-given question,
so forcing L1/L2 rows would damage the counterfactual design (Amendment A2's
resolution stands). **target-stable** exercises all three layers;
**invariance** is the equal-answer control. Preserved untouched: the coord
mother-item construction and the non-occluding L1 cue engine
(diagonal-first, ink-disjoint, pixel-verified).

## 3. What changed

1. **Footer neutralized, coord re-rendered as r2** — hier-owned renderer
   copy (`hier_v1_lib._render_hier_coordinate_register`; frozen module
   untouched for R19/premise reproducibility) with the layer-neutral footer
   **"Each point is identified by its printed label."**;
   `scripts/rerender_hier_coord_r2.py` re-rendered all 450 coord mothers
   from the RECORDED scenes into `data/hier_v1_dev_r2/` — no RNG: geometry,
   questions, answers, swap assignments, and L1 cue parameters read from the
   v1 manifests; re-drawn cues reproduce the recorded pixel counts exactly;
   2,100 images + masks; manifests differ from v1 only in image/mask
   paths+hashes and provenance (`render_rev: r2-footer-neutral`,
   `rendered_text`, v1 hashes retained). From-disk verification on r2:
   **0 problems**. Candidate registries rebuilt from r2 rows via the frozen
   registry builder — all 450 rows semantically identical to v1 (only image
   references differ). v1 tree untouched as the superseded render.
2. **Census v4** (`reports/generator_census_v4.{json,md}`; 162 manifests,
   52 families, 249 variants): stages now derive from the manifest rows'
   `layer` field (hier variants read L1 / L2 / L3 / L3-probe per manifest),
   attacker keys / candidate registries / caption releases are staged
   `derived-artifact`, and the doc map is a longest-needle-first last resort
   (shadowing bug dead, test-pinned). v3 kept; its hier stage rows are
   superseded.
3. **Guards added** (each with a fails-on-v1 fixture):
   - registered in-image text policy: per-family title+footer pinned in
     `REGISTERED_TEXT`; verifier screens for procedure tokens
     ("locate", "requested", "then read", "first find"), series names, and
     point-label patterns, and requires `provenance.rendered_text` to match
     the registered strings exactly (`tests/test_hier_footer_text_policy.py`
     — the v1 footer fails the screen);
   - pixel fixture: the hier coord renderer may differ from the frozen
     renderer only inside the footer strip;
   - hier gates in `audit_question_operands.py`: L3/probe must name neither
     side's target; L2/L1 must name exactly the shared identity, which must
     agree between sides (A2); hier rows can no longer fall into the
     unchecked bucket (`tests/test_question_operand_audit_hier.py`);
   - census staging fixtures (`tests/test_generator_census_stage.py`);
   - the permanent **file_size attacker** (dispatch 2026-08-16b; the 198/200
     PNG-size leak class) as a named univariate gate in
     `src/fliptrack/artifact_attackers.py` at the same folded ≤0.55 /
     CI-up ≤0.62 criterion (`tests/test_file_size_attacker.py`).
   All suites green (new fixtures + builder/operand/census/attacker suites).

## 4. Coordinate hierarchy — freeze readiness

All acceptance measurements were re-taken on the corrected r2 images
(`experiments/runs/hier_r2_*`; readouts `reports/hier_r2_*_v1.*`). For the
two freeze-candidate cells the footer change moved nothing materially —
every n8/n12 gate lands within 0.02 of its v1 value — so the v1 instruction
footer was doing no measurable work for the model there. **n20 is more
footer-sensitive**: L1 0.5300 (v1 0.5750, −0.0450) and L3 0.2800 (v1
0.3150, −0.0350); decoding is greedy, so these are real image-sensitivity
of the crowded 20-point scenes, not sampling noise — one more empirical
reason n20 sits in the exploratory hard tier.

- **Informativeness (HB.7, base 3B)**: n8 **0.7050 / 0.6300 / 0.4250**
  (L1/L2/L3; v1 deltas ≤ 0.02) and n12 **0.6550 / 0.6150 / 0.3300**
  (deltas ≤ 0.02) pass every cell gate; family L3 floor PASS; monotone
  L1 > L2 > L3 in all three cells. n20 fails only its L1 band under both
  renders (r2 0.5300 / v1 0.5750 vs the 0.60 bound) — consistent with its
  exploratory-hard-tier ruling (PART 6). L3 switch (reported separately):
  0.34 / 0.39 / 0.20.
- **Attacker gates (4 attackers incl. the new permanent file_size)**: pooled
  clean across the board — dinov2 0.5159, file_size **0.5092**,
  frequency_stat 0.5103, metadata 0.5136; every CI-upper ≤ 0.5954. The
  formal gate is false via exactly one per-template point: dinov2 **n12
  0.5569** (CI-up 0.5954). On v1 the sole violation was dinov2 **n20
  0.5577**. A threshold-grazing violation that jumps templates under a pure
  footer re-render is fold-noise around the 0.55 line, not a stable
  construction signature — reported as measured; the disposition (accept as
  noise, tighten, or re-fold) is a PI call.
- **Blind floors**: unchanged from v1 by construction (blind modes never see
  the real image) — coord L3 gray 0.1133–0.1367, no_image identical to four
  decimals, probes 0.0000 (r2 p23 readout).
- **Candidate ranking** (4 models × 6 registered configs, registries
  re-pinned to r2): L2 largely solvable (0.6403–0.9010 MRR), L3 drops in
  every cell (base 3B 0.4363–0.5009); base 7B leads all L3 cells
  (0.5686–0.7975); Gate-1 step-120 checkpoints stay within +0.08 of base 3B
  — no trained discovery, as in v1.
- **Caption stress (72B question-blind → base-3B QA, re-run on r2)**: family
  member accuracy **0.2200** (v1: 0.2367) — n8 0.30–0.39, n12 0.18–0.22,
  n20 0.08–0.15, vs blind floors 0.11–0.14. The footer removal did not
  collapse the caption channel: the modest leakage rides the captioner's
  transcription of point labels and positions, strongest at n8's sparse
  scenes. No registered HB caption ceiling exists yet — registering one is a
  freeze prerequisite (a premise-v2-style "blind floor + 0.10" reading would
  pass n12/n20 and fail n8; the choice is registration work, not mine).

**Verdict: the coordinate hierarchy is ready to freeze on the r2 render for
n8 and n12, subject to three PI-side items** — (1) the human audit (HB.8,
never self-certified; the r2 sample can be packaged on request), (2) the
dinov2-marginal disposition above, (3) a registered caption ceiling. n20
enters the freeze only as the exploratory hard tier per PART 6. The r2 tree
(`data/hier_v1_dev_r2/`) is the freeze basis; v1 is retained as the
superseded render.

## 5. Chart side — what remains unresolved

1. **The ratified chart-v2 revision is still to execute** (attacker-gate
   failure: switch edit unidirectional 200/200; low-cell PNG-size 198/200;
   pooled frequency 0.6957, s5_low 0.9819). It will regenerate under the
   corrected conventions from this cleanup (registered text policy,
   rendered_text provenance, per-layer census staging) plus the A3-pending
   symmetrized-switch + band-preserving-edit amendment. Note: direction
   symmetrization alone will NOT fix the size leak in low-crossing cells —
   any band-breaking edit adds ink; the revision needs small-magnitude
   switch edits (top-2 adjacency at the anchor x) and in-band stable edits.
2. **Low-cell L3 difficulty caveat**: in low-crossing cells the
   highest-at-xa series is the visually topmost line nearly everywhere, so
   L3 "discovery" is partially saliency; the highest 3B L3 ranking MRRs sit
   exactly in the attacker-flagged low cells (0.6395 / 0.5936 vs
   0.4428 / 0.4033 high). The chart-v2 re-run will show how much survives
   the leak fix.
3. **Chart caption resistance is confirmed** (caption member accuracy
   0.0413 vs blind 0.0000 — the 9-series rationale holds and 5-series is
   equally resistant on this batch).
4. **Human gates queued, never self-certified**: chart-v08 no-zoom audit
   (Richard — blocks chart-side freeze); census v4 review supersedes v3's
   hier rows; hier_chart review in the package remains diagnostic-only until
   chart-v2.

## 6. Artifacts

`data/hier_v1_dev_r2/` + `reports/hier_coord_r2_rerender_v1.json` ·
`reports/generator_census_v4.{json,md}` · Amendment A3 in
`docs/registered_hier_benchmark_v1.md` · guards in
`scripts/{hier_v1_lib,verify_hier_dev_batch,audit_question_operands,build_generator_census}.py`
+ 4 new test files · r2 re-measure runs `experiments/runs/hier_r2_*` ·
r2 attacker gate `reports/hier_r2_attacker_gate_hier_coord_v1.json` ·
blind diagnostics `reports/hier_blind_diagnostics_v1.{json,md}` ·
caption stress v1 `reports/hier_caption_stress_readout_v1.{json,md}` (+ r2
coord caption re-run).
