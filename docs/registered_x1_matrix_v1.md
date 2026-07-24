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
