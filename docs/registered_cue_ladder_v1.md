# Registered: CL — cue ladder on existing checkpoints (v1)

Registered 2026-07-27, **before any cue-ladder image is scored**. Serves
`docs/PAPER1_RESEARCH_DOC.md` §3 **F4b** and doubles as Paper 2 Track 1 (P1.1).
Inference only; no training.

**Labelled a post-hoc decomposition**, per F4b's own wording. It is registered in
advance of scoring so the readings are sealed, but it decomposes an effect that
has already been observed, and no rung result may be presented as a
pre-registered primary endpoint.

## Why now

`reports/f2d_template_decomposition_v1.md` found that both blind-trained arms
**decline on the primary visual anchor** (A2 gray −0.0422, A2b −0.0272, both CIs
excluding zero) while **rising on the oracle-localized readout control** (+0.0556,
+0.0233). Their flat overall R19 numbers are two real effects of opposite sign
cancelling. The natural reading is that blind-reward corrosion is specific to
search and binding, and that a cue supplying localization protects against it.

That reading makes a falsifiable prediction, which is what this ladder tests.

## Instrument

Four rungs rendered from the **same nine-series scene program** — identical
values, identical target series, identical target abscissa, identical seed — with
**only the annotation layer changing** (I12). The scene generator is
`generate_nine_series_chart_pairs` in `src/fliptrack/build_v02.py`; the renderer
is `src/fliptrack/render_chart_v08.py`, whose legend star and cue caption are the
entire annotation layer.

| rung | legend star | in-image caption | question text |
|---|---|---|---|
| `exact` | on the target series | "Read its value at x = N" | as R19 today |
| `region` | on the target series | abscissa **not** given | as R19 today |
| `none` | absent | absent | names the series **and** the abscissa |
| `decoy` | on a **non-target** series | "Read its value at x = N" | names the target series; **gold follows the question** |

`exact` reproduces the current R19 nine-series condition and acts as the
within-ladder anchor: if it does not reproduce the R19 numbers, the ladder build
is reported invalid and nothing else from it is read.

**Decoy gold follows the question, never the cue** (I12). The decoy rung is a
**stress condition** and is never averaged with the three ordinary rungs (I13).

Counterfactual pair structure, the frozen prompt contract `answer-tags-v1`, the
canonical-v2 parser, greedy decoding and `max_new_tokens` are all unchanged from
the R19 build. Both lenient and contract-strict scoring are reported (I7).

## Cells

Base plus all four arms at step 100 across three seeds (13 model cells) × four
rungs. Free GPUs only; trainer GPUs are never touched.

## Pre-committed readings

Let `Deficit(arm, rung) = Acc(A1, rung) − Acc(arm, rung)` for the blind arms
(A2 gray, A2b), on pair accuracy, averaged over seeds.

- **(a) Localization-specific corrosion.** If, for both blind arms,
  `Deficit(arm, none)` and `Deficit(arm, region)` each exceed
  `Deficit(arm, exact)` with non-overlapping paired item-level bootstrap CIs
  against the exact rung, the F2d reading is **confirmed**: blind-reward damage
  is specific to search and binding, and supplying localization removes it. F5 is
  then reported as a localization-layer harm rather than a diffuse one.
- **(b) Uniform deficit.** If the three deficits are mutually comparable
  (all pairwise CI overlaps include zero difference), the damage is **not**
  localization-specific and the F2d reading is **withdrawn** — the R19
  anchor/control split would then reflect something other than cue strength, and
  F2d is reported descriptively only.
- **(c) Intermediate.** Any other pattern is reported descriptively with no claim
  change, and the specific rung ordering is stated.

Independently of (a)/(b)/(c):

- **Cue reliance (decoy rung).** The fraction of responses matching the decoyed
  cue's value rather than the question's gold is reported per arm as
  `CueFollowRate`. **No directional prediction is registered.** A rise in
  `CueFollowRate` under training would indicate RLVR increasing reliance on
  annotation over instruction; a fall would indicate the opposite. Reported as a
  stress-condition finding either way, never folded into a capability score.
- **Rung monotonicity in the base model.** If the frozen base does not degrade
  from `exact` to `region` to `none`, the ladder is not measuring cue strength
  and (a)/(b) are void. This is a build-validity gate, checked first.

## Locks

- §9 language locks apply. "Search", "binding" and "localization" name
  measurement layers here, not cognitive states.
- Rungs are reported separately; no aggregate spans rungs, and the decoy rung is
  never averaged with the ordinary ones (I13).
- R19 and R20 are untouched. The ladder is a **new** track rendered alongside
  them and is never substituted for a frozen task (I11).
- Acceptance gates (caption stress, blind floor, attacker check, difficulty band)
  are **not** claimed here. Until they are run this track is usable for this
  registered decomposition only, and **not** for training or for release
  reporting (I14).
