# Seed-1 R19 Null Audit V1

Status:
- Independent machine audit: `pass` across 60 enumerated checks.
- Scientific interpretation and gate decisions remain outside this audit.

Evidence:
- Machine audit: `reports/pilot_4arm_seed1_r19_null_v1_audit.json`.
- The 36 `(arm, checkpoint, template/category)` keys are unique and cover
  exactly four arms, three checkpoints, and three frozen templates.
- Every observed/null/p-value is finite and bounded; the current frozen scorer
  hash matches the hash recorded before analysis.
- Shared step-0 cells are byte-value identical across arms within category.
- For all 12 arm/checkpoint chart cells, prediction counts sum to 600, shares
  sum to one, answer-conditioned denominators sum to 600, and every reported
  step-0 change recomputes exactly.
- Artifact hashes are pinned in the machine audit.

Problems:
- This is an accounting and reproducibility audit, not a mechanism test.

Decision:
- None. Downstream chart-delta figures must register the audited machine
  artifact as a hash-pinned input.
