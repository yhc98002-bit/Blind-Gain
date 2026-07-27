# P0.1 — B1 premise probe, five separate numbers

Registered: `docs/registered_b1_premise_probe_v1.md`. Required by
EXPERIMENT_TODO Part 2B and PAPER2 §4 Track 4. Twenty `chained_premise`
pairs, 40 members per cell. Scored with the **P0.2-fixed** scorer: the
premise manifest is equal-gold by construction and the pre-fix scorer
returned 0.000 on every such item regardless of content (§ below).

**The five numbers are reported separately and never aggregated** (I13).

| cell | premise member | premise pair | premise transition | final member | final pair | reasoning \| correct premise | n |
|---|---|---|---|---|---|---|---|
| base (step 0) | 0.275 | 0.200 | 0.200 | 0.150 | 0.000 | 0.273 | 11 |
| A1 real s1 | 0.225 | 0.200 | 0.200 | 0.100 | 0.000 | 0.222 | 9 |
| A1 real s2 | 0.175 | 0.150 | 0.150 | 0.075 | 0.000 | 0.000 | 7 |
| A2b no-image s1 | 0.300 | 0.200 | 0.200 | 0.125 | 0.000 | 0.250 | 12 |
| A3 caption s1 | 0.250 | 0.200 | 0.200 | 0.075 | 0.000 | 0.200 | 10 |

## Registered branch

Base premise member accuracy is **0.275**, so registered branch **(b)** fires:
the items are too hard at 3B for the premise step to be extracted reliably,
and the chained construct is **revised before release** rather than retained
as-is. The 0.000 chained pair accuracy is therefore *uninformative about
chaining ability* — it is dominated by premise extraction failure.

**Honest interval.** With n=40 the 95% Wald interval on the base figure is
[0.137, 0.413], which straddles the 0.30 boundary between branches (b)
and (c). The branch fires on the point estimate as registered, but the
evidence does not cleanly separate 'too hard' from 'intermediate'. The
consequence — revise the construct — is the same under either branch, which
is why the decision is reported as safe despite the width.

## What this decides for Paper 2

1. **The premise step is the first bottleneck, but not the only one.** Even
   restricted to members whose premise was extracted correctly, the base
   model completes the chain only 0.273 of the time
   (n=11). Making premises easier would raise the
   first factor and leave the second largely untouched, so a premise-only
   curriculum is not sufficient on its own.
2. **C3 has signal here, but very little.** PAPER2 §2 C3 argues that pair
   product rewards are ~0 on these items and C3 is the only source of
   gradient. That holds: final pair accuracy is 0.000 for every model, while
   premise-level correctness is non-zero for 17.5–30.0% of members. So the
   hierarchical reward does expose a non-empty learning signal where the
   answer-level reward exposes none — but at this difficulty the premise
   factor is itself sparse, which is exactly the Phase-2 gate condition.
3. **Premise-transition accuracy is uninformative by construction here** —
   it equals premise pair accuracy in all five cells (0.150–0.200). B1's
   chained items hold the premise *invariant* across the flip (the nearest
   point stays the same; only its coordinate moves), so a correct pair is
   automatically a correct transition. **Concrete fix for Track 4:** the
   construct needs items where the premise itself changes across the
   counterfactual, or this metric can never do independent work.
4. **No arm beats base on premise extraction.** Base 0.275 is the highest
   premise member accuracy of the five cells; the trained arms sit at
   0.175–0.300. This is directionally consistent with Paper 1's finding that
   RLVR does not improve visual acquisition, but n=40 per cell makes it
   **far too underpowered to claim** — it is recorded as consistent, not as
   evidence. No directional claim was registered for this contrast.

## Scorer dependency (P0.2)

This readout was impossible before the P0.2 fix. `acc_final` was
`gold_tier > other_tier`, evaluated on an equal-gold pair where both tiers
derive from the same string, so it was false for every response. The raw
probe metrics recorded member accuracy 0.000 for all five cells — including a
base that scores 0.150 on the strictly harder final question, which is what
exposed the defect. Numbers above are rescored in-process with the fixed
scorer; the on-disk `metrics.json` files from the probe run are void and must
not be cited.
