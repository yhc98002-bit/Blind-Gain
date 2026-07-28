# M5 terminal readout — ladder rung R2

Rule: `docs/MAIN_PHASE_RULING_20260716.md` R1. Endpoint is **R19 geometry pair
accuracy** — the primary visual anchor, the only R19 task requiring search and
binding — at step 400 minus step 100, with an item-paired bootstrap 95% CI.

Artifact: `reports/m5_terminal_readout_v1.json`. n=600 pairs.

## Result

| | step 100 | step 400 | Δ | 95% CI |
|---|---|---|---|---|
| lenient pair acc | 0.4800 | 0.4133 | **-0.0667** | [-0.0933, -0.0400] |
| contract-strict | 0.4800 | 0.4133 | -0.0667 | [-0.0933, -0.0400] |

## Registered verdict: **FALLING**

The rule declares FALLING iff Δ ≤ −0.05 **and** the CI upper bound is below
zero. Both hold: Δ = -0.0667 and the interval is
[-0.0933, -0.0400], entirely negative. This is not a
borderline call and required no discretion.

**Step 400 is terminal. There is no extension or rerun under any outcome**, so
this is the R2 result as it stands.

## What it says

Extending RLVR from 100 to 400 steps does not build visual competence on the
certified anchor — it **erodes** it. The step-400 checkpoint scores 0.4133,
which is below not only its own step-100 value (0.4800) but also the **frozen
base** (0.4717): four times the training leaves the model worse on the primary
visual anchor than no RL training at all.

Two features make this hard to dismiss as noise or as a scoring artifact:

1. **The strict and lenient endpoints move identically** (both −0.0667). Every
   correct answer is contract-valid at both checkpoints, so the decline is
   answer content, not formatting or extraction. This matches the identity G0.4
   established: trained arms satisfy `acc_strict == acc_final`.
2. **The descriptive trajectory is monotone.** Overall R19 pair accuracy at
   steps 150 / 200 / 300 / 400 is 0.5600 / 0.5433 / 0.5383 / 0.5167. The
   endpoint does not wander; it declines steadily. Per the ruling these steps are
   **descriptive only and cannot select the endpoint** — they are reported here
   as trajectory context, not as evidence for the verdict.

## How it bears on the paper's thesis

This strengthens rather than complicates the readout-policy account. If RLVR
were acquiring visual distinctions, more of it should buy more competence on the
anchor. Instead the task reward keeps rising while the certified counterfactual
endpoint falls, which is what a policy optimising a proxy it can satisfy without
the image looks like when it is run for longer.

It also extends F6 (blind-reward corrosion) along the *time* axis: F6 shows blind
reward corroding grounding across training **conditions**; R2 shows the same
endpoint corroding across training **duration**, in the arm trained on real
images. The corrosion is not exclusive to information-starved arms.

**Scope.** One long-horizon run, one corpus, one scale. The verdict is about this
anchor arm's trajectory, not a general law about RLVR duration; §9 language locks
apply.
