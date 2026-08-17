
---

## 11. Reflection — what the evidence adds up to

Written 2026-07-27, after C1, D2, D3 and the X-series. Registered language locks
apply: statements below are either registered results or explicitly marked as
hypothesis.

**1. The strongest single finding is that "blind training barely works" was
largely a measurement artifact.** Published recoveries (gray 6.6%, no-image
19.1% mean) compare each arm inside its own training condition. D3 crosses the
factors and the picture inverts: evaluated *with images*, the blind-trained arms
recover **42–57%** of A1's gain (registered branch (a), ratios 2.21–13.07, all
three seeds, both arms). Blind training learned considerably more than the
matched-condition figure implied — it simply had no channel to express it.

**2. Yet the image is required for expression, in every arm.** D2: only
12–17% of A1's gain survives removing the image at inference (three seeds,
registered band (a)). D3 shows the same for arms that never saw an image in
training — A2b scores 0.303 with images and 0.114 without. So the picture that
holds together is: RLVR improves something substantially condition-general,
**but realizing it requires visual input at test time**. That the training
signal could be image-free while the payoff cannot is the most surprising
structural result here.

**3. Whatever improves, it is content-bound, not presence-bound.** X1/X5: a
same-template image with the *wrong* content produces statistically zero margin
inflation in every arm and both seeds, while correct-image inflation is clearly
non-zero. Under the twin image, the twin's gold is preferred for ~95% of
members — including in the frozen base. The base model already tracks image
content closely; training sharpens margins on that existing signal.

**4. The headline dissociation survives, but weaker than first reported.** The
+0.2435 task gain is solid and is not a formatting artifact. The flat
counterfactual endpoint is *not* a passed control: it holds on lenient scoring
and collapses under contract-strict scoring, because A1 degrades answer-contract
compliance (0.9500 → 0.7367) and the fallback extractor masks it (§2). The
honest claim is a large task gain alongside a counterfactual endpoint that does
not move *when measured leniently*, with the measurement fragility disclosed.

**5. Costs are real and reproducible.** A2 gray's −0.045 geometry decline is
item-identifiable across seeds (Jaccard 0.724 vs null 0.098) and 97.6%
answer-deterministic, concentrated in nearest-gridline off-by-ones. Blind reward
does not merely fail to help; it corrodes specific, identifiable items.

**6. Two claims were downgraded by our own checks.** The 0.9067
latent-competence figure is predominantly candidate-set structure (X2 bottom
branch), and the three-seed equivalence verdict was overstated (§2, §9). Both
were found by adversarial re-derivation rather than by review.

**Hypothesis, not result (§7 locks):** these patterns are *consistent with*
RLVR improving evidence utilization and answer production on top of visual
representations the base model already has, rather than improving visual
extraction itself. The forced-choice and premise-probe evidence needed to
license that as a result has not been obtained.
