# Registered: M7 single-image restriction (amendment v2)

Amends `docs/registered_m7_heldout_split_v2.md` and
`docs/registered_m7_amendment_v1.md`. Registered 2026-07-28, **before the first
optimizer step of any M7 arm** (I9). No M7 arm has yet completed a training step.

## Why

M7's training recipe is deliberately the Geometry3K pilot recipe with only the
corpus changed — that is what makes R3 a second-corpus test of the same method
rather than a new experiment. Geometry3K is single-image, so the recipe carries
`max_prompt_length: 2048` with `max_pixels: 4194304`, i.e. roughly 5,350 vision
tokens for one image at the resolution cap.

ViRL39K is not single-image. Measured over the registered splits:

| images per row | train | heldout |
|---|---|---|
| 1 | 23,542 | 4,239 |
| 2 | 984 | 152 |
| 3 | 307 | 40 |
| 4 | 279 | 44 |
| 5 | 133 | 25 |
| 6–8 | 10 | 1 |

A single image at the resolution cap already exceeds the 2,048-token prompt
budget; eight cannot fit under any setting. Empirically, raising
`worker.rollout.limit_images` to 8 so that multi-image rows are servable caused
vLLM's worst-case multimodal memory profiling to kill a worker during
`actor_rollout_ref_init_model` (run
`m7_virl_a1_real_seed1_an12_20260728T100830Z`, `ncclRemoteError` reporting the
remote process exit).

So the registered corpus contains rows the registered recipe cannot serve. One
of the two has to move.

## Decision

**Restrict M7 to single-image rows.** `worker.rollout.limit_images` is set to 1.

This keeps the recipe **byte-identical to the Geometry3K pilot**, which is the
property R3 depends on: any difference in recovery between the corpora is then
attributable to the corpus, not to a retuned context window or a changed image
resolution. The rejected alternatives each break that:

- raising `max_prompt_length` changes a parameter that affects results;
- lowering `max_pixels` changes the visual input for **every** row, which is
  indefensible in a paper about visual information access;
- capping at 2 images still changes the split while leaving the memory risk.

## What this costs, stated exactly

Retained: **23,542 / 25,255 train rows (93.2%)** and **4,239 / 4,501 heldout
rows (94.2%)**. Dropped: 1,713 train and 262 heldout rows carrying 2–8 images.

**The registered primary estimand is unaffected.** M7's rank statistic runs over
joint `(source, category)` strata with at least 30 held-out items. Measured
before and after the restriction: **22 strata qualify under both**, and **zero
strata fall below the threshold**. The per-stratum table and the
recovery-tracks-`q_bar` prediction are therefore computed on the same 22 strata
that the original split would have used.

## Locks

- The prediction registered in `registered_m7_amendment_v1.md` — that recovery
  tracks stratum blind reward-opportunity `q_bar` — is **unchanged**, including
  its Informed-Prediction Disclosure.
- Strata, seeds, steps, reward, and every other recipe field are unchanged.
- The restriction is applied identically to all four arms and both seeds; no arm
  sees a different corpus.
- Any readout must state the restriction and the retained fractions above.
- New split files are written as `_v3` rather than overwriting `_v2`, so the
  original registered split remains inspectable.
