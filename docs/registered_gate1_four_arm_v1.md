# Registered: Paper-2 Gate 1 — four-arm decomposition (v1)

Prepared 2026-07-27, **before the first optimizer step of any Gate-1 arm** (I9).
Serves `docs/PAPER2_RESEARCH_DOC.md` §5 Gate 1 and `docs/EXPERIMENT_TODO.md` §2E.

**Launch condition.** Gate 1 does not launch until (a) Mini-A5's two registered
arms complete and F7 is read out, and (b) a node is free under the one-RL-trainer-
per-node rule. This document exists so that, if F7 is positive, arms 3–4 launch
without registration lag — per the PI's decision to run two arms now and prepare
the four-arm registration in parallel.

## Arms

Four arms, answering **in sequence** whether each component earns its place.

| # | arm | data | selection | reward | question it answers |
|---|---|---|---|---|---|
| 1 | standard GRPO | ordinary items | uniform | answer-only | the baseline |
| 2 | paired-data GRPO | intervention-group data, flattened to single samples | uniform | answer-only | **is the data enough?** |
| 3 | necessity + answer-only | intervention-group data, flattened | Δq sampling | answer-only | **is item selection enough?** |
| 4 | full IGPO | intervention groups, scored jointly | Δq sampling | relational (C2) + premise-verified (C3) | **does the relational reward add?** |

Arm 2 isolates the data from the objective: it sees exactly the same rendered
material as arm 4 but scores each member independently, so any gain it shows is
attributable to data rather than to the intervention-group objective.

## Matching (any violation invalidates the comparison)

Identical across all four arms: corpus, prompt template, prompt contract
`answer-tags-v1`, rollout group size G, optimizer, learning-rate schedule, total
optimizer steps, total token budget, seed set, and evaluation harness build.
Arms differ **only** in the three factors tabled above.

Token budget is matched on **total tokens consumed**, not on step count, since
arm 4's groups contain more members per scene; if the two cannot be matched
simultaneously, steps are held equal and the token difference is reported as a
deviation with its size.

## Implementation invariants this registration binds

- **I1** — necessity enters as **sampling probability** ∝ f(Δq_i). It is *never*
  reward scaling: Δq is constant within a group and cancels exactly in GRPO's
  `(r − mean)/std`. The post-normalization loss-weight form is an ablation for
  Stage 2, not Gate 1.
- **I2** — relational rewards must vary **across rollouts within a group**.
- **I3** — group members are scored **jointly**; negative-control conditions live
  inside the group and are never scored separately.
- **I4** — member presentation order is randomized per rollout.
- **I5** — arm 4 trains causal and invariance groups together; causal-only is not
  a Gate-1 arm.
- **I15** — every group is validated by
  `src/train/intervention_group_schema.py` at load; the loader fails closed.
- **I16** — if any arm uses a premise warm start, an SFT-warm-start + standard-GRPO
  comparator is trained alongside, or every gain is attributable to the SFT.

**Advantage-tensor equivalence test.** Before arm 4's first optimizer step, the
shared-group-uid broadcast-reward path must reproduce standard GRPO's advantage
tensor exactly when the relational reward is replaced by the answer reward. The
readout is void if this test has not passed — it is the check that arm 4 differs
from arm 1 by the objective and nothing else.

## Success criteria

**Primary: held-out-template counterfactual pair accuracy.** Held out at the
**scene-program** level, never by random item split (I6).

Secondary, reported separately and never aggregated (I13): structured
hard-negative discrimination, binding swap, invariance specificity, prior
conflict.

**Margins are not a success criterion.** Paper 1's X2 ladder fired its bottom
branch — margin-style separations are substantially candidate-set structure — so
a Gate-1 arm that moves margins without moving pair accuracy has not succeeded.

**Chained premise is excluded from the Gate-1 criteria.** P0.1 fired registered
branch (b): base premise accuracy is 0.275 and the construct is under revision,
so chained items cannot discriminate between these arms at 3B. They are recorded
descriptively and carry no weight in the gate decision.

Both lenient and contract-strict scoring are reported for every criterion (I7).
G0.4 showed the format channel saturates identically across trained arms, so a
between-arm difference in the strict figure that is absent in the lenient one
would be anomalous and must be explained before the readout is accepted.

## Pre-committed branches (from PAPER2 §6, bound here to the arm numbering)

- **Arm 4 > arm 3 > arm 2 > arm 1** on the primary criterion, with non-overlapping
  paired item-level bootstrap CIs at each step → the full dependency chain is
  validated and the method proceeds as specified.
- **Arm 4 > arm 1, but arm 4 ≈ arm 3** → the relational reward adds nothing over
  necessity sampling; C2 is demoted and the method simplifies to the audit-driven
  recipe (C1 + C3).
- **Arm 2 ≈ arm 1** → the paired data alone is inert, which is the expected result
  and is what licenses attributing any arm-4 gain to the objective rather than to
  the rendering.
- **Arm 2 > arm 1 and arm 4 ≈ arm 2** → the gain is data, not method. Reported as
  such; the method contribution is withdrawn and the benchmark becomes the
  contribution.
- **Nothing moves the primary criterion, including arm 4** → published as *the
  limits of outcome-reward RL for visual acquisition*, per PAPER2 §6's final
  branch: diagnosis, systematic negative surface, representation-level boundary.

**Attribution constraint (co-primary B).** No branch above may be read as success
unless VAG is positive: real-image accuracy rises, blind accuracy does not
significantly fall, and the competence criterion rises jointly (I8). An arm whose
image-dependence grows only because its blind accuracy degraded has not
succeeded, and is reported as a corrosion result instead.

## What Gate 0 already contributes

G0.1 found that per-item gains rise monotonically across Δq terciles for both A1
and A2b (ρ +0.198 / +0.192, permutation p ≤ 0.0005). That is measured support for
C1's premise, obtained before any Gate-1 compute is spent: item selection on Δq
targets the region where RLVR already delivers most of its gain. Arm 3 tests
whether acting on that measurement helps; arm 3 ≈ arm 2 would mean the
concentration exists but is not actionable by sampling.
