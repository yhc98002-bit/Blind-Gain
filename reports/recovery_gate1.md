# Recovery Gate 1

Status:
- Corrected machine status: `fail`.
- Stage 0 proposal status remains `conditional`, not pass.
- Status is now the logical AND of enumerated sub-gates in `scripts/compute_recovery_gate1.py`.

Evidence:
- The 30-step GRPO engineering anchor completed on `an12` GPUs 0,1; it is not a published reproduction.
- FlipTrack V0.1 contains 300 pairs. P0.1 rescoring found Qwen2.5-VL-7B caption-only pair accuracy 0.5133 rather than the old 0.5167.
- The V0.1 path-based metadata attacker reached AUC 1.0; therefore `artifact_gate_v01_complete=false`.
- Dataset/license triage remains `partial`; therefore `dataset_license_triage_complete=false`.
- `tests/test_gate_logic.py` proves a pass is impossible while any enumerated sub-gate is false.
- Machine output: `reports/recovery_gate1.json`.

Problems:
- Required model/dataset license triage is incomplete.
- V0.1 is not artifact-robust and is superseded by the in-progress opaque V0.2 package.
- P0.2 parser agreement remains blocked because the recovery run did not preserve at least 300 usable generations.
- The recipe-scale P1.1 anchor is still running and has not produced its required curve.

Decision:
- Do not treat Recovery Gate 1 as passed.
- Keep the 30-step run labeled `engineering anchor`.
- Use V0.2, not sanitized V0.1 symlinks, for the corrected artifact gate.

Next actions:
- Finish and lint the V0.2 package, then run grouped artifact attackers on the actual release manifest.
- Complete the recipe anchor and V0.2 hardness scoring.
- Resolve required licenses and the ViRL39K loader path.
