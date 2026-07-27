# Gate 0 — stratification analyses (G0.1–G0.4)

Required by `docs/EXPERIMENT_TODO.md` Part 2A and `docs/PAPER2_RESEARCH_DOC.md` §5.
Cached predictions only, no GPU. Artifact: `reports/gate0_stratification_v1.json`,
built by `scripts/build_gate0_stratification.py` and
`scripts/build_g02_headroom_control.py`.

**Provenance check.** Base per-item comes from the guarded-rescore runs the seed
readouts name as `geo_baselines`; on the 601-item eval split they reproduce the
registered step-0 values exactly — acc_final 0.1747,
acc_strict 0.0599, contract_valid
0.4393 against registered 0.1747 / 0.0599 / 0.4393.

**Condition discipline.** Each arm's own geo audit is its *matched* training
condition (A2b's is `none`, A2's is `gray`). Every Gate-0 question is about the
**image-present** gain, so all four analyses use the D3 crossed cells with the arm
evaluated under `real`, verified `status: complete` and `condition == real`. Using
the matched cells instead would have reported A2b's gain as −0.0605 rather than
+0.1287 — the same arithmetic error the D3 registration exists to prevent.

| arm | image-present gain | matched-condition gain |
|---|---|---|
| A1 real | +0.2435 [+0.2080, +0.2801] | +0.2435 |
| A2b no-image | +0.1287 [+0.0943, +0.1631] | -0.0605 |
| A2 gray | +0.1187 [+0.0854, +0.1520] | -0.0688 |
| A3 caption | +0.1747 [+0.1387, +0.2108] | +0.1398 |

A1's two columns agree because A1's matched condition *is* `real`, and its
+0.2435 reproduces the published three-seed gain exactly — an end-to-end check
that the join, the base source, and the crossed cells are all consistent.

## G0.1 — do the gains concentrate on high-Δq items?

Δq = q_real − q_blind per item, taken from the registered blind reward-opportunity
audit's own `q_i`. Terciles of Δq, mean per-item image-present gain in each:

| arm | low Δq | mid Δq | high Δq | Spearman ρ | perm p |
|---|---|---|---|---|---|
| A1 real | +0.149 (n=329) | +0.278 (n=121) | +0.422 (n=151) | +0.198 | 0.0005 |
| A2b no-image | +0.061 (n=329) | +0.121 (n=121) | +0.283 (n=151) | +0.192 | 0.0005 |

**Answer: yes, and for both arms.** The gain rises monotonically across Δq
terciles, ρ ≈ +0.19–0.20 with permutation p ≤ 0.0005. Improvement lands
preferentially where the image carried reward opportunity the blind model lacked.
**Consequence for Paper 2: H1 is supported and C1 (visual-necessity sampling)
earns its place in the method** — item selection on Δq targets exactly the region
where RLVR already delivers most of its gain, so concentrating sampling there is
justified by measurement rather than by intuition. Note the effect is present in
A2b too, so high-Δq items are not preferentially learned *because* the image was
shown during training.

## G0.2 — does A2b's image-present gain concentrate on low blind-solvability items?

*This analysis freezes Paper 1's title claim.*

`q_blind` is Jeffreys-smoothed, so items with no observed blind success sit at the
floor 0.1387. The split is therefore **blind-answerable**
(≥1 observed blind success, n=117) versus **not**
(n=484). Blind-answerable items are easier — base real
accuracy 0.2308 vs
0.1612 — so the contrast is
reported both raw and restricted to base-wrong items, where every arm faces an
identical 0→1 headroom.

| arm | all: blind-answerable | all: not | base-wrong: blind-answerable | base-wrong: not |
|---|---|---|---|---|
| A1 real | +0.3276 | +0.2231 | +0.4667 | +0.3218 |
| A2b no-image | +0.2764 | +0.0930 | +0.4259 | +0.1970 |
| A2 gray | +0.2735 | +0.0813 | +0.4296 | +0.1839 |
| A3 caption | +0.2393 | +0.1591 | +0.3704 | +0.2635 |

**Answer: no — it concentrates on blind-*answerable* items, the opposite of the
hypothesis, and the effect survives the headroom control.** Expressed as the share
of A1's gain that image-free training recovers:

- on blind-answerable items, A2b recovers **84%** of A1's gain;
- on items with no observed blind success, only **42%**.

Restricted to base-wrong items the same ordering holds (91% vs 61%), so this is
not a ceiling artifact. Both blind-trained arms show the steep version of the
pattern while A1 and A3 do not, which is the signature expected if blind training
can only capture the blind-attainable component.

**Consequence for the title claim.** The claim survives but acquires a scope
qualifier. Image-free RLVR does produce a real image-dependent gain on items that
*require* the image — +0.197 on base-wrong, not-blind-answerable items, which is
far from zero — so the gain is not merely generic text-side improvement. But it is
**disproportionately** the blind-attainable component: image-free training captures
most of what was reachable without pixels and only about half of what was not.
The honest headline is that roughly half the gain is image-free *on average*, with
the image-free share falling as the item's dependence on the image rises. This is
direct measured support for Paper 2's **H1**: reward opportunity attainable blind
is what image-free training harvests.

## G0.3 — overlap of the A1 and A2b newly-correct sets

Newly correct = base wrong and arm right, both evaluated image-present. Jaccard
against a permutation null that reshuffles A2b's newly-correct set among base-wrong
items:

| seed | A1 new | A2b new | ∩ | ∪ | Jaccard | null | p |
|---|---|---|---|---|---|---|---|
| 1 | 178 | 128 | 91 | 215 | 0.423 | 0.177 | 0.0001 |
| 2 | 176 | 113 | 84 | 205 | 0.410 | 0.161 | 0.0001 |
| 3 | 164 | 114 | 74 | 204 | 0.363 | 0.157 | 0.0001 |

**Answer: substantially overlapping policies, not identical ones.** Jaccard
0.363–0.423 against a null of 0.157–0.177, p ≤ 0.004 in all three seeds. Image-free
training fixes a large, reliably shared subset of the items image-present training
fixes — evidence that the two are moving much the same mechanism rather than two
unrelated ones — while roughly 60% of the union is claimed by only one arm, so they
are not interchangeable.

## G0.4 — answer gain vs format gain

AnswerGain = Δacc_final, StrictGain = Δacc_strict, FormatGain = StrictGain −
AnswerGain, all image-present, mean over three seeds:

| arm | answer gain | strict gain | format gain | contract-validity gain |
|---|---|---|---|---|
| A1 real | +0.2435 | +0.3583 | +0.1148 | +0.5430 |
| A2b no-image | +0.1287 | +0.2435 | +0.1148 | +0.5380 |
| A2 gray | +0.1187 | +0.2335 | +0.1148 | +0.5341 |
| A3 caption | +0.1747 | +0.2895 | +0.1148 | +0.5275 |

**Answer: the access-matrix result is not a formatting artifact, and the reason is
an identity rather than a coincidence.** Format gain is *exactly* +0.1148 for all
four arms. Every trained arm satisfies `acc_strict == acc_final` on every item —
once trained, every correct answer is contract-valid — so FormatGain collapses to
`base_acc_final − base_acc_strict` = 0.1747 − 0.0599 = 0.1148, a constant that
depends only on the frozen base. The format channel is saturated identically by all
four arms, including the two that never saw an image in training.

Therefore every between-arm contrast in the access matrix — the entire F1 result —
is format-free by construction: the formatting component cancels exactly in any
arm-minus-arm comparison. What differs between arms is answer content alone.
