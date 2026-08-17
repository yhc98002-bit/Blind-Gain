# Registered: Hierarchical benchmark v1 (Paper-2 core instrument) — Discover → Ground → Read

Authored 2026-08-16 per the PI dispatch of 2026-08-16 (item 4) and the
hierarchy plan **adopted 2026-08-12 as amended** (EXPERIMENT_TODO PART 5,
"GPT hierarchy plan = adopted 08-12 as amended (cue-ladder v2 superseded by
the L1 derivation)"). Contents follow EXPERIMENT_TODO §2C-HB (HB.0–HB.9) and
PAPER2_RESEARCH_DOC §4 Layer B. This registration merges **before any HB item
exists** (HB.0). The 2026-08-16 round executes **only §8 (the answer-balance
constraint) and its premise-v2 regeneration scope**; HB dev-batch generation
(§7 one-shot batches) is a separate later execution under this same document.

## 1. Families — two, and only two

- **`hier_coord_v1`** on the premise-v2 scene generator
  (`scripts/build_track4_premise_v2_dev_batch.py` lineage; renderer
  `src/fliptrack/build_v02.py`, frozen).
- **`hier_chart_v1`** on the chart-v08 renderer.

No further render families for v1 (PAPER2 §4 "Explicitly not built"). R19/R20
are never modified, regenerated, or trained on (I11); hierarchy items are
added alongside the frozen instrument, never replacing it.

## 2. Mother-item derivation (HB.1)

Every L3 scene auto-derives:
- **L2 — target oracle**: the correct target identity is given in the prompt.
- **L1 — location oracle**: a non-occluding cue marks the target
  (offset callout or out-of-data-region pointer; never on-point occlusion).

Identical across the three derivations: scene data, renderer, visual facts,
final answer, distractors, scene-program ID. **Only oracle information
varies.** `mother_item_id` links the three layers. Verifier obligations, each
with an adversarial fixture the buggy behavior fails (I10, I21):
(a) L1 cue ink pixel-disjoint from all data ink — mask intersection empty,
checked per render; (b) gold recomputed per layer from scene truth for the
question-named entity; (c) rendered-diff across L1/L2/L3 of one mother-item
shows only the cue region differing (L2/L3 images byte-identical); (d)
mother-item matching check — answers/distractors/scene hashes identical
across layers; (e) registered candidate sets + structured hard negatives
emitted per L2/L3 item at generation time (HB.5).

## 3. L3 relations (HB.2)

- Coordinate family canonical L3: **extremum discovery** (highest/lowest y,
  leftmost/rightmost).
- **Nearest-neighbor is the labeled hard tier**, at n=5 and n=8 — the
  premise-v2 full-run gates already forced n=5 (branch (c),
  `registered_track4_premise_v2_design_v1.md` §5), so nearest sits near floor
  at 3B and cannot carry the canonical tier.
- Chart family L3: argmax-at-x, then read the same series at another x.

## 4. Pair roles (HB.4)

target-switch (**primary L3 causal diagnostic**, PAPER2 §4) · target-stable
(isolates post-discovery behaviour) · invariance (specificity, anti-gaming).
Reported separately, never averaged (I13). Prior-conflict and binding-swap
remain exploratory generator cells outside the core taxonomy.

## 5. Probes and readouts (HB.5, HB.6)

