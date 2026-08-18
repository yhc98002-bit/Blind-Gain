# ST3 arm 2 — the registered k=4 joint reward is below the trainable threshold

**Status:** pre-launch blocker, found before any arm-2 GPU time was spent.
**Date:** 2026-08-18. **Author:** agent. **PI decision requested** on the one
item flagged OPEN at the bottom; the rest is pinned under the authority
`registered_stage3_7b_v1.md` §3 already grants the launch-gate amendment.

## 1. What was measured and why

Arm 2 scores an intervention group with the PRODUCT of its members'
accuracies. Under GRPO a group's advantage is `(r - mean)/std` across that
group's rollouts, so a group whose rollouts **all** score 0 — or all score 1 —
contributes exactly nothing to the update. With group size `k` and per-member
accuracy `p`, the joint reward rate is `~p^k`. A correct hypothesis can
therefore be untestable for purely numerical reasons: the reward never fires
often enough to produce a gradient.

The members of a group are **separate prompts, sampled independently**, so this
needs no simulation. Given per-member `p`:

    q_g      = prod_m p_m                     expected joint reward of group g
    P(var)_g = 1 - q_g^R - (1 - q_g)^R        chance g yields any gradient at R rollouts

`p_m` is taken from the registered Δq `real` pass (16 samples, T=1, base
checkpoint, full 2880-row coverage) — the same measurement C1's necessity
weights are built from. **No new GPU time was required for any number here.**

Scripts: `scripts/diagnose_st3_joint_feasibility.py`,
`scripts/st3_joint_design_options.py`.
Machine-readable: `reports/st3_joint_feasibility_v1.json`,
`reports/st3_joint_design_options_v1.json`,
`reports/mini_a5_joint_feasibility_v1.json`.

## 2. The finding

Base per-member accuracy on the ST3 training corpus (Qwen2.5-VL-7B-Instruct):

| member | mean p | items with p = 0 |
|---|---|---|
| `l3_a`   | 0.1980 | 10.8% |
| `l3_b`   | 0.2061 | 10.7% |
| `probe_a`| 0.3036 |  1.3% |
| `probe_b`| 0.2982 |  2.5% |
| **all**  | **0.2515** | |

At k=4 the product collapses: mean `q` = **0.0050**, median 0.0022. At R=5
rollouts only **2.41%** of groups can produce any gradient — about **1.4 of the
60 groups in a step**. The matched arm-1 member reward has 66.7% of prompts
usable (~160 of 240). **Arm 2 would start with 1/41st of arm 1's usable signal.**

### The anchor: our own working precedent

The registration names Mini-A5's broadcast-reward path as *the reference
implementation for C2*. That arm trained successfully. Scored by identical
code at the same R=5:

| | Mini-A5 CP arm (k=2, 3B) — trained | ST3 arm 2 (k=4, 7B) — as registered |
|---|---|---|
| base member p | 0.3517 | 0.2515 |
| mean joint q | 0.1733 | 0.0050 |
| median joint q | 0.0781 | 0.0022 |
| groups with any gradient | **42.2%** | **2.4%** |
| signal vs its own member arm | 0.63× | 0.04× |

ST3 arm 2 as specified sits **17× below the design the registration itself
cites as the working reference**. Two causes compound: the group grew from k=2
to k=4, and the ST3 task is harder at base (L3 items at p≈0.20).

Had this launched, arm 2 would very likely have underperformed arm 1 and the
honest reading would have been "IGPO does not buy hierarchy" — when the actual
cause is that a 4-way product at p=0.25 is numerically dead. That is a wrong
conclusion about the method, drawn from ~16 GPU-hours.

### Related observation: arm 1 saturates early

The same shadow logs show arm-1 training accuracy climbing **0.269 → 0.974 by
step 19** of a planned 100, with format compliance saturating separately within
2 steps (0.879 → 1.000). This is genuine task accuracy, not a format artifact.
Steps ~20–100 of arm 1 carry little gradient. Worth the PI's attention when
reading arm-1's endpoint: the training split is easy for a member reward even
though it is hard for a joint one.

## 3. Options, scored on the same measurement

| candidate arm-2 grouping | mean q | groups that can learn | vs Mini-A5 |
|---|---|---|---|
| **A. k=4 joint, as registered** (C2 × C3) | 0.0050 | 0.0241 | 0.06× |
| **B. k=2 per-side premise gate** (C3) | 0.0623 | **0.2524** | 0.60× |
| **C. k=2 counterfactual pair** (C2) | 0.0477 | 0.1960 | 0.46× |
| D. k=4 at R=16 rollouts | 0.0050 | 0.0711 | 0.17× |
| E. member reward (arm 1 baseline) | 0.2515 | 0.6669 | 1.58× |

D is rejected on two grounds: still 6× below the reference, and it would break
§4's identical rollout budget.

A warm start would rescue the registered k=4 reward outright — at member
p = 0.70 it reaches 0.746 usable, the healthiest number in this document — but
that changes the base checkpoint, which §4 fixes as identical and which §3 does
**not** delegate to me. Flagged OPEN below rather than taken.

## 4. What is being pinned, and under what authority

§3 states the concrete batch — *"family cells, **group counts**, Δq metadata for
C1"* — is **pinned by amendment at launch-gate time**. Group structure is
therefore a launch-gate parameter, not a ratified constant; k=4 was an
implementation choice made in `build_st3_train_corpus.py`, not a PI ruling.

**Pinned: option B — the k=2 per-side premise gate.** The reward group becomes
`(mother item, side)` with members `{l3, probe}`; the read counts only when that
side's discovery probe was also right in the same rollout. Reasons:

1. It is the highest-signal viable option (0.2524, 0.60× the working reference).
2. It is the literal statement of C3 — "the answer counts only when the premise
   (which target is relevant) was itself identified" — which is the *new*
   mechanism Paper 2 needs. Option C is a 7B replication of Mini-A5's already
   demonstrated counterfactual pair.
3. k=2 reduces exactly to the pinned binary implementation, which
   `tests/test_hier_group_scoring.py::test_binary_case_matches_the_pinned_implementation`
   asserts against `src/train/cp_grouping.py` row by row.

**Cost, recorded honestly:** C2's requirement that *both sides* of the
counterfactual land in the same rollout is dropped from the **reward**. Both
sides remain present and group-adjacent in every batch, so I2–I5 invariance-group
presence is unaffected — but the both-sides product is not part of arm 2's
objective under this pinning, and any claim about C2 at 7B must not be read off
this arm.

## 5. OPEN — PI decision

The only way to test the registered C2 × C3 k=4 reward as written is a **shared
warm start**: run a short std warmup (~4 steps, ≈40 min) and branch *both* arms
from that identical checkpoint, which restores k=4 to ~0.75 usable and keeps §4
matching intact by construction. It deviates from "base checkpoint =
Qwen2.5-VL-7B-Instruct", which is outside what §3 delegates.

Say the word and it runs as a third arm; otherwise arm 2 proceeds as pinned in
§4 above.

## 6. Status

- Arm 1 (`st3_std_seed1_7b_an29_20260818T013741Z`) is **running and unaffected** —
  valid under every option here, and the source of the warm checkpoint if §5 is
  taken. No arm-2 GPU time has been spent.
- Arm 2 is blocked on arm 1 regardless, by the one-ramping-trainer-per-node rule.
