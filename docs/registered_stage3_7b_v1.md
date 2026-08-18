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

---

## Launch amendment 2 — arm-2 group structure pinned to k=2 (2026-08-18)

Authority: §3, which states the concrete batch — *"family cells, **group
counts**, Δq metadata for C1"* — is pinned by amendment at launch-gate time.
Group size was never a ratified constant; k=4 was an implementation choice made
in `scripts/build_st3_train_corpus.py`, and this amendment revises it on
measured evidence before any arm-2 GPU time is spent.

### Evidence

Members of an intervention group are separate prompts sampled independently, so
the joint reward rate is exactly `q = prod_m p_m` and a group yields a GRPO
gradient with probability `1 - q^R - (1-q)^R`. Using the registered Δq `real`
pass (16 samples, T=1, base checkpoint, full 2880-row coverage):

* base per-member accuracy 0.2515 (`l3_a` 0.1980, `l3_b` 0.2061,
  `probe_a` 0.3036, `probe_b` 0.2982);
* at k=4, mean q = 0.0050 and only **2.41%** of groups can produce a gradient at
  R=5 — ~1.4 of the 60 groups per step, against 66.7% of prompts for arm 1;
* Mini-A5's k=2 CP arm — which §2 names as C2's reference implementation and
  which trained successfully — scores **42.2%** on identical code at the same R.

Arm 2 as previously implemented was therefore 17× below the working reference,
and would most likely have produced a false negative about the method.
Full record: `reports/st3_joint_feasibility_v1.md`.

### Pinned

Arm 2's reward group is **`(mother item, side)` with members `{l3, probe}`**,
k=2: a side's read counts only when that side's discovery probe was also correct
in the same rollout. This is the literal statement of C3 (premise-verified
hierarchical reward) and scores 0.2524 usable, 0.60× the Mini-A5 reference.

Unchanged: base checkpoint, training items (the same 720 mother items, now
contributing two reward groups each), total optimizer steps, batch and rollout
budget, save cadence, eval schedule, decoding lock, and C1's necessity sampling
(which remains a sampling probability only, I1).

### Deviation recorded against §2

C2's requirement that **both sides** of the counterfactual be correct in one
rollout is dropped from arm 2's **reward**. Both sides remain present and
group-adjacent in every batch, so invariance-group presence (I2–I5) is
unaffected, but **no claim about C2 at 7B may be read off this arm**. The
arm-1 counterpart of this deviation is: none — arm 1's member reward is
unchanged.

### Open for the PI

Testing the registered C2 × C3 k=4 reward as written requires a **shared warm
start** (~4 std steps, ≈40 min, both arms branching from that identical
checkpoint), which restores k=4 to ~0.75 usable and keeps §4 matching intact by
construction, but changes the base checkpoint — outside what §3 delegates. Not
taken; available as a third arm on request.
