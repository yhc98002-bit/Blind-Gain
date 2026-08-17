
---

## 12. Gate 0 and Phase 0 — results, implementation, and what they imply

Added 2026-07-27 under the three-document authority (`EXPERIMENT_TODO.md`,
`PAPER1_RESEARCH_DOC.md`, `PAPER2_RESEARCH_DOC.md`). All of this section is
cached-prediction or CPU work; no result here consumed a trainer GPU.

### 12.1 A scorer defect that was silently voiding invariance items (P0.2)

`src/eval/fliptrack_metrics.py` scored every member as

    acc_final = gold_tier > other_tier and gold_tier > 0

On a pair whose two members share a gold — every invariance item — `gold_tier`
and `other_tier` are computed from the *same string*, so the comparison is never
true. A member answering the gold exactly scored **wrong**, and every match was
flagged ambiguous. It surfaced when the premise probe returned member accuracy
**0.000 for all five models**, including a base that scores 0.150 on the strictly
harder final question.

Fixed with an equal-gold branch (`gold_tier > 0`, ambiguity disabled — there is no
competing answer to discriminate against). Ships a 7-case adversarial fixture the
pre-fix code fails, two cases of which lock causal-pair discrimination unchanged.

**Blast radius is nil for Paper 1.** R19 contains **zero** equal-gold pairs and
rescores to 0.4717 lenient / 0.4433 strict, matching pinned exactly. The frozen
R20 scorer is byte-identical (I11). What *was* affected: B1's `style_twin` (14/14)
and `distractor_only` (16/16), which had been resting on a single-gold workaround
— precisely the situation P0.2 was written to end. Those must be rescored before
reuse.

*Principle:* a discriminative criterion and an invariance construct are
incompatible by construction. Any scorer that credits "your gold beats the other
gold" silently reports 0 on every item where the two golds coincide. The
`collapsed` field already carried the guard, so this was an oversight rather than
a design choice — which is exactly why it survived: the code looked right.

### 12.2 Premise probe, five separate numbers (P0.1) — registered branch (b)

Twenty `chained_premise` pairs, 40 members per cell, rescored with the fixed
scorer.

| cell | premise member | premise pair | premise transition | final member | final pair | reasoning \| correct premise |
|---|---|---|---|---|---|---|
| base | 0.275 | 0.200 | 0.200 | 0.150 | 0.000 | 0.273 (n=11) |
| A1 real s1 | 0.225 | 0.200 | 0.200 | 0.100 | 0.000 | 0.222 (n=9) |
| A1 real s2 | 0.175 | 0.150 | 0.150 | 0.075 | 0.000 | 0.000 (n=7) |
| A2b no-image s1 | 0.300 | 0.200 | 0.200 | 0.125 | 0.000 | 0.250 (n=12) |
| A3 caption s1 | 0.250 | 0.200 | 0.200 | 0.075 | 0.000 | 0.200 (n=10) |

Base premise accuracy **0.275** (95% Wald [0.137, 0.413]) fires registered branch
**(b)**: the construct is revised before release, and its 0.000 pair accuracy is
*uninformative about chaining* rather than evidence against it. The interval
straddles the 0.30 (b)/(c) boundary; the consequence is identical either way.

Three consequences for Paper 2:

1. **Premise extraction is the first bottleneck but not the only one.** Even among
   members whose premise was extracted correctly, the base completes the chain
   only 0.273 of the time. An easier premise curriculum alone would raise the
   first factor and leave the second largely untouched.
2. **C3 has signal here, but thin.** Final pair accuracy is 0.000 for every model
   while premise-level correctness is non-zero for 17.5–30.0% of members, so the
   hierarchical reward does expose a non-empty gradient where the answer-level
   reward exposes none — which is C3's stated rationale, now measured. But the
   premise factor is itself sparse, which is the Phase-2 gate condition.
3. **Premise-transition accuracy is uninformative by construction.** It equals
   premise pair accuracy in all five cells because B1 holds the premise invariant
   across the flip (the nearest point stays the same; only its coordinate moves).
   **Track 4 needs items whose premise itself changes**, or the metric can never
   do independent work.

No arm beats base on premise extraction (base 0.275 is the highest of five
cells). Directionally consistent with RLVR not improving acquisition, but n=40
makes it far too underpowered to claim; recorded as consistent, not as evidence.

