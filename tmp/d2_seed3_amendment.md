
---

## Amendment v1a — seed-3 extension (registered 2026-07-27, before seed-3 inference)

Seed-3 values opened with the three-seed summary (`reports/three_seed_summary_v1.*`),
so the same diagnostic is extended to the seed-3 lineages. **No statistic,
band, threshold, or interpretation changes**; only the model list grows.

Additional models (merged step-100 actors, index SHA256 pinned in the run
manifests):

- `a1_seed3_step100`: `checkpoints/pilot/mech_a1_real_seed3/global_step_100/actor/huggingface`
- `a2b_seed3_step100`: `checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100/actor/huggingface`

Additional cells (4): `a1_seed3_step100` × {real, gray, none} and
`a2b_seed3_step100` × {real}.

Pinned inputs for seed 3, taken from the registered readouts rather than
re-measured:

- Base cells unchanged (`real` 0.1747, `gray` 0.0899, `none` 0.0682) — the same
  frozen base under the same conditions on the same 601-row set.
- Published seed-3 step-100 values used only as checks:
  A1 real 0.4060 (reproduction check, ±0.01 tolerance, same rule as seeds 1–2);
  A2b none 0.1215 (the `none` term of the A2b secondary).

The registered primary statistic `RetainedGainBlind`, the bands
(a) ≤ 0.25, (b) 0.25–0.75, (c) ≥ 0.75, and the requirement that seeds agree on
a band before a branch is assigned all apply unchanged — now across three seeds
rather than two. If the seeds do not all fall in one band, no branch is
assigned and all three values are reported.
