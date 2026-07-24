# Registered X1 image-condition matrix (v1)

Committed verbatim from the PI dispatch of 2026-07-24; this block is the
registration and must be committed before first inference.

---

X1 — REGISTERED image-condition matrix (this block is the registration; commit it verbatim as
docs/registered_x1_matrix_v1.md before first inference):
Models: base + seed-1 step-100 checkpoints of A1/A2/A2b/A3. Items: all 1,200 R19 pairs.
Conditions per member: (1) correct image, (2) mismatched real image = a different pair's image
from the same template (fixed derangement, seeded 20260724, recorded per item), (3) paired-
counterfactual image = the twin member's image, (4) gray, (5) no-image. Layers: open-form
realization (locked contract, greedy) AND candidate-evidence ranking (frozen 16-candidate sets;
per-candidate mean-token logprob; margins, normalized entropy, top1−top2 gap). Registered
readings, pre-committed: (a) mismatched-real sharpening ≈ correct-image sharpening (margin
inflation ratio in [0.8, 1.25]) → image-presence gating; (b) correct ≫ mismatched (ratio > 1.25
with non-overlapping CIs) → content-specific evidence sharpening; (c) under condition (3), the
margin sign flips toward the twin's gold → direct content sensitivity (report flip rate).
Secondary from the same dumps: wrong-item vs right-item margin-inflation ratio per arm.
Report: reports/x1_image_condition_matrix_v1.md + machine JSON + audited artifact. No
interpretation beyond the registered readings.


---

## Addendum (PI dispatch 2026-07-24, committed before any X2 scoring)

X2 pre-committed interpretation ladder for hard-negative ranking pair-success (geometry,
base model): >= 0.75 -> the latent-competence finding ships at FULL strength as a Paper-1
co-headline ("a large fraction of task-relevant visual answer information is present
before RLVR and survives adversarial candidates; open-form generation realizes only ~47%
of it"). 0.55–0.75 -> mid-form: "substantial latent preference, partially candidate-
sensitive"; realization gap remains a major finding with the measured number. < 0.55 ->
the 91% is predominantly candidate-set structure; realization-gap demotes to a
measurement-methods finding. Whichever branch obtains is reported without renegotiation.
Additionally: "already perceived/understood" is PERMITTED as hypothesis language in
framing and discussion sections at all times; it becomes result language only on the
top branch plus premise-probe convergence (Track B1).
