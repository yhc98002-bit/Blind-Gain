# Registered: ST3-7B — the decisive Stage-3 7B pilot (v1) — **DRAFT, AWAITING PI RATIFICATION**

Drafted 2026-08-16 per the PI dispatch (item 6) and EXPERIMENT_TODO PART 5:
*"New decisive experiment (registration before launch): ST3-7B — two arms on
the HB training split, standard GRPO vs necessity-sampled intervention-group
reward; pre-committed method-paper / limits-paper branches per PAPER2 §5.
Launch order: after the two-seed R3 readout lands and HB P2 gates pass."*

**Status: DRAFT. This document does not authorize a launch.** Registration
merges are PI sign-offs (EXPERIMENT_TODO Part 3); the ratification line at the
end is unsigned. No launcher and no training configs exist for this stage.

## 1. Purpose

PAPER2 §5, quoted verbatim (the governing text):

> **Stage 3 — the decisive 7B pilot (registration before launch).** Motivated
> by C6: 7B real-image standard GRPO moves the primary anchor +0.025 —
> capacity is implicated where reward shape was not. Two arms on the HB
> training split: standard GRPO vs necessity-sampled intervention-group
> reward (C1+C2+C3). Pre-committed: IGPO content gain > standard's on the
> primary anchor and hierarchy L2/L3 → the method paper proceeds; otherwise →
> the limits paper ("resolvability and capacity govern; reward shape does
> not"), published as such. One pilot decides which paper this is.

Gate-1's branch reading (PI, 2026-08-16): the lever at 3B is reward
**resolvability**, not reward shape; Stage 3 at 7B is the method's
make-or-break. The Stage-2 3B ablation matrix is cancelled.

## 2. Arms (two, single node each; I17 baseline integrity applies)

| # | Arm | Reward | Data |
|---|---|---|---|
| 1 | `st3_std` | standard GRPO answer reward (as in C5's 7B recipe lineage) | HB training split |
| 2 | `st3_igpo` | necessity-sampled intervention-group reward — C1 sampling probability (never reward scaling, I1) + C2 joint intervention-group scoring with invariance groups present (I2–I5) + C3 premise-verified hierarchical reward | identical HB training split |

Backbone: Qwen2.5-VL-7B-Instruct, both arms; identical base checkpoint,
data, optimizer budget, and decoding-locked evaluation (I7). Member
presentation order randomized per rollout (I4). Mini-A5's
shared-group-uid broadcast-reward path and its advantage-tensor equivalence
test are the reference implementation for C2.

## 3. Training data — the HB training split

The **training bucket** of the hierarchical benchmark's program-level split as
registered in `registered_hier_benchmark_v1.md` §7 (scene-program-level
buckets; R19/R20 and the confirmatory bucket excluded, I6). The concrete
batch (family cells, group counts, Δq metadata for C1) is **pinned by
amendment at launch-gate time**, after HB P2 informativeness gates pass —
it cannot be pinned earlier because the gates decide which knob cells are
informative.

## 4. Matching (any violation invalidates the comparison)

Identical: base checkpoint hash, training items (scene-program set), total
optimizer steps, batch/rollout budget, save cadence, eval schedule, decoding
lock. Different: the reward function and C1's sampling distribution only.
Every deviation forced by the IGPO arm's group structure is recorded in the
deviations log with its st3_std counterpart stated.

## 5. Primary endpoints (pre-committed)

1. **Held-out content on the primary anchor** — R19 coordinate-register pair
   accuracy (lenient primary, strict co-reported), frozen instrument,
   Layer-A conditions; against the frozen base and between arms.
2. **Hierarchy L2 and L3** — per-layer accuracies and pair-role readouts
   (target-switch primary) on the HB development/confirmatory instrument per
   `registered_hier_benchmark_v1.md`; reported per layer, never averaged
   (I13).

Co-primary discipline (PAPER2 §3): competence and attribution are co-primary;
the VAG attribution readout requires the matched same-data blind control —
whether Stage 3 carries its own blind control arm or inherits A2b-lineage
controls is a **PI decision recorded at ratification**, flagged open here.

## 6. Pre-committed branches (bound from PAPER2 §5 — quoted verbatim in §1, restated here as the two branch readings)

- **IGPO content gain > standard's on the primary anchor AND hierarchy
  L2/L3** → the method paper proceeds.
- **Otherwise** → the limits paper — *"resolvability and capacity govern;
  reward shape does not"* — published as such.

One pilot decides which paper this is. The branch reading itself is the
PI's (PAPER2 §5 discipline); this registration only binds the endpoints and
the two readings.

## 7. Launch gates (ALL required before any optimizer step)

1. **Two-seed R3 readout landed** (`reports/m7_r3_readout_v2.*`).
2. **HB P2 informativeness gates passed** on base 3B per
   `registered_hier_benchmark_v1.md` §7.
3. **PI merge of this registration** (ratification below) with the
   launch-time amendment pinning the training batch, configs, seeds, GPU
   placement (single-node per arm), and storage plan.

Launchers fail closed on merged-at-HEAD (I9).

## 8. Explicitly out of scope

No Stage-2 3B matrix (cancelled 2026-08-16). No new render families. No
training on R19/R20 or any Layer-A/confirmatory item. No baseline hybrids
(I17): B-PR1/B-VPPO comparisons, if run, are separate registrations.

## Ratification

- PI sign-off: ____________________ (date: __________)  — **UNSIGNED DRAFT**

## Launch amendment 1 — coord-only split (2026-08-17, pre-commitment fired)

The registered fallback in the PI's dispatch 2026-08-16b — *"coord-only split
if chart-v2 fails its re-run gates twice"* — **has fired**. chart-v2 failed its
one-shot acceptance (`reports/hier_chart_v2_acceptance_v1.md`) and chart-v3,
the second and final attempt, failed on the dinov2 channel
(`reports/hier_chart_v3_acceptance_v1.md`). No third attempt was made.

**Training split, pinned here per §3:** the training bucket of
`hier_coord_v1` at the frozen r2 render, cells **n8 and n12** only (n20
excluded per EXPERIMENT_TODO PART 6), scene-program bucket `training`
([0,60)), generated at `data/hier_train_v1` (120 mother-items per role per
cell). No chart item is trained on. R19/R20 and the confirmatory bucket remain
excluded (I6, I11).

**Endpoints** are unchanged (§5): R19 held-out content on the primary anchor,
and hierarchy L2/L3 per-layer readouts — now on the coordinate confirmatory
bucket, with chart-v3 s9_low available as a development-tier secondary.

**Blind control**: inherited A2b-lineage controls, per the PI's ratification
answer; no third arm.

## Deviations log

- (none)