### 12.3 Gate 0 (G0.1–G0.4)

**Implementation note that changes the numbers.** Each arm's own geo audit is its
*matched* training condition — A2b's is `none`, A2's is `gray`. Every Gate-0
question is about the **image-present** gain, so all four analyses use the D3
crossed cells with the arm evaluated under `real`. Using the matched cells would
have reported A2b's gain as **−0.0605** instead of **+0.1287**. Base per-item comes
from the guarded-rescore `geo_baselines`, which reproduce registered step-0
exactly (0.1747 / 0.0599 / 0.4393), and A1 image-present reproduces the published
+0.2435 — an end-to-end consistency check on the join.

**G0.1 — do gains concentrate on high-Δq items? Yes, for both arms.**

| arm | low Δq | mid Δq | high Δq | Spearman ρ | perm p |
|---|---|---|---|---|---|
| A1 real | +0.149 | +0.278 | +0.422 | +0.198 | 0.0005 |
| A2b no-image | +0.061 | +0.121 | +0.283 | +0.192 | 0.0005 |

H1 is supported and **C1 necessity sampling earns its place in the method**:
selection on Δq targets exactly where RLVR already delivers most of its gain. The
effect is present in A2b too, so high-Δq items are not preferentially learned
*because* the image was shown in training.

**G0.2 — does A2b's image-present gain concentrate on low blind-solvability
items? No — the opposite, and it survives a headroom control.**

`q_blind` is Jeffreys-smoothed, so the split is "≥1 observed blind success"
(n=117) vs none (n=484). Those groups differ in base accuracy (0.2308 vs 0.1612),
so the contrast is also run restricted to base-wrong items, where every arm faces
identical 0→1 headroom.

| arm | all: blind-answerable | all: not | base-wrong: answerable | base-wrong: not |
|---|---|---|---|---|
| A1 real | +0.3276 | +0.2231 | +0.4667 | +0.3218 |
| A2b no-image | +0.2764 | +0.0930 | +0.4259 | +0.1970 |
| A2 gray | +0.2735 | +0.0813 | +0.4296 | +0.1839 |
| A3 caption | +0.2393 | +0.1591 | +0.3704 | +0.2635 |

As a share of A1's gain, A2b recovers **84%** where blind reward opportunity
exists and **42%** where it does not (91% vs 61% restricted to base-wrong). Both
blind-trained arms show the steep version; A1 and A3 do not.

*This is the sharpest result of the round.* The title claim survives with a scope
qualifier it can carry honestly: image-free RLVR produces a real image-dependent
gain on items that genuinely require the image (+0.197, far from zero), so it is
not merely generic text-side improvement — but it is **disproportionately** the
blind-attainable component. Image-free training harvests most of what was
reachable without pixels and about half of what was not. This is direct measured
support for Paper 2's **H1**.

**G0.3 — A1 and A2b newly-correct sets.** Jaccard 0.363–0.423 against a
permutation null of 0.157–0.177, p ≤ 0.004 in all three seeds. Substantially
overlapping policies — the two are moving much the same mechanism — but ~60% of
the union belongs to only one arm, so they are not interchangeable.

**G0.4 — answer vs format. The access matrix is format-free by identity.**

| arm | answer gain | strict gain | format gain | contract-validity gain |
|---|---|---|---|---|
| A1 real | +0.2435 | +0.3583 | +0.1148 | +0.543 |
| A2b no-image | +0.1287 | +0.2435 | +0.1148 | +0.538 |
| A2 gray | +0.1187 | +0.2335 | +0.1148 | +0.534 |
| A3 caption | +0.1747 | +0.2895 | +0.1148 | +0.528 |

Format gain is *exactly* +0.1148 for all four arms — not a coincidence but an
identity. Every trained arm satisfies `acc_strict == acc_final` on every item, so
FormatGain collapses to `base_final − base_strict` = 0.1747 − 0.0599 = 0.1148, a
constant depending only on the frozen base. **The formatting component therefore
cancels exactly in any arm-minus-arm comparison**, so the entire F1 access matrix
is format-free by construction. What differs between arms is answer content alone.