Ranking layer ships with the items: registered candidate sets + structured
hard negatives per L2/L3 item (same-entity other-axis, neighbor value,
look-alike label, nearest gridline, twin's gold; symmetric composition).
Diagnosis without CoT: discovery probe (predicted target identity) +
per-layer accuracies + pair successes; registered failure patterns
L1✓L2✓L3✗ = discovery bottleneck; L1✓L2✗ = grounding bottleneck;
L1✗ = readout weak.

## 6. Difficulty-knob grids (pre-registered; no iteration beyond the grid)

- `hier_coord_v1`: `n_points ∈ {8, 12, 20}` × the margin knobs the premise-v2
  generator already carries (`MARGIN_A/B/D3 = 1.0`, `CHAINED_STAY_MARGIN =
  0.5` lineage values; recorded per cell in the build report).
- `hier_chart_v1`: `series ∈ {5, 9}` × crossing density. **Chart confirmatory
  cells keep 9-series density for caption resistance** (HB.7).

## 7. Development validation and split policy (HB.7, P1.7)

One-shot dev batches: **150 mother-items per family per knob cell**, generated
once per cell after this registration is at HEAD. Evaluation: base 3B, base
7B, and the existing standard-GRPO and CP Gate-1 checkpoints
(`mini_a5_std_seed1` / `mini_a5_cp_seed1`, terminal `global_step_120` — the
retained, §21-referenced endpoints), locked decoding (I7), open-form and
candidate-ranking readouts.

**Informativeness gates, quoted from EXPERIMENT_TODO HB.7, scored on base 3B
only:** monotone L1 > L2 > L3; L1 ∈ [0.60, 0.95]; L2 ∈ [0.20, 0.80];
L3 ≥ 0.05 in at least one pre-registered knob cell per family. Report
pass/fail per cell; no knob iteration beyond the registered grid.

Splits at the **scene-program level, never random item split** (I6):
training / development / confirmatory buckets per the premise-v2 lineage
hash-bucket rule (`SPLIT_BUCKETS = training [0,60) · development [60,80) ·
confirmatory [80,100)`); R19+R20 excluded from all three; no scene program
shared with Layer A or the confirmatory set.

**P3 freeze (HB.8) requires**: human audit (Richard), blind floor, caption
stress, attacker checks, difficulty calibration, verifier-operand audit,
mother-item matching checks, program-level split — none self-certified.
Note: the chart-v08 no-zoom audit (Richard) blocks chart-v08 freeze and P2 of
this build.

## 8. Registered answer-balance constraint (operative 2026-08-16)

**Motivation (E2 record, `reports/track4_premise_v2_gate_readout_v1.md`):**
blind final-member accuracy exceeded the registered 0.133 ceiling for all
five premise-v2 intervention types (0.1375–0.250) via a degenerate constant
answer meeting a **non-uniform gold distribution** — a generator answer-balance
property, not a visual leak (blind pair accuracy 0.000, collapse 1.000).

**Constraint (registered here; applies to every premise-v2 / `hier_coord_v1`
generation from this point, including the 2026-08-16 dev_v2 regeneration):**

> For each intervention type, over all causal-pair member golds (both sides
> pooled), **no single final-answer value may account for more than 0.10 of
> the members**. The answer-support size k per template is measured and
> recorded in the build report; if the support makes the 0.10 cap
> unattainable (k < 10), generation must widen the support — the cap is never
> relaxed.

Rationale for 0.10: it bounds the best blind constant-answer attacker at
0.10 member accuracy, 25% under the registered E2 ceiling of 0.133 (2/15),
with margin for finite-sample wobble. The E2 criterion itself is unchanged.
Enforcement is by deterministic constrained resampling at generation time,
verified by the batch verifier; the verifier check ships with an adversarial
fixture that a skewed-answer batch fails (I10).

**Regeneration scope (dispatch item 4, PI-decided 2026-08-16):** the five
E2-failing types are regenerated **one-shot** under this constraint into
`data/track4_premise_v2_dev_v2`, executing in the same one-shot the approved
E1 branch-(c) step to n=5 for the easy variant
(`chained_premise_easy` as primary carrier, `premise_transition_easy`
secondary), exactly per `registered_track4_premise_v2_design_v1.md` §5.
The v1 batch is untouched. E1 and E2 are re-read on the v2 batch with the
registered instrument; E3 (caption stress) re-runs on the regenerated types
only. E3's `chained_premise_easy` remains **indeterminate** until this lands;
both readings are reported and reading (a) is not relaxed.

## 9. What this registration does not do

It does not modify R19/R20, the premise-v2 v1 batch, any frozen scorer, or
the E2/E3/E4 criteria. It does not authorize training on any HB item: P4
method evaluation stays gated on Mini-A5's registered readout and the ST3-7B
launch gates (`registered_stage3_7b_v1.md`). It does not self-certify any
human gate.

## Amendment A1 (2026-08-16, pre-generation) — concrete grids and derivation
parameters pinned before any HB item exists

Registered here because §6's chart crossing-density knob and the per-cell
role allocation were named abstractly; HB.0 requires the grids concrete
before generation. Nothing below alters §1–§9; no item existed when this
amendment merged.

- **Pair-role allocation**: 150 mother-pairs per family per knob cell =
  **50 target-switch + 50 target-stable + 50 invariance**, reported
  separately per §4.
- **Coordinate family (`hier_coord_v1`)**: canonical L3 relation rotates
  deterministically over the four registered extremum kinds (largest y,
  smallest y, leftmost, rightmost; recorded per item). Read axis: y-extrema
  answer the target's x-coordinate; x-extrema answer the target's
  y-coordinate. Extremum-uniqueness margin: extremum-axis gap between top-1
  and top-2 ≥ 1 grid unit on BOTH sides of every pair (the premise-v2 margin
  lineage). Question forms — L3: "Consider the point with the <extremum>.
  What is its <read-axis>-coordinate?"; L2 and L1: "Point <T> has the
  <extremum>. What is the <read-axis>-coordinate of point <T>?" (identical
  L2/L1 text; L1 adds only the image cue).
- **Chart family (`hier_chart_v1`)**: L3: "Consider the series with the
  highest value at x = <xa>. What value does that series have at
  x = <xr>?"; L2/L1 name the series. xa ≠ xr, both interior (2..6 of the
  7-slot axis). Argmax-uniqueness margin at xa ≥ the cell's value-grid
  granularity, both sides. **Crossing-density cells** (measured, per the
  chart-v08 `adjacent_crossing_fraction` instrument, evaluated at the READ
  point xr): low = fraction ≤ 0.25; high = fraction ≥ 0.50; scenes outside
  the cell's band are resampled (a generation filter, not an item edit).
  Nine-series cells use a 3-entry additive extension of the chart-v08
  palette/linestyle/marker/label tuples (CVD-checked with the same CIE76
  instrument); the 6-entry originals are untouched.