*Principle:* training saturates the answer-contract channel to ceiling in every
arm, including arms that never saw an image. Contract compliance is not a visual
capability and does not discriminate between training conditions — it is a
one-time fixed offset the base model pays and every trained model recovers.

### 12.4 F2d — where the R19 movement lands, and a correction to PAPER1

Base rates by task:

| task | role | n | pair | strict pair | member |
|---|---|---|---|---|---|
| coordinate survey register | primary visual anchor | 600 | 0.4717 | 0.4433 | 0.6450 |
| header-cued verification table | saturated control / retention canary | 300 | **0.8667** | 0.1800 | 0.9000 |
| nine-series calibration trace | oracle-localized readout control | 300 | 0.4367 | 0.4200 | 0.6617 |

**Correction.** PAPER1 §5 describes the header-cued table as "saturated at 1.000
for every model including base" and unable to show improvement, and §3 F2 builds
its mechanism on that table contributing "nothing to any delta." Measured on R19
the base is **0.8667**, not 1.000, and it moves in *every* arm (+0.019 to +0.023;
A2 gray's interval excludes zero), contributing **18.7%** of A1's overall
movement. The retention-canary function still holds — nothing drops — but the
premise that it is pinned at ceiling and arithmetically inert is false and needs
correcting in both sections. Note also its lenient/strict split (0.8667 vs
0.1800): it is the R19 task most dependent on fallback extraction.

**The F2 mechanism survives the correction.** For A1: the oracle-localized readout
control moves **+0.0711** (CI [+0.0256, +0.1167], excludes zero) supplying **70%**
of overall movement, while the primary visual anchor — the only R19 task requiring
search and binding — moves **+0.0056** with an interval spanning zero, supplying
11%. The gain lands where localization has already been supplied by the cue.

**New finding: the blind arms separate the layers more sharply than A1 does.**

| arm | primary visual anchor | oracle-localized readout control |
|---|---|---|
| A2 gray | **−0.0422** [−0.0683, −0.0161] | **+0.0556** [+0.0100, +0.1011] |
| A2b no-image | **−0.0272** [−0.0522, −0.0017] | +0.0233 [−0.0200, +0.0678] |

Both blind-trained arms **decline on the search-and-binding anchor** with
intervals excluding zero while **rising on the cued readout control**. Their flat
overall R19 numbers (−0.0014, −0.0019) are not inertness — they are two real
effects of opposite sign cancelling inside an aggregate that should never have
been read as one capability score.

*This localizes F5.* Blind-reward corrosion is not diffuse damage; it is specific
to the task requiring a model to locate a label and bind it to a point, and it
coexists with genuine improvement where the target is already marked. A cue that
supplies localization is enough to protect a blind-trained model from its own
corrosion. That is a sharper statement of the utilization thesis than any overall
number can express, and it yields a **falsifiable prediction for the cue ladder
(F4b): the damage should appear at the search rungs and vanish at the exact-cue
rung.**

### 12.5 D3 TrainShare (PAPER1 §8 estimand)

| arm | s1 | s2 | s3 | pooled | 95% CI (paired item-level) |
|---|---|---|---|---|---|
| A2 gray | 0.507 | 0.527 | 0.424 | **0.487** | [0.383, 0.588] |
| A2b no-image | 0.572 | 0.493 | 0.518 | **0.528** | [0.424, 0.629] |
| A3 caption | 0.743 | 0.716 | 0.691 | **0.718** | [0.617, 0.821] |

Branch: **headline at full strength**, and not marginally — every interval lies
entirely above 0.35 (nearest lower bound 0.383) and all nine seed-arm values fall
in the same branch.

> **Ordering disclosure.** All 36 D3 cells were read under the ratio-based
> `registered_d3_condition_matrix_v1.md` *before* TrainShare was computed. This is
> a **declared post-hoc recomputation of already-read data**; it does not satisfy
> I9 and is not a sealed pre-registered reading. Reported because PAPER1 §8 names
> the estimand.

Read with G0.2, the pooled 0.53 is an average over a gradient (84% blind-
answerable, 42% not), not a constant.

### 12.6 Instrument determinism (unplanned)

The premise probe was accidentally launched twice. All five cells came out
**byte-identical** across the two independent runs — an unplanned confirmation
that the locked greedy decoding contract is reproducible end to end (I7).