- **L1 cue (both families)**: an offset pointer — line segment plus open
  arrowhead approaching the target from one of 8 compass directions,
  terminating outside the target's marker and label bounding boxes. The
  registered ink rule, checked per render (verifier (a)): every pixel the L1
  image changes relative to the L2 image must be background or plot-fill in
  the L2 image — the cue may not touch ANY existing ink (points, labels,
  lines, gridlines, axes, chrome). Direction search is deterministic;
  a scene with no passing direction is resampled, never force-drawn.
- **Discovery probe** (HB.6): one probe row per mother-pair at the L3 oracle
  level — coordinate family: "Which labeled point has the <extremum>?"
  (answers = target labels per side); chart family: "Which series has the
  highest value at x = <xa>?" (answers = series names per side).

## Amendment A2 (2026-08-16, pre-generation) — layer × role derivation matrix

Implementation of §2 surfaced a contradiction the source plan did not
address: a **target-switch** pair has different targets on its two sides, so
no single L2/L1 question can state the target identity truthfully for both
members — and re-targeting the question per side would change the side-B
answer relative to L3, violating the answers-identical-across-layers
obligation (§2(d)). Resolution, registered before any item exists:

- **L3 rows derive for all three roles** (target-switch · target-stable ·
  invariance). Target-switch remains the **primary L3 causal diagnostic**,
  exactly as §4 designates.
- **L2 and L1 rows derive for the side-stable roles only** (target-stable ·
  invariance), where the identity-given question is truthful for both
  members and answers are identical across the three layers. §2(c) is
  unchanged: L2/L3 images byte-identical; L1 differs only in the cue region.
- **Informativeness gates (§7)** are scored per layer on the **stable +
  invariance member accuracies** — a composition held constant across the
  three layers — so the monotone L1 > L2 > L3 comparison is like-for-like.
  L3 target-switch results are reported separately (per §4, never averaged).
- **Discovery probes** derive for all 150 mothers per cell (switch probes
  carry differing per-side golds — the discovery signal itself).
- Per-cell row counts: 150 L3 pairs + 100 L2 pairs + 100 L1 pairs +
  150 probe rows.

## Amendment A3 — pre-freeze cleanup (2026-08-17, PI review; before any re-render)

**Normative layer semantics** (PI wording, verbatim; classification is by the
capability actually required, never by filename or historical role):

- **L1 — Readout:** target location is given.
- **L2 — Grounding:** target identity is given, but the model must find it.
- **L3 — Target Discovery:** the model must first determine which target is
  relevant.

The discovery **probe** isolates the L3 selection step (gold = the target
identity). Pair roles against these definitions: **target-switch** is the L3
counterfactual discovery diagnostic and is deliberately NOT paired at L1/L2
(no truthful identity-given question exists for a switch pair — Amendment A2;
forcing such pairs would damage the counterfactual design). **target-stable**
exercises all three layers with one truthful identity; **invariance** is the
equal-answer control.

**Registered in-image text policy.** Each family draws exactly one title and
one layer-neutral encoding footer, pinned as registered strings
(`scripts/hier_v1_lib.py` `REGISTERED_TEXT`):

- `hier_coord_v1`: title "Coordinate Survey Register"; footer **"Each point
  is identified by its printed label."**
- `hier_chart_v1`: title "Multi-Series Measurement Trace"; footer "Each
  series is identified by its legend entry (color, line style, marker)."

In-image text must never state task procedure or name targets: the v1 coord
footer ("Locate the requested label, then read its coordinate from the
numbered axes.") stated the L3→L2 decomposition inside every layer's image
and is retired. Enforcement: the verifier's static policy check
(procedure-token / label / series-name screen) + exact `rendered_text`
provenance matching + a fixture pinning that the hier-owned coord renderer
differs from the frozen `build_v02` renderer only inside the footer strip.

**Render revision r2 (`r2-footer-neutral`).** The coord dev batch is
re-rendered from the RECORDED scenes into `data/hier_v1_dev_r2/` — no RNG,
no geometry/question/answer/swap/cue-parameter change; manifests differ from
v1 only in image/mask paths + hashes and provenance
(`render_rev`, `rendered_text`, v1 image hashes retained). The v1 tree is
kept untouched as the superseded render. Coord acceptance numbers for the
freeze are those measured on r2. Chart images are unchanged (footer already
layer-neutral); the ratified chart-v2 revision regenerates under this policy.

**Census staging rule.** The generator census assigns `capability_stage`
from the manifest rows' `layer` field where present (per-layer stages);
derived artifacts (attacker keys, candidate registries, caption-stress
releases) are staged `derived-artifact`; the doc-substring map is a last
resort with longest-needle-first matching (the v3 census's "chart" needle
shadowed "hier_chart" and mislabeled every hier chart variant L1 — corrected
in census v4; v3 retained with a correction note).

## Deviations log

- (none)
